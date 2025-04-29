"""
毛玻璃背景生成（仅放大背景，不改变画布尺寸）
----------------------------------------------------------------
核心算法
1. 把原图放大 scale_factor 倍
2. 把放大后的图像 **随机 / 中心** 裁剪到 output_size
   —— 为避免看不到变化，这里采用“中心裁剪”。
   用户拖动放大倍数时，毛玻璃纹理会呈现显著放大/缩小效果，
   但画布大小、前景位置完全不受影响。
"""

import math
from PIL import Image, ImageFilter, ImageOps


def create_blur_background(
    original_img,
    output_size: tuple,
    scale_factor: float = 1.2,
    blur_radius: int = 10,
):
    """
    original_img : PIL.Image
    output_size  : (width, height) → 画布固定大小
    scale_factor : 背景放大倍数 (1.0 – 5.0)
    blur_radius  : 模糊半径
    """
    out_w, out_h = output_size
    base = original_img.convert("RGB")    # 保证无 alpha
    ow, oh = base.size

    # ------ 1. 放大 ------
    # 至少等于需求以免出现黑边
    min_scale = max(out_w / ow, out_h / oh)
    scale = max(scale_factor, min_scale)

    enlarged = base.resize(
        (math.ceil(ow * scale), math.ceil(oh * scale)),
        Image.LANCZOS,
    )

    # ------ 2. 中心裁剪到固定画布 ------
    bg_core = ImageOps.fit(
        enlarged, (out_w, out_h),
        method=Image.LANCZOS,
        centering=(0.5, 0.5)              # 中心
    )

    # ------ 3. 模糊 ------
    if blur_radius > 0:
        bg_core = bg_core.filter(ImageFilter.GaussianBlur(blur_radius))

    return bg_core.convert("RGBA")
