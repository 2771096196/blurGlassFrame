import math
from PIL import Image, ImageFilter

def create_blur_background(original_img, output_size, scale_factor=1.2, blur_radius=10):
    """
    根据原图生成毛玻璃模糊背景层。
    original_img: PIL Image对象，原始清晰图片。
    output_size: 输出画布大小(tuple, 如 (width, height))，背景需要填充该画布。
    scale_factor: 背景放大倍数（>1表示背景相对原图放大比例）。
    blur_radius: 背景高斯模糊半径。
    返回值: 处理后的背景图层 (RGBA格式)。
    """
    # 确保原图为RGB模式（背景无需透明通道，避免模糊时考虑透明区域）
    base_img = original_img.convert("RGB")
    orig_w, orig_h = base_img.size
    out_w, out_h = output_size
    # 计算实际使用的放大倍数：确保背景覆盖整个输出画布
    # 如果用户提供的scale_factor不足以覆盖四周，则提高到所需最小倍数
    needed_scale = max(out_w / orig_w, out_h / orig_h)
    actual_scale = max(scale_factor, needed_scale)
    # 在计算时稍微增加一点，避免精度问题导致边缘漏出
    actual_scale += 0.01
    # 计算放大后的背景尺寸
    bg_w = math.ceil(orig_w * actual_scale)
    bg_h = math.ceil(orig_h * actual_scale)
    # 放大原图作为背景图
    bg_img = base_img.resize((bg_w, bg_h), Image.LANCZOS)
    # 对背景图应用高斯模糊
    if blur_radius > 0:
        bg_img = bg_img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    # 创建输出画布，并将模糊背景粘贴居中
    bg_canvas = Image.new("RGBA", (out_w, out_h), (0, 0, 0, 0))
    # 计算背景图粘贴位置，使原图中心对准画布中心
    paste_x = (out_w - bg_w) // 2
    paste_y = (out_h - bg_h) // 2
    # 将模糊背景图粘贴到画布上（无mask，直接覆盖）
    bg_canvas.paste(bg_img, (paste_x, paste_y))
    # 模糊背景层完成，返回RGBA图像
    return bg_canvas
