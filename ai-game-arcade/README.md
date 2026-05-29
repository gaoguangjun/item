# AI Game Arcade - AI 游戏乐园

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?logo=flask&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)

一个 AI 驱动的游戏创建与游玩平台，灵感来自 [Astrocade](https://www.astrocade.com/)。用文字描述即可生成可玩的 HTML5 游戏。

## 功能特性

### 游戏大厅
- 浏览、搜索、分类筛选游戏
- 热门趋势 / 最多点赞 / 最新创建排序
- 一键游玩，内嵌游戏播放器

### AI 创建游戏
- 输入文字描述，AI 自动生成完整 HTML5 Canvas 游戏
- 生成前可预览，满意后保存
- 支持重新生成
- 兼容 OpenAI / Claude / 本地大模型 API

### 我的作品
- 管理已创建的游戏
- 编辑游戏信息（标题、描述、分类、公开/私有）
- 删除游戏

### 个人中心
- 用户名自定义
- 统计数据（创建数、获赞数、游玩数）

### 游戏播放器
- 全屏模态弹窗
- 沙盒化 iframe 安全运行
- 点赞、分享功能
- 自动记录游玩次数

## 快速开始

```bash
cd ai-game-arcade
pip install -r requirements.txt
python app.py
```

启动后访问 **http://localhost:5002**

### 配置 AI（可选）

设置环境变量以启用 AI 游戏生成：

```bash
# OpenAI
export LLM_API_KEY=sk-xxx
export LLM_BASE_URL=https://api.openai.com/v1
export LLM_MODEL=gpt-4o

# 或兼容 API（如本地模型）
export LLM_API_KEY=your-key
export LLM_BASE_URL=http://localhost:8000/v1
export LLM_MODEL=your-model
```

不配置 API Key 时，仍可使用内置 Demo 游戏和生成基础游戏。

## 项目结构

```
ai-game-arcade/
├── app.py              # Flask 主应用
├── db.py               # SQLite 数据库操作
├── ai_generator.py     # AI 游戏代码生成
├── config.py           # 配置文件
├── demo_games.py       # 内置 Demo 游戏
├── requirements.txt    # Python 依赖
├── data/               # 数据库（自动创建）
├── templates/
│   └── index.html      # 前端页面
└── static/
    ├── css/style.css   # 深色主题样式
    └── js/app.js       # 前端逻辑
```

## 技术栈

- **后端**: Flask + SQLite
- **前端**: 原生 JavaScript + CSS3
- **AI**: OpenAI 兼容 API（urllib，无额外依赖）
- **游戏引擎**: HTML5 Canvas
- **主题**: 深色紫色主题

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/games` | GET | 游戏列表（支持排序/搜索/分类） |
| `/api/games` | POST | 创建游戏 |
| `/api/games/<id>` | GET | 游戏详情 |
| `/api/games/<id>` | PUT | 更新游戏 |
| `/api/games/<id>` | DELETE | 删除游戏 |
| `/api/games/<id>/play` | POST | 记录游玩 |
| `/api/games/<id>/like` | POST | 点赞/取消 |
| `/api/generate` | POST | AI 生成游戏代码 |
| `/api/user` | GET/PUT | 用户信息 |
| `/api/user/games` | GET | 我的游戏 |
| `/api/categories` | GET | 分类列表 |

## 内置 Demo 游戏

| 游戏 | 分类 | 说明 |
|------|------|------|
| 接球游戏 | 休闲 | 控制篮子接住掉落的球 |
| 打砖块 | 益智 | 经典打砖块，反弹球消除砖块 |
| 贪吃蛇 | 益智 | 经典贪吃蛇，吃食物变长 |
| 点击反应 | 休闲 | 快速点击随机出现的圆圈 |
