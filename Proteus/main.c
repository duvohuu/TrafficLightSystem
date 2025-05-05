#include <xc.h>
#include "pic16f887.h"
#include "traffic.h"
#include "lcd_i2c.h"
#include <string.h>
#include "uart.h"


#define _XTAL_FREQ 4000000

volatile uint8_t tick_500ms = 0;
volatile uint8_t last_mode = -1;
volatile uint8_t road1_flag = 0;
volatile uint8_t road2_flag = 0;


void System_Init(void) {
    // Cấu hình chân Digital
    ANSEL = 0;
    ANSELH = 0;

    // PORTA: Output cho đèn
    TRISA = 0x00;
    PORTA = 0x00;

    // PORTB: Input nút nhấn
    TRISB = 0b00000111;
    PORTB = 0x00;

    // PORTC, PORTE: Output
    TRISC = 0x00;
    PORTC = 0x00;
    TRISE = 0x00;
    TRISCbits.TRISC3 = 1; // SCL
    TRISCbits.TRISC4 = 1; // SDA

    // Reset tất cả đèn giao thông
    RED1 = GREEN1 = YELLOW1 = 0;
    RED2 = GREEN2 = YELLOW2 = 0;
}

void Interrupt_Init(void) {
    // Cấu hình ngắt ngoài RB0
    INTCONbits.INTE = 1;
    OPTION_REGbits.INTEDG = 1;

    // Cấu hình Timer1 
    T1CON = 0b00110001; // Prescaler 1:8
    TMR1 = 3036; // Cho 50ms
    PIR1bits.TMR1IF = 0;
    PIE1bits.TMR1IE = 1;

    // Cho phép ngắt toàn cục
    INTCONbits.PEIE = 1;
    INTCONbits.GIE = 1;
}

// Ngắt toàn cục
void __interrupt() ISR(void) {
    if (PIR1bits.RCIF) {
        if (RCSTAbits.OERR || RCSTAbits.FERR) {
            RCSTAbits.CREN = 0; RCSTAbits.CREN = 1;
        }
        while (PIR1bits.RCIF) {
            char dummy = RCREG;
            (void)dummy;
        }
        static char buffer[8];
        static uint8_t index = 0;
        char data = RCREG;
        if (data < 32 && data != '\n') {
            index = 0;
            PIR1bits.RCIF = 0;
            return;
        }
        if (data == '\n') {
            buffer[index] = '\0';
            if (strcmp(buffer, "M") == 0) {
                mode = (mode + 1) % 3;
                exitsign = 1;
                timer_counter = 0;
            } else if (mode == 1) {
                if (strcmp(buffer, "R1") == 0) {
                    road1_flag = 1;
                } else if (strcmp(buffer, "R2") == 0) {
                    road2_flag = 1;
                }
            }
            index = 0;
            __delay_ms(100);
        } else if (index < 7) {
            buffer[index++] = data;
        } else {
            index = 0;
        }
        PIR1bits.RCIF = 0;
    }

    if (PIR1bits.TMR1IF) {
        PIR1bits.TMR1IF = 0;
        TMR1 = 3036; 
        tick_500ms++;
        if (tick_500ms >= 2) { 
            tick_500ms = 0;
            timer_counter++;
        }
    }

    if (INTCONbits.INTF) {
        INTCONbits.INTF = 0;
        __delay_ms(50);
        mode = (mode + 1) % 3;
        exitsign = 1;
        timer_counter = 0;
    }
}

// Hàm main
int main(void) {
    System_Init();
    UART_Init();
    Interrupt_Init();
    I2C_Master_Init();
    LCD_Init(0x4E);
    while (1) {
        if (last_mode != mode) { 
            LCD_Clear();
            LCD_Set_Cursor(1, 1);

            switch (mode) {
                case 0: LCD_Write_String("Auto Mode"); break;
                case 1: LCD_Write_String("Midnight Mode"); break;
                case 2: LCD_Write_String("Manual Mode"); break;
                default: LCD_Write_String("Unknown Mode"); break;
            }

            last_mode = mode; // Cập nhật lại
        }
        switch (mode) {
            case 0: 
                Auto_Mode_Timer(); 
                break;
            case 1: 
                Midnight_Mode_Timer(); 
                break;
            case 2: 
                Manual_Mode(); 
                break;
            default: mode = 0; break;
        }
    }
}
