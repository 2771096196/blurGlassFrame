"""
背景层生成
-------------------------------------------------
核心改进
1. 任何情况下都保证整张画布被模糊背景完全填充
   —— 先放大，再用 ImageOps.fit 截取居中区域。
2. 返回的背景图为 **不透明 RGBA**，杜绝透明导致的
   黑 / 白底问题。
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
    original_img : PIL.Image (任意模式)
    output_size  : (width, height) —— 目标画布大小
    scale_factor : 用户希望的放大倍数 (1.0~5.0)
    blur_radius  : 高斯模糊半径
    返回值       : RGBA 模式、与 output_size 相同的背景层
    """
    out_w, out_h = output_size
    base = original_img.convert("RGB")          # 确保无透明
    orig_w, orig_h = base.size

    # 至少要覆盖整张画布
    needed_scale = max(out_w / orig_w, out_h / orig_h)
    scale = max(scale_factor, needed_scale)     # 取更大的那个

    # 先按 scale 放大
    new_size = (math.ceil(orig_w * scale), math.ceil(orig_h * scale))
    enlarged = base.resize(new_size, Image.LANCZOS)

    # 再裁剪 / 缩放到精确画布尺寸（保证全覆盖、居中）
    fitted = ImageOps.fit(enlarged, (out_w, out_h), Image.LANCZOS, centering=(0.5, 0.5))

    # 模糊
    if blur_radius > 0:
        fitted = fitted.filter(ImageFilter.GaussianBlur(blur_radius))

    # 转 RGBA（完全不透明，α=255），避免透明导致的黑白底
    bg_layer = fitted.convert("RGBA")
    return bg_layer
