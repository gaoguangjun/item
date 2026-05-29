# Python Tools Collection

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?logo=flask&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![Repo Size](https://img.shields.io/github/repo-size/gaoguangjun/item)
![Last Commit](https://img.shields.io/github/last-commit/gaoguangjun/item)
![Issues](https://img.shields.io/github/issues/gaoguangjun/item)
![Stars](https://img.shields.io/github/stars/gaoguangjun/item?style=social)

一套实用的 Python 工具集合，涵盖 SLA 计算、项目管理、文件查找和媒体处理等场景。

---

<p align="center">
  <a href="#1-sla-calculator---sla-计算器">SLA 计算器</a> &nbsp;|&nbsp;
  <a href="#2-project-manager---项目管理器">项目管理器</a> &nbsp;|&nbsp;
  <a href="#3-duplicate-file-finder---重复文件查找器">文件查找器</a> &nbsp;|&nbsp;
  <a href="#4-video-audio-extractor---视频音频提取器">音频提取器</a> &nbsp;|&nbsp;
  <a href="#5-ebook2audiobook---电子书转有声书">电子书转有声书</a>
</p>

---

## 项目列表

### 1. SLA Calculator - SLA 计算器

服务等级协议（SLA）计算工具，帮助计算服务可用性、停机时间和赔偿金额。

**功能特性：**
- 根据正常运行时间百分比计算各周期停机时间
- 多 SLA 等级对比
- SLA 赔偿金额计算
- 实际可用性反推
- 反向计算所需 SLA 等级

```bash
cd sla-calculator
pip install -r requirements.txt
python app.py
# 访问 http://localhost:5001
```

---

### 2. Project Manager - 项目管理器

自动检索和管理本地项目与软件的 Web 应用。

**功能特性：**
- 自动扫描检测各类项目（Python、Node.js、Java、Go 等）
- 已安装软件列表管理
- 一键打开项目文件夹
- 按名称、类型搜索过滤

```bash
cd project-manager
pip install -r requirements.txt
python app.py
# 访问 http://localhost:5000
```

---

### 3. Duplicate File Finder - 重复文件查找器

扫描指定目录，查找并管理重复文件。

**功能特性：**
- 基于文件内容哈希的精确匹配
- 支持大目录快速扫描
- 可视化重复文件列表
- 批量删除重复文件

```bash
cd duplicate-file-finder
pip install -r requirements.txt
python main.py
```

---

### 4. Video Audio Extractor - 视频音频提取器

从视频文件中提取音频轨道，支持多种视频格式。

**功能特性：**
- 支持多种视频格式（MP4、AVI、MKV 等）
- 批量提取音频
- 可选输出格式（MP3、WAV 等）
- Web 界面操作

```bash
cd video-audio-extractor
pip install -r requirements.txt
python app.py
```

---

### 5. Ebook2Audiobook - 电子书转有声书

将电子书转换为有声读物，支持多种 TTS 引擎。

**功能特性：**
- 支持多种电子书格式（EPUB、PDF 等）
- 多语言 TTS 支持
- Docker 部署
- Gradio Web 界面

```bash
cd ebook2audiobook
pip install -r requirements.txt
python app.py
```

## 技术栈

| 项目 | 后端 | 前端 | 部署 |
|------|------|------|------|
| SLA Calculator | Flask | JavaScript + CSS3 | - |
| Project Manager | Flask | JavaScript + CSS3 | - |
| Duplicate File Finder | Python Tkinter | - | - |
| Video Audio Extractor | Flask | JavaScript + CSS3 | - |
| Ebook2Audiobook | Python | Gradio | Docker |

## 环境要求

- Python 3.8+
- pip

## 许可证

MIT License
