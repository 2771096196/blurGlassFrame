import io
import zipfile
import streamlit as st
from controller import processing_controller

def _calc_output_size(orig_w, orig_h, params):
    """
    根据原图尺寸和参数计算最终输出尺寸 (含边距)。
    """
    frame_margin = params.get("frame_margin", 0)
    target_ratio = params.get("target_ratio")

    # 先根据比例扩展
    if target_ratio:
        rw, rh = target_ratio
        target_r = rw / rh
        orig_r = orig_w / orig_h
        if orig_r > target_r:
            base_w = orig_w
            base_h = int(orig_w / target_r)
        elif orig_r < target_r:
            base_h = orig_h
            base_w = int(orig_h * target_r)
        else:
            base_w, base_h = orig_w, orig_h
    else:
        base_w, base_h = orig_w, orig_h

    # 再加边距
    out_w = base_w + 2 * frame_margin
    out_h = base_h + 2 * frame_margin
    return out_w, out_h

def show_download_section():
    """导出下载区域：单图或批量 ZIP。"""
    if "images" not in st.session_state or len(st.session_state["images"]) == 0:
        st.info("请先上传图片。")
        return

    images = st.session_state["images"]
    filenames = st.session_state["filenames"]

    col1, col2 = st.columns(2)

    # ---------- 单张导出 ----------
    with col1:
        if st.button("导出当前预览图片"):
            params = st.session_state.get("params", {}).copy()
            idx = st.session_state.get("preview_index", 0)

            out_w, out_h = _calc_output_size(*images[idx].size, params)
            params["output_size"] = (out_w, out_h)

            result = processing_controller.process_single_image(images[idx],
                                                                params)
            buf = io.BytesIO()
            result.save(buf, format="PNG")
            buf.seek(0)
            st.download_button("下载图像",
                               buf,
                               file_name=f"{filenames[idx]}_output.png",
                               mime="image/png")

    # ---------- 批量导出 ----------
    with col2:
        if st.button("批量导出 ZIP"):
            params = st.session_state.get("params", {}).copy()
            zip_buffer = io.BytesIO()

            with zipfile.ZipFile(zip_buffer, "w") as zf:
                for img, fname in zip(images, filenames):
                    out_w, out_h = _calc_output_size(*img.size, params)
                    params["output_size"] = (out_w, out_h)

                    processed = processing_controller.process_single_image(img,
                                                                           params)
                    if processed is None:
                        continue
                    img_buf = io.BytesIO()
                    processed.save(img_buf, format="PNG")
                    img_buf.seek(0)
                    out_name = f"{fname.rsplit('.',1)[0]}_output.png"
                    zf.writestr(out_name, img_buf.read())

            zip_buffer.seek(0)
            st.download_button("下载 ZIP 文件",
                               zip_buffer,
                               file_name="processed_images.zip",
                               mime="application/zip")
