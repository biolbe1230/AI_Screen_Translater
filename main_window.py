"""
主窗口
包含 API 设置、语言选择、区域选择、按键截图翻译
翻译流程：按键触发截图 → 压缩到~1MB → 发给 Qwen 视觉模型 → 中英对照悬浮窗
"""

import traceback
import keyboard

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QDoubleSpinBox,
    QGroupBox, QMessageBox, QSlider, QSpinBox, QApplication,
    QShortcut, QCheckBox,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QKeySequence

from config import Config, LANGUAGES
from capture import ScreenCapture
from translator import AITranslator
from region_selector import RegionSelector
from overlay_window import OverlayWindow


# ====================================================================== #
#  单次翻译工作线程（按键触发，完成后自动结束）
# ====================================================================== #
class TranslationWorker(QThread):
    """后台线程：压缩图片 → Qwen 视觉翻译 → 返回中英对照"""
    translation_ready = pyqtSignal(str)    # 翻译结果
    error_occurred = pyqtSignal(str)
    status_update = pyqtSignal(str)

    def __init__(self, config: Config, img, parent=None):
        super().__init__(parent)
        self.config = config
        self._img = img

    def run(self):
        try:
            img = self._img
            print(f"[截图] 尺寸: {img.size}")

            # 根据配置决定是否保存截图
            if self.config.save_screenshot:
                import os, datetime
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshots_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "/tmp/screenshots")
                os.makedirs(screenshots_dir, exist_ok=True)
                save_path = os.path.join(screenshots_dir, f"screenshot_{ts}.png")
                img.save(save_path)
                print(f"[截图] 已保存: {save_path}")

            # 发送给 AI 视觉模型翻译
            self.status_update.emit("🤖 AI 视觉翻译中…")
            translator = AITranslator(
                api_key=self.config.api_key,
                api_base=self.config.api_base,
                model=self.config.model,
            )
            result = translator.translate_image(
                img,
                self.config.source_lang,
                self.config.target_lang,
            )

            self.translation_ready.emit(result)
            self.status_update.emit("✅ 翻译完成")

        except Exception as e:
            traceback.print_exc()
            err_msg = str(e)
            if len(err_msg) > 200:
                err_msg = err_msg[:200] + "…"
            self.error_occurred.emit(f"翻译出错: {err_msg}")
            self.status_update.emit("❌ 出错")


