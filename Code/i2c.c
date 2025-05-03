#include "i2c.h"

void i2c_init(void)
{

    SSPCONbits.SSPM3 = 1;
    SSPADD = 0x09;
    SSPCONbits.SSPEN = 1;
}

void i2c_start(void) { 
    uint16_t timeout = 10000; // Timeout 10000 chu kỳ 
    SSPCON2bits.SEN = 1; 
    while (SSPCON2bits.SEN && timeout) { 
        timeout--; 
    } 
    if (timeout == 0) { 
        SSPCONbits.SSPEN = 0; // Reset I2C 
        SSPCONbits.SSPEN = 1; 
    } 
}

void i2c_stop(void) { 
    uint16_t timeout = 10000; 
    SSPCON2bits.PEN = 1; 
    while (SSPCON2bits.PEN && timeout) { 
        timeout--; 
    } 
    if (timeout == 0) { 
        SSPCONbits.SSPEN = 0; 
        SSPCONbits.SSPEN = 1; 
    } 
}

uint8_t i2c_write(uint8_t u8Data) { 
    uint16_t timeout = 10000; 
    PIR1bits.SSPIF = 0; 
    SSPBUF = u8Data; 
    while (PIR1bits.SSPIF == 0 && timeout) { 
        timeout--; 
    } 
    if (timeout == 0) { 
        SSPCONbits.SSPEN = 0; 
        SSPCONbits.SSPEN = 1; 
        return 1; // Lỗi 
    } 
    return SSPCON2bits.ACKSTAT; 
}

uint8_t i2c_read(uint8_t u8Ack) { 
    uint16_t timeout = 10000; 
    uint8_t tmp;
    SSPCON2bits.RCEN = 1;
    while (SSPCON2bits.RCEN && timeout) {
        timeout--;
    }
    if (timeout == 0) {
        SSPCONbits.SSPEN = 0;
        SSPCONbits.SSPEN = 1;
        return 0; // Lỗi
    }
    tmp = SSPBUF;
    SSPCON2bits.RCEN = 0;
    if (u8Ack) {
        SSPCON2bits.ACKDT = 1;
    } else {
        SSPCON2bits.ACKDT = 0;
    }

    SSPCON2bits.ACKEN = 1;
    timeout = 10000;
    while (SSPCON2bits.ACKEN && timeout) {
        timeout--;
    }
    if (timeout == 0) {
        SSPCONbits.SSPEN = 0;
        SSPCONbits.SSPEN = 1;
    }

    return tmp;
}

void i2c_repeat_start(void) { 
    uint16_t timeout = 10000; 
    SSPCON2bits.RSEN = 1; 
    while (SSPCON2bits.RSEN && timeout) { 
        timeout--; 
    } 
    if (timeout == 0) { 
        SSPCONbits.SSPEN = 0;
        SSPCONbits.SSPEN = 1; 
    } 
}
