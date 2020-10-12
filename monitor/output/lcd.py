import importlib.util
import time

try:
    importlib.util.find_spec("RPi.GPIO")
    import RPi.GPIO as GPIO
except ImportError:
    """
    import FakeRPi.GPIO as GPIO
    OR
    import FakeRPi.RPiO as RPiO
    """
    import FakeRPi.GPIO as GPIO  # noqa

# Define some device constants
LCD_WIDTH = 16  # Maximum characters per line
LCD_CHR = True
LCD_CMD = False

LCD_LINE_1 = 0x80  # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0  # LCD RAM address for the 2nd line

# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005


class RPiLcd:
    def __init__(
        self,
        gpio_lcd_rs=7,
        gpio_lcd_e=8,
        gpio_lcd_d4=25,
        gpio_lcd_d5=24,
        gpio_lcd_d6=23,
        gpio_lcd_d7=18,
    ) -> None:
        self._gpio_lcd_rs = gpio_lcd_rs
        self._gpio_lcd_e = gpio_lcd_e
        self._gpio_lcd_d4 = gpio_lcd_d4
        self._gpio_lcd_d5 = gpio_lcd_d5
        self._gpio_lcd_d6 = gpio_lcd_d6
        self._gpio_lcd_d7 = gpio_lcd_d7

        self._lcd_init()

    def set_line_txt(self, txt, line_no):
        self._lcd_string(txt, LCD_LINE_1 if line_no == 1 else LCD_LINE_2)

    def _lcd_init(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)  # Use BCM GPIO numbers
        GPIO.setup(self._gpio_lcd_e, GPIO.OUT)  # E
        GPIO.setup(self._gpio_lcd_rs, GPIO.OUT)  # RS
        GPIO.setup(self._gpio_lcd_d4, GPIO.OUT)  # DB4
        GPIO.setup(self._gpio_lcd_d5, GPIO.OUT)  # DB5
        GPIO.setup(self._gpio_lcd_d6, GPIO.OUT)  # DB6
        GPIO.setup(self._gpio_lcd_d7, GPIO.OUT)  # DB7

        # Initialise display
        self._lcd_byte(0x33, LCD_CMD)  # 110011 Initialise
        self._lcd_byte(0x32, LCD_CMD)  # 110010 Initialise
        self._lcd_byte(0x06, LCD_CMD)  # 000110 Cursor move direction
        self._lcd_byte(0x0C, LCD_CMD)  # 001100 Display On,Cursor Off, Blink Off
        self._lcd_byte(0x28, LCD_CMD)  # 101000 Data length, number of lines, font size
        self._lcd_byte(0x01, LCD_CMD)  # 000001 Clear display
        time.sleep(E_DELAY)

    def _lcd_byte(self, bits, mode):
        # Send byte to data pins
        # bits = data
        # mode = True  for character
        #        False for command
        GPIO.output(self._gpio_lcd_rs, mode)  # RS

        # High bits
        GPIO.output(self._gpio_lcd_d4, False)
        GPIO.output(self._gpio_lcd_d5, False)
        GPIO.output(self._gpio_lcd_d6, False)
        GPIO.output(self._gpio_lcd_d7, False)
        if bits & 0x10 == 0x10:
            GPIO.output(self._gpio_lcd_d4, True)
        if bits & 0x20 == 0x20:
            GPIO.output(self._gpio_lcd_d5, True)
        if bits & 0x40 == 0x40:
            GPIO.output(self._gpio_lcd_d6, True)
        if bits & 0x80 == 0x80:
            GPIO.output(self._gpio_lcd_d7, True)

        # Toggle 'Enable' pin
        self._lcd_toggle_enable()

        # Low bits
        GPIO.output(self._gpio_lcd_d4, False)
        GPIO.output(self._gpio_lcd_d5, False)
        GPIO.output(self._gpio_lcd_d6, False)
        GPIO.output(self._gpio_lcd_d7, False)
        if bits & 0x01 == 0x01:
            GPIO.output(self._gpio_lcd_d4, True)
        if bits & 0x02 == 0x02:
            GPIO.output(self._gpio_lcd_d5, True)
        if bits & 0x04 == 0x04:
            GPIO.output(self._gpio_lcd_d6, True)
        if bits & 0x08 == 0x08:
            GPIO.output(self._gpio_lcd_d7, True)

        # Toggle 'Enable' pin
        self._lcd_toggle_enable()

    def _lcd_toggle_enable(self):
        # Toggle enable
        time.sleep(E_DELAY)
        GPIO.output(self._gpio_lcd_e, True)
        time.sleep(E_PULSE)
        GPIO.output(self._gpio_lcd_e, False)
        time.sleep(E_DELAY)

    def _lcd_string(self, message, line):
        # Send string to display
        message = message.ljust(LCD_WIDTH, " ")

        self._lcd_byte(line, LCD_CMD)

        for i in range(LCD_WIDTH):
            self._lcd_byte(ord(message[i]), LCD_CHR)
