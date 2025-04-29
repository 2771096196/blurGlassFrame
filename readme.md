本项目基于 **Streamlit** 和 **Pillow**，实现了一款用于批量处理图片的Web应用。主要功能是：

- 给图片添加 **毛玻璃模糊背景**
- 生成 **柔和的立体阴影**
- 应用 **圆角效果**
- 支持 **批量上传、多图批处理** 和 **一键打包下载**

适用于抖音、小红书、B站等平台制作适配竖屏比例的内容图。

------

## 项目结构

```
makefile复制项目目录结构:
├─ app.py                # 应用主入口
├─ requirements.txt      # Python依赖清单
├─ model/                # 图像处理模块（背景、阴影、前景处理）
│   ├─ background.py
│   ├─ shadow.py
│   └─ foreground.py
├─ controller/           # 控制器层（业务逻辑中转）
│   ├─ image_controller.py
│   └─ processing_controller.py
├─ view/                 # 界面展示层（Streamlit页面布局）
│   ├─ upload_view.py
│   ├─ param_view.py
│   ├─ preview_view.py
│   └─ output_view.py
└─ README.md              # 项目说明文档
```

------

## 环境依赖

- Python 3.8及以上
- 必需安装以下Python库：

```
bash


复制
pip install -r requirements.txt
```

依赖列表（requirements.txt）：

```
nginx复制streamlit
Pillow
numpy
```

1. **启动应用**

在项目根目录运行：

```
bash


复制编辑
streamlit run app.py
```

然后浏览器会自动打开，访问 `http://localhost:8501` 查看应用界面。