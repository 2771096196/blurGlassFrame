from concurrent.futures import ThreadPoolExecutor
from PIL import Image
from model import background, shadow, foreground

# ---------- 工具函数 ----------
def _canvas_size(ow, oh, p):
    """根据四边边距和目标比例计算画布尺寸 & 前景基线位置（不含安全边距）。"""
    # 计算边距的像素值（支持百分比单位）
    if p.get("margin_unit", "px") != "px":
        l = int(p["margin_left"] / 100 * ow)
        r = int(p["margin_right"] / 100 * ow)
        t = int(p["margin_top"] / 100 * oh)
        b = int(p["margin_bottom"] / 100 * oh)
    else:
        l, r = p["margin_left"], p["margin_right"]
        t, b = p["margin_top"], p["margin_bottom"]
    base_w, base_h = ow + l + r, oh + t + b
    ratio = p.get("target_ratio")
    if ratio:
        rw, rh = ratio
        tar = rw / rh
        cur = base_w / base_h
        if cur > tar:  # 偏宽 → 扩高
            canvas_w, canvas_h = base_w, int(base_w / tar)
            left_m, top_m = l, t + (canvas_h - base_h) // 2
        elif cur < tar:  # 偏高 → 扩宽
            canvas_h, canvas_w = base_h, int(base_h * tar)
            left_m, top_m = l + (canvas_w - base_w) // 2, t
        else:
            canvas_w, canvas_h = base_w, base_h
            left_m, top_m = l, t
    else:
        canvas_w, canvas_h = base_w, base_h
        left_m, top_m = l, t
    return canvas_w, canvas_h, left_m, top_m

def _offset_px(cw, ch, p):
    """根据偏移单位获取像素偏移量。"""
    if p.get("offset_unit", "px") == "px":
        return p["offset_x_val"], p["offset_y_val"]
    # 百分比偏移：按画布尺寸转换为像素
    return int(p["offset_x_val"] / 100 * cw), int(p["offset_y_val"] / 100 * ch)

# ---------- 单张图像处理 ----------
def process_single_image(img, p):
    ow, oh = img.size
    # 计算画布尺寸和前景起始位置
    canvas_w, canvas_h, base_x, base_y = _canvas_size(ow, oh, p)
    # 计算安全边距（阴影向外扩散的最大距离）
    pad = 0
    if p.get("shadow_enabled"):
        if p.get("shadow_unit", "px") != "px":
            pad = int(p["shadow_spread"] / 100 * min(ow, oh) + p["shadow_blur"] / 100 * min(ow, oh))
        else:
            pad = p["shadow_spread"] + p["shadow_blur"]
    full_w, full_h = canvas_w + 2 * pad, canvas_h + 2 * pad

    # -------- 背景层 --------
    if p.get("background_enabled"):
        # 放大并模糊原图作为背景（裁剪至画布大小）
        bg_core = background.create_blur_background(
            img,
            (canvas_w, canvas_h),
            scale_factor=p["background_scale"],
            blur_radius=p["background_blur"],
        )
    else:
        bg_core = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    # 将背景放置到包含安全边距的画布中央
    bg = Image.new("RGBA", (full_w, full_h), (0, 0, 0, 0))
    bg.paste(bg_core, (pad, pad))

    # -------- 前景偏移层 --------
    off_x, off_y = _offset_px(canvas_w, canvas_h, p)
    fg_x = pad + base_x + off_x
    fg_y = pad + base_y + off_y

    # -------- 阴影偏移（考虑前景和边距联动） --------
    # 将阴影偏移值转换为像素
    if p.get("shadow_unit", "px") != "px":
        base_sh_x = int(p["shadow_offset_x"] / 100 * canvas_w)
        base_sh_y = int(p["shadow_offset_y"] / 100 * canvas_h)
    else:
        base_sh_x = p["shadow_offset_x"]
        base_sh_y = p["shadow_offset_y"]
    # 前景偏移联动阴影偏移
    sh_off_x = base_sh_x + (off_x if p.get("shadow_link") else 0)
    sh_off_y = base_sh_y + (off_y if p.get("shadow_link") else 0)
    # 边距变化联动阴影偏移：按左右、上下边距差额调整
    if p.get("shadow_follow_margin"):
        if p.get("margin_unit", "px") != "px":
            l = int(p["margin_left"] / 100 * ow)
            r = int(p["margin_right"] / 100 * ow)
            t = int(p["margin_top"] / 100 * oh)
            b = int(p["margin_bottom"] / 100 * oh)
        else:
            l, r = p["margin_left"], p["margin_right"]
            t, b = p["margin_top"], p["margin_bottom"]
        sh_off_x += (l - r) // 2
        sh_off_y += (t - b) // 2

    # -------- 阴影层 --------
    if p.get("shadow_enabled"):
        # 计算阴影扩散和模糊的像素值
        if p.get("shadow_unit", "px") != "px":
            spread = int(p["shadow_spread"] / 100 * min(ow, oh))
            blur = int(p["shadow_blur"] / 100 * min(ow, oh))
        else:
            spread = p["shadow_spread"]
            blur = p["shadow_blur"]
        # 前景圆角半径像素值
        corner_radius = int(p.get("corner_radius_pct", 0) / 100 * min(ow, oh))
        sh_layer = shadow.create_shadow_layer(
            img.size,
            (full_w, full_h),
            corner_radius,
            spread,
            blur,
            p["shadow_opacity"],
            sh_off_x,
            sh_off_y,
        )
    else:
        sh_layer = Image.new("RGBA", (full_w, full_h), (0, 0, 0, 0))

    # -------- 前景层 --------
    cr_px = int(p["corner_radius_pct"] / 100 * min(ow, oh))
    fg_img = foreground.apply_round_corners(img, cr_px)
    fg_layer = Image.new("RGBA", (full_w, full_h), (0, 0, 0, 0))
    fg_layer.paste(fg_img, (fg_x, fg_y), fg_img)

    # -------- 图层合成与裁剪输出 --------
    merged = Image.alpha_composite(bg, sh_layer)
    merged = Image.alpha_composite(merged, fg_layer)
    # 裁剪掉安全边距区域，得到最终输出画布图像
    return merged.crop((pad, pad, pad + canvas_w, pad + canvas_h))

# ---------- 批量处理 ----------
def process_all_images(images, params, max_workers: int = 4):
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(process_single_image, img, params) for img in images]
    return [f.result() for f in futures]
