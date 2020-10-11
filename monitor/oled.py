from os import path
from typing import List

from Adafruit_SSD1306 import SSD1306_128_64
from monitor.util import console_log
from PIL import Image, ImageDraw, ImageFont

# Raspberry Pi pin configuration:
DC = 23
SPI_PORT = 0
SPI_DEVICE = 0
PADDING = -2
LINE_HEIGHT = 8


class RpiOled:
    def __init__(self) -> None:
        self._disp = SSD1306_128_64(rst=None)
        # Initialize library.
        self._disp.begin()
        # Clear display.
        self._disp.clear()
        self._disp.display()
        self._line_heights = [8, 10, 10]

        # Create blank image for drawing.
        # Make sure to create image with mode '1' for 1-bit color.
        self._width = self._disp.width
        self._height = self._disp.height
        self._image = Image.new("1", (self._width, self._height))
        console_log(f"Detected display H/W [{self._height}/{self._width}]")
        # Get drawing object to draw on image.
        self._draw = ImageDraw.Draw(self._image)

        # self._font = ImageFont.load_default()
        # Grabbed font from: http://www.dafont.com/bitmap.php
        self._font = ImageFont.truetype(
            f"{path.dirname(__file__)}/Retron2000.ttf", LINE_HEIGHT
        )

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
            line_height = self._line_heights[idx]
            y_pos = self._top + (idx * line_height)
            self._draw.text((0, y_pos), line, font=self._font, fill=255)

        # Lastly, actually write the thing out
        self._disp.image(self._image)
        self._disp.display()
