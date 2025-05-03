#include <xc.h>
#include "pic16f887.h"
#include "traffic.h"

// Biến toàn cục
volatile uint16_t timer_counter = 0;
volatile uint8_t system_state = 0;
volatile uint8_t exitsign = 0;
volatile uint8_t mode = 0;
volatile uint8_t countdown_NS = 0;
volatile uint8_t countdown_EW = 0;

static const uint8_t led7seg_digits[10] = {
    0xC0, // 0
    0xF9, // 1
    0xA4, // 2
    0xB0, // 3
    0x99, // 4
    0x92, // 5
    0x82, // 6
    0xF8, // 7
    0x80, // 8
    0x90  // 9
};

void Opposite_State(void) {
    RED2 = GREEN1;
    GREEN2 = RED1;
}

// Auto Mode
void Auto_Mode_Timer(void) {
    switch (system_state) {
        case 0: // Road1 Green
            RED1 = 0; GREEN1 = 1; YELLOW1 = 0;
            YELLOW2 = 0;
            Opposite_State();
            countdown_EW = (GREEN1_TIME > timer_counter) ? (GREEN1_TIME - timer_counter) : 0;
            countdown_NS = countdown_EW + YELLOW_TIME + 1;
            if (timer_counter > GREEN1_TIME) {
                timer_counter = 0;
                system_state = 1;
            }
            break;

        case 1: // Road1 Yellow
            GREEN1 = 0; YELLOW1 = 1;
            YELLOW2 = 0;
            countdown_EW = (YELLOW_TIME > timer_counter) ? (YELLOW_TIME - timer_counter) : 0;
            countdown_NS = countdown_EW;
            if (timer_counter > YELLOW_TIME) {
                timer_counter = 0;
                system_state = 2;
            }
            break;

        case 2: // Road2 Green
            RED1 = 1; GREEN1 = 0; YELLOW1 = 0;
            YELLOW2 = 0;
            Opposite_State();
            countdown_NS = (GREEN2_TIME > timer_counter) ? (GREEN2_TIME - timer_counter) : 0;
            countdown_EW = countdown_NS + YELLOW_TIME + 1;
            if (timer_counter > GREEN2_TIME) {
                timer_counter = 0;
                system_state = 3;
            }
            break;

        case 3: // Road2 Yellow
            GREEN2 = 0; YELLOW2 = 1;
            YELLOW1 = 0;
            countdown_NS = (YELLOW_TIME > timer_counter) ? (YELLOW_TIME - timer_counter) : 0;
            countdown_EW = countdown_NS;
            if (timer_counter > YELLOW_TIME) {
                timer_counter = 0;
                system_state = 0;
            }
            break;
    }

    if (exitsign) {
        exitsign = 0;
        timer_counter = 0;
        system_state = 0;
    }

    // Hiển thị đếm ngược 
    Display_Countdown(countdown_EW, countdown_NS);
}

// Manual Mode 
void Manual_Mode(void) {
    Clear_Display();
    if (RB1 == 1 || road1_flag == 1) {
        RED1 = 0; GREEN1 = 1; YELLOW1 = 0; YELLOW2 = 0;
        Opposite_State();
        road1_flag = 0;
    } else if (RB2 == 1 || road2_flag == 1) {
        RED1 = 1; GREEN1 = 0; YELLOW1 = 0; YELLOW2 = 0;
        Opposite_State();
        road2_flag = 0;
    }

    if (exitsign) {
        exitsign = 0;
        timer_counter = 0;
    }
}

// Midnight Mode
void Midnight_Mode_Timer(void) {
    Clear_Display();  
    RED1 = 0; GREEN1 = 0; RED2 = 0; GREEN2 = 0; 
    if (timer_counter >= 1) {
        YELLOW1 = !YELLOW1;
        YELLOW2 = !YELLOW2;
        timer_counter = 0;
    }
    if (exitsign) {
        exitsign = 0;
        timer_counter = 0;
    }
}

// ShiftOut
void ShiftOut_1Bit(uint8_t bitVal) {
    RC1 = bitVal ? 1 : 0;
    RC0 = 1; __delay_us(1);
    RC0 = 0; __delay_us(1);
}

void ShiftOut_1Byte(uint8_t data) {
    for (int8_t i = 7; i >= 0; i--) {
        ShiftOut_1Bit((data >> i) & 0x01);
    }
}

// Dispay Countdown
void Display_Countdown(uint8_t countdown_NS, uint8_t countdown_EW) {
    uint8_t tens_NS = countdown_NS / 10;
    uint8_t ones_NS = countdown_NS % 10;
    uint8_t tens_EW = countdown_EW / 10;
    uint8_t ones_EW = countdown_EW % 10;

    ShiftOut_1Byte(led7seg_digits[ones_EW]);
    ShiftOut_1Byte(led7seg_digits[tens_EW]);
    ShiftOut_1Byte(led7seg_digits[ones_NS]);
    ShiftOut_1Byte(led7seg_digits[tens_NS]);

    RC2 = 1;
    __delay_us(1);
    RC2 = 0;
}

// Clear display
void Clear_Display(void) {
    for (int i = 0; i < 8; i++) {
        ShiftOut_1Byte(0xFF);  
    }
    RC2 = 1;
    __delay_us(1);
    RC2 = 0;
}
