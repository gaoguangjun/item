# Video Audio Extractor - 视频音频提取器

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?logo=flask&logoColor=white)
![FFmpeg](https://img.shields.io/badge/FFmpeg-Required-007808?logo=ffmpeg&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)

一个简单的 Web 应用，用于从视频文件中提取音频并保存到本地。

## 功能特性

- 支持批量处理多个视频文件
- 支持多种视频格式输入：MP4, AVI, MOV, MKV, WebM, FLV, WMV, M4V, MPEG, MPG
- 支持多种音频格式输出：MP3, WAV, AAC, M4A, OGG, FLAC
- 友好的 Web 界面，支持拖拽上传
- 实时显示处理进度和结果

## 快速开始

### 1. 安装 FFmpeg

MoviePy 依赖 FFmpeg，请先安装：

| 平台 | 安装方式 |
|------|---------|
| Windows | [下载预编译版本](https://ffmpeg.org/download.html) |
| macOS | `brew install ffmpeg` |
| Linux | `sudo apt install ffmpeg` |

### 2. 安装依赖并启动

```bash
# 安装依赖
pip install -r requirements.txt

# 启动应用
python app.py
```

启动后访问 **http://localhost:8001**

## 项目结构

```
video-audio-extractor/
├── app.py              # Flask 应用主文件
├── requirements.txt    # Python 依赖
├── static/
│   ├── style.css       # 样式文件
│   └── script.js       # 前端交互脚本
├── templates/
│   └── index.html      # 主页面
├── uploads/            # 临时上传目录（自动创建）
└── output/             # 输出文件目录（自动创建）
```

## 技术栈

- **后端**: Flask + MoviePy
- **前端**: 原生 HTML/CSS/JavaScript
- **媒体处理**: FFmpeg

## 使用方法

1. 选择一个或多个视频文件（支持拖拽）
2. 选择输出音频格式（默认 MP3）
3. 点击「开始提取」
4. 等待处理完成后，点击下载按钮获取音频文件

## 支持的格式

**输入视频格式：** MP4, AVI, MOV, MKV, WebM, FLV, WMV, M4V, MPEG, MPG

**输出音频格式：** MP3, WAV, AAC, M4A, OGG, FLAC

## 系统要求

- Python 3.8+
- FFmpeg
- 现代浏览器
