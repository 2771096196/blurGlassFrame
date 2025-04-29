# -*- coding: utf-8 -*-
"""
参数调整界面视图 (param_view.py)
-------------------------------------------------
负责渲染所有用户可调参数的控件，并管理这些参数的状态。

主要功能:
1. 初始化 session_state 中的所有参数默认值。
2. 提供全局和各部分的参数重置功能。
3. 使用选项卡 (Tabs) 分类显示不同类型的参数控件 (背景、阴影、前景、边距、偏移)。
4. 将控件直接绑定到 st.session_state 中的相应键 (key)。
5. 处理单位切换（像素 vs 百分比）、独立边距切换等逻辑。
6. 返回包含所有当前参数值的字典。

改动记录:
- 2025-04-29:
    - 根据用户要求，注释掉了背景内容缩放 (background_scale) 的滑块。
    - 确认蒙版不透明度 (background_mask_opacity) 滑块通过 key 直接绑定 session_state，
      理论上应能实时更新预览，无需额外逻辑。添加注释说明。
    - 添加更详细的中文注释，统一代码风格。
"""

import math
import streamlit as st

# -------- 默认参数表 (DEFAULTS) --------
# 定义所有可配置参数及其默认值
# 这个字典是参数状态管理的基石
DEFAULTS = {
    "background_enabled": True,          # 是否启用背景
    "background_scale": 1.0,             # 背景内容缩放比例 (>=1.0) - 相关滑块已注释掉
    "background_blur": 20,               # 背景高斯模糊半径 (像素)
    "background_mask": "无",             # 背景蒙版类型 ("无", "白色透明蒙版", "黑色透明蒙版")
    "background_mask_opacity": 40,       # 背景蒙版不透明度 (0-100, 百分比)
    "shadow_enabled": True,              # 是否启用阴影
    "shadow_spread": 16,                 # 阴影扩散半径 (像素)
    "shadow_blur": 30,                   # 阴影模糊半径 (像素)
    "shadow_opacity": 0.72,              # 阴影不透明度 (0.0-1.0)
    "shadow_offset_x": 10,               # 阴影水平偏移 (像素)
    "shadow_offset_y": 10,               # 阴影垂直偏移 (像素)
    "shadow_unit": "像素(px)",           # 阴影参数单位 ("像素(px)" 或 "百分比(%)")
    "shadow_spread_pct": 5,              # 阴影扩散半径 (百分比)
    "shadow_blur_pct": 5,                # 阴影模糊半径 (百分比)
    "shadow_offset_x_pct": 1,            # 阴影水平偏移 (百分比)
    "shadow_offset_y_pct": 1,            # 阴影垂直偏移 (百分比)
    "corner_radius_pct": 0,              # 前景圆角半径 (相对于短边的百分比)
    "margin_all": 40,                    # 统一边距 (像素)
    "margin_top": 40,                    # 上边距 (像素)
    "margin_bottom": 40,                 # 下边距 (像素)
    "margin_left": 40,                   # 左边距 (像素)
    "margin_right": 40,                  # 右边距 (像素)
    "margin_unit": "像素(px)",           # 边距单位 ("像素(px)" 或 "百分比(%)")
    "margin_all_pct": 10,                # 统一边距 (百分比)
    "margin_top_pct": 10,                # 上边距 (百分比)
    "margin_bottom_pct": 10,             # 下边距 (百分比)
    "margin_left_pct": 10,               # 左边距 (百分比)
    "margin_right_pct": 10,              # 右边距 (百分比)
    "offset_unit": "像素(px)",           # 前景偏移单位 ("像素(px)" 或 "百分比(%)")
    "offset_x_val": 0,                   # 前景水平偏移值 (像素)
    "offset_y_val": 0,                   # 前景垂直偏移值 (像素)
    "offset_x_val_pct": 0,               # 前景水平偏移值 (百分比)
    "offset_y_val_pct": 0,               # 前景垂直偏移值 (百分比)
    "shadow_link": True,                 # 阴影是否跟随前景一起偏移
    "shadow_follow_margin": True,        # 阴影是否根据边距差值自动调整位置
    "ratio": None,                       # 输出画面比例 (None 或 (宽比例, 高比例) tuple)
    "ind_margin": False,                 # 是否启用独立边距控制
}

