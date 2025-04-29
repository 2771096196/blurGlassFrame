"""
毛玻璃背景生成
----------------------------------------------------------------
核心算法 V2 (根据用户需求调整):
1. 把原图按 scale_factor 放大得到 enlarged_img。
2. 从 enlarged_img 的中心裁剪出 output_size 大小的区域得到 cropped_bg。
3. 对 cropped_bg 应用高斯模糊得到 blurred_bg。
4. (新增) 根据 mask_type 和 mask_opacity 在 blurred_bg 上叠加蒙版。
"""

import math
from PIL import Image, ImageFilter, ImageOps

def create_blur_background(
    original_img,
    output_size: tuple,
    scale_factor: float = 1.0,
    blur_radius: int = 20,
    mask_type: str = "无",
    mask_opacity: int = 40 # 新增：蒙版不透明度 (0-100)
):
    """
    生成毛玻璃背景，支持缩放裁剪和颜色蒙版。

    Args:
        original_img (PIL.Image): 原始图像。
        output_size (tuple): 最终背景图层需要的尺寸 (宽, 高)。
        scale_factor (float): 背景内容的放大倍数 (>=1.0)。
        blur_radius (int): 高斯模糊半径。
        mask_type (str): 蒙版类型 ("无", "白色透明蒙版", "黑色透明蒙版")。
        mask_opacity (int): 蒙版的不透明度 (0-100, 百分比)。

    Returns:
        PIL.Image: 处理后的 RGBA 背景图像。
    """
    out_w, out_h = output_size
    if out_w <= 0 or out_h <= 0:
        return Image.new("RGBA", (1, 1), (0, 0, 0, 0))

    base = original_img.convert("RGB")
    ow, oh = base.size

    # --- 1. 按 scale_factor 放大原图 ---
    scale = max(1.0, scale_factor)
    enlarged_w = math.ceil(ow * scale)
    enlarged_h = math.ceil(oh * scale)

    if enlarged_w < out_w or enlarged_h < out_h:
         min_req_scale_w = out_w / ow if ow > 0 else 1
         min_req_scale_h = out_h / oh if oh > 0 else 1
         required_scale = max(min_req_scale_w, min_req_scale_h)
         scale = max(scale, required_scale)
         enlarged_w = math.ceil(ow * scale)
         enlarged_h = math.ceil(oh * scale)

    if scale > 1.0:
        try:
            enlarged_img = base.resize((enlarged_w, enlarged_h), Image.LANCZOS)
        except ValueError:
             enlarged_img = base
             enlarged_w, enlarged_h = ow, oh
    else:
        enlarged_img = base
        enlarged_w, enlarged_h = ow, oh

    # --- 2. 从放大图像中心裁剪到 output_size ---
    try:
        cropped_bg = ImageOps.fit(
            enlarged_img,
            (out_w, out_h),
            method=Image.LANCZOS,
            centering=(0.5, 0.5)
        )
    except ValueError:
         return Image.new("RGBA", (out_w, out_h), (0, 0, 0, 0))

    # --- 3. 应用高斯模糊 ---
    if blur_radius > 0:
        blurred_bg = cropped_bg.filter(ImageFilter.GaussianBlur(blur_radius))
    else:
        blurred_bg = cropped_bg

    final_bg = blurred_bg.convert("RGBA")

    # --- 4. 应用颜色蒙版 (使用传入的透明度) ---
    if mask_type != "无":
        # 将百分比透明度 (0-100) 转换为 alpha 值 (0-255)
        alpha_value = max(0, min(255, int((mask_opacity / 100.0) * 255)))

        if mask_type == "白色透明蒙版":
            mask_color = (255, 255, 255, alpha_value)
            color_mask_layer = Image.new('RGBA', (out_w, out_h), mask_color)
            final_bg = Image.alpha_composite(final_bg, color_mask_layer)
        elif mask_type == "黑色透明蒙版":
            mask_color = (0, 0, 0, alpha_value)
            color_mask_layer = Image.new('RGBA', (out_w, out_h), mask_color)
            final_bg = Image.alpha_composite(final_bg, color_mask_layer)

    return final_bg