from PIL import Image
from model import background, shadow, foreground

def process_single_image(image, params):
    """
    按照给定参数处理单张图片，生成带毛玻璃背景和阴影效果的图像。
    image: PIL Image对象，原始输入图片。
    params: 参数字典，包含背景、阴影、圆角等设置。要求包含键：
        - 'output_size': 输出图像尺寸 (宽, 高)
        - 'background_enabled': 是否启用背景层 (bool)
        - 'background_scale': 背景放大倍数 (float)
        - 'background_blur': 背景模糊半径 (int)
        - 'shadow_enabled': 是否启用阴影层 (bool)
        - 'shadow_spread': 阴影扩散半径 (int)
        - 'shadow_blur': 阴影模糊半径 (int)
        - 'shadow_opacity': 阴影不透明度 (0~1 浮点)
        - 'shadow_offset_x': 阴影X偏移 (int)
        - 'shadow_offset_y': 阴影Y偏移 (int)
        - 'corner_radius': 圆角半径 (int) 或 'corner_radius_pct': 圆角半径百分比
    返回处理后的图像 (PIL Image, RGBA)。
    """
    # 输出画布尺寸
    output_size = params.get('output_size')
    out_w, out_h = output_size
    orig_w, orig_h = image.size
    # Step 1: 生成背景层
    if params.get('background_enabled'):
        bg_layer = background.create_blur_background(image, output_size,
                                                    scale_factor=params.get('background_scale', 1.0),
                                                    blur_radius=params.get('background_blur', 0))
    else:
        # 如果背景关闭，则创建透明背景
        bg_layer = Image.new("RGBA", output_size, (0, 0, 0, 0))
    # Step 2: 生成阴影层
    if params.get('shadow_enabled'):
        shadow_layer = shadow.create_shadow_layer((orig_w, orig_h), output_size,
                                                 corner_radius=params.get('corner_radius', 0),
                                                 spread_radius=params.get('shadow_spread', 0),
                                                 blur_radius=params.get('shadow_blur', 0),
                                                 opacity=params.get('shadow_opacity', 0.5),
                                                 offset_x=params.get('shadow_offset_x', 0),
                                                 offset_y=params.get('shadow_offset_y', 0))
    else:
        # 阴影未启用时，创建全透明的图层
        shadow_layer = Image.new("RGBA", output_size, (0, 0, 0, 0))
    # Step 3: 处理原图前景层（应用圆角透明）
    # 计算圆角半径像素值（如果参数以百分比给出，则转换为对应像素）
    corner_pct = params.get('corner_radius_pct', None)
    if corner_pct is not None:
        # corner_pct是在0-100范围，表示短边的百分比
        corner_radius_px = int(corner_pct / 100.0 * min(orig_w, orig_h))
        # 确保圆角半径不超过短边的一半
        corner_radius_px = min(corner_radius_px, min(orig_w, orig_h) // 2)
    else:
        corner_radius_px = params.get('corner_radius', 0)
    fg_image = foreground.apply_round_corners(image, corner_radius_px)
    # 将前景图放置到输出画布相同尺寸的位置（居中）
    fg_layer = Image.new("RGBA", output_size, (0, 0, 0, 0))
    paste_x = (out_w - orig_w) // 2
    paste_y = (out_h - orig_h) // 2
    fg_layer.paste(fg_image, (paste_x, paste_y), mask=fg_image)
    # Step 4: 合成三层图像：背景 + 阴影 + 前景
    # 先将阴影叠加到背景上，然后叠加前景
    base = Image.alpha_composite(bg_layer, shadow_layer)
    result_img = Image.alpha_composite(base, fg_layer)
    return result_img

def process_all_images(images, params):
    """
    批量处理多张图片。对列表中的每张图片应用相同的参数处理。
    images: PIL Image对象列表。
    params: 参数字典，同process_single_image要求。
    返回处理后的图像列表（PIL Image对象列表）。
    """
    result_images = []
    for img in images:
        try:
            processed = process_single_image(img, params)
            result_images.append(processed)
        except Exception as e:
            # 若单张处理失败，跳过但在返回列表中添加None占位
            result_images.append(None)
    return result_images
