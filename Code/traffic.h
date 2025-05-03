#ifndef TRAFFIC_H
#define TRAFFIC_H

#include <stdint.h>
#include <xc.h> 

// Các thông số thời gian
#define GREEN1_TIME   10
#define GREEN2_TIME   15
#define YELLOW_TIME  3

// Định nghĩa chân đèn giao thông
#define GREEN1   RA0  
#define YELLOW1  RA1  
#define RED1     RA2         
#define GREEN2   RA3  
#define YELLOW2  RA4    
#define RED2     RA5     

// Các biến toàn cục
extern volatile uint16_t timer_counter;
extern volatile uint8_t system_state;
extern volatile uint8_t exitsign;
extern volatile uint8_t mode;
extern volatile uint8_t countdown_NS; 
extern volatile uint8_t countdown_EW; 
extern volatile uint8_t road1_flag;
extern volatile uint8_t road2_flag;

// Các hàm điều khiển đèn
void Auto_Mode_Timer(void);
void Midnight_Mode_Timer(void);
void Manual_Mode(void);
void Opposite_State(void);
void Display_Countdown(uint8_t number1, uint8_t number2);
void ShiftOut_1Byte(uint8_t data);
void Clear_Display(void);

#endif
