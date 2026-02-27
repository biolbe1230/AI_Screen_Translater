"""
区域选择器
全屏透明覆盖层，用户可以拖动鼠标选择屏幕区域
"""

from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QCursor


class RegionSelector(QWidget):
    """
    全屏半透明覆盖层
    用户拖动鼠标框选需要翻译的屏幕区域
    选择完成后发出 region_selected 信号
    """
    region_selected = pyqtSignal(int, int, int, int)  # x, y, w, h

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择翻译区域")
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(QCursor(Qt.CrossCursor))

        # 获取所有屏幕的合并几何区域
        screen_geo = QApplication.desktop().geometry()
        self.setGeometry(screen_geo)

        self._start_pos = QPoint()
        self._end_pos = QPoint()
        self._selecting = False

    def paintEvent(self, event):
        painter = QPainter(self)

        # 半透明遮罩
        painter.fillRect(self.rect(), QColor(0, 0, 0, 80))

        if self._selecting and not self._start_pos.isNull() and not self._end_pos.isNull():
            rect = QRect(self._start_pos, self._end_pos).normalized()

            # 清除选区内的遮罩（让选区变亮）
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(rect, Qt.transparent)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

            # 绿色边框
            pen = QPen(QColor(0, 200, 80), 2, Qt.SolidLine)
            painter.setPen(pen)
            painter.drawRect(rect)

            # 显示尺寸标签
            size_text = f"{rect.width()} × {rect.height()}"
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Microsoft YaHei", 10))
            painter.drawText(rect.x(), rect.y() - 6, size_text)

        # 提示文字
        painter.setPen(QColor(255, 255, 255, 200))
        painter.setFont(QFont("Microsoft YaHei", 14))
        painter.drawText(self.rect(), Qt.AlignTop | Qt.AlignHCenter,
                         "\n\n🖱️ 按住鼠标拖动选择翻译区域  |  按 ESC 取消")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._start_pos = event.globalPos()
            self._end_pos = event.globalPos()
            self._selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        if self._selecting:
            self._end_pos = event.globalPos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._selecting:
            self._selecting = False
            rect = QRect(self._start_pos, self._end_pos).normalized()
            if rect.width() > 10 and rect.height() > 10:
                # 获取 DPI 缩放比例，将逻辑坐标转为物理像素坐标
                # mss 使用物理像素，Qt 高 DPI 模式下返回逻辑坐标
                ratio = self.devicePixelRatioF()
                px = int(rect.x() * ratio)
                py = int(rect.y() * ratio)
                pw = int(rect.width() * ratio)
                ph = int(rect.height() * ratio)
                print(f"[区域] 逻辑坐标: ({rect.x()}, {rect.y()}) {rect.width()}x{rect.height()}")
                print(f"[区域] 物理像素: ({px}, {py}) {pw}x{ph}  (缩放比: {ratio})")
                self.region_selected.emit(px, py, pw, ph)
            self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
