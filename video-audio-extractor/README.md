# 视频音频提取器

一个简单的 Web 应用，用于从视频文件中提取音频并保存到本地。

## 功能特点

- 支持批量处理多个视频文件
- 支持多种视频格式输入：MP4, AVI, MOV, MKV, WebM, FLV, WMV, M4V, MPEG, MPG
- 支持多种音频格式输出：MP3, WAV, AAC, M4A, OGG, FLAC
- 友好的 Web 界面，支持拖拽上传
- 实时显示处理进度和结果

## 安装

1. 确保已安装 Python 3.8+

2. 安装 FFmpeg（moviepy 依赖）：
   - Windows: 使用 [预编译版本](https://ffmpeg.org/download.html)
   - Mac: `brew install ffmpeg`
   - Linux: `sudo apt install ffmpeg`

3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

## 运行

```bash
python app.py
```

启动后访问 http://localhost:8001

## 使用方法

1. 选择一个或多个视频文件（支持拖拽）
2. 选择输出音频格式（默认 MP3）
3. 点击"开始提取"
4. 等待处理完成后，点击下载按钮获取音频文件

## 技术栈

- 后端：Flask + MoviePy
- 前端：原生 HTML/CSS/JavaScript

## 项目结构

```
video-audio-extractor/
├── app.py              # Flask 应用主文件
├── requirements.txt    # Python 依赖
├── static/            # 静态资源
│   ├── style.css      # 样式文件
│   └── script.js      # 前端交互脚本
├── templates/         # HTML 模板
│   └── index.html     # 主页面
├── uploads/           # 临时上传目录（自动创建）
└── output/            # 输出文件目录（自动创建）
```
