import random
import sys
import os
from urllib.parse import urlparse

from PIL import Image
from PIL.ImageQt import ImageQt

from PySide6 import QtGui
from PySide6.QtCore import Qt, Slot, QRectF, QSize, QPoint
from PySide6.QtWidgets import (QApplication, QLabel, QPushButton, QWidget, QSpinBox,
                               QComboBox, QFileDialog,
                               QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout)

from image_comparator_widget import ImageComparator
from model import Model

class MainWindow(QWidget):
    def __init__(self):
        QWidget.__init__(self)

        self.model = Model()

        c_label = QLabel("C")
        c_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        c_spin_box = QSpinBox()
        c_spin_box.setValue(3)
        c_label.setBuddy(c_spin_box)
        
        d_label = QLabel("D")
        d_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        d_spin_box = QSpinBox()
        d_spin_box.setValue(20)
        d_label.setBuddy(d_spin_box)
        
        g_label = QLabel("G")
        g_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        g_spin_box = QSpinBox()
        g_spin_box.setValue(64)
        g_label.setBuddy(g_spin_box)
        
        g0_label = QLabel("G0")
        g0_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        g0_spin_box = QSpinBox()
        g0_spin_box.setValue(64)
        g0_label.setBuddy(g0_spin_box)

        x_label = QLabel("x")
        x_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        x_spin_box = QSpinBox()
        x_spin_box.setValue(2)
        x_label.setBuddy(x_spin_box)

        model_label = QLabel("Model")
        model_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        model_combo_box = QComboBox()
        model_combo_box.addItems(self.model.networks)
        model_label.setBuddy(model_combo_box)

        form = QWidget()
        form_layout = QGridLayout(form)
        form_layout.addWidget(c_label, 0, 0)
        form_layout.addWidget(c_spin_box, 0, 1)
        form_layout.addWidget(d_label, 1, 0)
        form_layout.addWidget(d_spin_box, 1, 1)
        form_layout.addWidget(g_label, 0, 2)
        form_layout.addWidget(g_spin_box, 0, 3)
        form_layout.addWidget(g0_label, 1, 2)
        form_layout.addWidget(g0_spin_box, 1, 3)
        form_layout.addWidget(x_label, 0, 4)
        form_layout.addWidget(x_spin_box, 0, 5)
        form_layout.addWidget(model_label, 1, 4)
        form_layout.addWidget(model_combo_box, 1, 5)

        self.c_spin_box = c_spin_box
        self.d_spin_box = d_spin_box
        self.g_spin_box = g_spin_box
        self.g0_spin_box = g0_spin_box
        self.x_spin_box = x_spin_box
        self.model_combo_box = model_combo_box

        upscale_button = QPushButton("\nUpscale\n")
        upscale_button.setEnabled(False)
        upscale_button.clicked.connect(self.do_upscale)

        load_button = QPushButton("\nOpen\n")
        load_button.clicked.connect(self.load_image)
        
        save_button = QPushButton("\nSave\n")
        save_button.setEnabled(False)
        save_button.clicked.connect(self.save_image)

        self.ribbon = QWidget()
        self.ribbon_layout = QHBoxLayout(self.ribbon)
        self.ribbon_layout.addWidget(load_button)
        self.ribbon_layout.addWidget(form)
        self.ribbon_layout.addWidget(upscale_button)
        self.ribbon_layout.addWidget(save_button)
        self.ribbon_layout.addStretch()
        
        self.view = ImageComparator()

        self.setAcceptDrops(True)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.ribbon)
        self.main_layout.addWidget(self.view)

        self.model.add_source_listener(self.view.set_left_image)
        self.model.add_result_listener(self.view.set_right_image)
        self.model.add_loading_listener(lambda loading: upscale_button.setEnabled(not loading))
        self.model.add_result_listener(lambda result: save_button.setEnabled(result is not None))
        self.model.add_source_listener(lambda source: upscale_button.setEnabled(source is not None))

    def dragEnterEvent(self, e):
        if e.mimeData().hasImage() or e.mimeData().hasUrls():
            e.accept()
        else:
            e.ignore()
            
    def dropEvent(self, e):
        if e.mimeData().hasImage():
            qtimage = e.mimeData().imageData()
            image = Image.fromqimage(qtimage)
            self.display_image(image)
        elif e.mimeData().urls()[0].scheme() == "file":
            url = e.mimeData().urls()[0].toString()
            parsed = urlparse(url)
            path = parsed.path
            if ":" in path and path[0] == "/":
                path = path[1:]
                
            image = Image.open(path).convert("RGBA")
            self.model.set_source(image)

    def load_image(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self,"Open Image", "","Images (*.png *.jpg);;All Files (*)", options=options)
        if filename:
            image = Image.open(filename).convert("RGBA")
            self.model.set_source(image)

    def do_upscale(self):
        c = self.c_spin_box.value()
        d = self.d_spin_box.value()
        g = self.g_spin_box.value()
        g0 = self.g0_spin_box.value()
        x = self.x_spin_box.value()
        model = self.model_combo_box.currentIndex()
        self.model.process_image(c=c, d=d, g=g, g0=g0, x=x, model=model)

    def save_image(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getSaveFileName(self,"Save Image", "Untitled.png", "PNG (*.png);;JPEG (*.jpg);;All Files (*)", options=options)
        if filename:
            self.model.save(filename)



        
        
    

if __name__ == "__main__":
    app = QApplication(sys.argv)

    widget = MainWindow()
    widget.show()

    sys.exit(app.exec())
