# 🌐 屏幕截图翻译工具

一款基于 AI 视觉模型的桌面截图翻译软件。框选屏幕区域，按快捷键一键截图，AI 自动识别文字并翻译，中英对照结果显示在悬浮窗中。

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![PyQt5](https://img.shields.io/badge/PyQt5-GUI-green)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ 功能特点

- **🤖 AI 视觉翻译**：截图直接发送给视觉大模型（如 Qwen3.5），一步完成 OCR + 翻译，无需本地 OCR
- **📸 快捷键截图**：全局快捷键（默认 `Ctrl+1`）
- **🗜️ 智能压缩**：截图自动压缩到 ~1MB，节省带宽和 Token
- **📐 自由框选**：鼠标拖动选择屏幕任意区域
- **🪟 悬浮窗显示**：半透明、圆角、可拖拽、可调整大小的双语对照翻译窗口
- **🌍 多语言支持**：中/英/日/韩/法/德/西/俄等 13 种语言互译
- **⌨️ 自定义快捷键**：在界面中自由设置全局快捷键
- **💾 可选保存截图**：开关控制是否将截屏图片保存到本地
- **⚙️ 灵活配置**：支持任何 OpenAI 兼容 API（阿里云 DashScope、DeepSeek、Azure 等）

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行程序

```bash
python main.py
```

### 3. 使用步骤

1. 在主窗口填入 **API 地址** 和 **API 密钥**
2. 选择 **模型**（推荐 `qwen3.5-plus`）
3. 设置 **源语言** 和 **目标语言**
4. 点击 **📐 选择屏幕区域** → 鼠标拖动框选需要翻译的区域
5. 按 **Ctrl+1**（或自定义快捷键）→ 截图发送给 AI → 翻译结果显示在悬浮窗中

---

## 🔧 配置说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| API 地址 | OpenAI 兼容的 API 地址 | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| API 密钥 | 你的 API Key | 空 |
| 模型 | 视觉大模型名称 | `qwen-vl-max` |
| 源语言 | 截图中的语言 | 英语 |
| 目标语言 | 翻译目标语言 | 中文 |
| 快捷键 | 全局截图翻译快捷键 | `ctrl+1` |
| 保存截图 | 是否保存截屏到本地 | 关闭 |
| 字体大小 | 悬浮窗字体大小 | 15 |
| 透明度 | 悬浮窗透明度 | 90% |

所有配置保存在 `config.json` 中，下次启动自动恢复。

---

## 📁 项目结构

```
Translater/
├── main.py              # 入口文件
├── main_window.py       # 主窗口 UI + 快捷键 + 翻译调度
├── translator.py        # AI 视觉翻译（图片压缩 + API 调用）
├── capture.py           # 屏幕截图（mss）
├── region_selector.py   # 全屏区域框选
├── overlay_window.py    # 中英对照翻译悬浮窗
├── config.py            # 配置管理
├── config.json          # 用户配置（自动生成）
├── requirements.txt     # 依赖列表
└── screenshots/         # 截图保存目录（可选）
```

---

## 📄 License

MIT
