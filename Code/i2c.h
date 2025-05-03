#ifndef I2C_H_
#define I2C_H_

#include <xc.h>
#include <stdint.h>

void i2c_init(void);
void i2c_start(void);
void i2c_repeat_start(void);
void i2c_stop(void);
uint8_t i2c_write(uint8_t u8Data);
uint8_t i2c_read(uint8_t u8Ack);

#endif
