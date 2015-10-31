"""
The class is a font container. Is used as a font driver for text() method
of LCD class.
Copyright (c) 2015, Moklyak Alexandr.

Font file is a binary file created by font_generator utilit. This file
contains pixel image of awery symbol ASCII. When Font() class is created
the path to font file needs to be pointed. Symbol position, size and bit
masks are read avery time directly from the file. Thus, the display time
increases slightly but significantly save memory.
"""

import math

class Font(object):  
    def __init__(self, fileName):
        self.file = None
        self.fileName = fileName
        self.open()

    def __del__(self):
        self.close()

    def open(self):
        """
        The method openes font file for reading. This method is could
        automaticle when created. But is file close by close() method you
        can open a file with this method again.
        """
        if not self.file:
            self.file = open(self.fileName, 'rb')
            self.file.seek(31)
            self.height = self.file.read(1)[0] # Читаем высоту шрифта

    def close(self):
        """
        The method closes font file stream.
        Don't for get to coll it when font is not needed.
        """
        if self.file: self.file.close()
        self.file = None

    def char_size(self, c):
        """
        The method reads from font file header raster position and symbol width.
        Returns back tuple (position, width).
        """
        f = self.file
        # Смещаемся в потоке на нужный символ
        f.seek(32 + c * 3)
        p = f.read(3)
        x = (p[1] << 8) + p[0]
        w = p[2]
        return(x, w)
        
    def char_data(self, c):
        """
        The method is for getting symbol image.
        Returns back bit masks list for font drawing.
        """
        cs = self.char_size(c)        
        bh = math.ceil(self.height / 8)
        f = self.file
        # Смещаемся в потоке на нужный символ
        f.seek(32 + 256 * 3 + cs[0] * bh)
        res = []
        # Читаем нужный символ
        for x in range(cs[1]):
            b = 0
            for y in range(bh):
                r = f.read(1)
                b |= r[0] << (y * 8)
            res.append(b)
        return(res)
