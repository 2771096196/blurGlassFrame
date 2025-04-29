import math
import streamlit as st

# -------- 默认参数表 --------
DEFAULTS = {
    "background_enabled": True,
    "background_scale": 1.20,
    "background_blur": 20,
    "shadow_enabled": True,
    "shadow_spread": 16,
    "shadow_blur": 30,
    "shadow_opacity": 0.72,
    "shadow_offset_x": 10,
    "shadow_offset_y": 10,
    # 新增：阴影参数单位及百分比默认值
    "shadow_unit": "px",
    "shadow_spread_pct": 5,
    "shadow_blur_pct": 5,
    "shadow_offset_x_pct": 1,
    "shadow_offset_y_pct": 1,
    "corner_radius_pct": 0,
    "margin_all": 40,
    "margin_top": 40,
    "margin_bottom": 40,
    "margin_left": 40,
    "margin_right": 40,
    # 新增：边距单位及百分比默认值
    "margin_unit": "px",
    "margin_all_pct": 10,
    "margin_top_pct": 10,
    "margin_bottom_pct": 10,
    "margin_left_pct": 10,
    "margin_right_pct": 10,
    "offset_unit": "px",
    "offset_x_val": 0,
    "offset_y_val": 0,
    # 新增：Offset 偏移的百分比值默认
    "offset_x_val_pct": 0,
    "offset_y_val_pct": 0,
    "shadow_link": True,
    # 新增：阴影跟随边距默认开启
    "shadow_follow_margin": True,
    "ratio": None,
}

def _reset(keys):
    """把给定 keys 重置成 DEFAULTS"""
    for k in keys:
        if k in DEFAULTS:
            st.session_state[k] = DEFAULTS[k]