def initialize_state():
    """
    初始化 Streamlit Session State。
    确保 DEFAULTS 字典中定义的每个参数都在 st.session_state 中有对应的初始值。
    防止因缺少键而导致的 KeyError。
    """
    for key, default_value in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

def _reset(keys_to_reset):
    """
    重置 Session State 中指定的参数。
    将 `keys_to_reset` 列表中的每个键的值恢复为其在 DEFAULTS 中定义的默认值。
    重置后调用 st.rerun() 强制刷新界面。

    Args:
        keys_to_reset (list): 需要重置的参数键名列表。
    """
    for k in keys_to_reset:
        if k in DEFAULTS:
            st.session_state[k] = DEFAULTS[k]
    st.rerun() # 强制页面重新运行以应用默认值

def show_parameter_controls():
    """
    渲染所有参数控制 UI 元素（滑块、复选框、单选按钮等）。
    使用 Streamlit 的 Tabs 组件将参数分组显示。
    所有控件的值都直接通过 `key` 参数绑定到 `st.session_state`。
    最后，从 `st.session_state` 收集所有参数值，处理统一边距逻辑，并返回参数字典。

    Returns:
        dict: 包含当前所有参数设置的字典。
    """
    initialize_state() # 确保所有状态已初始化

    # --- 全局重置按钮 ---
    if st.button("全局恢复默认设置"):
        _reset(list(DEFAULTS.keys())) # 重置所有参数

    # --- 输出画面比例 ---
    # 定义可选的画面比例及其对应的标签
    ratio_map = {
        "原图比例": None,
        "9:16 竖屏": (9, 16),
        "4:5 竖屏": (4, 5),
        # 可以根据需要添加更多比例选项
    }
    current_ratio = st.session_state.ratio # 获取当前状态中的比例值
    ratio_values = list(ratio_map.values()) # 获取所有比例值列表
    try:
        # 找到当前比例值在列表中的索引，用于设置 selectbox 的默认选项
        ratio_index = ratio_values.index(current_ratio)
    except ValueError:
        # 如果当前状态中的值无效或不存在，则使用默认值的索引
        ratio_index = ratio_values.index(DEFAULTS["ratio"])
        st.session_state.ratio = DEFAULTS["ratio"] # 同时更新状态为默认值

    # 使用 selectbox 让用户选择比例
    ratio_label = st.selectbox(
        "输出画面比例",
        options=list(ratio_map.keys()), # 显示给用户的选项标签
        index=ratio_index,               # 默认选中的索引
        key="ratio_selector",            # 为控件分配一个 key (虽然这里不直接用它来读值)
        help="选择最终输出图片的宽高比。选择“原图比例”将保持原始宽高比，仅受边距影响。" # 添加提示信息
    )
    # 当用户选择新的比例时，直接更新 session_state 中的 'ratio' 值
    st.session_state.ratio = ratio_map[ratio_label]

    # --- 参数选项卡 ---
    # 使用 Tabs 将参数设置分组
    tab_bg, tab_shadow, tab_fg, tab_margin, tab_offset = st.tabs(
        ["背景设置", "阴影设置", "前景设置", "边距设置", "偏移设置"]
    )

    # -------- 背景设置 (Background Tab) --------
    with tab_bg:
        # 背景部分重置按钮
        if st.button("恢复背景默认", key="rst_bg"):
            _reset([
                "background_enabled",
                "background_scale",      # 即使滑块注释了，也重置其状态值
                "background_blur",
                "background_mask",
                "background_mask_opacity"
            ])

        # 启用/禁用背景复选框
        st.checkbox("启用毛玻璃背景", key="background_enabled", help="是否生成并显示模糊的背景图层。")

        # --- 【修改要求 2】背景内容缩放功能（代码注释掉） ---
        # st.slider(
        #     "背景内容缩放",
        #     min_value=1.0, max_value=5.0, step=0.05,
        #     key="background_scale",
        #     help="调整背景层相对于原始图像内容的放大程度，越大越模糊。1.0 表示不缩放。"
        # )
        # st.caption("背景内容缩放滑块已根据要求注释掉。将始终使用默认值 1.0。") # 添加说明

        # 背景模糊半径滑块
        st.slider(
            "背景模糊半径",
            min_value=0, max_value=100,
            key="background_blur",
            help="调整背景层的高斯模糊强度，0 表示不模糊。"
        )

        # 背景蒙版类型单选按钮
        bg_mask_options = ["无", "白色透明蒙版", "黑色透明蒙版"]
        # 确保状态中的值是有效选项，否则设为默认值
        if st.session_state.background_mask not in bg_mask_options:
            st.session_state.background_mask = DEFAULTS["background_mask"]
        st.radio(
            "背景蒙版",
            options=bg_mask_options,
            key="background_mask", # 直接绑定到 state
            horizontal=True,       # 水平排列选项
            help="在模糊背景上叠加一层半透明颜色蒙版。"
        )

        # --- 【修改要求 1 相关】蒙版不透明度 ---
        # 仅当选择了蒙版类型（非 "无"）时，才显示不透明度滑块
        if st.session_state.background_mask != "无":
            st.slider(
                "蒙版不透明度 (%)",
                min_value=0, max_value=100,
                key="background_mask_opacity", # 直接绑定到 state，值改变会自动触发 rerun
                help="调整蒙版的透明度，0% 完全透明，100% 完全不透明。此滑块直接更新预览。"
            )
            # **说明**: 此处使用 key 直接绑定 session_state，Streamlit 会在值改变时自动重新运行脚本，
            # preview_view.py 在每次重新运行时会读取最新的 session_state['background_mask_opacity']，
            # 因此理论上不需要切换其他按钮，效果就应该实时更新。如果仍有问题，可能与 Streamlit 版本或缓存有关。

    # -------- 阴影设置 (Shadow Tab) --------
    with tab_shadow:
        # 阴影部分重置按钮
        if st.button("恢复阴影默认", key="rst_shadow"):
             _reset([
                 "shadow_enabled", "shadow_spread", "shadow_blur", "shadow_opacity",
                 "shadow_offset_x", "shadow_offset_y", "shadow_unit",
                 "shadow_spread_pct", "shadow_blur_pct", "shadow_offset_x_pct", "shadow_offset_y_pct"
             ])
        # 启用/禁用阴影复选框
        st.checkbox("启用阴影效果", key="shadow_enabled", help="是否为前景图像添加阴影。")

        # 阴影参数单位选择 (像素 vs 百分比)
        shadow_unit_options = ["像素(px)", "百分比(%)"]
        # 确保状态中的单位有效
        if st.session_state.shadow_unit not in shadow_unit_options:
             st.session_state.shadow_unit = DEFAULTS["shadow_unit"]
        st.radio(
             "阴影参数单位",
             options=shadow_unit_options,
             key="shadow_unit", # 直接绑定 state
             horizontal=True,
             help="选择阴影相关参数（扩散、模糊、偏移）的单位。百分比是相对于画布尺寸计算的。"
        )

        # 根据选择的单位显示对应的滑块
        is_px_shadow = st.session_state.shadow_unit == "像素(px)"
        if is_px_shadow:
             st.slider("扩散半径(px)", 0, 100, key="shadow_spread", help="阴影向外扩展的大小。")
             st.slider("阴影模糊强度(px)", 0, 100, key="shadow_blur", help="阴影边缘的模糊程度。")
             st.slider("阴影偏移 X(px)", -400, 400, key="shadow_offset_x", help="阴影在水平方向的偏移量，正右负左。")
             st.slider("阴影偏移 Y(px)", -400, 400, key="shadow_offset_y", help="阴影在垂直方向的偏移量，正下负上。")
        else: # 百分比单位
             st.slider("扩散半径(%)", 0, 100, key="shadow_spread_pct", help="阴影向外扩展的大小（占画布短边百分比）。")
             st.slider("阴影模糊强度(%)", 0, 100, key="shadow_blur_pct", help="阴影边缘的模糊程度（占画布短边百分比）。")
             st.slider("阴影偏移 X(%)", -50, 50, key="shadow_offset_x_pct", help="阴影水平偏移（占画布宽度百分比）。")
             st.slider("阴影偏移 Y(%)", -50, 50, key="shadow_offset_y_pct", help="阴影垂直偏移（占画布高度百分比）。")

        # 阴影不透明度滑块 (显示为 0-100，存储为 0.0-1.0)
        # 使用一个临时的 key (shadow_opacity_display) 来处理显示值，然后更新实际的 state (shadow_opacity)
        opacity_display = st.slider(
             "阴影不透明度(%)",
             min_value=0, max_value=100,
             # 将 state 中的小数转换为百分比整数显示
             value=int(st.session_state.shadow_opacity * 100),
             key="shadow_opacity_display", # 临时 key
             help="调整阴影的整体不透明度。"
        )
        # 将滑块的百分比值转换回 0.0-1.0 的小数并更新到实际的 session_state
        st.session_state.shadow_opacity = float(opacity_display) / 100.0

    # -------- 前景设置 (Foreground Tab) --------
    with tab_fg:
        # 前景部分重置按钮
        if st.button("恢复前景默认", key="rst_fg"):
             _reset(["corner_radius_pct"])
        # 圆角半径滑块
        st.slider(
            "圆角半径(%)",
            min_value=0, max_value=50,
            key="corner_radius_pct", # 直接绑定 state
            help="设置前景图像的圆角大小，百分比相对于图像短边。"
        )

    # -------- 边距设置 (Margin Tab) --------
    with tab_margin:
        # 边距部分重置按钮
        if st.button("恢复边距默认", key="rst_margin"):
             _reset([
                 "margin_all", "margin_top", "margin_bottom", "margin_left", "margin_right",
                 "margin_unit", "margin_all_pct", "margin_top_pct", "margin_bottom_pct",
                 "margin_left_pct", "margin_right_pct", "ind_margin", "shadow_follow_margin"
             ])
        # 边距单位选择 (像素 vs 百分比)
        margin_unit_options = ["像素(px)", "百分比(%)"]
        # 确保状态中的单位有效
        if st.session_state.margin_unit not in margin_unit_options:
             st.session_state.margin_unit = DEFAULTS["margin_unit"]
        st.radio(
            "边距单位",
            options=margin_unit_options,
            key="margin_unit", # 直接绑定 state
            horizontal=True,
            help="选择边距值的单位。百分比是相对于原始图像尺寸计算的。"
        )

        # 独立边距控制复选框
        st.checkbox("启用独立边距", key="ind_margin", help="勾选后可以分别设置上下左右四个方向的边距，否则使用统一边距。")

        # 根据单位和是否独立边距显示对应滑块
        is_px_margin = st.session_state.margin_unit == "像素(px)"
        use_independent = st.session_state.ind_margin

        if use_independent: # 独立边距
             if is_px_margin:
                 st.slider("顶部边距(px)", 0, 400, key="margin_top")
                 st.slider("底部边距(px)", 0, 400, key="margin_bottom")
                 st.slider("左侧边距(px)", 0, 400, key="margin_left")
                 st.slider("右侧边距(px)", 0, 400, key="margin_right")
             else: # 百分比
                 st.slider("顶部边距(%)", 0, 100, key="margin_top_pct")
                 st.slider("底部边距(%)", 0, 100, key="margin_bottom_pct")
                 st.slider("左侧边距(%)", 0, 100, key="margin_left_pct")
                 st.slider("右侧边距(%)", 0, 100, key="margin_right_pct")
        else: # 统一边距
             if is_px_margin:
                 st.slider("统一边距(px)", 0, 400, key="margin_all")
             else: # 百分比
                 st.slider("统一边距(%)", 0, 100, key="margin_all_pct")

        # 阴影是否跟随边距变化复选框
        st.checkbox(
            "阴影跟随边距变化",
            key="shadow_follow_margin",
            help="勾选后，阴影的位置会根据上下边距差和左右边距差自动调整，以模拟光源方向。"
        )

    # -------- 偏移设置 (Offset Tab) --------
    with tab_offset:
        # 偏移部分重置按钮
        if st.button("恢复偏移默认", key="rst_offset"):
             _reset([
                 "offset_unit", "offset_x_val", "offset_y_val", "offset_x_val_pct",
                 "offset_y_val_pct", "shadow_link"
             ])
        # 偏移单位选择 (像素 vs 百分比)
        offset_unit_options = ["像素(px)", "百分比(%)"]
        # 确保状态中的单位有效
        if st.session_state.offset_unit not in offset_unit_options:
             st.session_state.offset_unit = DEFAULTS["offset_unit"]
        st.radio(
            "偏移单位",
            options=offset_unit_options,
            key="offset_unit", # 直接绑定 state
            horizontal=True,
            help="选择前景图像整体偏移的单位。百分比是相对于画布尺寸计算的。"
        )

        # 根据选择的单位显示对应的偏移滑块
        is_px_offset = st.session_state.offset_unit == "像素(px)"
        if is_px_offset:
             st.slider("水平偏移(px)", -400, 400, key="offset_x_val", help="前景图像在水平方向的偏移量，正右负左。")
             st.slider("垂直偏移(px)", -400, 400, key="offset_y_val", help="前景图像在垂直方向的偏移量，正下负上。")
        else: # 百分比
             st.slider("水平偏移(%)", -50, 50, key="offset_x_val_pct", help="前景图像水平偏移（占画布宽度百分比）。")
             st.slider("垂直偏移(%)", -50, 50, key="offset_y_val_pct", help="前景图像垂直偏移（占画布高度百分比）。")

        # 阴影是否跟随前景偏移复选框
        st.checkbox(
            "阴影跟随前景偏移",
            key="shadow_link",
            help="勾选后，阴影会和前景图像一起移动相同的偏移量。"
        )

    # --- 构建并返回最终的参数字典 ---
    params = {}
    # 从 session_state 中读取所有在 DEFAULTS 中定义的参数值
    for key in DEFAULTS:
        # 使用 .get() 方法安全地读取，如果键不存在（理论上不会，因为有 initialize_state），则使用 DEFAULTS 的值
        params[key] = st.session_state.get(key, DEFAULTS[key])

    # --- 后处理：处理统一边距逻辑 ---
    # 如果用户选择了统一边距 (ind_margin 为 False)，
    # 则需要将统一边距的值 (margin_all 或 margin_all_pct) 覆盖到独立的四个边距参数上，
    # 这样后续的处理逻辑（如 _canvas_size）可以统一使用独立的边距值。
    if not params["ind_margin"]:
        if params["margin_unit"] == "像素(px)":
            unified_margin = params["margin_all"]
            params["margin_top"] = unified_margin
            params["margin_bottom"] = unified_margin
            params["margin_left"] = unified_margin
            params["margin_right"] = unified_margin
        else: # 百分比单位
            unified_margin_pct = params["margin_all_pct"]
            params["margin_top_pct"] = unified_margin_pct
            params["margin_bottom_pct"] = unified_margin_pct
            params["margin_left_pct"] = unified_margin_pct
            params["margin_right_pct"] = unified_margin_pct

    # 返回包含所有当前有效参数的字典
    return params