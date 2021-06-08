from PySide6 import QtGui
from PySide6.QtCore import Qt, Slot, QRectF, QSize, QPoint
from PySide6.QtWidgets import (QGraphicsScene, QGraphicsView, QScrollArea, QSizePolicy, QWidget)


def clamp(x, min, max):
    if x < min:
        return min
    if x > max:
        return max
    return x


class DropableGraphicsScene(QGraphicsScene):
    def dragMoveEvent(self, e):
        e.accept()


class ImageComparator(QGraphicsView):
    def __init__(self):
        self.scene_ = DropableGraphicsScene()
        super().__init__(self.scene_)
        self.scene_.setSceneRect(0, 0, 300, 300)
        self.setAcceptDrops(True)
        
        self.canvas_size = None
        self.zoom_level = 1
        
        self.left_cursor = None
        self.left_img_widget = None
        self.left_pil_image = None
        self.left_lens = None
        
        self.right_cursor = None
        self.right_img_widget = None
        self.right_pil_image = None
        self.right_lens = None

    def set_left_image(self, image):
        self.left_pil_image = image
        if self.left_img_widget:
            self.scene().removeItem(self.left_img_widget)
            self.left_img_widget = None
        self._hide_ui()
        self.create_components()
        
    def set_right_image(self, image):
        self.right_pil_image = image
        if self.right_img_widget:
            self.scene().removeItem(self.right_img_widget)
            self.right_img_widget = None
        self._hide_ui()
        self.create_components()

    def create_components(self):
        self.scene().clear()
        self.cursor_outline = QtGui.QPen(QtGui.QBrush(Qt.cyan), 3)
        
        if self.left_pil_image:
            self.left_pixmap = self.left_pil_image.toqpixmap()
            self.left_img_widget = self.scene().addPixmap(self.left_pixmap)
            self.left_img_widget.setAcceptHoverEvents(True)
            
        if self.right_pil_image:
            self.right_pixmap = self.right_pil_image.toqpixmap()
            self.right_img_widget = self.scene().addPixmap(self.right_pixmap)
            self.right_img_widget.setAcceptHoverEvents(True)
        self.draw_images()
        self.scene().update()

    def wheelEvent(self, e):
        if e.angleDelta().y() > 0:
            self.zoom_level += 1
        elif self.zoom_level > 1:
            self.zoom_level -= 1

        self._handle_mouse_move_event(self.last_mouse_pos)

    def enterEvent(self, e):
        pass
        
    def leaveEvent(self, e):
        self._hide_ui()

    def _hide_ui(self):
        if self.left_cursor:
            self.scene().removeItem(self.left_cursor)
            self.left_cursor = None
        if self.right_cursor:
            self.scene().removeItem(self.right_cursor)
            self.right_cursor = None
        if self.left_lens:
            self.scene().removeItem(self.left_lens)
            self.left_lens = None
        if self.right_lens:
            self.scene().removeItem(self.right_lens)
            self.right_lens = None

    def mouseMoveEvent(self, event):
        self.last_mouse_pos = event.localPos()
        self._handle_mouse_move_event(self.last_mouse_pos)
        super(ImageComparator, self).mouseMoveEvent(event)
        
    def _handle_mouse_move_event(self, raw_pos):
        draw_rect = self._get_draw_rect()
        if not draw_rect:
            return

        draw_x, draw_y, draw_width, draw_height = draw_rect
        pos = QPoint(raw_pos.x() - draw_x, raw_pos.y() - draw_y)
        if pos.x() < 0 or pos.x() > draw_width or pos.y() < 0 or pos.y() > draw_height:
            self._hide_ui()
            return

        if pos.x() > draw_width // 2:
            pos.setX(pos.x() - draw_width // 2)

        lens_width = draw_width / 2
        lens_height = lens_width / 3

        cursor_width = lens_width ** 2 / (self.left_pil_image.width * self.zoom_level)   # lens_width / self.zoom_level
        cursor_height = lens_height * draw_height / (self.left_pil_image.height * self.zoom_level)  # lens_height / self.zoom_level
        cursor_x = clamp(pos.x() - cursor_width / 2, 0, draw_width / 2 - cursor_width)
        cursor_y = clamp(pos.y() - cursor_height / 2, 0, draw_height - cursor_height)
        
        lens_offset = 0
        lens_y = cursor_y + cursor_height + lens_offset
        if lens_y + lens_height > self.canvas_size.height():
            lens_y = cursor_y - lens_height - lens_offset

        if self.left_img_widget:
            img_pos = self.left_img_widget.pos()
            rect = QRectF(
                cursor_x + img_pos.x(),
                cursor_y + img_pos.y(),
                cursor_width,
                cursor_height)
            if self.left_cursor:
                self.left_cursor.setRect(rect)
            else:
                self.left_cursor = self.scene().addRect(rect, pen=self.cursor_outline)
            
            scale = draw_height / self.left_pil_image.height
            self.left_lens_pixmap = self.left_pil_image \
                .crop((cursor_x / scale, cursor_y / scale, (cursor_x + cursor_width) / scale, (cursor_y + cursor_height) / scale)) \
                .toqpixmap() \
                .scaled(QSize(lens_width, lens_height), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            if self.left_lens:
                self.left_lens.setPixmap(self.left_lens_pixmap)
            else:
                self.left_lens = self.scene().addPixmap(self.left_lens_pixmap)
            self.left_lens.setPos(draw_x, lens_y)
                
        if self.right_img_widget:
            img_pos = self.right_img_widget.pos()
            rect = QRectF(
                cursor_x + img_pos.x(),
                cursor_y + img_pos.y(),
                cursor_width,
                cursor_height)
            if self.right_cursor:
                self.right_cursor.setRect(rect)
            else:
                self.right_cursor = self.scene().addRect(rect, pen=self.cursor_outline)
            
            scale = draw_height / self.right_pil_image.height
            self.right_lens_pixmap = self.right_pil_image \
                    .crop((cursor_x / scale, cursor_y / scale, (cursor_x + cursor_width) / scale, (cursor_y + cursor_height) / scale)) \
                    .toqpixmap() \
                    .scaled(QSize(lens_width, lens_height), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            if self.right_lens:
                self.right_lens.setPixmap(self.right_lens_pixmap)
            else:
                self.right_lens = self.scene().addPixmap(self.right_lens_pixmap)
            self.right_lens.setPos(draw_x + draw_width / 2, lens_y)

    def resizeEvent(self, event):
        self.canvas_size = event.size()
        self.scene_.setSceneRect(0, 0, self.canvas_size.width(), self.canvas_size.height())
        self._hide_ui()
        self.draw_images()

    def _get_draw_rect(self):
        canvas_width = self.canvas_size.width()
        canvas_height = self.canvas_size.height()
        if self.left_pil_image and self.right_pil_image:
            img_width = max(self.left_pil_image.width, self.right_pil_image.width) * 2
            img_height = max(self.left_pil_image.height, self.right_pil_image.height)
        elif self.left_pil_image:
            img_width = self.left_pil_image.width * 2
            img_height = self.left_pil_image.height
        elif self.right_pil_image:
            img_width = self.right_pil_image.width * 2
            img_height = self.right_pil_image.height
        else:
            return None

        if img_width / img_height > canvas_width / canvas_height:
            draw_width = canvas_width
            draw_height = img_height / img_width * canvas_width
            draw_x = 0
        else:
            draw_width = img_width / img_height * canvas_height
            draw_height = canvas_height
            draw_x = (canvas_width - draw_width) / 2

        return draw_x, 0, draw_width, draw_height
        
    def draw_images(self):
        draw_rect = self._get_draw_rect()
        if not draw_rect:
            return

        draw_x, draw_y, draw_width, draw_height = draw_rect

        if self.left_pil_image:
            self.left_img_widget.setPos(draw_x, draw_y)
            self.left_pixmap = self.left_pil_image.toqpixmap().scaled(QSize(draw_width // 2, draw_height), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.left_img_widget.setPixmap(self.left_pixmap)
            
        if self.right_pil_image:
            self.right_img_widget.setPos(draw_x + draw_width / 2, draw_y)
            self.right_pixmap = self.right_pil_image.toqpixmap().scaled(QSize(draw_width // 2, draw_height), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.right_img_widget.setPixmap(self.right_pixmap)
            
    def dragEnterEvent(self, e):
        e.ignore()
