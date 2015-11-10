"""
The class for work with graphic screen.
Copyright (c) 2015, Moklyak Alexandr.

Using the geometric primitives and the text is done in the video buffer. After
completing the necessary graphics must call the action show () which will
update the screen data according to the video buffer. The class constructor
must specify an instance of your driver screen preset ports communicate with
pyboard. There is also an optional flip. It should be used in cases
constructively when you need to install the screen in the housing upside down.
If the flip = True, the entire image information supplied to the video buffer
will be rotated 180 degrees.

This example demonstrates the connection to the screen of a mobile phone
Trium Mars and drawing lines with the use of software emulation SPI port:
>>> from lcd import LCD
>>> from lcddrv import TriumMars
>>> from lcddrv import SoftSPI
>>> spi = SoftSPI('X8', 'X6')
>>> l = LCD(TriumMars(spi, 'X1', 'X3'))
>>> l.line(1, 1, 50, 50)
>>> l.show()

This example demonstrates the connection to the screen of a mobile phone
Trium Mars and drawing lines with hardware SPI ports:
>>> from lcd import LCD
>>> from lcddrv import TriumMars
>>> from pyb import SPI
>>> from lcddrv import SoftSPI
>>> spi = SPI(1)
>>> l = LCD(TriumMars(spi, 'X1', 'X3'))
>>> l.line(1, 1, 50, 50)
>>> l.show()

A more complex example of drawing in an infinite loop. used drawing rectangle,
line, clearing the screen and determining whether the pixel is painted:
>>> import math
>>> from lcd import LCD
>>> from lcddrv import TriumMars
>>> from lcddrv import SoftSPI
>>> spi = SoftSPI('X8', 'X6')
>>> l = LCD(TriumMars(spi, 'X1', 'X3'))
>>> l.rect(0, 0, l.width() - 1, l.height() - 1)
>>> i = 0
>>> while 1:
>>>     cx = 47
>>>     cy = 32
>>>     x = round(30 * math.sin(i)) + cx
>>>     y = round(30 * math.cos(i)) + cy
>>>     if l.pixel(x, y):
>>>         l.clear()
>>>         l.rect(0, 0, l.width() - 1, l.height() - 1)
>>>     l.line(cx, cy, x, y)
>>>     l.show()
>>>     i += math.pi / 18
>>>     pyb.delay(50)

NOTE: Performance tests have shown that rendering of images is speeded more
than twice when the hardware SPI port is used. However, since its number
is limited, and the location is fixed, the software emulation of port is a
quite satisfying alternative.
"""

import math

