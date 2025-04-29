# ---------------- 工具 ----------------
def _canvas_size(orig_w, orig_h, params):
    l, r = params["margin_left"], params["margin_right"]
    t, b = params["margin_top"], params["margin_bottom"]
    base_w, base_h = orig_w + l + r, orig_h + t + b
    ratio = params.get("target_ratio")
    if ratio:
        rw, rh = ratio
        tar = rw / rh
        cur = base_w / base_h
        if cur > tar:
            return base_w, int(base_w / tar)
        elif cur < tar:
            return int(base_h * tar), base_h
    return base_w, base_h
