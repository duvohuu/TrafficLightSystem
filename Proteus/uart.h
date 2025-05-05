#ifndef UART_H
#define UART_H

#include <stdint.h>

void UART_Init(void);
void UART_TxChar(char data);
void UART_TxString(const char* str);
void UART_TxTrafficState(void);

#endif