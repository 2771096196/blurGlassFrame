from concurrent.futures import ThreadPoolExecutor
from PIL import Image
from model import background, shadow, foreground

# --- 工具函数 (_canvas_size, _offset_px 保持不变，使用上一轮修正后的版本) ---
def _canvas_size(ow, oh, p):
    """根据四边边距和目标比例计算画布尺寸 & 前景基线位置（不含安全边距）。"""
    is_px_margin = p.get("margin_unit", "像素(px)") == "像素(px)"
    use_independent = p.get("ind_margin", False)
    if use_independent:
        if is_px_margin:
            l, r = p.get("margin_left", 0), p.get("margin_right", 0)
            t, b = p.get("margin_top", 0), p.get("margin_bottom", 0)
        else:
            l = int(p.get("margin_left_pct", 0) / 100 * ow)
            r = int(p.get("margin_right_pct", 0) / 100 * ow)
            t = int(p.get("margin_top_pct", 0) / 100 * oh)
            b = int(p.get("margin_bottom_pct", 0) / 100 * oh)
    else:
        if is_px_margin:
            margin_all = p.get("margin_all", 0)
            l = r = t = b = margin_all
        else:
            margin_all_pct = p.get("margin_all_pct", 0)
            l = r = int(margin_all_pct / 100 * ow)
            t = b = int(margin_all_pct / 100 * oh)
    base_w = ow + l + r
    base_h = oh + t + b
    ratio = p.get("target_ratio")
    if ratio:
        rw, rh = ratio
        tar = rw / rh
        cur = base_w / base_h if base_h > 0 else tar
        if cur > tar:
            canvas_w = base_w
            canvas_h = int(base_w / tar) if tar > 0 else base_h
            base_x = l
            base_y = t + (canvas_h - base_h) // 2
        elif cur < tar:
            canvas_h = base_h
            canvas_w = int(base_h * tar)
            base_x = l + (canvas_w - base_w) // 2
            base_y = t
        else:
            canvas_w, canvas_h = base_w, base_h
            base_x, base_y = l, t
    else:
        canvas_w, canvas_h = base_w, base_h
        base_x, base_y = l, t
    return canvas_w, canvas_h, base_x, base_y

def _offset_px(cw, ch, p):
    """根据偏移单位 ("像素(px)" 或 "百分比(%)") 获取像素偏移量。"""
    is_px_offset = p.get("offset_unit", "像素(px)") == "像素(px)"
    if is_px_offset:
        return p.get("offset_x_val", 0), p.get("offset_y_val", 0)
    else:
        off_x_pct = p.get("offset_x_val_pct", 0)
        off_y_pct = p.get("offset_y_val_pct", 0)
        return int(off_x_pct / 100 * cw), int(off_y_pct / 100 * ch)


