"""
业务控制层：单图 / 多图处理
-------------------------------------------------
改动：
1. 批量处理 process_all_images() 采用 ThreadPoolExecutor 并行，
   默认并发 4 个工作线程，可通过参数 max_workers 调节。
2. 单图流程保持上一版本（含安全画布防截断算法）。
"""

from concurrent.futures import ThreadPoolExecutor
from PIL import Image
from model import background, shadow, foreground


# ---------------- 单图处理（保持不变） ----------------
def _build_canvas_size(base_w: int, base_h: int, params: dict):
    safe_pad = 0
    if params.get("shadow_enabled", False):
        safe_pad = params.get("shadow_spread", 0) + params.get("shadow_blur", 0)
    return base_w + 2 * safe_pad, base_h + 2 * safe_pad, safe_pad


def process_single_image(image, params: dict):
    base_out_w, base_out_h = params["output_size"]
    canvas_w, canvas_h, pad = _build_canvas_size(base_out_w, base_out_h, params)

    # 背景
    if params.get("background_enabled", True):
        bg_layer = background.create_blur_background(
            image,
            (canvas_w, canvas_h),
            params.get("background_scale", 1.2),
            params.get("background_blur", 20),
        )
    else:
        bg_layer = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))

    # 阴影
    if params.get("shadow_enabled", True):
        shadow_layer = shadow.create_shadow_layer(
            image.size,
            (canvas_w, canvas_h),
            params.get("corner_radius", 0),
            params.get("shadow_spread", 30),
            params.get("shadow_blur", 30),
            params.get("shadow_opacity", 0.5),
            params.get("shadow_offset_x", 0),
            params.get("shadow_offset_y", 0),
        )
    else:
        shadow_layer = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))

    # 前景
    pct = params.get("corner_radius_pct")
    if pct is not None:
        corner_px = int(pct / 100.0 * min(image.size))
        corner_px = min(corner_px, min(image.size) // 2)
    else:
        corner_px = params.get("corner_radius", 0)

    fg_img = foreground.apply_round_corners(image, corner_px)
    fg_layer = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    fg_layer.paste(
        fg_img, ((canvas_w - image.width) // 2, (canvas_h - image.height) // 2), fg_img
    )

    # 合成
    merged = Image.alpha_composite(bg_layer, shadow_layer)
    merged = Image.alpha_composite(merged, fg_layer)

    # 裁剪回最终尺寸
    final = merged.crop((pad, pad, pad + base_out_w, pad + base_out_h))
    return final


# ---------------- 批量并行处理 ----------------
def process_all_images(images, params: dict, max_workers: int = 4):
    """
    并行处理多张图片。
    - images: PIL.Image 列表
    - params: 公共参数
    - max_workers: 线程数量（默认 4）
    """
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(process_single_image, img, params) for img in images]
        return [f.result() for f in futures]
