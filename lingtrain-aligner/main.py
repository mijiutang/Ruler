#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
表格编辑器主程序入口
UI和后端分离的PyQt5应用程序
"""

import sys
import argparse
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow

# CSV存储模式
from utils.csv_controller import CSVTableController

def main():
    """主函数，启动应用程序"""
    # 添加命令行参数支持
    parser = argparse.ArgumentParser(description='表格编辑器')
    parser.add_argument('--storage', choices=['csv'], default='csv', 
                       help='选择存储模式: csv(CSV文件)')
    args = parser.parse_args()
    
    app = QApplication(sys.argv)
    
    # 创建控制器，使用CSV存储
    # 不再创建默认的空白表格，而是根据实际CSV文件来显示
    controller = CSVTableController()
    
    # 创建主窗口并传入控制器
    window = MainWindow(controller)
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()