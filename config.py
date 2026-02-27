"""
配置管理模块
管理 API 设置、语言选项、截屏区域等所有配置项
"""

import json
import os
import sys

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

DEFAULT_CONFIG = {
    "api_key": "",
    "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "model": "qwen3.5-plus",
    "source_lang": "英语",
    "target_lang": "中文",
    "capture_interval": 2.0,
    "mode": "vision",            # "vision" = 截图直接发给AI视觉模型
    "region": None,              # {"x": 0, "y": 0, "width": 100, "height": 100}
    "overlay_opacity": 0.90,
    "overlay_font_size": 15,
    "overlay_position": None,    # {"x": 0, "y": 0}
    "hotkey": "ctrl+1",          # 全局截图翻译快捷键
    "save_screenshot": False,    # 是否保存截屏图片到本地
}

# 支持的语言列表
LANGUAGES = [
    "中文", "英语", "日语", "韩语", "法语", "德语", "西班牙语",
    "俄语", "葡萄牙语", "意大利语", "阿拉伯语", "泰语", "越南语",
]


class Config:
    """配置管理器：加载/保存/更新配置"""

    def __init__(self):
        self._data = dict(DEFAULT_CONFIG)
        self.load()

    # ---- 属性快捷访问 ----
    @property
    def api_key(self):
        return self._data.get("api_key", "")

    @property
    def api_base(self):
        return self._data.get("api_base", "https://api.openai.com/v1")

    @property
    def model(self):
        return self._data.get("model", "gpt-4o")

    @property
    def source_lang(self):
        return self._data.get("source_lang", "英语")

    @property
    def target_lang(self):
        return self._data.get("target_lang", "中文")

    @property
    def capture_interval(self):
        return self._data.get("capture_interval", 2.0)

    @property
    def mode(self):
        return self._data.get("mode", "vision")

    @property
    def region(self):
        return self._data.get("region", None)

    @property
    def overlay_opacity(self):
        return self._data.get("overlay_opacity", 0.90)

    @property
    def overlay_font_size(self):
        return self._data.get("overlay_font_size", 15)

    @property
    def overlay_position(self):
        return self._data.get("overlay_position", None)

    @property
    def hotkey(self):
        return self._data.get("hotkey", "ctrl+1")

    @property
    def save_screenshot(self):
        return self._data.get("save_screenshot", False)

    # ---- 更新 ----
    def update(self, **kwargs):
        """批量更新配置项"""
        for k, v in kwargs.items():
            if k in DEFAULT_CONFIG:
                self._data[k] = v

    def set(self, key, value):
        """设置单个配置项"""
        self._data[key] = value

    def get(self, key, default=None):
        return self._data.get(key, default)

    # ---- 持久化 ----
    def load(self):
        """从 config.json 加载"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                self._data.update(saved)
            except Exception:
                pass

    def save(self):
        """保存到 config.json"""
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Config] 保存失败: {e}")

    def to_dict(self):
        return dict(self._data)
