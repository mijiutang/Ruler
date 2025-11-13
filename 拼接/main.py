#!/usr/bin/env python3
"""
图片裁剪与拼接工具 - 主程序入口
基于PyQt5和OpenCV实现的图片处理工具
"""

import sys
import os

# 添加UI模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'ui'))

from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    """主函数"""
    # 创建应用程序
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()