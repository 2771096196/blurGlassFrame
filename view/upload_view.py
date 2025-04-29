import streamlit as st
from controller import image_controller

def show_upload_section():
    """
    显示文件上传区域，处理用户上传的图片，并在界面上显示缩略图列表。
    设置 st.session_state 包含上传的图片和缩略图。
    """
    st.header("批量图片上传")
    uploaded_files = st.file_uploader("拖拽或点击上传图片文件", accept_multiple_files=True, type=["png", "jpg", "jpeg"])
    if uploaded_files:
        # 调用控制器加载图片
        images, filenames, errors = image_controller.load_images(uploaded_files)
        if errors:
            # 显示错误提示
            st.error("以下文件不是有效的图像或无法打开: " + ", ".join(errors))
        if images:
            # 生成缩略图列表用于预览
            thumbs = image_controller.create_thumbnails(images, max_size=300)
            # 将结果存入会话状态
            st.session_state["images"] = images
            st.session_state["filenames"] = filenames
            st.session_state["thumbs"] = thumbs
            # 显示上传成功的缩略图预览
            st.subheader("已上传图片预览")
            cols = st.columns(4)
            for idx, thumb in enumerate(thumbs):
                col = cols[idx % 4]
                # 在网格中显示缩略图和文件名
                with col:
                    st.image(thumb, caption=filenames[idx], use_column_width=True)
    else:
        # 如果尚未上传文件，给出提示
        st.info("请上传一张或多张图片。支持PNG、JPG格式。")