def show_parameter_controls():
    """
    渲染所有控件并返回参数 dict。
    默认值写在 DEFAULTS 中，支持全局和分组“恢复默认”按钮。
    """
    # ----- 全局重置按钮 -----
    if st.button("全局恢复默认设置"):
        _reset(list(DEFAULTS.keys()))

    # ---------- 输出画面比例 ----------
    ratio_map = {
        "原图比例": None,
        "9:16 竖屏": (9, 16),
        "4:5 竖屏": (4, 5),
    }
    ratio_label = st.selectbox(
        "输出画面比例", list(ratio_map.keys()),
        index=list(ratio_map.values()).index(
            st.session_state.get("ratio", DEFAULTS["ratio"])
        ),
        key="ratio_label"
    )
    p = {}
    p["target_ratio"] = ratio_map[ratio_label]
    st.session_state["ratio"] = p["target_ratio"]

    # ---------- 参数选项卡 ----------
    tab_bg, tab_shadow, tab_fg, tab_margin, tab_offset = st.tabs(
        ["背景设置", "阴影设置", "前景设置", "边距设置", "偏移设置"]
    )

    # ========== 背景设置 ==========
    with tab_bg:
        if st.button("恢复默认", key="rst_bg"):
            _reset(["background_enabled", "background_scale", "background_blur"])
        p["background_enabled"] = st.checkbox(
            "启用毛玻璃背景",
            value=st.session_state.get("background_enabled", DEFAULTS["background_enabled"]),
            key="background_enabled"
        )
        p["background_scale"] = st.slider(
            "背景放大倍数", 1.0, 5.0,
            value=st.session_state.get("background_scale", DEFAULTS["background_scale"]),
            step=0.05, key="background_scale"
        )
        p["background_blur"] = st.slider(
            "背景模糊半径", 0, 100,
            value=st.session_state.get("background_blur", DEFAULTS["background_blur"]),
            key="background_blur"
        )

    # ========== 阴影设置 ==========
    with tab_shadow:
        if st.button("恢复默认", key="rst_shadow"):
            _reset([
                "shadow_enabled", "shadow_spread", "shadow_blur",
                "shadow_opacity", "shadow_offset_x", "shadow_offset_y",
                "shadow_unit", "shadow_spread_pct", "shadow_blur_pct",
                "shadow_offset_x_pct", "shadow_offset_y_pct"
            ])
        p["shadow_enabled"] = st.checkbox(
            "启用阴影效果",
            value=st.session_state.get("shadow_enabled", DEFAULTS["shadow_enabled"]),
            key="shadow_enabled",
        )
        # 阴影参数单位选择
        shadow_unit_sel = st.radio(
            "阴影参数单位", ["像素(px)", "百分比(%)"],
            horizontal=True,
            index=0 if str(st.session_state.get("shadow_unit", DEFAULTS["shadow_unit"])).endswith("px") else 1,
            key="shadow_unit"
        )
        # 将选项映射为内部值
        p["shadow_unit"] = "px" if shadow_unit_sel.endswith("(px)") else "%"

        p["shadow_spread"] = st.slider(
            f"扩散半径({'px' if p['shadow_unit']=='px' else '%'})",
            0, 100,
            value=(st.session_state.get("shadow_spread_pct", DEFAULTS["shadow_spread_pct"]) if p["shadow_unit"] == "%"
                   else st.session_state.get("shadow_spread", DEFAULTS["shadow_spread"])),
            key=("shadow_spread" if p["shadow_unit"] == "px" else "shadow_spread_pct")
        )
        p["shadow_blur"] = st.slider(
            f"阴影模糊强度({'px' if p['shadow_unit']=='px' else '%'})",
            0, 100,
            value=(st.session_state.get("shadow_blur_pct", DEFAULTS["shadow_blur_pct"]) if p["shadow_unit"] == "%"
                   else st.session_state.get("shadow_blur", DEFAULTS["shadow_blur"])),
            key=("shadow_blur" if p["shadow_unit"] == "px" else "shadow_blur_pct")
        )
        p["shadow_opacity"] = st.slider(
            "阴影不透明度(%)", 0, 100,
            value=int(st.session_state.get("shadow_opacity", DEFAULTS["shadow_opacity"]) * 100),
            key="shadow_opacity_slider",
        ) / 100.0
        st.session_state["shadow_opacity"] = p["shadow_opacity"]

        # 阴影偏移控制方式：手动偏移 or 光源角度
        mode = st.radio("阴影偏移控制", ["手动偏移", "光源角度"], horizontal=True, key="shadow_mode")
        if mode == "光源角度":
            deg = st.slider("光源方向 (°)", 0, 360, 45, key="shadow_deg")
            d = p["shadow_spread"]
            # 根据光源角度计算阴影偏移（若为百分比单位，计算结果视为百分比）
            p["shadow_offset_x"] = int(d * math.cos(math.radians(deg)))
            p["shadow_offset_y"] = int(-d * math.sin(math.radians(deg)))
        else:
            p["shadow_offset_x"] = st.slider(
                f"阴影偏移 X({'px' if p['shadow_unit']=='px' else '%'})",
                -400 if p["shadow_unit"] == "px" else -50,
                400 if p["shadow_unit"] == "px" else 50,
                value=(st.session_state.get("shadow_offset_x_pct", DEFAULTS["shadow_offset_x_pct"]) if p["shadow_unit"] == "%"
                       else st.session_state.get("shadow_offset_x", DEFAULTS["shadow_offset_x"])),
                key=("shadow_offset_x" if p["shadow_unit"] == "px" else "shadow_offset_x_pct"),
            )
            p["shadow_offset_y"] = st.slider(
                f"阴影偏移 Y({'px' if p['shadow_unit']=='px' else '%'})",
                -400 if p["shadow_unit"] == "px" else -50,
                400 if p["shadow_unit"] == "px" else 50,
                value=(st.session_state.get("shadow_offset_y_pct", DEFAULTS["shadow_offset_y_pct"]) if p["shadow_unit"] == "%"
                       else st.session_state.get("shadow_offset_y", DEFAULTS["shadow_offset_y"])),
                key=("shadow_offset_y" if p["shadow_unit"] == "px" else "shadow_offset_y_pct"),
            )

    # ========== 前景设置 ==========
    with tab_fg:
        if st.button("恢复默认", key="rst_fg"):
            _reset(["corner_radius_pct"])
        p["corner_radius_pct"] = st.slider(
            "圆角半径(%)", 0, 50,
            value=st.session_state.get("corner_radius_pct", DEFAULTS["corner_radius_pct"]),
            key="corner_radius_pct",
        )

    # ========== 边距设置 ==========
    with tab_margin:
        if st.button("恢复默认", key="rst_margin"):
            _reset([
                "margin_all", "margin_top", "margin_bottom", "margin_left", "margin_right",
                "margin_unit", "margin_all_pct", "margin_top_pct", "margin_bottom_pct", "margin_left_pct", "margin_right_pct",
                "shadow_follow_margin"
            ])
        # 边距单位选择
        margin_unit_sel = st.radio(
            "边距单位", ["像素(px)", "百分比(%)"], horizontal=True,
            index=0 if str(st.session_state.get("margin_unit", DEFAULTS["margin_unit"])).endswith("px") else 1,
            key="margin_unit"
        )
        p["margin_unit"] = "px" if margin_unit_sel.endswith("(px)") else "%"

        if p["margin_unit"] == "px":
            uni = st.slider(
                "统一边距(px)", 0, 400,
                value=st.session_state.get("margin_all", DEFAULTS["margin_all"]),
                key="margin_all",
            )
        else:
            uni = st.slider(
                "统一边距(%)", 0, 100,
                value=st.session_state.get("margin_all", DEFAULTS["margin_all"]),
                key="margin_all_pct",
            )
        adv = st.checkbox("启用独立边距", key="ind_margin")
        if adv:
            if p["margin_unit"] == "px":
                p["margin_top"] = st.slider("顶部边距(px)", 0, 400,
                                            value=st.session_state.get("margin_top", uni),
                                            key="margin_top")
                p["margin_bottom"] = st.slider("底部边距(px)", 0, 400,
                                               value=st.session_state.get("margin_bottom", uni),
                                               key="margin_bottom")
                p["margin_left"] = st.slider("左侧边距(px)", 0, 400,
                                             value=st.session_state.get("margin_left", uni),
                                             key="margin_left")
                p["margin_right"] = st.slider("右侧边距(px)", 0, 400,
                                              value=st.session_state.get("margin_right", uni),
                                              key="margin_right")
            else:
                p["margin_top"] = st.slider("顶部边距(%)", 0, 100,
                                            value=st.session_state.get("margin_top_pct", uni),
                                            key="margin_top_pct")
                p["margin_bottom"] = st.slider("底部边距(%)", 0, 100,
                                               value=st.session_state.get("margin_bottom_pct", uni),
                                               key="margin_bottom_pct")
                p["margin_left"] = st.slider("左侧边距(%)", 0, 100,
                                             value=st.session_state.get("margin_left_pct", uni),
                                             key="margin_left_pct")
                p["margin_right"] = st.slider("右侧边距(%)", 0, 100,
                                              value=st.session_state.get("margin_right_pct", uni),
                                              key="margin_right_pct")
        else:
            # 应用统一边距数值到四个边（根据单位区分像素或百分比）
            p["margin_top"] = p["margin_bottom"] = p["margin_left"] = p["margin_right"] = uni

        # 阴影跟随边距变化
        p["shadow_follow_margin"] = st.checkbox(
            "阴影跟随边距变化",
            value=st.session_state.get("shadow_follow_margin", DEFAULTS["shadow_follow_margin"]),
            key="shadow_follow_margin",
        )

    # ========== 偏移设置 ==========
    with tab_offset:
        if st.button("恢复默认", key="rst_offset"):
            _reset(["offset_unit", "offset_x_val", "offset_y_val", "offset_x_val_pct", "offset_y_val_pct", "shadow_link"])
        offset_unit_sel = st.radio(
            "偏移单位", ["像素(px)", "百分比(%)"], horizontal=True,
            index=0 if str(st.session_state.get("offset_unit", DEFAULTS["offset_unit"])).endswith("px") else 1,
            key="offset_unit"
        )
        p["offset_unit"] = "px" if offset_unit_sel.endswith("(px)") else "%"
        if p["offset_unit"] == "px":
            p["offset_x_val"] = st.slider("水平偏移(px)", -400, 400,
                                          value=st.session_state.get("offset_x_val", DEFAULTS["offset_x_val"]),
                                          key="offset_x_val")
            p["offset_y_val"] = st.slider("垂直偏移(px)", -400, 400,
                                          value=st.session_state.get("offset_y_val", DEFAULTS["offset_y_val"]),
                                          key="offset_y_val")
        else:
            p["offset_x_val"] = st.slider("水平偏移(%)", -50, 50,
                                          value=st.session_state.get("offset_x_val", DEFAULTS["offset_x_val"]),
                                          key="offset_x_val_pct")
            p["offset_y_val"] = st.slider("垂直偏移(%)", -50, 50,
                                          value=st.session_state.get("offset_y_val", DEFAULTS["offset_y_val"]),
                                          key="offset_y_val_pct")
        p["shadow_link"] = st.checkbox(
            "阴影跟随前景偏移",
            value=st.session_state.get("shadow_link", DEFAULTS["shadow_link"]),
            key="shadow_link",
        )

    return p
