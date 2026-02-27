"""
AI 视觉翻译模块
- 将截屏压缩到 ~1MB
- 直接发送给 Qwen 视觉模型进行识别 + 翻译
- 返回中英对照结果
"""

import io
import base64
import traceback
from PIL import Image
from openai import OpenAI


# ====================================================================== #
#  图片压缩：确保 ≤ target_size_kb（默认 ~1024KB ≈ 1MB）
# ====================================================================== #
def compress_image(img: Image.Image, target_size_kb: int = 1024) -> str:
    """
    将 PIL Image 压缩为 JPEG base64 字符串，目标大小 ≤ target_size_kb。
    策略：先按比例缩小分辨率，再降低 JPEG quality。
    返回 base64 编码的 JPEG 字符串。
    """
    # 确保 RGB 模式（去掉 alpha 通道）
    if img.mode != "RGB":
        img = img.convert("RGB")

    # 1. 如果分辨率过大，先缩小（最大长边 1920px）
    max_edge = 1920
    w, h = img.size
    if max(w, h) > max_edge:
        scale = max_edge / max(w, h)
        new_w, new_h = int(w * scale), int(h * scale)
        img = img.resize((new_w, new_h), Image.LANCZOS)

    # 2. 二分法找到最优 JPEG quality
    quality_low, quality_high = 20, 95
    best_buf = None

    while quality_low <= quality_high:
        quality_mid = (quality_low + quality_high) // 2
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality_mid, optimize=True)
        size_kb = buf.tell() / 1024

        if size_kb <= target_size_kb:
            best_buf = buf
            quality_low = quality_mid + 1  # 尝试更高质量
        else:
            quality_high = quality_mid - 1  # 需要降低质量

    # 如果所有质量都超标，用最低质量
    if best_buf is None:
        best_buf = io.BytesIO()
        img.save(best_buf, format="JPEG", quality=20, optimize=True)

    best_buf.seek(0)
    b64 = base64.b64encode(best_buf.getvalue()).decode("utf-8")
    size_kb = best_buf.tell() / 1024
    print(f"[压缩] 图片大小: {size_kb:.0f}KB, 分辨率: {img.size}")
    return b64


# ====================================================================== #
#  AI 视觉翻译器
# ====================================================================== #
class AITranslator:
    """调用 Qwen / OpenAI 兼容视觉 API 进行截图翻译"""

    def __init__(self, api_key: str, api_base: str, model: str):
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=api_base)

    def update_client(self, api_key: str, api_base: str, model: str):
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=api_base)

    def translate_image(
        self, img: Image.Image, source_lang: str, target_lang: str
    ) -> str:
        """
        将截屏图片直接发给视觉 AI，返回中英对照翻译结果。
        图片会先压缩到 ~1MB。
        """
        # 压缩图片
        b64_image = compress_image(img)

        system_prompt = (
            f"你是一位专业翻译和 OCR 专家。请仔细阅读图片中的所有{source_lang}文字内容，"
            f"然后翻译为{target_lang}。\n"
            f"要求：\n"
            f"1. 输出【中英对照】格式：每一行先显示原文，下一行显示对应翻译，"
            f"原文和译文之间用空行分隔，每对之间用分隔线 --- 分开。\n"
            f"2. 保持原文的段落结构和顺序。\n"
            f"3. 只翻译文字内容，不要描述图片本身。\n"
            f"4. 如果图片中没有文字，只回复：（无文字内容）\n"
            f"5. 不要附加任何额外解释。\n\n"
            f"示例输出格式：\n"
            f"Hello World\n"
            f"你好世界\n\n"
            f"---\n\n"
            f"This is a test.\n"
            f"这是一个测试。"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{b64_image}",
                                },
                            },
                            {
                                "type": "text",
                                "text": f"请识别并翻译图片中的所有{source_lang}文字为{target_lang}，用中英对照格式输出。",
                            },
                        ],
                    },
                ],
                max_tokens=4096,
                temperature=0.1,
                extra_body={"enable_thinking": False},
            )
            result = response.choices[0].message.content.strip()
            print(f"[AI] 返回结果 ({len(result)} 字):\n{result}")
            return result
        except Exception as e:
            traceback.print_exc()
            print(f"[ERROR] AI 视觉翻译失败: {e}")
            raise
