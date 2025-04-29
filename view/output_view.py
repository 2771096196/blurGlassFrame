"""
导出视图：单图 / 批量下载，并自动将文件保存到本地 output/ 目录
--------------------------------------------------------------------
新增功能：
1. 单图导出时，PNG 自动写入 output/<文件名>_output.png
2. 批量导出时，ZIP 自动写入 output/processed_images.zip
"""

import io
import os
import zipfile
import streamlit as st
from controller import processing_controller


# ---------- 工具函数 ----------
def _ensure_output_folder():
    os.makedirs("output", exist_ok=True)


def _calc_output_size(orig_w, orig_h, params):
    """考虑目标比例和用户边距，返回 (base_out_w, base_out_h)。"""
    frame_margin = params.get("frame_margin", 0)
    target_ratio = params.get("target_ratio")

    # 先根据目标比例扩展
    if target_ratio:
        rw, rh = target_ratio
        target_r = rw / rh
        orig_r = orig_w / orig_h
        if orig_r > target_r:             # 原图偏宽
            base_w = orig_w
            base_h = int(orig_w / target_r)
        elif orig_r < target_r:           # 原图偏高
            base_h = orig_h
            base_w = int(orig_h * target_r)
        else:
            base_w, base_h = orig_w, orig_h
    else:
        base_w, base_h = orig_w, orig_h

    base_w += 2 * frame_margin
    base_h += 2 * frame_margin
    return base_w, base_h


# ---------- 主导出区域 ----------
def show_download_section():
    if "images" not in st.session_state or not st.session_state["images"]:
        st.info("请先上传图片。")
        return

    images = st.session_state["images"]
    filenames = st.session_state["filenames"]
    params_base = st.session_state.get("params", {}).copy()

    col1, col2 = st.columns(2)

    # === 单图导出 ===
    with col1:
        if st.button("导出当前预览图片"):
            idx = st.session_state.get("preview_index", 0)
            img = images[idx]
            params = params_base.copy()

            out_w, out_h = _calc_output_size(img.width, img.height, params)
            params["output_size"] = (out_w, out_h)

            result = processing_controller.process_single_image(img, params)

            # 保存到本地 output/
            _ensure_output_folder()
            out_fname = f"{filenames[idx].rsplit('.',1)[0]}_output.png"
            save_path = os.path.join("output", out_fname)
            result.save(save_path, format="PNG")

            # 提供下载
            buf = io.BytesIO()
            result.save(buf, format="PNG")
            buf.seek(0)
            st.download_button("下载图像", buf, file_name=out_fname, mime="image/png")
            st.success(f"已保存到 {save_path}")

    # === 批量导出 ZIP ===
    with col2:
        if st.button("批量导出 ZIP"):
            params = params_base.copy()
            zip_buffer = io.BytesIO()

            with zipfile.ZipFile(zip_buffer, "w") as zf:
                for img, fname in zip(images, filenames):
                    out_w, out_h = _calc_output_size(img.width, img.height, params)
                    params["output_size"] = (out_w, out_h)
                    processed = processing_controller.process_single_image(img, params)
                    if processed is None:
                        continue
                    img_bytes = io.BytesIO()
                    processed.save(img_bytes, format="PNG")
                    img_bytes.seek(0)
                    out_name = f"{fname.rsplit('.',1)[0]}_output.png"
                    zf.writestr(out_name, img_bytes.read())

            zip_buffer.seek(0)

            # 保存 ZIP 到本地 output/
            _ensure_output_folder()
            zip_path = os.path.join("output", "processed_images.zip")
            with open(zip_path, "wb") as f:
                f.write(zip_buffer.getvalue())

            st.download_button("下载 ZIP 文件",
                               zip_buffer,
                               file_name="processed_images.zip",
                               mime="application/zip")
            st.success(f"ZIP 文件已保存到 {zip_path}")
