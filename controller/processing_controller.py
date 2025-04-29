# -*- coding: utf-8 -*-
"""
图像处理核心控制器 (processing_controller.py)
-------------------------------------------------
负责根据用户参数处理单张或多张图像，应用背景、阴影、前景效果。

主要功能:
1.  提供 `process_single_image` 函数处理单张图片，包括：
    - 计算画布尺寸 (`_canvas_size`)，考虑边距和目标比例。
    - 计算像素偏移量 (`_offset_px`)。
    - 生成背景层 (调用 `background.create_blur_background`)。
    - 生成阴影层 (调用 `shadow.create_shadow_layer`)，考虑偏移联动和边距跟随。
    - 生成前景层 (调用 `foreground.apply_round_corners`)。
    - 合成图层并按最终画布尺寸裁剪。
2.  提供 `process_all_images` 函数，使用线程池并行处理多张图片。
3.  包含核心计算逻辑的辅助函数 `_canvas_size` 和 `_offset_px`。

改动记录:
- 2025-04-29:
    - 修正 `_canvas_size` 函数中读取画面比例参数的键名错误。
      原为 `p.get("target_ratio")`，应为 `p.get("ratio")`，以匹配 param_view.py 中设置的状态键。
    - 添加/更新中文注释，保持代码风格一致。
    - 确认 `background.create_blur_background` 调用时传递了 `mask_opacity`。
"""

from concurrent.futures import ThreadPoolExecutor
from PIL import Image
# 导入模型子模块 (假设在 model/ 目录下)
from model import background, shadow, foreground

# --- 工具函数 ---

def _canvas_size(ow, oh, p):
    """
    根据原始尺寸、四边边距和目标比例计算最终画布尺寸及前景内容在其上的基线位置。

    Args:
        ow (int): 原始图像宽度。
        oh (int): 原始图像高度。
        p (dict): 包含所有参数的字典。

    Returns:
        tuple: (canvas_w, canvas_h, base_x, base_y)
               - canvas_w: 计算后的画布宽度。
               - canvas_h: 计算后的画布高度。
               - base_x: 前景内容在画布上的左上角 x 坐标（不含阴影扩展区域）。
               - base_y: 前景内容在画布上的左上角 y 坐标（不含阴影扩展区域）。
    """
    # --- 1. 计算基础边距 (像素) ---
    is_px_margin = p.get("margin_unit", "像素(px)") == "像素(px)"
    use_independent = p.get("ind_margin", False) # 是否使用独立边距

    if use_independent:
        # 分别读取或计算四个方向的边距
        if is_px_margin:
            l = p.get("margin_left", 0)
            r = p.get("margin_right", 0)
            t = p.get("margin_top", 0)
            b = p.get("margin_bottom", 0)
        else: # 百分比单位，基于原图尺寸计算
            l = int(p.get("margin_left_pct", 0) / 100 * ow)
            r = int(p.get("margin_right_pct", 0) / 100 * ow)
            t = int(p.get("margin_top_pct", 0) / 100 * oh)
            b = int(p.get("margin_bottom_pct", 0) / 100 * oh)
    else:
        # 读取或计算统一边距
        if is_px_margin:
            margin_all = p.get("margin_all", 0)
            l = r = t = b = margin_all
        else: # 百分比单位
            margin_all_pct = p.get("margin_all_pct", 0)
            l = r = int(margin_all_pct / 100 * ow)
            t = b = int(margin_all_pct / 100 * oh)

    # --- 2. 计算包含边距的基础画布尺寸 ---
    base_w = ow + l + r
    base_h = oh + t + b

    # --- 3. 应用目标画面比例 ---
    # 【BUG修复】修正参数键名：应为 'ratio' 而非 'target_ratio'
    ratio = p.get("ratio") # 从参数字典获取目标比例 (e.g., (9, 16) or None)

    if ratio: # 如果指定了目标比例
        rw, rh = ratio # 比例的宽高值
        target_aspect = rw / rh if rh > 0 else 1 # 计算目标宽高比

        # 计算当前基础画布的宽高比
        current_aspect = base_w / base_h if base_h > 0 else target_aspect

        # 比较当前宽高比与目标宽高比，调整画布尺寸以匹配目标
        if current_aspect > target_aspect:
            # 当前画布过宽 (或不够高) -> 保持宽度，增加高度
            canvas_w = base_w
            canvas_h = int(base_w / target_aspect) if target_aspect > 0 else base_h
            # 计算前景在垂直方向上的居中位置
            base_x = l
            base_y = t + (canvas_h - base_h) // 2
        elif current_aspect < target_aspect:
            # 当前画布过窄 (或不够宽) -> 保持高度，增加宽度
            canvas_h = base_h
            canvas_w = int(base_h * target_aspect)
            # 计算前景在水平方向上的居中位置
            base_x = l + (canvas_w - base_w) // 2
            base_y = t
        else:
            # 宽高比已匹配 -> 无需调整
            canvas_w, canvas_h = base_w, base_h
            base_x, base_y = l, t
    else:
        # 未指定目标比例 -> 画布尺寸即为基础尺寸
        canvas_w, canvas_h = base_w, base_h
        base_x, base_y = l, t

    # 确保画布尺寸至少为 1x1
    canvas_w = max(1, canvas_w)
    canvas_h = max(1, canvas_h)

    return canvas_w, canvas_h, base_x, base_y

