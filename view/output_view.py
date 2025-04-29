import io, os, zipfile, streamlit as st
from controller import processing_controller
# 导入 DEFAULTS 以便获取所有参数键和默认值
from view.param_view import DEFAULTS

def _ensure_output():
    """确保 output 目录存在"""
    os.makedirs("output", exist_ok=True)

# _canvas_size 函数在导出时不再需要，因为 processing_controller 会计算
# def _canvas_size(ow, oh, p): ... (可以移除)

def _get_current_export_params():
    """从 session_state 直接读取所有参数用于导出"""
    params = {}
    for key, default_value in DEFAULTS.items():
        params[key] = st.session_state.get(key, default_value)

    # --- 处理统一边距逻辑 ---
    # (确保 controller 在处理前也能拿到正确的独立边距值)
    if not params.get("ind_margin", False):
        if params.get("margin_unit", "像素(px)") == "像素(px)":
            unified_margin = params.get("margin_all", 0)
            params["margin_top"] = unified_margin
            params["margin_bottom"] = unified_margin
            params["margin_left"] = unified_margin
            params["margin_right"] = unified_margin
        else: # "%"
            unified_margin_pct = params.get("margin_all_pct", 0)
            params["margin_top_pct"] = unified_margin_pct
            params["margin_bottom_pct"] = unified_margin_pct
            params["margin_left_pct"] = unified_margin_pct
            params["margin_right_pct"] = unified_margin_pct
    return params


def _export_one(img, fname, p):
    """处理单张图片并返回文件名和数据流"""
    # process_single_image 会处理尺寸计算，不再需要预先计算 output_size
    # p["output_size"] = (cw, ch) # 移除
    out_img = processing_controller.process_single_image(img, p)
    if out_img is None: # 处理失败的情况
        st.error(f"处理图片 '{fname}' 失败。")
        return None, None

    buf = io.BytesIO()
    out_img.save(buf, format="PNG")
    buf.seek(0)
    # 构造输出文件名
    base, ext = os.path.splitext(fname)
    out_name = f"{base}_output.png" # 保证是 png
    return out_name, buf

def show_download_section():
    """显示导出按钮区域"""
    if "images" not in st.session_state or not st.session_state["images"]:
        # st.info("请先上传图片。") # 避免重复提示，app.py 已有
        return

    images = st.session_state["images"]
    fnames = st.session_state["filenames"]

    # *** 修改点：直接从 state 读取参数 ***
    export_params = _get_current_export_params() # 获取最新的参数

    col1, col2 = st.columns(2)
    with col1:
        st.write("#### 导出选项") # 添加小标题
        if st.button("导出当前预览图片"):
            # 获取当前预览的索引
            idx = st.session_state.get("preview_index", 0)
            if idx < len(images):
                img_to_export = images[idx]
                fname_to_export = fnames[idx]
                st.info(f"正在处理: {fname_to_export}...")
                # 使用最新的参数进行处理
                out_name, buf = _export_one(img_to_export, fname_to_export, export_params.copy())
                if out_name and buf:
                    _ensure_output()
                    # 可选：保存到服务器 output 目录
                    # with open(os.path.join("output", out_name), "wb") as f:
                    #     f.write(buf.getbuffer())
                    st.download_button("下载处理后图片", buf, file_name=out_name, mime="image/png", key="dl_single")
                    # st.success(f"已保存 output/{out_name}") # 如果不保存到服务器则移除
                    st.success(f"'{out_name}' 已准备好下载。")
                else:
                     st.error(f"无法导出图片 {fname_to_export}。")

            else:
                st.warning("无法找到要导出的预览图片索引。")

    with col2:
        st.write("#### 批量导出") # 添加小标题
        if st.button("批量导出为 ZIP"):
            _ensure_output()
            zip_mem = io.BytesIO()
            processed_count = 0
            with zipfile.ZipFile(zip_mem, "w") as zf:
                progress_bar = st.progress(0)
                status_text = st.empty()
                total_images = len(images)
                for i, (img, fname) in enumerate(zip(images, fnames)):
                    status_text.text(f"正在处理第 {i+1}/{total_images} 张: {fname}")
                    # 对每张图片使用最新的参数进行处理
                    out_name, buf = _export_one(img, fname, export_params.copy())
                    if out_name and buf:
                        zf.writestr(out_name, buf.getvalue())
                        processed_count += 1
                    else:
                        status_text.text(f"处理第 {i+1}/{total_images} 张 '{fname}' 失败，已跳过。")
                    progress_bar.progress((i + 1) / total_images)

            zip_mem.seek(0)
            zip_name = "processed_images.zip"
            # 可选：保存 ZIP 到服务器 output 目录
            # with open(os.path.join("output", zip_name), "wb") as f:
            #     f.write(zip_mem.getbuffer())
            st.download_button("下载 ZIP 压缩包", zip_mem, file_name=zip_name, mime="application/zip", key="dl_zip")
            # st.success(f"ZIP 已保存 output/{zip_name}") # 如果不保存到服务器则移除
            status_text.text(f"ZIP 文件已准备好，包含 {processed_count}/{total_images} 张处理成功的图片。")