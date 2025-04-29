"""
处理核心（单图 / 批量）
修复：阴影 safe_pad 不再影响背景缩放
----------------------------------------------------------------
"""

from concurrent.futures import ThreadPoolExecutor
from PIL import Image
from model import background, shadow, foreground


# ---------- 工具函数 ----------


def _calc_canvas_size(orig_w, orig_h, p):
    """边距 + 比例 → 输出画布尺寸 (canvas_w, canvas_h) & 左上边距偏移。"""
    l, r = p["margin_left"], p["margin_right"]
    t, b = p["margin_top"], p["margin_bottom"]
    base_w, base_h = orig_w + l + r, orig_h + t + b

    ratio = p.get("target_ratio")
    if ratio:
        rw, rh = ratio
        tar = rw / rh
        cur = base_w / base_h
        if cur > tar:
            return base_w, int(base_w / tar), l, t + (int(base_w / tar) - base_h) // 2
        elif cur < tar:
            return int(base_h * tar), base_h, l + (int(base_h * tar) - base_w) // 2, t
    # 无比例变换
    return base_w, base_h, l, t


def _safe_pad(p):
    return p["shadow_spread"] + p["shadow_blur"] if p.get("shadow_enabled") else 0


def _offset_pixels(cw, ch, p):
    if p["offset_unit"] == "px":
        return p["offset_x_val"], p["offset_y_val"]
    return int(p["offset_x_val"] / 100 * cw), int(p["offset_y_val"] / 100 * ch)


# ---------- 单张处理 ----------


def process_single_image(img, p):
    ow, oh = img.size
    canvas_w, canvas_h, margin_x, margin_y = _calc_canvas_size(ow, oh, p)
    pad = _safe_pad(p)

    # ----- 1. 构建“总画布” -----
    full_w, full_h = canvas_w + 2 * pad, canvas_h + 2 * pad

    # ----- 2. 背景：只生成 canvas 大小，然后贴到 full 画布 -----
    bg_core = background.create_blur_background(
        img,
        (canvas_w, canvas_h),
        scale_factor=p["background_scale"],
        blur_radius=p["background_blur"],
    ) if p.get("background_enabled") else Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))

    bg = Image.new("RGBA", (full_w, full_h), (0, 0, 0, 0))
    bg.paste(bg_core, (pad, pad))

    # ----- 3. 阴影 -----
    if p.get("shadow_enabled"):
        sh = shadow.create_shadow_layer(
            img.size,
            (full_w, full_h),
            p.get("corner_radius", 0),
            p["shadow_spread"],
            p["shadow_blur"],
            p["shadow_opacity"],
            p["shadow_offset_x"],
            p["shadow_offset_y"],
        )
    else:
        sh = Image.new("RGBA", (full_w, full_h), (0, 0, 0, 0))

    # ----- 4. 前景 -----
    cr_px = int(p["corner_radius_pct"] / 100 * min(ow, oh))
    fg_img = foreground.apply_round_corners(img, cr_px)

    # 计算前景左上角
    off_x, off_y = _offset_pixels(canvas_w, canvas_h, p)
    pos_x = pad + margin_x + off_x
    pos_y = pad + margin_y + off_y

    fg_layer = Image.new("RGBA", (full_w, full_h), (0, 0, 0, 0))
    fg_layer.paste(fg_img, (pos_x, pos_y), fg_img)

    # ----- 5. 合成 & 裁剪 -----
    merged = Image.alpha_composite(bg, sh)
    merged = Image.alpha_composite(merged, fg_layer)
    # 把安全边距裁掉
    return merged.crop((pad, pad, pad + canvas_w, pad + canvas_h))


# ---------- 批量并行 ----------


def process_all_images(images, params, max_workers=4):
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = [ex.submit(process_single_image, im, params) for im in images]
    return [f.result() for f in futs]