# ====================================================================== #
#  主窗口
# ====================================================================== #
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.config = Config()
        self._worker = None
        self._overlay = None
        self._selector = None
        self._is_translating = False

        self.setWindowTitle("🌐 屏幕翻译")
        self.setMinimumWidth(520)
        self.adjustSize()
        self._init_ui()
        self._load_config_to_ui()
        self._setup_shortcuts()

    # ------------------------------------------------------------------ #
    #  快捷键
    # ------------------------------------------------------------------ #
    def _setup_shortcuts(self):
        # 从配置读取快捷键并注册
        self._register_hotkey(self.config.hotkey)

    def _register_hotkey(self, hotkey: str):
        """注册/重新注册全局热键"""
        try:
            keyboard.unhook_all()
            keyboard.add_hotkey(hotkey, self._on_hotkey_triggered)
            print(f"[热键] 已注册全局快捷键: {hotkey}")
        except Exception as e:
            print(f"[热键] 注册失败: {e}")
            # fallback 到 ctrl+1
            keyboard.add_hotkey('ctrl+1', self._on_hotkey_triggered)
            print("[热键] 已回退到 ctrl+1")

    def _on_hotkey_triggered(self):
        """全局热键回调（在 keyboard 线程中），通过信号切回主线程"""
        # keyboard 回调在后台线程，必须通过信号回到 Qt 主线程
        from PyQt5.QtCore import QMetaObject, Qt, Q_ARG
        QMetaObject.invokeMethod(self, "_on_translate", Qt.QueuedConnection)

    # ------------------------------------------------------------------ #
    #  UI
    # ------------------------------------------------------------------ #
    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)

        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e2e; }
            QGroupBox {
                color: #cdd6f4; font-weight: bold; font-size: 13px;
                border: 1px solid #45475a; border-radius: 8px;
                margin-top: 14px; padding-top: 22px;
            }
            QGroupBox::title {
                subcontrol-origin: margin; left: 14px; padding: 0 6px;
                top: 2px;
            }
            QLabel { color: #bac2de; font-size: 12px; }
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                background-color: #313244; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 6px;
                padding: 5px 8px; font-size: 12px;
            }
            QLineEdit:focus, QComboBox:focus { border-color: #89b4fa; }
            QPushButton {
                background-color: #89b4fa; color: #1e1e2e;
                border: none; border-radius: 6px;
                padding: 8px 16px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #74c7ec; }
            QPushButton:pressed { background-color: #89dceb; }
            QPushButton:disabled { background-color: #45475a; color: #6c7086; }
        """)

        # ======== API 设置 ========
        api_group = QGroupBox("🔑 API 设置")
        api_layout = QGridLayout()

        api_layout.addWidget(QLabel("API 地址:"), 0, 0)
        self._api_base_input = QLineEdit()
        self._api_base_input.setPlaceholderText("https://dashscope.aliyuncs.com/compatible-mode/v1")
        api_layout.addWidget(self._api_base_input, 0, 1)

        api_layout.addWidget(QLabel("API 密钥:"), 1, 0)
        self._api_key_input = QLineEdit()
        self._api_key_input.setEchoMode(QLineEdit.Password)
        self._api_key_input.setPlaceholderText("sk-...")
        api_layout.addWidget(self._api_key_input, 1, 1)

        api_layout.addWidget(QLabel("模型:"), 2, 0)
        self._model_input = QLineEdit()
        self._model_input.setPlaceholderText("qwen3.5-plus")
        api_layout.addWidget(self._model_input, 2, 1)

        api_group.setLayout(api_layout)
        layout.addWidget(api_group)

        # ======== 翻译设置 ========
        trans_group = QGroupBox("🌍 翻译设置")
        trans_layout = QGridLayout()

        trans_layout.addWidget(QLabel("源语言:"), 0, 0)
        self._source_lang_combo = QComboBox()
        self._source_lang_combo.addItems(LANGUAGES)
        trans_layout.addWidget(self._source_lang_combo, 0, 1)

        trans_layout.addWidget(QLabel("目标语言:"), 1, 0)
        self._target_lang_combo = QComboBox()
        self._target_lang_combo.addItems(LANGUAGES)
        trans_layout.addWidget(self._target_lang_combo, 1, 1)

        trans_group.setLayout(trans_layout)
        layout.addWidget(trans_group)

        # ======== 悬浮窗设置 ========
        overlay_group = QGroupBox("🪟 悬浮窗设置")
        overlay_layout = QGridLayout()

        overlay_layout.addWidget(QLabel("字体大小:"), 0, 0)
        self._font_size_spin = QSpinBox()
        self._font_size_spin.setRange(10, 40)
        self._font_size_spin.setValue(15)
        overlay_layout.addWidget(self._font_size_spin, 0, 1)

        overlay_layout.addWidget(QLabel("透明度:"), 1, 0)
        self._opacity_slider = QSlider(Qt.Horizontal)
        self._opacity_slider.setRange(30, 100)
        self._opacity_slider.setValue(92)
        self._opacity_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #313244; height: 6px; border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #89b4fa; width: 16px; height: 16px;
                margin: -5px 0; border-radius: 8px;
            }
        """)
        overlay_layout.addWidget(self._opacity_slider, 1, 1)

        overlay_group.setLayout(overlay_layout)
        layout.addWidget(overlay_group)

        # ======== 通用设置 ========
        general_group = QGroupBox("⚙ 通用设置")
        general_layout = QGridLayout()

        general_layout.addWidget(QLabel("快捷键:"), 0, 0)
        self._hotkey_input = QLineEdit()
        self._hotkey_input.setPlaceholderText("ctrl+1")
        self._hotkey_input.setToolTip("全局截图翻译快捷键，如 ctrl+1, ctrl+shift+t, f2 等")
        general_layout.addWidget(self._hotkey_input, 0, 1)

        self._save_screenshot_cb = QCheckBox("保存截屏图片到本地")
        self._save_screenshot_cb.setStyleSheet("color: #bac2de; font-size: 12px;")
        self._save_screenshot_cb.setToolTip("开启后截图会保存到项目 screenshots/ 目录")
        general_layout.addWidget(self._save_screenshot_cb, 1, 0, 1, 2)

        general_group.setLayout(general_layout)
        layout.addWidget(general_group)

        # ======== 区域选择 ========
        region_layout = QHBoxLayout()
        self._select_btn = QPushButton("📐 选择屏幕区域")
        self._select_btn.clicked.connect(self._on_select_region)
        region_layout.addWidget(self._select_btn)

        self._region_label = QLabel("未选择区域")
        self._region_label.setStyleSheet("color: #f38ba8; font-size: 12px;")
        region_layout.addWidget(self._region_label)
        layout.addLayout(region_layout)

        # ======== 截图翻译按钮 ========
        self._translate_btn = QPushButton("📸 截图翻译")
        self._translate_btn.setStyleSheet("""
            QPushButton {
                background-color: #a6e3a1; color: #1e1e2e;
                font-size: 18px; padding: 14px; font-weight: bold;
                border-radius: 10px;
            }
            QPushButton:hover { background-color: #94e2d5; }
            QPushButton:pressed { background-color: #89dceb; }
            QPushButton:disabled { background-color: #45475a; color: #6c7086; }
        """)
        self._translate_btn.clicked.connect(self._on_translate)
        layout.addWidget(self._translate_btn)

        # ======== 状态栏 ========
        self._status_bar_label = QLabel("就绪 — 选择区域后按 Ctrl+1 或点击按钮截图翻译")
        self._status_bar_label.setStyleSheet("color: #a6adc8; font-size: 11px; padding: 4px;")
        layout.addWidget(self._status_bar_label)

    # ------------------------------------------------------------------ #
    #  配置
    # ------------------------------------------------------------------ #
    def _load_config_to_ui(self):
        self._api_base_input.setText(self.config.api_base)
        self._api_key_input.setText(self.config.api_key)
        self._model_input.setText(self.config.model)

        idx_src = LANGUAGES.index(self.config.source_lang) if self.config.source_lang in LANGUAGES else 1
        idx_tgt = LANGUAGES.index(self.config.target_lang) if self.config.target_lang in LANGUAGES else 0
        self._source_lang_combo.setCurrentIndex(idx_src)
        self._target_lang_combo.setCurrentIndex(idx_tgt)

        self._font_size_spin.setValue(self.config.overlay_font_size)
        self._opacity_slider.setValue(int(self.config.overlay_opacity * 100))

        self._hotkey_input.setText(self.config.hotkey)
        self._save_screenshot_cb.setChecked(self.config.save_screenshot)

        if self.config.region:
            r = self.config.region
            self._region_label.setText(f"({r['x']}, {r['y']}) {r['width']}x{r['height']}")
            self._region_label.setStyleSheet("color: #a6e3a1; font-size: 12px;")

    def _save_ui_to_config(self):
        new_hotkey = self._hotkey_input.text().strip() or "ctrl+1"
        old_hotkey = self.config.hotkey

        self.config.update(
            api_base=self._api_base_input.text().strip(),
            api_key=self._api_key_input.text().strip(),
            model=self._model_input.text().strip() or "qwen3.5-plus",
            source_lang=self._source_lang_combo.currentText(),
            target_lang=self._target_lang_combo.currentText(),
            overlay_font_size=self._font_size_spin.value(),
            overlay_opacity=self._opacity_slider.value() / 100.0,
            hotkey=new_hotkey,
            save_screenshot=self._save_screenshot_cb.isChecked(),
        )
        self.config.save()

        # 如果快捷键变了，重新注册全局热键
        if new_hotkey != old_hotkey:
            self._register_hotkey(new_hotkey)

    # ------------------------------------------------------------------ #
    #  区域选择
    # ------------------------------------------------------------------ #
    def _on_select_region(self):
        self._selector = RegionSelector()
        self._selector.region_selected.connect(self._on_region_selected)
        self._selector.showFullScreen()

    def _on_region_selected(self, x, y, w, h):
        self.config.set("region", {"x": x, "y": y, "width": w, "height": h})
        self.config.save()
        self._region_label.setText(f"({x}, {y}) {w}x{h}")
        self._region_label.setStyleSheet("color: #a6e3a1; font-size: 12px;")
        self._status_bar_label.setText(f"✅ 已选择区域: ({x}, {y}) {w}x{h}  — 按 Ctrl+1 截图翻译")

    # ------------------------------------------------------------------ #
    #  截图翻译（按键 / 按钮触发）
    # ------------------------------------------------------------------ #
    from PyQt5.QtCore import pyqtSlot
    @pyqtSlot()
    def _on_translate(self):
        if self._is_translating:
            return  # 防止重复触发

        self._save_ui_to_config()

        if not self.config.api_key:
            QMessageBox.warning(self, "提示", "请输入 API 密钥！")
            return
        if not self.config.region:
            QMessageBox.warning(self, "提示", "请先选择屏幕区域！")
            return

        self._is_translating = True
        self._translate_btn.setEnabled(False)
        self._translate_btn.setText("⏳ 翻译中…")

        # 截图前隐藏主窗口和悬浮窗，避免遮挡截图内容
        self.hide()
        if self._overlay and self._overlay.isVisible():
            self._overlay.hide()

        # 延迟 100ms 让窗口完全消失后再截图
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(100, self._do_translate)

    def _do_translate(self):
        """实际执行截图翻译（窗口已隐藏后调用）"""
        # 1. 在窗口隐藏状态下先截图
        region = self.config.region
        capture = ScreenCapture()
        img = capture.capture_region(
            region["x"], region["y"],
            region["width"], region["height"],
        )
        capture.close()

        # 2. 截图完成，恢复主窗口
        self.show()

        # 确保悬浮窗
        if self._overlay is None:
            self._overlay = OverlayWindow(
                opacity=self.config.overlay_opacity,
                font_size=self.config.overlay_font_size,
            )
        else:
            self._overlay.update_style(
                opacity=self.config.overlay_opacity,
                font_size=self.config.overlay_font_size,
            )
        self._overlay.show()
        self._overlay.set_status("🤖 截图翻译中…")

        # 工作线程（单次任务，传入已截好的图片）
        self._worker = TranslationWorker(self.config, img)
        self._worker.translation_ready.connect(self._on_translation)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.status_update.connect(self._on_status)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

    def _on_worker_finished(self):
        """工作线程完成后恢复按钮"""
        self._is_translating = False
        self._translate_btn.setEnabled(True)
        self._translate_btn.setText("📸 截图翻译")

    # ------------------------------------------------------------------ #
    #  信号
    # ------------------------------------------------------------------ #
    def _on_translation(self, translated: str):
        if self._overlay:
            self._overlay.set_translation(translated)
            self._overlay.show()

    def _on_error(self, msg: str):
        self._status_bar_label.setText(f"❌ {msg}")
        if self._overlay:
            self._overlay.set_status("❌ 出错")

    def _on_status(self, status: str):
        self._status_bar_label.setText(status)
        if self._overlay:
            self._overlay.set_status(status)

    def closeEvent(self, event):
        keyboard.unhook_all()
        if self._worker and self._worker.isRunning():
            self._worker.wait(5000)
        self._save_ui_to_config()
        if self._overlay:
            self._overlay.close()
        event.accept()
