# SLA Calculator - 服务等级协议计算器

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?logo=flask&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)

一个功能完善的 SLA（服务等级协议）计算工具，帮助您计算服务可用性、停机时间和赔偿金额。

## 功能特性

### 可用性计算
- 根据 SLA 等级快速计算允许的停机时间
- 支持按天/周/月/季度/年显示停机时间
- 预设常用 SLA 等级（99%, 99.9%, 99.99%, 99.999%）
- 滑块与输入框双向同步

### SLA 对比
- 同时对比多个 SLA 等级
- 直观展示不同等级的停机时间差异
- 帮助选择合适的服务等级

### 赔偿计算
- 根据实际可用性计算赔偿金额
- 支持自定义月服务费用
- 分级赔偿标准

### 实际可用性
- 根据总时间和停机时间反推可用性百分比
- 自动匹配最接近的 SLA 等级

### 反向计算
- 根据允许的停机时间计算需要的 SLA 等级
- 支持时/分/秒转换

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 启动应用
python app.py
```

启动后访问 **http://localhost:5001**

## 项目结构

```
sla-calculator/
├── app.py              # Flask 主应用
├── requirements.txt    # Python 依赖
├── README.md           # 项目文档
├── templates/
│   └── index.html      # 前端页面
└── static/
    ├── css/
    │   └── style.css   # 深色主题样式
    └── js/
        └── app.js      # 前端交互逻辑
```

## 技术栈

- **后端**: Flask (Python)
- **前端**: 原生 JavaScript + CSS3
- **界面**: 深色主题，响应式设计

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 主页 |
| `/api/calculate` | POST | 计算停机时间 |
| `/api/sla-levels` | GET | 获取所有 SLA 等级 |
| `/api/compare` | POST | 对比多个 SLA 等级 |
| `/api/credit` | POST | 计算赔偿金额 |
| `/api/actual-uptime` | POST | 计算实际可用性 |
| `/api/reverse-calculate` | POST | 反向计算 SLA |

## SLA 等级参考

| 等级 | 描述 | 每月停机时间 | 每年停机时间 |
|------|------|-------------|-------------|
| 90% | 基本可用 | ~3 天 | ~36.5 天 |
| 95% | 良好可用 | ~1.5 天 | ~18.3 天 |
| 99% | 高可用 | ~7.2 小时 | ~3.7 天 |
| 99.9% | 极高可用 (2个9) | ~43 分钟 | ~8.8 小时 |
| 99.99% | 近乎完美 (4个9) | ~4.3 分钟 | ~52.6 分钟 |
| 99.999% | 完美可用 (5个9) | ~26 秒 | ~5.3 分钟 |
| 99.9999% | 六个9 | ~2.6 秒 | ~31.5 秒 |

## 界面预览

五个功能模块，侧边栏导航切换：

- **可用性计算** - 滑块调节百分比，实时显示各周期停机时间
- **SLA 对比** - 勾选多个等级，表格对比停机差异
- **赔偿计算** - 输入 SLA 承诺、实际可用性、月费用，计算赔偿
- **实际可用性** - 输入停机时间，反推可用率
- **反向计算** - 输入允许停机时间，计算所需 SLA 等级
