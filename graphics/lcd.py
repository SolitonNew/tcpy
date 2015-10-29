"""
Класс для работы с монохромными графическими экранами.
Copyright (c) 2015, Moklyak Alexandr.

Работа с геометрическими примитивами и текстом выполняется в видеобуфере.
После окончания необходимых графических действий необходимо вызвать метод
show() который выполнит обновление экрана согласно данными видеобуфера.
В конструкторе класса необходимо указать экземпляр класса драйвера Вашего
экрана с предварительной настройкой портов взаимодействия с pyboard.
Также есть необязательный параметр flip. Его следует использовать в случаях,
когда конструктивно необходимо установить экран в корпусе верх ногами.
Если flip = True, то вся графическая информация поступающая в видеобуфер
будет переворачиваться на 180 градусов.

Пример демонстрирует подключение к экрану от мобильного телефона Trium Mars
и отрисовка линии с использовании программной эмуляции SPI порта:
>>> from lcd import LCD
>>> from lcddrv import TriumMars
>>> from lcddrv import SoftSPI
>>> spi = SoftSPI('X8', 'X6')
>>> l = LCD(TriumMars(spi, 'X1', 'X3'))
>>> l.line(1, 1, 50, 50)
>>> l.show()

Пример демонстрирует подключение к экрану от мобильного телефона Trium Mars
и отрисовка линии с использовании аппаратного SPI порта:
>>> from lcd import LCD
>>> from lcddrv import TriumMars
>>> from pyb import SPI
>>> from lcddrv import SoftSPI
>>> spi = SPI(1)
>>> l = LCD(TriumMars(spi, 'X1', 'X3'))
>>> l.line(1, 1, 50, 50)
>>> l.show()

Более сложный пример отрисовки в бесконечном цыкле. Используется отрисовка
прямоугольника, линии, очистка экрана и определение покрашен ли пиксель:
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

ПРИМЕЧАНИЕ: Тесты производительности показали, что использование аппаратного
SPI порта ускоряет более чем в два раза отрисовку изображений. Но поскольку
количество их окраничено, а расположение фиксировано, то программная эмуляция
порта является вполне удовлетворительной альтернативой.

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
        Отправляет видеобуфер в экран. Метод не вызывается автоматически.
        После серии изменений видеобуфера этот метод нужно вызвать, что бы
        изменения отобразились на экране.
        """
        self.driver.send(self.canvas)

    def contrast(self, percent = -1):
        """
        Метод позволяет задать контрастность экрана. Параметр percent - это
        число в диапазоне от 1-100. Если параметр не задан, то метод возвращает
        ранее установленое значение контрастности.
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
        Метод выполняет очистку видеобуфера.
        """
        for i in range(len(self.canvas)):
            self.canvas[i] = 0

    def width(self):
        """
        Метод возвращает ширину отображаемой области экрана в пикселях.
        """
        return(self.driver.SCREEN_W)

    def height(self):
        """
        Метод возвращает высоту отображаемой области экрана в пикселях.
        """
        return(self.driver.SCREEN_H)    

    def pixel(self, x, y, v = None):
        """
        Метод позволяет записать в видеобуфер значение пикселя с координатами
        X, Y или получить по этим координатам записаное ранее значение пикселя.
        Если указан параметр V (1 или 0) то выполняется запись в видеобуфер
        значения пикселя. Если параметр V не указан, то метод возвращает
        значение пикселя.
        """
        if self.flip:
            x = self.width() - x - 1
            y = self.height() - y - 1

        if x < 0 or x > self.width() - 1: return(0)
        if y < 0 or y > self.height() - 1: return(0)

        l = y // 8 # Строка в контроллере экрана
        bi = self.driver.CHIP_W * l + x # Номер байта в canvas
        c = 1 << (y - (l * 8)) # Бит байта контроллера экрана

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
        Метод отрисовывает в видеобуфере линию между точками X1, Y1 и X2, Y2
        по алгоритму Брезенхема.
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
        Метод отрисовывает прямоугольник с координатами X1, Y1, X2, Y2.
        Параметр solid позволяет указать закрашивать ли прямоугольник.
        Если параметр указан True или 1, то прямоугольник будет закрашен.
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
        Метод очищает область экрана прямоугольной формы с координатами
        X1, Y1, X2, Y2.
        """
        for y in range(y1, y2):
            for x in range(x1, x2):
                self.pixel(x, y, 0)

    def circle(self, x, y, r, solid = False):
        """
        Метод отрисовывает круг по алгоритму Брезенхема с координатами центра
        X, Y и радиуом R. Параметр solid позволяет указать закрашивать ли круг.
        Если параметр указан True или 1, то круг будет закрашен.
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
        Метод выполняет расчет прямоугольной области, которую будет занимать
        текст при выводе. Возвращает кортеж (ширина, высота).
        text - измеряемый текст
        font - экземпляр класса Font
        """
        chars = font.chars;
        w = 0
        for c in text:
            w += chars[ord(c)][1]
        return(w, font.height)

    def text(self, x, y, text, font, wrap = False, inv = False):
        """
        Метод выполняет вывод текстовой строки в начиная с указанной позиции.
        text - отображаемый на экране текст
        font - экземпляр класса Font
        wrap - указывает выполнять ли посимвольный перенос текст при достижении
               границы экрана. Если True, то текст, который не помещается в
               экран будет перенесен на новую строку начиная с прежней
               горизонтальной позицией.
               Если False, то текст будет отображаться до края экрана, а лишний
               будет обрезан.
        inv - Если True или 1, то текст будет выведен в инвертированом виде.
        """
        chars = font.chars;
        cx = x
        h = font.height
        for c in text:
            o = ord(c)
            if o > 0xff: # Переводим кириллицу Unicode в ASCII
                o -= 848
            if o > 255:
                o = 32
            if cx + chars[o][1] > self.width():
                if wrap:
                    cx = x
                    y += h
                else:
                    if cx + chars[o][1] >= self.width() + chars[32][1]:
                        return()
            for col in font.charData(o):
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
        Метод выполняет отрисовку растрового изображения в указаную позицию.
        image - экземпляр растрового изображения
        inv - Если True или 1, то изображение будет выведено в инвертированом виде.
        """
        for ky in range(image.height()):
            for kx in range(image.width()):
                if inv:
                    if not image.pixel(kx, ky):
                        self.pixel(x + kx, y + ky, 1)
                else:
                    if image.pixel(kx, ky):
                        self.pixel(x + kx, y + ky, 1)