def _offset_px(cw, ch, p):
    """
    根据参数设置计算前景内容的像素偏移量。

    Args:
        cw (int): 画布宽度。
        ch (int): 画布高度。
        p (dict): 参数字典。

    Returns:
        tuple: (offset_x_px, offset_y_px) 水平和垂直方向的像素偏移量。
    """
    is_px_offset = p.get("offset_unit", "像素(px)") == "像素(px)"
    if is_px_offset:
        # 直接使用像素值
        return p.get("offset_x_val", 0), p.get("offset_y_val", 0)
    else:
        # 使用百分比计算像素值 (相对于画布尺寸)
        off_x_pct = p.get("offset_x_val_pct", 0)
        off_y_pct = p.get("offset_y_val_pct", 0)
        return int(off_x_pct / 100 * cw), int(off_y_pct / 100 * ch)


# ---------- 单张图像处理核心函数 ----------
def process_single_image(img, p):
    """
    处理单张 PIL 图像，应用所有选定的效果。

    Args:
        img (PIL.Image): 输入的原始图像 (RGBA 或 RGB)。
        p (dict): 包含所有处理参数的字典。

    Returns:
        PIL.Image: 处理完成的 RGBA 图像，或在极端情况下返回一个空的 1x1 图像。
    """
    if img is None:
        return Image.new("RGBA", (1, 1), (0, 0, 0, 0)) # 处理空输入

    ow, oh = img.size # 获取原图尺寸

    # --- 1. 计算最终画布尺寸和前景基线位置 ---
    # 调用 _canvas_size 计算考虑边距和比例后的画布尺寸 (canvas_w, canvas_h)
    # 以及前景内容在此画布上的左上角位置 (base_x, base_y)
    canvas_w, canvas_h, base_x, base_y = _canvas_size(ow, oh, p)

    # --- 2. 计算阴影所需的安全边距 (padding) ---
    # 阴影可能会超出原图+边距的范围，需要额外的画布空间绘制
    pad = 0 # 默认无额外边距
    if p.get("shadow_enabled"):
        is_px_shadow = p.get("shadow_unit", "像素(px)") == "像素(px)"
        if is_px_shadow:
             spread = p.get("shadow_spread", 0)
             blur = p.get("shadow_blur", 0)
        else: # 百分比单位，基于原图短边计算
             min_dim = min(ow, oh) if min(ow,oh) > 0 else 1 # 防止除零
             spread = int(p.get("shadow_spread_pct", 0) / 100 * min_dim)
             blur = int(p.get("shadow_blur_pct", 0) / 100 * min_dim)
        # 安全边距约等于扩散半径+模糊半径 (确保模糊效果不被裁剪)
        pad = max(0, spread + blur)

    # 计算包含安全边距的总画布尺寸
    full_w = canvas_w + 2 * pad
    full_h = canvas_h + 2 * pad
    # 确保总画布尺寸至少为 1x1
    full_w = max(1, full_w)
    full_h = max(1, full_h)


    # --- 3. 创建背景层 ---
    # 先创建一个透明画布，尺寸为不含安全边距的 canvas_w x canvas_h
    bg_core = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    if p.get("background_enabled"):
        # 如果启用了背景效果，则调用 background 模块生成
        bg_core = background.create_blur_background(
            original_img=img,                      # 原始图像
            output_size=(canvas_w, canvas_h),      # 目标背景尺寸
            scale_factor=p.get("background_scale", 1.0), # 背景内容缩放
            blur_radius=p.get("background_blur", 0),    # 背景模糊半径
            mask_type=p.get("background_mask", "无"),   # 背景蒙版类型
            mask_opacity=p.get("background_mask_opacity", 40) # 背景蒙版不透明度
        )

    # 创建包含安全边距的总背景画布 (全透明)
    bg = Image.new("RGBA", (full_w, full_h), (0, 0, 0, 0))
    # 将生成的背景核心内容粘贴到总背景画布的中心区域 (考虑安全边距 pad)
    bg.paste(bg_core, (pad, pad))

    # --- 4. 计算前景内容在总画布上的最终位置 (考虑偏移) ---
    # 获取像素偏移量
    off_x, off_y = _offset_px(canvas_w, canvas_h, p)
    # 前景最终位置 = 安全边距 + 基线位置 + 偏移量
    fg_x = pad + base_x + off_x
    fg_y = pad + base_y + off_y

    # --- 5. 计算阴影的偏移量 (考虑联动和边距跟随) ---
    # 基础阴影偏移
    is_px_shadow = p.get("shadow_unit", "像素(px)") == "像素(px)"
    if is_px_shadow:
        base_sh_x = p.get("shadow_offset_x", 0)
        base_sh_y = p.get("shadow_offset_y", 0)
    else: # 百分比单位，基于画布尺寸计算
        base_sh_x = int(p.get("shadow_offset_x_pct", 0) / 100 * canvas_w)
        base_sh_y = int(p.get("shadow_offset_y_pct", 0) / 100 * canvas_h)

    # 联动偏移：如果设置了阴影跟随前景偏移 (shadow_link)
    sh_off_x = base_sh_x + (off_x if p.get("shadow_link") else 0)
    sh_off_y = base_sh_y + (off_y if p.get("shadow_link") else 0)

    # 边距跟随调整：如果设置了阴影跟随边距变化 (shadow_follow_margin)
    if p.get("shadow_follow_margin"):
        # 重新计算像素边距值 (即使单位是百分比，这里也需要像素值来计算差值)
        is_px_margin = p.get("margin_unit", "像素(px)") == "像素(px)"
        use_independent = p.get("ind_margin", False)
        if use_independent:
            if is_px_margin:
                l_px, r_px = p.get("margin_left", 0), p.get("margin_right", 0)
                t_px, b_px = p.get("margin_top", 0), p.get("margin_bottom", 0)
            else:
                l_px = int(p.get("margin_left_pct", 0) / 100 * ow)
                r_px = int(p.get("margin_right_pct", 0) / 100 * ow)
                t_px = int(p.get("margin_top_pct", 0) / 100 * oh)
                b_px = int(p.get("margin_bottom_pct", 0) / 100 * oh)
        else: # 统一边距
            if is_px_margin:
                margin_all_px = p.get("margin_all", 0)
                l_px = r_px = t_px = b_px = margin_all_px
            else:
                margin_all_pct = p.get("margin_all_pct", 0)
                min_dim_ow = ow if ow > 0 else 1
                min_dim_oh = oh if oh > 0 else 1
                l_px = r_px = int(margin_all_pct / 100 * min_dim_ow)
                t_px = b_px = int(margin_all_pct / 100 * min_dim_oh)
        # 根据左右边距差和上下边距差调整阴影偏移，模拟光源效果
        sh_off_x += (l_px - r_px) // 2
        sh_off_y += (t_px - b_px) // 2

    # --- 6. 创建阴影层 ---
    # 创建一个透明的总画布用于绘制阴影
    sh_layer = Image.new("RGBA", (full_w, full_h), (0, 0, 0, 0))
    if p.get("shadow_enabled"):
        # 如果启用了阴影
        # 获取阴影参数（像素或百分比转换后的像素）
        is_px_shadow = p.get("shadow_unit", "像素(px)") == "像素(px)"
        if is_px_shadow:
             spread_px = p.get("shadow_spread", 0)
             blur_px = p.get("shadow_blur", 0)
        else:
             min_dim = min(ow, oh) if min(ow,oh) > 0 else 1
             spread_px = int(p.get("shadow_spread_pct", 0) / 100 * min_dim)
             blur_px = int(p.get("shadow_blur_pct", 0) / 100 * min_dim)
        # 获取圆角半径（百分比转像素）
        min_dim = min(ow, oh) if min(ow,oh) > 0 else 1
        corner_radius_px = int(p.get("corner_radius_pct", 0) / 100 * min_dim)

        # 调用 shadow 模块生成阴影层
        sh_layer = shadow.create_shadow_layer(
            orig_size=(ow, oh),                 # 原图尺寸，用于确定阴影形状
            output_size=(full_w, full_h),       # 阴影绘制的总画布尺寸
            corner_radius=corner_radius_px,     # 圆角半径
            spread_radius=max(0, spread_px),    # 扩散半径 (确保非负)
            blur_radius=max(0, blur_px),        # 模糊半径 (确保非负)
            opacity=p.get("shadow_opacity", 0.5), # 阴影不透明度
            offset_x=sh_off_x,                  # 计算后的总水平偏移
            offset_y=sh_off_y,                  # 计算后的总垂直偏移
        )

    # --- 7. 创建前景层 ---
    # 计算前景圆角半径 (像素)
    min_dim = min(ow, oh) if min(ow,oh) > 0 else 1
    cr_px = int(p.get("corner_radius_pct", 0) / 100 * min_dim)
    # 应用圆角
    fg_img = foreground.apply_round_corners(img, cr_px)
    # 创建透明的总画布用于放置前景
    fg_layer = Image.new("RGBA", (full_w, full_h), (0, 0, 0, 0))
    # 将带圆角的前景图粘贴到计算好的最终位置 (fg_x, fg_y)
    # 使用 fg_img 作为 mask 进行粘贴，以保留透明圆角区域
    fg_layer.paste(fg_img, (fg_x, fg_y), fg_img)

    # --- 8. 图层合成与最终裁剪 ---
    # 合成顺序：背景 -> 阴影 -> 前景
    merged = Image.alpha_composite(bg, sh_layer) # 背景上叠加阴影
    merged = Image.alpha_composite(merged, fg_layer) # 再叠加上前景

    # 定义最终裁剪区域（去除安全边距 pad，得到 canvas_w x canvas_h）
    final_crop_box = (pad, pad, pad + canvas_w, pad + canvas_h)

    # 确保裁剪坐标在有效范围内
    final_crop_box = (
        max(0, final_crop_box[0]), max(0, final_crop_box[1]),
        min(full_w, final_crop_box[2]), min(full_h, final_crop_box[3])
    )

    # 执行裁剪，前提是裁剪区域有效 (宽度和高度大于0)
    if final_crop_box[2] > final_crop_box[0] and final_crop_box[3] > final_crop_box[1]:
        return merged.crop(final_crop_box)
    else:
        # 如果裁剪区域无效（例如画布尺寸为0），返回一个默认的空图像
        print(f"警告: 最终裁剪区域无效 {final_crop_box}，画布尺寸 W={canvas_w}, H={canvas_h}")
        return Image.new("RGBA", (max(1, canvas_w), max(1, canvas_h)), (0,0,0,0))


