#!/usr/bin/python3

"""
The utility to create fonts. Is included in the graphic library for
micropython board.
Copyright (c) 2015, Moklyak Alexandr.

The utility is using PyQt5 library.
There is a possibility to use limited ASCII tables excluding unnessesery
symbols.
"""

import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout,
                             QDesktopWidget, QPushButton, QMessageBox, QFontComboBox,
                             QSpinBox, QScrollArea, QFileDialog, QLabel, QSplitter)
from PyQt5.QtGui import (QPainter, QPicture, QColor, QFont, QPixmap, QBrush,
                         QFontMetrics)
from PyQt5.QtCore import Qt, QRect, QSize
import math

class FontGenerator(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Font generator v1.0')
        self.resize(550, 500)
        gr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        gr.moveCenter(cp)
        self.move(gr.topLeft())        
        
        self._createUI()

        self.selectedChar = 1
        self.hoverChar = 1
        self.buildCharList()        
        
        self.show()

    def _createUI(self):
        # Create components
        fontList = QFontComboBox(self)
        fontSize = QSpinBox(self)
        chars = ClickableLabel(self)
        chars.topWidget = self
        chars.setMouseTracking(True)
        chars.setCursor(Qt.PointingHandCursor)
        charScroller = QScrollArea(self)        
        charScroller.setWidget(chars)        
        charPreview = QLabel(self)
        charPreviewScroller = QScrollArea(self)
        charPreviewScroller.setWidget(charPreview)
        btnSave = QPushButton('Save...', self)
        bottomLabel = QLabel('', self)
        charFrom = QSpinBox(self)
        charTo = QSpinBox(self)

        # Components layout
        mainBox = QVBoxLayout(self)
        topBox = QHBoxLayout(self)
        topBox.addWidget(QLabel('Font list:', self))
        topBox.addWidget(fontList, 1)
        topBox.addWidget(QLabel('   Font size:', self))
        topBox.addWidget(fontSize)
        mainBox.addLayout(topBox)

        rangeBox = QHBoxLayout(self)
        rangeBox.addWidget(QLabel('Char list for pack.'), 1)
        rangeBox.addWidget(QLabel('Start with'))
        rangeBox.addWidget(charFrom)
        rangeBox.addWidget(QLabel('to'))
        rangeBox.addWidget(charTo)
        mainBox.addLayout(rangeBox)
        
        splBox = QSplitter(Qt.Vertical, self)
        splBox.addWidget(charScroller)
        splBox.addWidget(charPreviewScroller)
        mainBox.addWidget(splBox)
        bottBox = QHBoxLayout(self)
        bottBox.addWidget(btnSave, 0, Qt.AlignLeft)
        bottBox.addWidget(bottomLabel)
        mainBox.addLayout(bottBox)
                              
        # Configure and assign handlers
        fontList.activated[str].connect(lambda: self.buildCharList())
        fontSize.setValue(11)
        fontSize.valueChanged[str].connect(lambda: self.buildCharList())
        fontSize.setRange(5, 99)
        charFrom.setRange(0, 255)
        charFrom.setValue(0)
        charFrom.valueChanged[str].connect(lambda: self.buildCharList())
        charTo.setRange(0, 255)
        charTo.setValue(255)
        charTo.valueChanged[str].connect(lambda: self.buildCharList())
        chars.setPixmap(QPixmap())        
        btnSave.clicked.connect(self.save)
        splBox.setSizes([100, 300])

        # Registering to access the components inside the class
        self.fontList = fontList
        self.fontSize = fontSize
        self.charScroller = charScroller
        self.charPreviewScroller = charPreviewScroller
        self.chars = chars
        self.charPreview = charPreview
        self.bottomLabel = bottomLabel
        self.charFrom = charFrom
        self.charTo = charTo
        self.splBox = splBox

    def save(self):
        if self.bottomLabel.styleSheet() != "":
            return
        
        fileName = self.fontList.currentFont().family() + '_' + str(self.fontSize.value())        
        fn = QFileDialog(self).getSaveFileName(self, 'Save as', fileName)[0]
        if fn:
            self._saveToFile(fn)

    def _saveToFile(self, fileName):
        cFrom = self.charFrom.value()
        cTo = self.charTo.value()
        f = open(fileName, 'wb')

        pix = self.chars.pixmap()

        # Save header
        header = bytearray(32)
        header[0] = 1
        header[29] = cFrom
        header[30] = cTo
        header[31] = pix.height()
        f.write(header)        

        # Save metadata
        ba = bytearray((cTo - cFrom + 1) * 3)
        i = 0
        for c in self.charSizes:            
            ba[i] = c[0] & 0xff
            ba[i + 1] = c[0] >> 8
            ba[i + 2] = c[1]
            i += 3            
        f.write(ba)

        # Save mask
        img = pix.toImage()
        h = math.ceil(pix.height() / 8)
        pa = bytearray(pix.width() * h)
        for x in range(pix.width()):
            for y in range(h):
                b = 0
                for k in range(8):
                    ny = y * 8 + k + 1
                    if ny < pix.height() and QColor(img.pixel(x, ny)).lightness() == 0x0:
                        b |= (1<<k)
                pa[x * h + y] = b
        f.write(pa)

        f.close()

    def buildCharList(self):
        hoverColor = 0xcccccc
        selectedColor = 0x999999
        
        cFrom = self.charFrom.value()
        cTo = self.charTo.value() + 1

        if cTo <= cFrom:
            self.chars.setPixmap(QPixmap())
            self.charPreview.setPixmap(QPixmap())
            self.bottomLabel.setText("Invalid range of characters")
            self.bottomLabel.setStyleSheet("QLabel{color:#ff0000;}")
            return None
        else:
            self.bottomLabel.setStyleSheet("")
        
        cf = self.fontList.currentFont()
        cf.setPixelSize(self.fontSize.value())
        self.charSizes = []

        # Calc symbol size
        fm = QFontMetrics(cf)
        all_w = 0
        all_h = fm.height()
        for c in range(cFrom, cTo):
            s = chr(c)
            if c > 0x7e:
                s = chr(c + 848)            
            w = fm.width(s)
            self.charSizes += [[all_w, w]]
            all_w += w

        # Paint chars
        self.chars.resize(all_w, all_h)
        pix = QPixmap(all_w, all_h)
        p = QPainter()        
        p.begin(pix)        
        p.setPen(QColor(0xffffff))
        p.setBrush(QBrush(QColor(0xffffff), Qt.SolidPattern))
        p.drawRect(0, 0, pix.width(), pix.height())
        p.setPen(QColor(0x0))
        cf.setStyleStrategy(QFont.NoAntialias)
        p.setFont(cf)
        for c in range(cFrom, cTo):
            rc = c - cFrom
            
            if self.hoverChar == c:
                p.setBrush(QBrush(QColor(hoverColor), Qt.SolidPattern))
                p.setPen(QColor(hoverColor))
                p.drawRect(self.charSizes[rc][0], 0, self.charSizes[rc][1] - 1, pix.height() - 1)

            if self.selectedChar == c:
                p.setBrush(Qt.NoBrush)
                p.setPen(QColor(selectedColor))
                p.drawRect(self.charSizes[rc][0], 0, self.charSizes[rc][1] - 1, pix.height() - 1)

            if self.hoverChar != c and self.selectedChar != c:
                p.setBrush(QBrush(QColor(0xffffff), Qt.SolidPattern))

            p.setPen(QColor(0x0))

            s = chr(c)
            if c > 0x7e:
                s = chr(c + 848)
            
            p.drawText(QRect(self.charSizes[rc][0],
                             0,
                             self.charSizes[rc][1],
                             all_h), Qt.AlignLeft, s)
        p.end()
        self.chars.setPixmap(pix)
        self.buildCharPreview()

        # Calc statistics
        size = (32 + (cTo - cFrom + 1) * 3 + all_w * math.ceil(all_h / 8)) / 1000
        s = 'Line height: %dpx  |  Count symbols: %d  |  File size: %3.1fkb' % (all_h, (cTo - cFrom), size)
        self.bottomLabel.setText(s)

    def buildCharPreview(self):        
        char = self.selectedChar - self.charFrom.value()
        if char < 0:
            char = 0
        if char >= len(self.charSizes):
            char = len(self.charSizes) - 1
        
        k = 5
        s_x = self.charSizes[char][0]
        w = self.charSizes[char][1]
        
        charPix = self.chars.pixmap()
        charImage = charPix.toImage()

        self.charPreview.resize(w * k + 1, charPix.height() * k + 1)

        pix = QPixmap(w * k, charPix.height() * k)
        p = QPainter()
        p.begin(pix)
        p.setBrush(QBrush(QColor(0xffffff), Qt.SolidPattern))
        p.drawRect(0, 0, pix.width() - 1, pix.height() - 1)

        p.setBrush(QBrush(QColor(0x0), Qt.SolidPattern))        
        for x in range(w):
            for y in range(charPix.height()):
                if QColor(charImage.pixel(s_x + x, y)).lightness() == 0x0:
                    p.drawRect(x * k, y * k, k, k)
        p.end()
        self.charPreview.setPixmap(pix)


class ClickableLabel(QLabel):
    def _check_mouse_pos(self, x):
        parent = self.topWidget
        cFrom = parent.charFrom.value()
        cTo = parent.charTo.value() + 1
        for c in range(cFrom, cTo):
            rc = c - cFrom
            if x >= parent.charSizes[rc][0] and x < parent.charSizes[rc][0] + parent.charSizes[rc][1]:
                return c
        return 0
            
    def mousePressEvent(self, event):
        parent = self.topWidget
        parent.selectedChar = self._check_mouse_pos(event.localPos().x())
        parent.buildCharList()
        parent.buildCharPreview()

    def mouseMoveEvent(self, event):
        parent = self.topWidget
        parent.hoverChar = self._check_mouse_pos(event.localPos().x())
        parent.buildCharList()

    def leaveEvent(self, event):
        parent = self.topWidget
        parent.hoverChar = 0
        parent.buildCharList()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    form = FontGenerator()
    sys.exit(app.exec_())
