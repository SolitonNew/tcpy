"""
Класс является контейнером шрифта. Используется как драйвер шрифтов
для метода textOut класса LCD.
Файл шрифта представляет собой бинарный файл созданый отдельной утилитой.
Данные файла содержат точечный оттиск каждого символа ASCII. При создании
экземпляра класса Font необходимо указать путь к файлу шрифта. Сам класс
в начале зачитывает только заголовок файла с позициями и размерами шрифта.
Точечная информация зачитывается каждый раз прямо из файла. Тем самым
немного увеличивается время отображения, но значительно экономится память.
"""

import math

class Font(object):  
    def __init__(self, fileName):
        self.file = None
        self.fileName = fileName        
        self._loadMeta()

    def __del__(self):
        self.close()

    def _loadMeta(self):
        self.open()
        f = self.file        
        f.read(31) # Зарезервировано
        self.height = f.read(1)[0] # Высота шрифта
        self.chars = []
        for i in range(256): # Читаем метаданные символов
            p = f.read(3)
            x = (p[1] << 8) + p[0]
            w = p[2]
            self.chars.append([x, w])

    """
    Метод открывает файл шрифта на чтение. При создании этот метод
    вызывается автоматически. Но если файл был закрыт методом close(), этим
    методом его можно открыть заново.
    """
    def open(self):
        if not self.file:
            self.file = open(self.fileName, 'rb')

    """
    Метод закрывает файловый поток шрифта.
    Не забывайте его вызывать, если шрифт уже не понадобится.
    """
    def close(self):
        if self.file: self.file.close()
        self.file = None
        
    """
    Метод для получения точечного представления символа из соответствующего
    файла шрифта.
    """
    def charData(self, c):
        bh = math.ceil(self.height / 8)
        f = self.file
        # Смещаемся в потоке на нужный символ
        f.seek(32 + 256 * 3 + self.chars[c][0] * bh)
        res = []
        # Читаем нужный символ
        for x in range(self.chars[c][1]):
            b = 0
            for y in range(bh):
                r = f.read(1)
                b |= r[0] << (y * 8)
            res.append(b)
        return(res)
