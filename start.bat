@echo off
chcp 65001 >nul
title 钧哥天下无双 - 股票推荐系统

echo.
echo ========================================
echo    钧哥天下无双 - 股票推荐系统
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 安装依赖
echo [信息] 检查并安装依赖...
pip install -r requirements.txt -q

echo.
echo ========================================
echo    启动Web服务...
echo    访问: http://localhost:5000
echo ========================================
echo.

REM 启动应用
python app.py

pause

