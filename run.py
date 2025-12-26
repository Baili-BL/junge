#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
钧哥天下无双 - 快速启动脚本
直接启动Web推荐服务
"""

import subprocess
import sys
import os

def check_dependencies():
    """检查并安装依赖"""
    print("[INFO] Checking dependencies...")
    try:
        import akshare
        import flask
        import pandas
        print("[OK] Dependencies installed")
        return True
    except ImportError:
        print("[INFO] Installing dependencies...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"
        ])
        return True

def main():
    """主函数 - 直接启动Web服务"""
    print("""
============================================================
      JunGe TianXiaWuShuang - Stock Recommendation System
============================================================
    """)
    
    # 确保在正确的目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # 检查依赖
    check_dependencies()
    
    print("\n" + "="*50)
    print("[OK] Starting Web Server...")
    print("[INFO] Visit: http://localhost:5000")
    print("="*50 + "\n")
    
    try:
        from app import app
        app.run(debug=False, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n\n[INFO] Program exited")
        sys.exit(0)

if __name__ == "__main__":
    main()

