# Project Manager - 项目管理器

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?logo=flask&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)

一个用于自动检索和管理本地项目与软件的 Web 应用。

## 功能特性

- **自动扫描** - 自动检测目录下的各类项目（Python、Node.js、Java、Go 等）
- **软件管理** - 显示系统中已安装的软件列表
- **快速访问** - 一键打开项目文件夹
- **搜索过滤** - 支持按名称、类型搜索项目
- **Web 界面** - 现代化的深色主题界面

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 启动应用
python app.py
```

启动后访问 **http://localhost:5000**

> 默认扫描目录为当前用户桌面，可在 `app.py` 中修改 `ROOT_PATH` 变量自定义扫描路径。

## 项目结构

```
project-manager/
├── app.py              # Flask 主应用
├── scanner.py          # 扫描器（项目/软件检测）
├── process_manager.py  # 进程管理器
├── requirements.txt    # Python 依赖
├── templates/
│   └── index.html      # 前端页面
└── static/
    ├── css/
    │   └── style.css   # 样式文件
    └── js/
        └── app.js      # 前端逻辑
```

## 技术栈

- **后端**: Flask (Python)
- **前端**: 原生 JavaScript + CSS3
- **界面**: 深色主题

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 主页 |
| `/api/projects` | GET | 获取项目列表 |
| `/api/software` | GET | 获取软件列表 |
| `/api/scan` | GET | 扫描所有内容 |
| `/api/open` | POST | 打开项目目录 |
| `/api/info/<path>` | GET | 获取项目详情 |

## 支持的项目类型

| 类型 | 识别文件 |
|------|---------|
| Python | `requirements.txt`, `setup.py`, `pyproject.toml` |
| Node.js | `package.json` |
| Java | `pom.xml`, `build.gradle` |
| Go | `go.mod` |
| Rust | `Cargo.toml` |
| C/C++ | `CMakeLists.txt`, `Makefile` |
