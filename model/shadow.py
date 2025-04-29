import math
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

def create_shadow_layer(orig_size, output_size, corner_radius=0, spread_radius=10, blur_radius=20, opacity=0.5, offset_x=0, offset_y=0):
    """
    根据原图尺寸和参数生成阴影层 (RGBA图像)。
    orig_size: 原图尺寸 (宽, 高)。
    output_size: 输出画布尺寸 (宽, 高)。
    corner_radius: 原图圆角半径，用于确定阴影形状的圆角。
    spread_radius: 阴影扩散半径，即阴影相对于原图形状向外扩张的距离（像素）。
    blur_radius: 阴影模糊程度（高斯模糊半径）。
    opacity: 阴影不透明度 (0~1之间，小数)。
    offset_x, offset_y: 阴影偏移量（相对于原图位置，正值表示向右/向下偏移，负值表示向左/向上偏移）。
    返回值: 生成的阴影层图像 (RGBA)。
    """
    orig_w, orig_h = orig_size
    out_w, out_h = output_size
    # 创建灰度遮罩，用于绘制阴影形状（白色区域表示阴影形状，不透明区）
    shadow_mask = Image.new("L", (out_w, out_h), 0)
    draw = ImageDraw.Draw(shadow_mask)
    # 原图在输出画布中的位置（这里假定原图居中对齐）
    orig_x = (out_w - orig_w) // 2
    orig_y = (out_h - orig_h) // 2
    # 在遮罩上绘制一个与原图位置和大小相同的矩形（考虑圆角）
    rect_coords = [orig_x, orig_y, orig_x + orig_w, orig_y + orig_h]
    if corner_radius > 0:
        # 绘制圆角矩形
        draw.rounded_rectangle(rect_coords, radius=corner_radius, fill=255)
    else:
        # 绘制普通矩形
        draw.rectangle(rect_coords, fill=255)
    # 阴影扩散：使用最大值滤波 (MaxFilter) 扩大白色区域
    if spread_radius > 0:
        # Pillow的MaxFilter的kernel size应为 2*spread_radius + 1
        size = spread_radius * 2 + 1
        shadow_mask = shadow_mask.filter(ImageFilter.MaxFilter(size=size))
    # 应用高斯模糊，使阴影边缘柔和
    if blur_radius > 0:
        shadow_mask = shadow_mask.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    # 将灰度遮罩转换为NumPy数组以调整透明度分布（实现近似二次平方衰减）
    mask_array = np.array(shadow_mask, dtype=float) / 255.0
    # 二次衰减：灰度值取平方，使边缘更透明
    mask_array = mask_array ** 2
    # 应用整体不透明度参数
    mask_array = mask_array * opacity
    # 限制在[0,1]范围并转换回0-255灰度值
    mask_array = np.clip(mask_array, 0, 1)
    shadow_mask = Image.fromarray((mask_array * 255).astype('uint8'), mode='L')
    # 生成RGBA阴影图层（黑色），将计算得到的灰度遮罩用作alpha通道
    shadow_layer = Image.new("RGBA", (out_w, out_h), (0, 0, 0, 0))
    # 将阴影遮罩作为alpha应用到黑色图层
    black_bg = Image.new("RGB", (out_w, out_h), (0, 0, 0))
    black_bg.putalpha(shadow_mask)
    shadow_layer = black_bg.convert("RGBA")
    # 如果有偏移量，则将阴影层移动偏移后的位置
    if offset_x != 0 or offset_y != 0:
        shifted_layer = Image.new("RGBA", (out_w, out_h), (0, 0, 0, 0))
        # 计算粘贴位置，对于负偏移，需要调整起始坐标
        paste_x = offset_x
        paste_y = offset_y
        # 使用paste将阴影层偏移后粘贴，如果偏移为负，paste会自动裁剪
        shifted_layer.paste(shadow_layer, (paste_x, paste_y))
        shadow_layer = shifted_layer
    return shadow_layer
