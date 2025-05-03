#include "i2c.h" 
#include "i2c_lcd.h"

#define _XTAL_FREQ 4000000

void My_I2C_Init(void) { 
	i2c_init(); 
}

void I2C_Write(uint8_t u8Address, uint8_t *pu8Data, uint8_t u8Length) { 
	uint8_t i; 
	i2c_start(); 
	i2c_write(u8Address); 
	for (i = 0; i < u8Length; ++i) { 
		i2c_write(pu8Data[i]); 
	} 
	i2c_stop(); 
}

void I2C_Read(uint8_t u8Address, uint8_t *pu8Data, uint8_t u8Length) { 
	uint8_t i; 
	i2c_start(); 
	i2c_write(u8Address); 
	for (i = 0; i < u8Length - 1; ++i) { 
		pu8Data[i] = i2c_read(0); 
	} 
	pu8Data[i] = i2c_read(1); 
	i2c_stop(); 
}

static uint8_t u8LCD_Buff[8]; 
static uint8_t u8LcdTmp;

#define MODE_4_BIT 0x28 
#define CLR_SCR 0x01 
#define DISP_ON 0x0C 
#define CURSOR_ON 0x0E 
#define CURSOR_HOME 0x80

static void I2C_LCD_Write_4bit(uint8_t u8Data); 
static void I2C_LCD_FlushVal(void); 
static void I2C_LCD_WriteCmd(uint8_t u8Cmd);

static void I2C_LCD_FlushVal(void) { 
	uint8_t i; 
	for (i = 0; i < 8; ++i) { 
		u8LcdTmp >>= 1; 
		if (u8LCD_Buff[i]) { 
			u8LcdTmp |= 0x80; 
		} 
	} 
	I2C_Write(I2C_LCD_ADDR, &u8LcdTmp, 1); 
}

void I2C_LCD_Init(void) { 
	uint8_t i; 
	I2C_LCD_Delay_Ms(50); 
	My_I2C_Init(); 
	for (i = 0; i < 8; ++i) { 
		u8LCD_Buff[i] = 0; } 
		I2C_LCD_FlushVal(); 
		u8LCD_Buff[LCD_RS] = 0; 
		I2C_LCD_FlushVal(); 
		u8LCD_Buff[LCD_RW] = 0; 
		I2C_LCD_FlushVal(); 
		I2C_LCD_Write_4bit(0x03); 
		I2C_LCD_Delay_Ms(5); 
		I2C_LCD_Write_4bit(0x03); 
		I2C_LCD_Delay_Ms(1); 
		I2C_LCD_Write_4bit(0x03); 
		I2C_LCD_Delay_Ms(1); 
		I2C_LCD_Write_4bit(MODE_4_BIT >> 4); 
		I2C_LCD_Delay_Ms(1); 
		I2C_LCD_WriteCmd(MODE_4_BIT); 
		I2C_LCD_WriteCmd(DISP_ON); 
		I2C_LCD_WriteCmd(CURSOR_ON); 
		I2C_LCD_WriteCmd(CLR_SCR); 
}

static void I2C_LCD_Write_4bit(uint8_t u8Data) { 
	if (u8Data & 0x08) { 
		u8LCD_Buff[LCD_D7] = 1; 
	} 
	else { 
		u8LCD_Buff[LCD_D7] = 0; 
	} 
	if (u8Data & 0x04) { 
		u8LCD_Buff[LCD_D6] = 1; 
	} 
	else { 
		u8LCD_Buff[LCD_D6] = 0; 
	} 
	if (u8Data & 0x02) { 
		u8LCD_Buff[LCD_D5] = 1; 
	} 
	else { 
		u8LCD_Buff[LCD_D5] = 0; 
	} 
	if (u8Data & 0x01) { 
		u8LCD_Buff[LCD_D4] = 1; 
	} 
	else { 
		u8LCD_Buff[LCD_D4] = 0; 
	} 
	u8LCD_Buff[LCD_EN] = 1; 
	I2C_LCD_FlushVal(); 
	u8LCD_Buff[LCD_EN] = 0; 
	I2C_LCD_FlushVal(); 
}

void LCD_WaitBusy(void) { 
	char temp; uint16_t timeout = 10000; // Timeout 10000 chu kỳ
	u8LCD_Buff[LCD_D4] = 1;
	u8LCD_Buff[LCD_D5] = 1;
	u8LCD_Buff[LCD_D6] = 1;
	u8LCD_Buff[LCD_D7] = 1;
	I2C_LCD_FlushVal();
	u8LCD_Buff[LCD_RS] = 0;
	I2C_LCD_FlushVal();
	u8LCD_Buff[LCD_RW] = 1;
	I2C_LCD_FlushVal();
	do {
		u8LCD_Buff[LCD_EN] = 1;
		I2C_LCD_FlushVal();
		I2C_Read(I2C_LCD_ADDR + 1, &temp, 1);
		u8LCD_Buff[LCD_EN] = 0;
		I2C_LCD_FlushVal();
		u8LCD_Buff[LCD_EN] = 1;
		I2C_LCD_FlushVal();
		u8LCD_Buff[LCD_EN] = 0;
		I2C_LCD_FlushVal();
		timeout--;
		if (timeout == 0) break; // Thoát nếu timeout
	} while (temp & 0x08);
}

static void I2C_LCD_WriteCmd(uint8_t u8Cmd) { 
	LCD_WaitBusy(); 
	u8LCD_Buff[LCD_RS] = 0; 
	I2C_LCD_FlushVal(); 
	u8LCD_Buff[LCD_RW] = 0; 
	I2C_LCD_FlushVal(); 
	I2C_LCD_Write_4bit(u8Cmd >> 4); 
	I2C_LCD_Write_4bit(u8Cmd); 
}

void LCD_Write_Chr(char chr) { 
	LCD_WaitBusy(); 
	u8LCD_Buff[LCD_RS] = 1; 
	I2C_LCD_FlushVal(); 
	u8LCD_Buff[LCD_RW] = 0; 
	I2C_LCD_FlushVal(); 
	I2C_LCD_Write_4bit(chr >> 4); 
	I2C_LCD_Write_4bit(chr);
}

void I2C_LCD_Puts(char *sz) { 
	while (1) { 
		if (*sz) { 
			LCD_Write_Chr(*sz++); 
			__delay_us(10);
		} 
		else { break; } 
	} 
}

void I2C_LCD_Clear(void) { 
	I2C_LCD_WriteCmd(CLR_SCR); 
	__delay_ms(2);
}

void I2C_LCD_NewLine(void) { 
	I2C_LCD_WriteCmd(0xc0); 
}

void I2C_LCD_BackLight(uint8_t u8BackLight) { 
	if (u8BackLight) { 
		u8LCD_Buff[LCD_BL] = 1; 
	} 
	else { 
		u8LCD_Buff[LCD_BL] = 0; 
	} 
	I2C_LCD_FlushVal(); 
}