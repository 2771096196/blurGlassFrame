import exiftool
import os
import json # 用于更美观地打印字典
import traceback # 用于打印详细错误

# --- 指定 ExifTool 可执行文件的相对路径 ---
EXIFTOOL_PATH = "./exiftool-13.29_64/exiftool(-k).exe"

def get_image_metadata(image_path):
    """
    使用指定路径和 UTF-8 编码的 ExifTool 读取图片的元数据。

    Args:
        image_path (str): 图片文件的路径。

    Returns:
        dict: 包含提取到的元数据的字典，如果出错则返回 None。
    """
    metadata = {}

    # 1. 检查 ExifTool 可执行文件是否存在
    if not os.path.isfile(EXIFTOOL_PATH):
        print(f"错误：无法在指定路径找到 ExifTool 可执行文件 - {EXIFTOOL_PATH}")
        print("请确保路径正确，并且该文件存在。")
        return None

    # 2. 检查图片文件是否存在
    if not os.path.isfile(image_path):
        print(f"错误：图片文件未找到 - {image_path}")
        return None

    try:
        # *** 添加 encoding='utf-8' 参数 ***
        # 使用 with 语句确保 ExifTool 进程被正确关闭
        with exiftool.ExifTool(executable=EXIFTOOL_PATH, encoding='utf-8') as et:
            # 使用 execute_json 获取元数据
            all_metadata_list = et.execute_json(image_path)

            # 检查返回的列表是否有效且包含数据
            if not all_metadata_list or not isinstance(all_metadata_list, list) or len(all_metadata_list) == 0:
                print(f"警告：无法从 {image_path} 读取到元数据 (ExifTool 返回了空或无效的结果)。")
                return None

            # 获取列表中的第一个（也是唯一一个）字典
            tags = all_metadata_list[0]

            # 确保 tags 是一个字典
            if not isinstance(tags, dict):
                 print(f"警告：从 {image_path} 读取到的元数据格式不是预期的字典。")
                 return None

            # --- 提取我们关心的标签 ---
            # (逻辑与之前相同)
            metadata['Make'] = tags.get('EXIF:Make') or tags.get('MakerNotes:Make') or tags.get('XMP:Make')
            metadata['Model'] = tags.get('EXIF:Model') or tags.get('MakerNotes:Model') or tags.get('XMP:Model')
            if not metadata['Model']:
                 metadata['Model'] = tags.get('Composite:DeviceModelName') or tags.get('apple-iphone:Model')

            metadata['LensModel'] = (tags.get('EXIF:LensModel') or
                                   tags.get('MakerNotes:LensModel') or
                                   tags.get('XMP:Lens') or
                                   tags.get('Composite:LensID') or
                                   tags.get('MakerNotes:LensType') or
                                   tags.get('MakerNotes:Lens'))
            if not metadata['LensModel'] and tags.get('Composite:LensInfo'):
                 metadata['LensModel'] = tags.get('Composite:LensInfo')

            metadata['ISO'] = tags.get('EXIF:ISO') or tags.get('MakerNotes:ISO') or tags.get('EXIF:PhotographicSensitivity')

            metadata['FocalLength'] = tags.get('EXIF:FocalLength') or tags.get('MakerNotes:FocalLength')
            metadata['FocalLengthIn35mmFormat'] = tags.get('EXIF:FocalLengthIn35mmFilm') or tags.get('Composite:FocalLength35efl')

            metadata['ExposureTime'] = tags.get('EXIF:ExposureTime') or tags.get('MakerNotes:ExposureTime') or tags.get('Composite:ShutterSpeed')

            metadata['Aperture'] = tags.get('EXIF:FNumber') or tags.get('MakerNotes:FNumber')
            if not metadata['Aperture'] and tags.get('EXIF:ApertureValue'):
                 metadata['Aperture'] = tags.get('Composite:Aperture')

            # 清理 None 值，并格式化部分值
            cleaned_metadata = {}
            for key, value in metadata.items():
                if value is not None:
                    # (格式化逻辑与之前相同)
                    if key == 'Aperture':
                        if isinstance(value, (int, float)): cleaned_metadata[key] = f"f/{value:.1f}"
                        elif isinstance(value, str) and value.startswith('f/'): cleaned_metadata[key] = value
                        else:
                             try: fnum = float(value); cleaned_metadata[key] = f"f/{fnum:.1f}"
                             except (ValueError, TypeError): cleaned_metadata[key] = str(value)
                    elif key == 'ExposureTime':
                         if isinstance(value, str) and '/' in value: cleaned_metadata[key] = f"{value} s"
                         elif isinstance(value, (int, float)):
                             if 0 < value < 1: cleaned_metadata[key] = f"1/{int(1/value + 0.5)} s"
                             else: cleaned_metadata[key] = f"{value:.3f} s"
                         else: cleaned_metadata[key] = f"{value} s"
                    elif key == 'FocalLength' and isinstance(value, (int, float)): cleaned_metadata[key] = f"{value:.0f} mm"
                    elif key == 'FocalLengthIn35mmFormat' and isinstance(value, (int, float)): cleaned_metadata[key] = f"{value:.0f} mm (35mm equiv.)"
                    elif key == 'ISO':
                        if isinstance(value, list) and len(value)>0: cleaned_metadata[key] = value[0]
                        else: cleaned_metadata[key] = value
                    else: cleaned_metadata[key] = str(value)

            if cleaned_metadata:
                return cleaned_metadata
            else:
                print(f"警告: 从 {image_path} 中未能提取到任何所需的标签。")
                return None

    # *** 移除了不存在的 exiftool.ExifToolExecuteError 捕获 ***
    except Exception as e:
        # 捕获所有错误
        print(f"处理 {image_path} 时发生错误: {e}")
        traceback.print_exc() # 打印详细的回溯信息
        return None

# --- 主程序执行部分 ---
if __name__ == '__main__':
    image_to_process = './DSC03965.ARW'
    # image_to_process = '1.jpg'

    print(f"正在尝试处理图片: {image_to_process}")
    extracted_data = get_image_metadata(image_to_process)

    if extracted_data:
        print(f"\n--- 从 {image_to_process} 成功提取的元数据 ---")
        print(json.dumps(extracted_data, indent=4, ensure_ascii=False))
    else:
        print(f"\n未能从 {image_to_process} 提取到所需的元数据或处理过程中出错。")