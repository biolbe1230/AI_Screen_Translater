"""
屏幕截图模块
使用 mss 高效截取指定屏幕区域
"""

import io
import base64
from PIL import Image

try:
    import mss
    import mss.tools
except ImportError:
    mss = None


class ScreenCapture:
    """屏幕截图工具"""

    def __init__(self):
        if mss is None:
            raise ImportError("需要安装 mss: pip install mss")
        self._sct = mss.mss()

    def capture_region(self, x: int, y: int, width: int, height: int) -> Image.Image:
        """
        截取屏幕指定区域，返回 PIL Image 对象
        :param x: 左上角 x 坐标
        :param y: 左上角 y 坐标
        :param width: 宽度
        :param height: 高度
        :return: PIL.Image.Image
        """
        monitor = {"left": x, "top": y, "width": width, "height": height}
        screenshot = self._sct.grab(monitor)
        # mss 返回 BGRA，转为 RGB
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        return img

    def capture_full_screen(self) -> Image.Image:
        """截取整个屏幕"""
        monitor = self._sct.monitors[0]  # 所有屏幕的合并区域
        screenshot = self._sct.grab(monitor)
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        return img

    @staticmethod
    def image_to_base64(img: Image.Image, fmt: str = "PNG") -> str:
        """将 PIL Image 转为 base64 编码字符串"""
        buffer = io.BytesIO()
        img.save(buffer, format=fmt)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    @staticmethod
    def images_are_similar(img1: Image.Image, img2: Image.Image, threshold: float = 0.98) -> bool:
        """
        简单对比两张图片是否相似（基于像素均值差）
        用于避免屏幕内容未变化时重复翻译
        """
        if img1.size != img2.size:
            return False
        try:
            import numpy as np
            arr1 = np.array(img1.resize((160, 90)), dtype=np.float32)
            arr2 = np.array(img2.resize((160, 90)), dtype=np.float32)
            diff = np.abs(arr1 - arr2).mean()
            # diff 越小越相似；阈值约 3.0 以内视为相同
            return diff < (1.0 - threshold) * 255
        except ImportError:
            # 没有 numpy 则直接返回 False（每次都翻译）
            return False

    def close(self):
        try:
            self._sct.close()
        except Exception:
            pass
