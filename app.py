import streamlit as st
from view import upload_view, param_view, preview_view, output_view

# 页面基本设置
st.set_page_config(page_title="图片批量背景模糊和阴影工具", layout="wide")

# 标题和简介
st.title("图片毛玻璃背景和立体阴影批量处理工具")
st.markdown("本应用可将照片自动生成毛玻璃模糊背景和悬浮阴影效果，支持批量处理多张图片。您可以调整参数实时预览，并将处理结果一键打包下载。")

# 上传区域
upload_view.show_upload_section()

# 如果已经上传图片，则显示参数调整和预览
if "images" in st.session_state and len(st.session_state["images"]) > 0:
    # 将参数控制和预览区域并排显示
    col1, col2 = st.columns([1, 1.2])
    with col1:
        params = param_view.show_parameter_controls()
        # 保存当前参数配置供其他组件使用
        st.session_state["params"] = params
    with col2:
        preview_view.show_preview()
    # 导出下载区域
    output_view.show_download_section()
else:
    st.write("请上传图片后进行参数调整和预览。")
