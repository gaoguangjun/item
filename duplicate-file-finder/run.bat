@echo off
chcp 65001 >nul
title 重复文件检查工具

echo ========================================
echo    重复文件检查工具
echo ========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] 检查依赖...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo [2/3] 安装依赖中...
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
) else (
    echo [2/3] 依赖已安装，跳过...
)

echo [3/3] 启动服务器...
echo.
echo 服务器启动后，请在浏览器中访问: http://127.0.0.1:8000
echo 按 Ctrl+C 可停止服务器
echo.

python main.py