# ---------- 批量处理 ----------
def process_all_images(images, params, max_workers: int = 4):
    """
    使用线程池并行处理多张图像。

    Args:
        images (list): 包含 PIL.Image 对象的列表。
        params (dict): 应用于所有图像的参数字典。
        max_workers (int): 线程池的最大工作线程数。

    Returns:
        list: 包含处理后 PIL.Image 对象（或处理失败时的 None）的列表，顺序与输入一致。
    """
    results = [] # 用于存储结果，保持顺序
    # 使用线程池执行器
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        # 提交所有任务：为每张图片调用 process_single_image
        # 使用字典将 future 映射到原始索引，以便按顺序组合结果
        futures = {pool.submit(process_single_image, img, params.copy()): i for i, img in enumerate(images)}

        # 创建一个列表来按索引存储结果
        result_map = [None] * len(images)

        # 处理已完成的 future
        for future in futures:
            index = futures[future] # 获取原始索引
            try:
                # 获取任务结果，如果任务抛出异常，这里会重新抛出
                result_map[index] = future.result()
            except Exception as e:
                # 捕获处理单张图片时可能发生的异常
                print(f"处理图片索引 {index} 时出错: {e}")
                result_map[index] = None # 标记该图片处理失败

        results = result_map # 将按顺序排列的结果赋给 results

    return results