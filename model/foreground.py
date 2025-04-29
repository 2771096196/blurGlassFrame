from PIL import Image, ImageDraw

def apply_round_corners(image, corner_radius=0):
    """
    对输入图像应用圆角遮罩，返回带圆角透明区域的图像 (RGBA)。
    image: PIL Image对象（将被转换为RGBA以应用透明遮罩）。
    corner_radius: 圆角半径（像素）。
    """
    # 转换为RGBA模式，准备添加alpha通道
    img = image.convert("RGBA")
    if corner_radius <= 0:
        # 无圆角处理，直接返回转换后的图像
        return img
    w, h = img.size
    # 创建与图像尺寸相同的遮罩（L模式，0为透明，255为不透明）
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    # 在遮罩上绘制圆角矩形，白色部分为保留区域（不透明部分）
    draw.rounded_rectangle([0, 0, w, h], radius=corner_radius, fill=255)
    # 将遮罩应用为图像的alpha通道
    img.putalpha(mask)
    return img
