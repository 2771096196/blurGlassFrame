import math
import streamlit as st


def show_parameter_controls():
    """展示所有可调参数，返回 dict。"""

    # ---------- 输出比例 ----------
    ratio_opt = st.selectbox("输出画面比例",
                             ["原图比例", "9:16 竖屏", "4:5 竖屏"], 0)
    ratio_map = {"9:16 竖屏": (9, 16), "4:5 竖屏": (4, 5)}
    target_ratio = ratio_map.get(ratio_opt)

    # ---------- 分组 ----------
    tab_bg, tab_shadow, tab_fg, tab_margin, tab_offset = st.tabs(
        ["背景设置", "阴影设置", "前景设置", "边距设置", "偏移设置"]
    )
    p = {}       # 参数收集

    # === 背景 ===
    with tab_bg:
        p["background_enabled"] = st.checkbox("启用毛玻璃背景", True)
        p["background_scale"] = st.slider("背景放大倍数", 1.0, 5.0, 1.2, 0.05)
        p["background_blur"] = st.slider("背景模糊半径", 0, 100, 20)

    # === 阴影 ===
    with tab_shadow:
        p["shadow_enabled"] = st.checkbox("启用阴影效果", True)
        p["shadow_spread"] = st.slider("扩散半径", 0, 100, 30)
        p["shadow_blur"] = st.slider("阴影模糊强度", 0, 100, 30)
        p["shadow_opacity"] = st.slider("阴影不透明度(%)", 0, 100, 50) / 100.0

        # 手动 vs 光源角度
        mode = st.radio("阴影偏移控制", ["手动偏移", "光源角度"], horizontal=True)
        if mode == "光源角度":
            deg = st.slider("光源方向 (度)", 0, 360, 45)
            d = p["shadow_spread"]
            p["shadow_offset_x"] = int(d * math.cos(math.radians(deg)))
            p["shadow_offset_y"] = int(-d * math.sin(math.radians(deg)))
        else:
            p["shadow_offset_x"] = st.slider("阴影偏移 X(px)", -300, 300, 10)
            p["shadow_offset_y"] = st.slider("阴影偏移 Y(px)", -300, 300, 10)

    # === 前景 ===
    with tab_fg:
        p["corner_radius_pct"] = st.slider("圆角半径 (%)", 0, 50, 0)

    # === 边距 ===
    with tab_margin:
        uni = st.slider("统一边距 (px)", 0, 400, 40)
        adv = st.checkbox("启用独立边距")
        if adv:
            p["margin_top"] = st.slider("顶部边距 (px)", 0, 400, uni)
            p["margin_bottom"] = st.slider("底部边距 (px)", 0, 400, uni)
            p["margin_left"] = st.slider("左侧边距 (px)", 0, 400, uni)
            p["margin_right"] = st.slider("右侧边距 (px)", 0, 400, uni)
        else:
            p["margin_top"] = p["margin_bottom"] = p["margin_left"] = p["margin_right"] = uni

    # === 偏移 ===
    with tab_offset:
        unit = st.radio("偏移单位", ["像素(px)", "百分比(%)"], horizontal=True)
        p["offset_unit"] = "px" if unit == "像素(px)" else "%"
        if unit == "像素(px)":
            p["offset_x_val"] = st.slider("水平偏移 (px)", -400, 400, 0)
            p["offset_y_val"] = st.slider("垂直偏移 (px)", -400, 400, 0)
        else:
            p["offset_x_val"] = st.slider("水平偏移 (%)", -50, 50, 0)
            p["offset_y_val"] = st.slider("垂直偏移 (%)", -50, 50, 0)

    p["target_ratio"] = target_ratio
    return p
