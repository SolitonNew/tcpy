"""
Класс декодер растрового изображения формата BMP.
Copyright (c) 2015, Moklyak Alexandr.

Информация изображения зачитывается непосредственно из файла и не кешируется.
При создании экземпляра файл изображения открывается на чтение.
Если при открытии не произошло исключения, то информация о растровом
изображении становится доступной для чтения.
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
        Метод открывает файл изображения на чтение. При создании этот метод
        вызывается автоматически. Но если файл был закрыт методом close(), этим
        методом его можно открыть заново.
        """
        if self.file: return
        
        self.file = open(self.fileName, 'rb')
        f = self.file
        # Проверка сигнатуры BMP формата
        if f.read(2) == bytearray(b'BM'):
            # Чтение смещения блока пикселей
            f.seek(0x0A)
            self.dataOff = self._link_bytes(f.read(4))

            # Чтение размера/версии заголовка
            f.seek(0x0E)
            b = self._link_bytes(f.read(2))            

            if b == 12:
                self.version = 'CORE'
                bit_addr = 0x18
                pal_addr = 0x1A
                self.compression = 0
                self.clrUsed = 0
            else:
                # Читаем тип компрессии
                f.seek(0x1E)
                self.compression = self._link_bytes(f.read(4))

                # Читаем количество используемых цветов палитры
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

            # Чтение битности изображения
            f.seek(bit_addr)
            self.bits = self._link_bytes(f.read(2))

            # Проверяем длинну палитры
            if self.clrUsed == 0:
                if self.bits == 4:
                    self.clrUsed = 16
                elif self.bits == 8:
                    self.clrUsed = 256
                    
            # Если палитра нужна - загружаем ее
            if self.clrUsed > 0:
                self.palette = []
                f.seek(pal_addr)
                for i in range(self.clrUsed):
                    self.palette.append(self._link_bytes(f.read(3)))
    
            f.seek(0x12)
            # Реальная ширина картинки
            self.image_w = self._link_bytes(f.read(4))
            # Реальная высота картинки
            self.image_h = self._link_bytes(f.read(4))
        else:
            self.close()
            raise(BMPError('Формат не поддерживается'))

    def close(self):
        """
        Метод закрывает файловый поток растрового изображения.
        Не забывайте его вызывать, если изображение уже не понадобится.
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
        Реальная ширина растрового изображения.
        """
        if not self.file: raise(BMPError('Файл не открыт'))
        return(self.image_w)

    def height(self):
        """
        Реальная высота растрового изображения.
        """
        if not self.file: raise(BMPError('Файл не открыт'))
        return(abs(self.image_h))

    def pixel(self, x, y):
        """
        Метод возвращает значение пикселя изображения по указаным координатам X, Y.
        """
        if not self.file: raise(BMPError('Файл не открыт'))
        
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
Класс исключения для BMP декодера.
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
