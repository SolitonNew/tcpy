"""
The class is a raster image decoder.
Copyright (c) 2015, Moklyak Alexandr.

Image information is read from directly, and not cashing.
"""

import math

class BMP(object):
    def __init__(self, fileName):
        self.file = None
        self.fileName = fileName
        self.image_w = 0
        self.image_h = 0
        self.palette = False
        self.open()

    def __del__(self):
        self.close()
        
    def open(self):
        """
        The method openes image file for reading. This method is could
        automaticle when created. But is file close by close() method you
        can open a file with this method again.
        """
        if self.file: return
        
        self.file = open(self.fileName, 'rb')
        f = self.file
        # Signature check of BMP format.
        if f.read(2) == bytearray(b'BM'):
            # Reading of the pixel bloks offset.
            f.seek(0x0A)
            self.dataOff = self._link_bytes(f.read(4))

            # Reading of header size (version)
            f.seek(0x0E)
            b = self._link_bytes(f.read(2))            

            if b == 12:
                self.version = 'CORE'
                bit_addr = 0x18
                pal_addr = 0x1A
                self.compression = 0
                self.clrUsed = 0
            else:
                # Reading of compression type.
                f.seek(0x1E)
                self.compression = self._link_bytes(f.read(4))

                # Reading of the quantity of colors in palette.
                f.seek(0x2E)
                self.clrUsed = self._link_bytes(f.read(4))
                
                if b == 40:
                    self.version = '3'
                    bit_addr = 0x1C
                    if self.compression == 3:
                        pal_addr = 0x42
                    elif self.compression == 6:
                        pal_addr = 0x46
                    else:
                        pal_addr = 0x36
                elif b == 108:
                    self.version = '4'
                    bit_addr = 0x1C
                    pal_addr = 0x7A
                elif b == 124:
                    self.version = '5'
                    bit_addr = 0x1C
                    pal_addr = 0x8A                

            # Reading the bit depth images.
            f.seek(bit_addr)
            self.bits = self._link_bytes(f.read(2))

            # Checking palette length.
            if self.clrUsed == 0:
                if self.bits == 4:
                    self.clrUsed = 16
                elif self.bits == 8:
                    self.clrUsed = 256
                    
            # If palette is needed - uploading.
            if self.clrUsed > 0:
                self.palette = []
                f.seek(pal_addr)
                for i in range(self.clrUsed):
                    self.palette.append(self._link_bytes(f.read(3)))
    
            f.seek(0x12)
            # Real image width.
            self.image_w = self._link_bytes(f.read(4))
            # Real image height
            self.image_h = self._link_bytes(f.read(4))
        else:
            self.close()
            raise(BMPError('The format is not supported'))

    def close(self):
        """
        The method closes font file stream.
        Don't for get to coll it when font is not needed.
        """
        if self.file:
            self.file.close()
        self.file = None

    def _link_bytes(self, bts):
        res = 0
        i = 0
        for b in bts:
            b <<= i
            res |= b
            i += 8
        return res

    def width(self):
        """
        Real image width.
        """
        if not self.file: raise(BMPError('The file is not opened'))
        return(self.image_w)

    def height(self):
        """
        Real image height.
        """
        if not self.file: raise(BMPError('The file is not opened'))
        return(abs(self.image_h))

    def pixel(self, x, y):
        """
        The method returns image pixel value by pointed coordinats X, Y.
        """
        if not self.file: raise(BMPError('The file is not opened'))
        
        if 0 > x > self.image_w - 1:
            return 0
        if 0 > y > abs(self.image_h) - 1:
            return 0

        if self.bits == 1:
            return(self._pixel_1(x, y))
        elif self.bits == 4:
            return(self._pixel_4(x, y))
        elif self.bits == 8:
            return(self._pixel_8(x, y))
        elif self.bits == 16:
            return(self._pixel_16(x, y))
        elif self.bits == 24:
            return(self._pixel_24(x, y))
        elif self.bits == 32:
            return(self._pixel_32(x, y))     
    
    def _pixel_1(self, x, y): # 1 bit
        f = self.file
        n = ((self.image_h - y - 1) * math.ceil(self.image_w / 32) * 32) + x
        bn = n // 8
        pn = n - bn * 8
        f.seek(self.dataOff + bn)
        b = f.read(1)[0]
        return(b & (1 << (7 - pn)))

    def _pixel_4(self, x, y): # 4 bit
        f = self.file
        n = ((self.image_h - y - 1) * math.ceil(self.image_w / 32) * 32) + x
        bn = n // 2
        pn = n - bn * 2
        f.seek(self.dataOff + bn)
        b = f.read(1)[0]
        return(self.palette[b & (1 << (3 - pn))])

    def _pixel_8(self, x, y): # 8 bit
        f = self.file
        n = (self.image_h - y - 1) * self.image_w + x
        f.seek(self.dataOff + n)
        b = f.read(1)[0]
        return(self.palette[b])

    def _pixel_16(self, x, y): # 16 bit
        f = self.file
        n = (self.image_h - y - 1) * self.image_w + x
        f.seek(self.dataOff + n * 2)
        b = self._link_bytes(f.read(2))
        if self.palette:
            return(self.palette[b])
        else:
            return(b)

    def _pixel_24(self, x, y): # 24 bit
        f = self.file
        n = (self.image_h - y - 1) * self.image_w + x
        f.seek(self.dataOff + n * 3)
        b = self._link_bytes(f.read(4))
        return(b)

    def _pixel_32(self, x, y): # 32 bit
        f = self.file
        n = (self.image_h - y - 1) * self.image_w + x
        f.seek(self.dataOff + n * 4)
        b = self._link_bytes(f.read(3))
        return(b)

"""
Exception class for BMP decoder.
"""
class BMPError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return self.value

"""
bmp = BMP('images/mp.bmp')
for y in range(bmp.height()):
    s = ''
    for x in range(bmp.width()):
        if bmp.pixel(x, y):
            s += '*'
        else:
            s += ' '
    print(s)
bmp.close()
"""
