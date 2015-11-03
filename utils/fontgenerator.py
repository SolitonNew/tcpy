import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QBoxLayout, QDesktopWidget,
                             QPushButton, QMessageBox, QFontComboBox,
                             QSpinBox, QScrollArea, QFileDialog, QLabel)
from PyQt5.QtGui import (QPainter, QPicture, QColor, QFont, QPixmap, QBrush,
                         QFontMetrics)
from PyQt5.QtCore import Qt, QRect, QSize
import math

class FontGenerator(QWidget):
    def __init__(self):
        super().__init__()
        self.init()

    def init(self):
        self.setWindowTitle('Font generator v1.0')
        self.resize(550, 400)
        self.move(10, 10)

        # Установка в центр экрана
        gr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        gr.moveCenter(cp)
        self.move(gr.topLeft())

        # Главный лаяут
        mainBox = QBoxLayout(QBoxLayout.TopToBottom, self)
        self.mainBox = mainBox

        fontBox = QBoxLayout(QBoxLayout.LeftToRight, self)
        mainBox.addLayout(fontBox)
        
        mainBox.addLayout(fontBox)
        # Настройка комбобокса со шрифтами
        fontList = QFontComboBox(self)
        fontList.activated[str].connect(lambda: self.buildCharList())
        fontBox.addWidget(fontList, 1)

        # Поле ввода высоты шрифта
        fontSize = QSpinBox(self)
        fontSize.setValue(18)
        fontSize.valueChanged[str].connect(lambda: self.buildCharList())
        fontSize.setRange(5, 99)
        fontBox.addWidget(fontSize)

        # Поле степени проявления шрифта
        fontLigtness = QSpinBox(self)
        fontLigtness.setValue(100)
        fontLigtness.valueChanged[str].connect(lambda: self.buildCharList())
        fontLigtness.setRange(1, 255)
        fontBox.addWidget(fontLigtness)

        # Контейнер отрисованых шрифтов
        chars = ClickableLabel(self)
        chars.setPixmap(QPixmap())        

        # Область скролинга для символов        
        charScroller = QScrollArea(self)
        charScroller.move(10, 50)
        charScroller.setWidget(chars)
        mainBox.addWidget(charScroller)

        # Превьюшка выбраного мышкой символа
        charPreview = QLabel(self)
        charPreview.resize(200, 200)
        mainBox.addWidget(charPreview)

        # Кнопка сохранения шрифта
        btnSave = QPushButton('Save...', self)
        btnSave.clicked.connect(self.save)
        mainBox.addWidget(btnSave)

        # Сохраняем для публичного пользования указатели
        self.fontList = fontList
        self.fontSize = fontSize
        self.fontLigtness = fontLigtness
        self.chars = chars
        self.charPreview = charPreview

        self.selectedChar = 1
        
        self.show()

        self.buildCharList()

    def save(self):
        fileName = self.fontList.currentFont().family() + '_' + str(self.fontSize.value())        
        fn = QFileDialog(self).getSaveFileName(self, 'Save as', fileName)[0]
        if fn:
            self._saveToFile(fn)

    def _saveToFile(self, fileName):
        f = open(fileName, 'wb')

        # Зарезервировано
        f.write(bytearray(31))

        pix = self.chars.pixmap()

        # Сохраняем метаданные
        ba = bytearray(256 * 3 + 1)
        ba[0] = pix.height()
        i = 1
        for c in self.charSizes:
            ba[i + 1] = c[0] >> 8
            ba[i] = c[0] & 0xff
            ba[i + 2] = c[1]
            i += 3            
        f.write(ba)

        # Сохраняем маски
        img = pix.toImage()
        h = math.ceil(pix.height() / 8)
        pa = bytearray(pix.width() * h)
        for x in range(pix.width()):
            for y in range(h):
                b = 0
                for k in range(8):
                    ny = y * 8 + k + 1
                    if ny < pix.height() and QColor(img.pixel(x, ny)).lightness() < self.fontLigtness.value():
                        b |= (1<<k)
                pa[x * h + y] = b
        f.write(pa)

        f.close()

    def buildCharList(self):
        cf = self.fontList.currentFont()
        cf.setPixelSize(self.fontSize.value())
        self.charSizes = []

        # Выполняем расчет размеров символов
        fm = QFontMetrics(cf)
        all_w = 0
        all_h = fm.height()
        for c in range(256):
            s = chr(c)
            if c > 0x7e:
                s = chr(c + 848)            
            w = fm.width(s)
            self.charSizes += [[all_w, w]]
            all_w += w

        # Отрисовываем расчитаные символы
        self.chars.resize(all_w, all_h)
        pix = QPixmap(all_w, all_h)
        p = QPainter()
        p.begin(pix)
        p.setPen(QColor(0xffffff))
        p.setBrush(QBrush(QColor(0xffffff), Qt.SolidPattern))
        p.drawRect(0, 0, pix.width(), pix.height())
        p.setPen(QColor(0x0))
        p.setFont(cf)
        for c in range(256):
            s = chr(c)
            if c > 0x7e:
                s = chr(c + 848)
            p.drawText(QRect(self.charSizes[c][0],
                             0,
                             self.charSizes[c][1],
                             all_h), Qt.AlignLeft, s)
        p.end()
        self.chars.setPixmap(pix)
        self.buildCharPreview()

    def buildCharPreview(self):
        char = self.selectedChar
        
        k = 5
        s_x = self.charSizes[char][0]
        w = self.charSizes[char][1]
        
        charPix = self.chars.pixmap()
        charImage = charPix.toImage()

        pix = QPixmap(w * k, charPix.height() * k)
        p = QPainter()
        p.begin(pix)
        p.setBrush(QBrush(QColor(0xffffff), Qt.SolidPattern))
        p.drawRect(0, 0, pix.width() - 1, pix.height() - 1)

        p.setBrush(QBrush(QColor(0x0), Qt.SolidPattern))        
        for x in range(w):
            for y in range(charPix.height()):
                if QColor(charImage.pixel(s_x + x, y)).lightness() < self.fontLigtness.value():
                    p.drawRect(x * k, y * k, k, k)
        p.end()
        self.charPreview.setPixmap(pix)


class ClickableLabel(QLabel):
    def mousePressEvent(self, event):
        parent = self.parent().parent().parent()
        x = event.localPos().x()
        for c in range(256):
            if x >= parent.charSizes[c][0] and x < parent.charSizes[c][0] + parent.charSizes[c][1]:
                parent.selectedChar = c
                parent.buildCharPreview()
                break
        #print(event.localPos())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    form = FontGenerator()
    sys.exit(app.exec_())
