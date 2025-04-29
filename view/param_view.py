import math
import streamlit as st

def show_parameter_controls():
    """
    显示参数控制区域（背景、阴影、前景、边距设置），并返回参数字典。
    """
    # 输出比例
    aspect_option = st.selectbox("输出画面比例",
                                 ["原图比例", "9:16 竖屏", "4:5 竖屏"],
                                 index=0)
    if aspect_option == "原图比例":
        target_ratio = None
    elif aspect_option == "9:16 竖屏":
        target_ratio = (9, 16)
    else:
        target_ratio = (4, 5)

    # Tabs 分组
    tab_bg, tab_shadow, tab_fg, tab_margin = st.tabs(
        ["背景设置", "阴影设置", "前景设置", "边距设置"])

    params = {}

    # ---------- 背景 ----------
    with tab_bg:
        background_enabled = st.checkbox("启用毛玻璃背景", value=True)
        background_scale = st.slider("背景放大倍数", 1.0, 3.0, 1.2, 0.1)
        background_blur = st.slider("背景模糊半径", 0, 100, 20)
        params["background_enabled"] = background_enabled
        params["background_scale"] = background_scale
        params["background_blur"] = background_blur

    # ---------- 阴影 ----------
    with tab_shadow:
        shadow_enabled = st.checkbox("启用阴影效果", value=True)
        shadow_spread = st.slider("扩散半径", 0, 100, 30)
        shadow_blur = st.slider("阴影模糊强度", 0, 100, 30)
        shadow_opacity_pct = st.slider("阴影不透明度(%)", 0, 100, 50)
        shadow_opacity = shadow_opacity_pct / 100.0

        direction_mode = st.radio("阴影偏移控制", ["手动偏移", "光源角度"],
                                  index=0, horizontal=True)
        if direction_mode == "手动偏移":
            shadow_offset_x = st.slider("阴影偏移 X", -200, 200, 10)
            shadow_offset_y = st.slider("阴影偏移 Y", -200, 200, 10)
        else:
            shadow_angle = st.slider("光源方向 (角度)", 0, 360, 45)
            distance = shadow_spread
            rad = math.radians(shadow_angle)
            shadow_offset_x = int(distance * math.cos(rad))
            shadow_offset_y = -int(distance * math.sin(rad))

        params.update({
            "shadow_enabled": shadow_enabled,
            "shadow_spread": shadow_spread,
            "shadow_blur": shadow_blur,
            "shadow_opacity": shadow_opacity,
            "shadow_offset_x": shadow_offset_x,
            "shadow_offset_y": shadow_offset_y
        })

    # ---------- 前景 ----------
    with tab_fg:
        corner_pct = st.slider("圆角半径 (%)", 0, 50, 0,
                               help="相对于图片短边的百分比，50%≈圆形")
        params["corner_radius_pct"] = corner_pct

    # ---------- 边距 ----------
    with tab_margin:
        frame_margin = st.slider("边距 (px)", 0, 400, 40,
                                 help="中央高清图与毛玻璃背景边缘的距离")
        params["frame_margin"] = frame_margin

    params["target_ratio"] = target_ratio
    return params