class LCD(object):
    def __init__(self, driver, flip = False):
        self.driver = driver
        self.flip = flip
        self.contrast(50)
        l = math.ceil(driver.CHIP_H / 8)        
        self.canvas = bytearray(driver.CHIP_W * l)
        self.show()        

    def show(self):
        """
        It sends the video buffer to the screen. The method is not called
        automatically.
        After a series of changes to the video buffer, this method needs to be
        called, so that changes would appear on the screen.
        """
        self.driver.send(self.canvas)

    def contrast(self, percent = -1):
        """
        The method allows to set the screen contrast. Parameter percent - is
        a number between 1-100. If not specified, the method returns to the
        previously set contrast.
        """
        if percent >= 0:
            if percent > 100:
                percent = 100            
            self.percent = percent
            self.driver.contrast(percent)
        else:
            return(self.percent)

    def clear(self):
        """
        The method clears the video buffer.
        """
        for i in range(len(self.canvas)):
            self.canvas[i] = 0

    def width(self):
        """
        The method returns the width of the displayed area of the screen in
        pixels.
        """
        return(self.driver.SCREEN_W)

    def height(self):
        """
        The method returns the height of the displayed area of the screen in
        pixels.
        """
        return(self.driver.SCREEN_H)    

    def pixel(self, x, y, v = None):
        """
        The method allows to record video buffer value of a pixel with
        coordinates X, Y, or receive pixel value information recorded by these
        coordinates previously.
        If the option V (1 or 0) then the pixel value is recorded to the video
        buffer.
        If the parameter V is not specified, then method returns pixel value.
        """
        if self.flip:
            x = self.width() - x - 1
            y = self.height() - y - 1

        if x < 0 or x > self.width() - 1: return(0)
        if y < 0 or y > self.height() - 1: return(0)

        l = y // 8 # A line screen controller
        bi = self.driver.CHIP_W * l + x # Byte number in canvas
        c = 1 << (y - (l * 8)) # Bit of the screen controller byte

        if v == 1:
            self.canvas[bi] |= c
        elif v == 0:
            self.canvas[bi] &= ~c
        else:
            if self.canvas[bi] & c:
                return(1)
            else:
                return(0)
        
        return(0)

    def line(self, x1, y1, x2, y2):
        """
        The method is drawing a line in video buffer between points X1, Y1 и
        X2, Y2 by Bresenham's line algorithm.
        """
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        e = 0
        s = 1
        if dx > dy:
            y = y1
            if y1 > y2:
                s = -1
            rs = 1
            if x2 < x1:
                rs = -1
            for x in range(x1, x2, rs):
                self.pixel(x, y, 1)
                e += dy
                if (e << 1) >= dx:
                    y += s
                    e -= dx
        else:
            x = x1
            if x1 > x2:
                s = -1
            rs = 1
            if y2 < y1:
                rs = -1
            for y in range(y1, y2, rs):
                self.pixel(x, y, 1)
                e += dx
                if (e << 1) >= dy:
                    x += s
                    e -= dy
        self.pixel(x1, y1, 1)
        self.pixel(x2, y2, 1)
                    
    def rect(self, x1, y1, x2, y2, solid = False):
        """
        The method draws a rectangle with coordinates X1, Y1, X2, Y2.
        The solid parameter allows to specify whether to paint over a rectangle.
        If the parameter is specified either True or 1, then the rectangle will
        be painted over.
        """
        for x in range(x1, x2 + 1):
            self.pixel(x, y1, 1)
            self.pixel(x, y2, 1)
        if solid:
            for y in range(y1 + 1, y2):
                for x in range(x1, x2 + 1):
                    self.pixel(x, y, 1)
        else:
            for y in range(y1 + 1, y2):
                self.pixel(x1, y, 1)
                self.pixel(x2, y, 1)

    def clear_rect(self, x1, y1, x2, y2):
        """
        Method clears a rectangular shaped part of the screen with coordinates
        X1, Y1, X2, Y2.
        """
        for y in range(y1, y2):
            for x in range(x1, x2):
                self.pixel(x, y, 0)

    def circle(self, x, y, r, solid = False):
        """
        The method draws a circle by Bresenham's algorithm with center
        coordinates X, Y and radius R. Parameter solid allows you to specify
        whether the circle is painted.
        If the parameter is specified either True or 1, then the circle will
        be painted over.
        """
        px = 0
        py = r
        d = 1 - 2 * r
        err = 0
        while py >= 0:
            if solid:
                for i in range(x - px, x + px + 1):
                    self.pixel(i, y + py, 1)
                    self.pixel(i, y - py, 1)
            else:
                self.pixel(x + px, y + py, 1)
                self.pixel(x + px, y - py, 1)
                self.pixel(x - px, y + py, 1)
                self.pixel(x - px, y - py, 1)
            err = 2 * (d + py) - 1
            if d < 0 and err <= 0:
                px += 1
                d += 2 *px + 1
            else:
                err = 2 * (d - px) - 1
                if d > 0 and err > 0:
                    py -= 1
                    d += 1 - 2 * py
                else:
                    px += 1
                    d += 2 * (px - py)
                    py -= 1
                
    def calc_text_size(self, text, font):
        """
        The method calculates a rectangular area, which will take the text in
        the output. It returns a tuple (width, height).
        text - measured text
        font - instance of class Font
        """
        w = 0
        for c in text:
            o = ord(c)
            if o > 0xff: # Translate Cyrillic Unicode to ASCII
                o -= 848
            if o > 255:
                o = 32
            w += font.char_size(o)[1]
        return(w, font.height())

    def text(self, x, y, text, font, wrap = False, inv = False):
        """
        The method performs the output of a text line starting at a specified
        position.
        text - displayed text
        font - instance of class Font
        wrap - specifies whether to perform character-oriented text wrapping
               when reaching the edge of the screen. If True, then the text
               that does not fit in the screen will be moved to a new line
               starting with the same horizontal position.
               If False, the text will be displayed to the edge of the screen,
               and other will be cut off.
        inv - If True or 1, then text will be displayed in invert mode.
        """
        cx = x
        h = font.height()
        for c in text:
            o = ord(c)
            if o > 0xff: # Translate Cyrillic Unicode to ASCII
                o -= 848
            if o > 255:
                o = 32
            cs = font.char_size(o)
            if cx + cs[1] > self.width():
                if wrap:
                    cx = x
                    y += h
                else:
                    if cx + cs[1] >= self.width() + font.char_size(32)[1]:
                        return()
            for col in font.char_data(o):
                for i in range(h):
                    pix = col & (1 << i)
                    if inv:
                        if not pix:
                            self.pixel(cx, y + i, 1)
                    else:
                        if pix:
                            self.pixel(cx, y + i, 1)
                cx += 1

    def image(self, x, y, image, inv = False):
        """
        The method performs the drawing of raster Image to the specifyed
        position
        image - instance of raster Image
        inv - If True or 1, then image will be inverted.
        """

        kx, ky = 0, 0
        for b in image.all_pixels():
            if kx >= image.width() - 1:
                ky += 1
                kx = 0
            else:
                kx += 1

            if inv:
                if not b:
                    self.pixel(x + kx, y + ky, 1)
            else:
                if b:
                    self.pixel(x + kx, y + ky, 1)
