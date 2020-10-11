from Adafruit_SSD1306 import SSD1306_128_32
from PIL import Image, ImageDraw, ImageFont

# Raspberry Pi pin configuration:
from typing import List

DC = 23
SPI_PORT = 0
SPI_DEVICE = 0
PADDING = -2
LINE_HEIGHT = 20


class RpiOled:
    def __init__(self) -> None:
        self._disp = SSD1306_128_32(rst=None)
        # Initialize library.
        self._disp.begin()
        # Clear display.
        self._disp.clear()
        self._disp.display()

        # Create blank image for drawing.
        # Make sure to create image with mode '1' for 1-bit color.
        self._width = self._disp.width
        self._height = self._disp.height
        self._image = Image.new("1", (self._width, self._height))

        # Get drawing object to draw on image.
        self._draw = ImageDraw.Draw(self._image)

        self._font = ImageFont.load_default()
        # Alternatively load a TTF font.  Make sure the .ttf font file
        # is in the same directory as the python script!
        # Some other nice fonts to try: http://www.dafont.com/bitmap.php
        # font = ImageFont.truetype('Minecraftia.ttf', 8)

        self._top = PADDING
        self._bottom = self._height - PADDING

        self._clear_screen()

    def _clear_screen(self):
        # Draw a black filled box to clear the image.
        self._draw.rectangle((0, 0, self._width, self._height), outline=0, fill=0)

    def update_display(self, lines: List[str]):
        self._clear_screen()

        # write all the lines
        for idx, line in enumerate(lines):
            y_pos = self._top + (idx * LINE_HEIGHT)
            self._draw.text((0, y_pos), line, font=self._font, fill=255)

        # Lastly, actually write the thing out
        self._disp.image(self._image)
        self._disp.display()
