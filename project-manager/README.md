# 项目管理器

一个用于自动检索和管理本地项目与软件的 Web 应用。

## 功能特性

- 🔍 **自动扫描** - 自动检测目录下的各类项目（Python、Node.js、Java、Go 等）
- 💻 **软件管理** - 显示系统中已安装的软件列表
- 📂 **快速访问** - 一键打开项目文件夹
- 🔎 **搜索过滤** - 支持按名称、类型搜索项目
- 🌐 **Web 界面** - 现代化的深色主题界面

## 安装运行

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 修改扫描目录（如果需要）：
编辑 `app.py` 中的 `ROOT_PATH` 变量

3. 启动应用：
```bash
python app.py
```

4. 访问地址：http://localhost:5000

## 项目结构

```
project-manager/
├── app.py              # Flask 主应用
├── scanner.py          # 扫描器（项目/软件检测）
├── requirements.txt    # Python 依赖
├── templates/
│   └── index.html      # 前端页面
└── static/
    ├── css/
    │   └── style.css   # 样式文件
    └── js/
        └── app.js      # 前端逻辑
```

## API 接口

- `GET /` - 主页
- `GET /api/projects` - 获取项目列表
- `GET /api/software` - 获取软件列表
- `GET /api/scan` - 扫描所有内容
- `POST /api/open` - 打开项目目录
- `GET /api/info/<path>` - 获取项目详情
