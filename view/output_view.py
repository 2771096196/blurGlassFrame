"""
输出 / 下载视图
===============================================================
依赖：
- controller.processing_controller   : 图片处理
- streamlit.session_state 中字段：images, filenames, params
功能：
1. 单张导出 PNG
2. 批量导出 ZIP
---------------------------------------------------------------
兼容最新参数：
- 四边独立边距    margin_top / bottom / left / right
- 目标比例        target_ratio
- 偏移            offset_x_val / offset_y_val / offset_unit
"""

import io
import os
import zipfile
import streamlit as st
from controller import processing_controller


# ---------- 工具函数 ----------


def _ensure_output_dir():
    os.makedirs("output", exist_ok=True)


def _canvas_size(orig_w: int, orig_h: int, p: dict):
    """
    根据原图尺寸 & 参数，计算最终输出画布大小 (canvas_w, canvas_h)
    与 controller 中逻辑一致（不含安全 pad）。
    """
    # 加边距
    base_w = orig_w + p["margin_left"] + p["margin_right"]
    base_h = orig_h + p["margin_top"] + p["margin_bottom"]

    # 比例适配
    ratio = p.get("target_ratio")
    if not ratio:
        return base_w, base_h

    rw, rh = ratio
    tar = rw / rh
    cur = base_w / base_h
    if cur > tar:                       # 画布偏宽，扩展高
        return base_w, int(base_w / tar)
    elif cur < tar:                     # 画布偏高，扩展宽
        return int(base_h * tar), base_h
    return base_w, base_h               # 已匹配


def _prepare_params_for_export(base_params: dict, w: int, h: int):
    """
    复制 base_params 并写入 output_size (画布大小)，
    用于传递给 processing_controller。
    """
    p = base_params.copy()
    p["output_size"] = _canvas_size(w, h, base_params)
    return p


def _process_and_save(image, filename, params):
    """处理单张图片并返回 (文件名, BytesIO)."""
    processed = processing_controller.process_single_image(image, params)
    buf = io.BytesIO()
    processed.save(buf, format="PNG")
    buf.seek(0)
    out_name = f"{filename.rsplit('.', 1)[0]}_output.png"
    return out_name, buf


# ---------- 主入口 ----------


def show_download_section():
    """在页面下方显示下载区域（单图 & 批量）。"""
    if "images" not in st.session_state or not st.session_state["images"]:
        st.info("请先上传图片。")
        return

    images = st.session_state["images"]
    filenames = st.session_state["filenames"]
    base_params = st.session_state.get("params", {}).copy()

    col1, col2 = st.columns(2)

    # ===== 单张下载 =====
    with col1:
        if st.button("导出当前预览图片"):
            idx = st.session_state.get("preview_index", 0)
            img = images[idx]
            # 准备参数
            export_params = _prepare_params_for_export(base_params, *img.size)
            out_name, buf = _process_and_save(img, filenames[idx], export_params)

            # 保存到 output 目录
            _ensure_output_dir()
            save_path = os.path.join("output", out_name)
            with open(save_path, "wb") as f:
                f.write(buf.getbuffer())

            st.download_button("下载图像", buf, file_name=out_name, mime="image/png")
            st.success(f"已保存至 {save_path}")

    # ===== 批量 ZIP =====
    with col2:
        if st.button("批量导出 ZIP"):
            _ensure_output_dir()
            zip_buffer = io.BytesIO()

            with zipfile.ZipFile(zip_buffer, "w") as zf:
                for img, name in zip(images, filenames):
                    export_params = _prepare_params_for_export(base_params, *img.size)
                    out_name, img_buf = _process_and_save(img, name, export_params)
                    zf.writestr(out_name, img_buf.getvalue())

            zip_buffer.seek(0)
            zip_name = "processed_images.zip"
            zip_path = os.path.join("output", zip_name)
            with open(zip_path, "wb") as f:
                f.write(zip_buffer.getbuffer())

            st.download_button("下载 ZIP 文件",
                               zip_buffer,
                               file_name=zip_name,
                               mime="application/zip")
            st.success(f"ZIP 已保存至 {zip_path}")
