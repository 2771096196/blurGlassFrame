import streamlit as st
from controller import processing_controller

def show_preview():
    """
    预览区域：选择某张图片并根据当前参数实时预览处理效果。
    依赖 session_state: images, filenames, thumbs, params。
    """
    if "images" not in st.session_state or len(st.session_state["images"]) == 0:
        st.warning("暂无图片，请先上传。")
        return

    images = st.session_state["images"]
    filenames = st.session_state["filenames"]
    thumbs = st.session_state["thumbs"]

    # 选择预览图片
    selected_name = st.selectbox("选择预览图片", filenames, index=0)
    idx = filenames.index(selected_name)
    st.session_state["preview_index"] = idx

    params = st.session_state.get("params", {})
    preview_img = thumbs[idx]

    if params:
        params_preview = params.copy()

        # ============ 计算输出尺寸 ============
        orig_w, orig_h = preview_img.size
        frame_margin = params_preview.get("frame_margin", 0)
        target_ratio = params_preview.get("target_ratio")

        # 先按比例扩展（若指定）
        if target_ratio:
            ratio_w, ratio_h = target_ratio
            target_r = ratio_w / ratio_h
            orig_r = orig_w / orig_h
            if orig_r > target_r:                 # 原图偏宽
                base_w = orig_w
                base_h = int(orig_w / target_r)
            elif orig_r < target_r:               # 原图偏高
                base_h = orig_h
                base_w = int(orig_h * target_r)
            else:
                base_w, base_h = orig_w, orig_h
        else:
            base_w, base_h = orig_w, orig_h

        # 加上四边边距
        out_w = base_w + 2 * frame_margin
        out_h = base_h + 2 * frame_margin

        params_preview["output_size"] = (out_w, out_h)

        # 处理并显示
        result = processing_controller.process_single_image(preview_img,
                                                            params_preview)
        st.image(result, caption="效果预览", use_column_width=True)
    else:
        st.image(preview_img, caption="原图预览", use_column_width=True)
