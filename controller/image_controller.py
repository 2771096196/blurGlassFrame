import io
from PIL import Image

def load_images(uploaded_files):
    """
    从上传的文件对象列表中读取图像。
    uploaded_files: Streamlit上传的文件对象列表。
    返回 (images_list, filenames_list, errors_list)。
    images_list: 成功打开的PIL Image对象列表。
    filenames_list: 对应的文件名列表。
    errors_list: 无法打开的文件名列表（格式不支持或读取失败）。
    """
    images = []
    filenames = []
    errors = []
    for file in uploaded_files:
        try:
            # 读取文件内容并尝试打开为图像
            file_bytes = file.getvalue()
            img = Image.open(io.BytesIO(file_bytes))
            # 确保图像读入完成（有些懒加载需要调用load）
            img.load()
            filenames.append(file.name)
            images.append(img)
        except Exception as e:
            # 捕获任何图像打开异常，将该文件标记为错误
            errors.append(file.name)
    return images, filenames, errors

def create_thumbnails(images, max_size=300):
    """
    为给定图像列表创建缩略图列表，用于预览。
    images: PIL Image对象列表。
    max_size: 缩略图的最大边长像素尺寸。
    返回与images对应的缩略图Image列表。
    """
    thumbs = []
    for img in images:
        # 复制原图以制作缩略图，避免修改原始图像对象
        thumb = img.copy()
        # 使用thumbnail方法按比例缩放图像，最长边=max_size
        thumb.thumbnail((max_size, max_size))
        thumbs.append(thumb)
    return thumbs
