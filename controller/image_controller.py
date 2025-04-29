"""
处理上传文件：读取原图、生成缩略图
-------------------------------------------------
改动：
1. create_thumbnails() 默认 max_size = 600，保证预览最长边 ≤ 600，
   大幅降低实时预览运算量，又能保持清晰度。
"""

import io
from PIL import Image


def load_images(uploaded_files):
    """
    将 Streamlit 上传文件读取为 PIL.Image 列表。
    返回 (images, filenames, errors)。
    """
    images, filenames, errors = [], [], []
    for file in uploaded_files:
        try:
            img = Image.open(io.BytesIO(file.getvalue()))
            img.load()            # 强制读取
            images.append(img)
            filenames.append(file.name)
        except Exception:         # 格式错误 / 读取失败
            errors.append(file.name)
    return images, filenames, errors


def create_thumbnails(images, max_size: int = 600):
    """
    为预览生成缩略图，最长边不超过 max_size 像素。
    """
    thumbs = []
    for img in images:
        thumb = img.copy()
        thumb.thumbnail((max_size, max_size), Image.LANCZOS)
        thumbs.append(thumb)
    return thumbs
