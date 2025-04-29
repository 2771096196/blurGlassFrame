"""
核心合成逻辑
-------------------------------------------------------------
- 背景放大倍数：仅放大背景图，再居中裁剪到 canvas，不再改变画布尺寸
- 支持四边边距、目标比例、前景/阴影偏移 & 是否跟随
"""

from concurrent.futures import ThreadPoolExecutor
from PIL import Image
from model import background, shadow, foreground


# ---------- 工具 ----------


def _canvas_size(ow, oh, p):
    """根据四边边距 + 目标比例 计算画布尺寸 & 前景左上角基线 (不含 safe_pad)。"""
    l, r = p["margin_left"], p["margin_right"]
    t, b = p["margin_top"], p["margin_bottom"]
    base_w, base_h = ow + l + r, oh + t + b

    ratio = p.get("target_ratio")
    if ratio:
        rw, rh = ratio
        tar = rw / rh
        cur = base_w / base_h
        if cur > tar:                      # 偏宽 → 扩高
            canvas_w, canvas_h = base_w, int(base_w / tar)
            left_m, top_m = l, t + (canvas_h - base_h) // 2
        elif cur < tar:                    # 偏高 → 扩宽
            canvas_h, canvas_w = base_h, int(base_h * tar)
            left_m, top_m = l + (canvas_w - base_w) // 2, t
        else:
            canvas_w, canvas_h = base_w, base_h
            left_m, top_m = l, t
    else:
        canvas_w, canvas_h, left_m, top_m = base_w, base_h, l, t

    return canvas_w, canvas_h, left_m, top_m


def _safe_pad(p):
    return p["shadow_spread"] + p["shadow_blur"] if p.get("shadow_enabled") else 0


def _offset_px(cw, ch, p):
    if p["offset_unit"] == "px":
        return p["offset_x_val"], p["offset_y_val"]
    # 百分比
    return int(p["offset_x_val"] / 100 * cw), int(p["offset_y_val"] / 100 * ch)


# ---------- 单张处理 ----------


def process_single_image(img, p):
    ow, oh = img.size
    canvas_w, canvas_h, base_x, base_y = _canvas_size(ow, oh, p)
    pad = _safe_pad(p)
    full_w, full_h = canvas_w + 2 * pad, canvas_h + 2 * pad

    # -------- 背景层 --------
    if p.get("background_enabled"):
        # 仅在 canvas 尺寸内放大 & 裁剪
        bg_core = background.create_blur_background(
            img,
            (canvas_w, canvas_h),
            scale_factor=p["background_scale"],
            blur_radius=p["background_blur"],
        )
    else:
        bg_core = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))

    bg = Image.new("RGBA", (full_w, full_h), (0, 0, 0, 0))
    bg.paste(bg_core, (pad, pad))

    # -------- 偏移量 --------
    off_x, off_y = _offset_px(canvas_w, canvas_h, p)
    fg_x = pad + base_x + off_x
    fg_y = pad + base_y + off_y

    # 阴影偏移（可选跟随）
    sh_off_x = p["shadow_offset_x"] + (off_x if p.get("shadow_link") else 0)
    sh_off_y = p["shadow_offset_y"] + (off_y if p.get("shadow_link") else 0)

    # -------- 阴影层 --------
    if p.get("shadow_enabled"):
        sh = shadow.create_shadow_layer(
            img.size,
            (full_w, full_h),
            p.get("corner_radius", 0),
            p["shadow_spread"],
            p["shadow_blur"],
            p["shadow_opacity"],
            sh_off_x,
            sh_off_y,
        )
    else:
        sh = Image.new("RGBA", (full_w, full_h), (0, 0, 0, 0))

    # -------- 前景层 --------
    cr_px = int(p["corner_radius_pct"] / 100 * min(ow, oh))
    fg_img = foreground.apply_round_corners(img, cr_px)
    fg_layer = Image.new("RGBA", (full_w, full_h), (0, 0, 0, 0))
    fg_layer.paste(fg_img, (fg_x, fg_y), fg_img)

    # -------- 合成 & 裁剪 --------
    merged = Image.alpha_composite(bg, sh)
    merged = Image.alpha_composite(merged, fg_layer)
    return merged.crop((pad, pad, pad + canvas_w, pad + canvas_h))


# ---------- 批量并行 ----------


def process_all_images(images, params, max_workers: int = 4):
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futs = [pool.submit(process_single_image, im, params) for im in images]
    return [f.result() for f in futs]
