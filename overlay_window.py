"""
翻译悬浮窗
中英对照显示，无边框、置顶、圆角、半透明
支持拖拽移动、滚动查看、关闭、调整大小
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextBrowser, QPushButton, QSizeGrip, QApplication,
)
from PyQt5.QtCore import Qt, QPoint, QRectF
from PyQt5.QtGui import QFont, QColor, QPainter, QPainterPath, QBrush


class OverlayWindow(QWidget):
    """翻译结果悬浮窗 — 中英对照"""

    BG_COLOR = QColor(30, 30, 46)       # #1e1e2e
    TITLE_COLOR = QColor(35, 35, 52)    # 稍浅

    def __init__(self, opacity: float = 0.92, font_size: int = 15, parent=None):
        super().__init__(parent)
        self._drag_pos = QPoint()
        self._font_size = font_size

        self.setWindowTitle("翻译结果")
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowOpacity(opacity)
        self.setMinimumSize(320, 160)
        self.resize(520, 380)

        self._init_ui()

        # 默认右下角
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - self.width() - 30,
                  screen.height() - self.height() - 80)

    # ------------------------------------------------------------------ #
    #  UI
    # ------------------------------------------------------------------ #
    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---- 标题栏 ----
        title_bar = QWidget()
        title_bar.setFixedHeight(34)
        title_bar.setStyleSheet("background: transparent;")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(14, 0, 8, 0)

        title_label = QLabel("📝 中英对照翻译")
        title_label.setStyleSheet(
            "color: #cdd6f4; font-size: 13px; font-weight: bold; background: transparent;"
        )
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        self._status_label = QLabel("⏸ 就绪")
        self._status_label.setStyleSheet(
            "color: #a6adc8; font-size: 11px; background: transparent;"
        )
        title_layout.addWidget(self._status_label)

        clear_btn = QPushButton("🗑")
        clear_btn.setFixedSize(26, 26)
        clear_btn.setToolTip("清空内容")
        clear_btn.setStyleSheet("""
            QPushButton {
                color: #fab387; background: transparent;
                border: none; font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background-color: #45475a; border-radius: 4px; }
        """)
        clear_btn.clicked.connect(self._on_clear)
        title_layout.addWidget(clear_btn)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(26, 26)
        close_btn.setStyleSheet("""
            QPushButton {
                color: #f38ba8; background: transparent;
                border: none; font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background-color: #45475a; border-radius: 4px; }
        """)
        close_btn.clicked.connect(self.hide)
        title_layout.addWidget(close_btn)
        root.addWidget(title_bar)

        # ---- 内容区（HTML 富文本，支持中英对照排版）----
        self._text_area = QTextBrowser()
        self._text_area.setOpenExternalLinks(False)
        self._text_area.setFont(QFont("Microsoft YaHei", self._font_size))
        self._text_area.setStyleSheet("""
            QTextBrowser {
                background: transparent;
                color: #cdd6f4;
                border: none;
                padding: 10px 14px;
                selection-background-color: #45475a;
            }
            QScrollBar:vertical {
                background: transparent; width: 8px; border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #585b70; border-radius: 4px; min-height: 30px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        self._text_area.setPlaceholderText("翻译结果将显示在这里…")
        root.addWidget(self._text_area)

        # ---- 底栏 ----
        bottom = QWidget()
        bottom.setFixedHeight(14)
        bottom.setStyleSheet("background: transparent;")
        bl = QHBoxLayout(bottom)
        bl.setContentsMargins(0, 0, 2, 2)
        bl.addStretch()
        grip = QSizeGrip(self)
        grip.setStyleSheet("background: transparent;")
        bl.addWidget(grip)
        root.addWidget(bottom)

    # ------------------------------------------------------------------ #
    #  绘制圆角背景（避免白色直角）
    # ------------------------------------------------------------------ #
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 12, 12)
        painter.fillPath(path, QBrush(self.BG_COLOR))
        painter.end()

    # ------------------------------------------------------------------ #
    #  公开接口
    # ------------------------------------------------------------------ #
    def _on_clear(self):
        """清空翻译内容"""
        self._text_area.clear()
        self._status_label.setText("⏸ 已清空")

    def set_translation(self, text: str):
        """设置翻译结果（纯文本格式，自动转为 HTML 中英对照样式）"""
        html = self._format_bilingual_html(text)
        self._text_area.setHtml(html)

    def set_raw_parts(self, original: str, translated: str):
        """直接传入原文和译文，格式化为对照 HTML"""
        html = self._build_contrast_html(original, translated)
        self._text_area.setHtml(html)

    def set_status(self, status: str):
        self._status_label.setText(status)

    def update_style(self, opacity: float = None, font_size: int = None):
        if opacity is not None:
            self.setWindowOpacity(opacity)
        if font_size is not None:
            self._font_size = font_size
            self._text_area.setFont(QFont("Microsoft YaHei", font_size))

    # ------------------------------------------------------------------ #
    #  格式化
    # ------------------------------------------------------------------ #
    @staticmethod
    def _format_bilingual_html(text: str) -> str:
        """把 AI 返回的中英对照文本转成美观 HTML"""
        if not text:
            return ""
        # 将 --- 分隔的段落分别格式化
        blocks = text.split("---")
        parts = []
        for block in blocks:
            lines = [l.strip() for l in block.strip().splitlines() if l.strip()]
            if not lines:
                continue
            html_block = ""
            for i, line in enumerate(lines):
                # 启发式：如果包含中文字符，视为译文；否则视为原文
                has_cjk = any('\u4e00' <= c <= '\u9fff' for c in line)
                if has_cjk:
                    html_block += (
                        f'<div style="color:#a6e3a1; font-size:{14}px; '
                        f'margin:2px 0 8px 0;">{line}</div>'
                    )
                else:
                    html_block += (
                        f'<div style="color:#89b4fa; font-size:{14}px; '
                        f'margin:8px 0 2px 0;">{line}</div>'
                    )
            parts.append(html_block)

        separator = '<hr style="border:none; border-top:1px solid #45475a; margin:6px 0;">'
        return separator.join(parts)

    @staticmethod
    def _build_contrast_html(original: str, translated: str) -> str:
        """并排显示原文和译文"""
        orig_lines = original.strip().splitlines()
        trans_lines = translated.strip().splitlines()

        html_parts = []
        max_len = max(len(orig_lines), len(trans_lines))
        for i in range(max_len):
            orig = orig_lines[i] if i < len(orig_lines) else ""
            trans = trans_lines[i] if i < len(trans_lines) else ""
            html_parts.append(
                f'<div style="margin:4px 0;">'
                f'<span style="color:#89b4fa;">{orig}</span><br>'
                f'<span style="color:#a6e3a1;">{trans}</span>'
                f'</div>'
            )
        separator = '<hr style="border:none; border-top:1px solid #45475a; margin:4px 0;">'
        return separator.join(html_parts)

    # ------------------------------------------------------------------ #
    #  拖拽移动
    # ------------------------------------------------------------------ #
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.y() < 34:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = QPoint()
