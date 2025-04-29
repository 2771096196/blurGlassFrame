import streamlit as st
from PIL import Image
from controller import processing_controller

# ----- 与后端一致的画布计算 -----
def _canvas_size(ow, oh, p):
    # 根据边距计算预览画布尺寸（像素值）
    l, r = p["margin_left"], p["margin_right"]
    t, b = p["margin_top"], p["margin_bottom"]
    base_w, base_h = ow + l + r, oh + t + b
    ratio = p.get("target_ratio")
    if ratio:
        rw, rh = ratio
        tar = rw / rh
        cur = base_w / base_h
        if cur > tar:
            return base_w, int(base_w / tar)
        elif cur < tar:
            return int(base_h * tar), base_h
    return base_w, base_h

# ----- 将所有像素参数按 scale 同步缩放 -----
def _scaled_params(p: dict, scale: float):
    p2 = p.copy()
    # 缩放边距参数（仅当单位为像素）
    if p2.get("margin_unit", "px") == "px":
        for m in ["margin_top", "margin_bottom", "margin_left", "margin_right"]:
            p2[m] = int(p2[m] * scale)
    # 缩放阴影参数（仅当单位为像素）
    if p2.get("shadow_unit", "px") == "px":
        for s in ["shadow_spread", "shadow_blur", "shadow_offset_x", "shadow_offset_y"]:
            p2[s] = int(p2[s] * scale)
    # 缩放背景模糊半径（背景模糊始终为像素单位）
    p2["background_blur"] = int(p2.get("background_blur", 0) * scale)
    # 缩放前景偏移量（仅当单位为像素）
    if p2.get("offset_unit", "px") == "px":
        p2["offset_x_val"] = int(p2["offset_x_val"] * scale)
        p2["offset_y_val"] = int(p2["offset_y_val"] * scale)
    return p2

def show_preview():
    if "images" not in st.session_state or not st.session_state["images"]:
        st.warning("暂无图片，请上传。")
        return

    images = st.session_state["images"]
    thumbs = st.session_state["thumbs"]
    names = st.session_state["filenames"]

    sel_name = st.selectbox("选择预览图片", names, 0)
    idx = names.index(sel_name)
    st.session_state["preview_index"] = idx

    # ---------- 预览质量滑块 ----------
    quality = st.slider("预览质量 (%)", 10, 100, 10, key="preview_quality")
    scale = quality / 100.0  # 统一缩放系数

    # ---------- 准备缩小后的图像 ----------
    orig_img = images[idx]
    new_size = (max(1, int(orig_img.width * scale)),
                max(1, int(orig_img.height * scale)))
    preview_base = orig_img.resize(new_size, Image.LANCZOS)

    # ---------- 同步缩小参数 ----------
    base_p = st.session_state.get("params", {}).copy()
    p_scaled = _scaled_params(base_p, scale)

    # ---------- 画布尺寸 & 渲染预览 ----------
    cw, ch = _canvas_size(*preview_base.size, p_scaled)
    p_scaled["output_size"] = (cw, ch)

    preview_img = processing_controller.process_single_image(preview_base, p_scaled)
    st.image(preview_img, caption="效果预览", use_column_width=True)
