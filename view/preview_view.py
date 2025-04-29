import streamlit as st
from controller import processing_controller


def _canvas_size(ow, oh, params):
    """和 processing_controller 计算方式保持一致（用于预览）。"""
    l, r = params["margin_left"], params["margin_right"]
    t, b = params["margin_top"], params["margin_bottom"]
    base_w, base_h = ow + l + r, oh + t + b
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


def show_preview():
    if "images" not in st.session_state or not st.session_state["images"]:
        st.warning("暂无图片，请上传。")
        return

    imgs = st.session_state["images"]
    thumbs = st.session_state["thumbs"]
    names = st.session_state["filenames"]

    fname = st.selectbox("选择预览图片", names)
    idx = names.index(fname)
    st.session_state["preview_index"] = idx

    params = st.session_state.get("params", {}).copy()
    # 缩略图尺寸决定 max canvas (无需额外 thumbnail，这里为 <=600)
    tw, th = thumbs[idx].size
    params["output_size"] = _canvas_size(tw, th, params)

    preview = processing_controller.process_single_image(thumbs[idx], params)
    st.image(preview, caption="效果预览")