# ---------- 单张图像处理 ----------
def process_single_image(img, p):
    """处理单张图片，应用所有效果。"""
    ow, oh = img.size
    canvas_w, canvas_h, base_x, base_y = _canvas_size(ow, oh, p)
    pad = 0
    if p.get("shadow_enabled"):
        is_px_shadow = p.get("shadow_unit", "像素(px)") == "像素(px)"
        if is_px_shadow:
             spread = p.get("shadow_spread", 0)
             blur = p.get("shadow_blur", 0)
        else:
             spread = int(p.get("shadow_spread_pct", 0) / 100 * min(ow, oh))
             blur = int(p.get("shadow_blur_pct", 0) / 100 * min(ow, oh))
        pad = max(0, spread + blur)
    full_w = canvas_w + 2 * pad
    full_h = canvas_h + 2 * pad

    # -------- 背景层 --------
    bg_core = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    if p.get("background_enabled"):
        # *** 调用 background.create_blur_background 时传递蒙版不透明度 ***
        bg_core = background.create_blur_background(
            original_img=img,
            output_size=(canvas_w, canvas_h),
            scale_factor=p.get("background_scale", 1.0),
            blur_radius=p.get("background_blur", 0),
            mask_type=p.get("background_mask", "无"),
            mask_opacity=p.get("background_mask_opacity", 40) # 传递不透明度
        )

    bg = Image.new("RGBA", (full_w, full_h), (0, 0, 0, 0))
    bg.paste(bg_core, (pad, pad))

    # -------- 前景偏移层 --------
    off_x, off_y = _offset_px(canvas_w, canvas_h, p)
    fg_x = pad + base_x + off_x
    fg_y = pad + base_y + off_y

    # -------- 阴影偏移（考虑联动）--------
    is_px_shadow = p.get("shadow_unit", "像素(px)") == "像素(px)"
    if is_px_shadow:
        base_sh_x = p.get("shadow_offset_x", 0)
        base_sh_y = p.get("shadow_offset_y", 0)
    else:
        base_sh_x = int(p.get("shadow_offset_x_pct", 0) / 100 * canvas_w)
        base_sh_y = int(p.get("shadow_offset_y_pct", 0) / 100 * canvas_h)
    sh_off_x = base_sh_x + (off_x if p.get("shadow_link") else 0)
    sh_off_y = base_sh_y + (off_y if p.get("shadow_link") else 0)
    if p.get("shadow_follow_margin"):
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
        else:
            if is_px_margin:
                margin_all_px = p.get("margin_all", 0)
                l_px = r_px = t_px = b_px = margin_all_px
            else:
                margin_all_pct = p.get("margin_all_pct", 0)
                l_px = r_px = int(margin_all_pct / 100 * ow)
                t_px = b_px = int(margin_all_pct / 100 * oh)
        sh_off_x += (l_px - r_px) // 2
        sh_off_y += (t_px - b_px) // 2

    # -------- 阴影层 --------
    sh_layer = Image.new("RGBA", (full_w, full_h), (0, 0, 0, 0))
    if p.get("shadow_enabled"):
        is_px_shadow = p.get("shadow_unit", "像素(px)") == "像素(px)"
        if is_px_shadow:
             spread = p.get("shadow_spread", 0)
             blur = p.get("shadow_blur", 0)
        else:
             spread = int(p.get("shadow_spread_pct", 0) / 100 * min(ow, oh))
             blur = int(p.get("shadow_blur_pct", 0) / 100 * min(ow, oh))
        corner_radius_px = int(p.get("corner_radius_pct", 0) / 100 * min(ow, oh))
        sh_layer = shadow.create_shadow_layer(
            orig_size=img.size,
            output_size=(full_w, full_h),
            corner_radius=corner_radius_px,
            spread_radius=max(0, spread),
            blur_radius=max(0, blur),
            opacity=p.get("shadow_opacity", 0.5),
            offset_x=sh_off_x,
            offset_y=sh_off_y,
        )

    # -------- 前景层 --------
    cr_px = int(p.get("corner_radius_pct", 0) / 100 * min(ow, oh))
    fg_img = foreground.apply_round_corners(img, cr_px)
    fg_layer = Image.new("RGBA", (full_w, full_h), (0, 0, 0, 0))
    fg_layer.paste(fg_img, (fg_x, fg_y), fg_img)

    # -------- 图层合成与裁剪输出 --------
    merged = Image.alpha_composite(bg, sh_layer)
    merged = Image.alpha_composite(merged, fg_layer)
    final_crop_box = (pad, pad, pad + canvas_w, pad + canvas_h)
    final_crop_box = (
        max(0, final_crop_box[0]), max(0, final_crop_box[1]),
        min(full_w, final_crop_box[2]), min(full_h, final_crop_box[3])
    )
    if final_crop_box[2] > final_crop_box[0] and final_crop_box[3] > final_crop_box[1]:
        return merged.crop(final_crop_box)
    else:
        return Image.new("RGBA", (canvas_w if canvas_w>0 else 1, canvas_h if canvas_h>0 else 1), (0,0,0,0))


# ---------- 批量处理 ----------
def process_all_images(images, params, max_workers: int = 4):
    """使用线程池并行处理所有图像。"""
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(process_single_image, img, params.copy()): i for i, img in enumerate(images)}
        result_map = {}
        for future in futures:
            index = futures[future]
            try:
                result_map[index] = future.result()
            except Exception as e:
                print(f"Error processing image at index {index}: {e}")
                result_map[index] = None
        for i in range(len(images)):
             results.append(result_map.get(i))
    return results