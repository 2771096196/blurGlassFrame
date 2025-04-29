import streamlit as st
from PIL import Image
from controller import processing_controller
from view.param_view import DEFAULTS as default_params # 导入默认值以防万一

# ----- 画布计算 (这个函数在预览和最终输出中应该一致) -----
# 使用 processing_controller 中的版本，因为它更完整
_canvas_size = processing_controller._canvas_size

# ----- 将所有像素参数按 scale 同步缩放 -----
def _scaled_params(p: dict, scale: float):
    """为预览创建参数副本，并将像素单位参数按 scale 缩放。"""
    p2 = p.copy()
    # 缩放边距参数（仅当单位为像素）
    if p2.get("margin_unit", "像素(px)") == "像素(px)":
        use_independent = p2.get("ind_margin", False)
        if use_independent:
             for m in ["margin_top", "margin_bottom", "margin_left", "margin_right"]:
                 p2[m] = int(p2.get(m, 0) * scale)
        else:
             p2["margin_all"] = int(p2.get("margin_all", 0) * scale)
             # 同步更新独立值，以便 _canvas_size 能正确计算
             p2["margin_top"] = p2["margin_bottom"] = p2["margin_left"] = p2["margin_right"] = p2["margin_all"]

    # 缩放阴影参数（仅当单位为像素）
    if p2.get("shadow_unit", "像素(px)") == "像素(px)":
        for s in ["shadow_spread", "shadow_blur", "shadow_offset_x", "shadow_offset_y"]:
            # 偏移量可为负，其他非负
            val = p2.get(s, 0)
            scaled_val = int(val * scale)
            if "offset" not in s:
                 scaled_val = max(0, scaled_val)
            p2[s] = scaled_val

    # 缩放背景模糊半径
    p2["background_blur"] = max(0, int(p2.get("background_blur", 0) * scale))

    # 缩放前景偏移量（仅当单位为像素）
    if p2.get("offset_unit", "像素(px)") == "像素(px)":
        p2["offset_x_val"] = int(p2.get("offset_x_val", 0) * scale)
        p2["offset_y_val"] = int(p2.get("offset_y_val", 0) * scale)

    # --- 重要的：不缩放百分比值或比例值 ---
    # background_scale, corner_radius_pct, shadow_opacity, background_mask_opacity 等保持不变

    return p2

def show_preview():
    """显示图片预览区域及控制"""
    if "images" not in st.session_state or not st.session_state["images"]:
        st.warning("暂无图片，请上传。")
        return

    images = st.session_state["images"]
    thumbs = st.session_state["thumbs"]
    names = st.session_state["filenames"]

    # --- 选择预览图片 ---
    preview_idx = st.session_state.get("preview_index", 0)
    if preview_idx >= len(names):
        preview_idx = 0
    sel_name = st.selectbox(
        "选择预览图片", names,
        index=preview_idx,
        key="preview_selector"
    )
    current_preview_index = names.index(sel_name)
    st.session_state["preview_index"] = current_preview_index

    # --- 预览质量滑块 (控制缩放比例) ---
    # 降低默认值以提高初始性能
    quality = st.slider("预览质量 (%)", 10, 100, 50, key="preview_quality")
    scale = quality / 100.0

    # --- 准备缩小后的图像 ---
    original_img = images[current_preview_index]
    # 基于原图和缩放比例计算预览图尺寸
    preview_w = max(1, int(original_img.width * scale))
    preview_h = max(1, int(original_img.height * scale))
    try:
        preview_base_img = original_img.resize((preview_w, preview_h), Image.LANCZOS)
    except ValueError:
        st.error("无法生成预览图像，可能尺寸过小或过大。")
        return # 无法继续

    # --- 同步缩小参数 ---
    # 从 session_state 获取完整的、最新的参数集
    current_params = {}
    for key in default_params: # 使用导入的 DEFAULTS 确保 key 完整
         current_params[key] = st.session_state.get(key, default_params[key])

    # # 处理统一边距，确保 controller 能拿到正确的值
    # if not current_params["ind_margin"]:
    #      if current_params["margin_unit"] == "像素(px)":
    #          unified_margin = current_params["margin_all"]
    #          current_params["margin_top"] = unified_margin
    #          current_params["margin_bottom"] = unified_margin
    #          current_params["margin_left"] = unified_margin
    #          current_params["margin_right"] = unified_margin
    #      else: # "%"
    #          unified_margin_pct = current_params["margin_all_pct"]
    #          current_params["margin_top_pct"] = unified_margin_pct
    #          current_params["margin_bottom_pct"] = unified_margin_pct
    #          current_params["margin_left_pct"] = unified_margin_pct
    #          current_params["margin_right_pct"] = unified_margin_pct

    p_scaled = _scaled_params(current_params, scale)

    # --- 渲染预览 ---
    try:
        # 调用处理函数生成预览图
        preview_img = processing_controller.process_single_image(preview_base_img, p_scaled)

        # 显示预览图 (使用 use_container_width)
        st.image(
            preview_img,
            caption=f"效果预览: {names[current_preview_index]} @ {quality}%",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"生成预览时出错: {e}")
        st.image(preview_base_img, caption=f"预览失败，显示缩略图: {names[current_preview_index]}", use_container_width=True)