#include <xc.h>
#include <stdio.h>
#include "uart.h"
#include "traffic.h"
#include <string.h>

void UART_Init(void) {
    SPBRG = 25;       // Baud rate 9600 for 4MHz clock
    BRG16 = 0;        // 8-bit baud rate generator
    BRGH = 1;         // High baud rate
    SYNC = 0;         // Asynchronous mode
    SPEN = 1;         // Enable serial port
    TXEN = 1;         // Enable transmitter
    CREN = 1;         // Enable receiver (for GUI commands)
    PIE1bits.RCIE = 1; // Enable receive interrupt
}

void UART_TxChar(char data) {
    while (!TXIF);    // Wait for transmit buffer ready
    TXREG = data;     // Send data
}

void UART_TxString(const char* str) {
    while (*str) {
        UART_TxChar(*str++);
    }
}

void UART_TxTrafficState(void) {
    char buffer[40]; // Giảm từ 50 xuống 40
    sprintf(buffer, "%d,%d,%d,%d,%d,",
            mode,
            (int)RED1, (int)YELLOW1, (int)GREEN1, countdown_NS);
    sprintf(buffer + strlen(buffer), "%d,%d,%d,%d\n",
            (int)RED2, (int)YELLOW2, (int)GREEN2, countdown_EW);
    UART_TxString(buffer);
}