"""
导出视图：单图 / 批量 ZIP
-------------------------------------------------------
直接使用【原图 + 原始像素参数】，与预览质量无关，
确保最终导出始终最高清晰度且几何效果一致。
"""

import io, os, zipfile, streamlit as st
from controller import processing_controller


def _ensure_output():
    os.makedirs("output", exist_ok=True)


def _canvas_size(ow, oh, p):
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


def _export_one(img, fname, p):
    cw, ch = _canvas_size(*img.size, p)
    p["output_size"] = (cw, ch)
    out_img = processing_controller.process_single_image(img, p)
    buf = io.BytesIO()
    out_img.save(buf, format="PNG")
    buf.seek(0)
    out_name = f"{fname.rsplit('.',1)[0]}_output.png"
    return out_name, buf


def show_download_section():
    if "images" not in st.session_state or not st.session_state["images"]:
        st.info("请先上传图片。")
        return

    images = st.session_state["images"]
    fnames = st.session_state["filenames"]
    base_p = st.session_state.get("params", {}).copy()

    col1, col2 = st.columns(2)

    # ----- 单张 -----
    with col1:
        if st.button("导出当前预览图片"):
            idx = st.session_state.get("preview_index", 0)
            out_name, buf = _export_one(images[idx], fnames[idx], base_p.copy())
            _ensure_output()
            with open(os.path.join("output", out_name), "wb") as f:
                f.write(buf.getbuffer())
            st.download_button("下载图像", buf, file_name=out_name, mime="image/png")
            st.success(f"已保存 output/{out_name}")

    # ----- 批量 ZIP -----
    with col2:
        if st.button("批量导出 ZIP"):
            _ensure_output()
            zip_mem = io.BytesIO()
            with zipfile.ZipFile(zip_mem, "w") as zf:
                for img, fname in zip(images, fnames):
                    out_name, buf = _export_one(img, fname, base_p.copy())
                    zf.writestr(out_name, buf.getvalue())
            zip_mem.seek(0)
            zip_name = "processed_images.zip"
            with open(os.path.join("output", zip_name), "wb") as f:
                f.write(zip_mem.getbuffer())
            st.download_button("下载 ZIP", zip_mem,
                               file_name=zip_name, mime="application/zip")
            st.success(f"ZIP 已保存 output/{zip_name}")
