#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试粘贴功能是否能正确扩展表格
"""

import sys
import os
import time
from PyQt5.QtWidgets import QApplication, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QClipboard

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.csv_controller import CSVTableController
from ui.main_window import MainWindow

def test_paste_functionality():
    """测试粘贴功能是否能正确扩展表格"""
    print("=== 测试粘贴功能 ===\n")
    
    # 创建应用程序实例（需要QApplication来处理剪贴板）
    app = QApplication(sys.argv)
    
    # 创建控制器和主窗口
    controller = CSVTableController(10, 4)  # 创建10行4列的表格
    window = MainWindow(controller)
    
    # 创建一个10x4的表格
    table_name = "测试粘贴表格"
    controller.new_table(10, 4, table_name)
    
    print(f"1. 创建了一个10行4列的表格: {table_name}")
    print(f"   当前行数: {controller.get_row_count()}")
    print(f"   当前列数: {controller.get_column_count()}")
    
    # 模拟粘贴20行数据（超过原始表格的10行）
    print("\n2. 模拟粘贴20行数据...")
    
    # 准备测试数据（20行，每行5列）
    test_data = []
    for i in range(20):
        row_data = []
        for j in range(5):  # 5列，超过原始表格的4列
            row_data.append(f"数据{i}_{j}")
        test_data.append(row_data)
    
    # 将数据放入剪贴板
    clipboard = QApplication.clipboard()
    text_data = '\n'.join(['\t'.join(row) for row in test_data])
    clipboard.setText(text_data)
    
    print(f"   准备粘贴的数据: {len(test_data)}行, 每行{len(test_data[0])}列")
    
    # 获取表格控件
    table = window.get_table()
    
    # 确保表格有焦点
    table.setFocus()
    table.setCurrentCell(0, 0)
    
    # 调用粘贴方法
    window.on_paste()
    
    # 检查表格是否已扩展
    print(f"\n3. 粘贴后的表格大小:")
    print(f"   UI表格行数: {table.rowCount()}")
    print(f"   UI表格列数: {table.columnCount()}")
    print(f"   数据管理器行数: {controller.get_row_count()}")
    print(f"   数据管理器列数: {controller.get_column_count()}")
    
    # 验证数据是否正确粘贴
    data = controller.get_data()
    print(f"\n4. 验证数据是否正确粘贴:")
    print(f"   前5行数据:")
    for i in range(min(5, len(data))):
        print(f"   行{i}: {data[i]}")
    
    print(f"   最后5行数据:")
    for i in range(max(0, len(data)-5), len(data)):
        print(f"   行{i}: {data[i]}")
    
    # 检查所有数据是否都正确保存
    expected_rows = 20
    expected_cols = 5
    success = True
    
    if controller.get_row_count() < expected_rows:
        print(f"\n错误: 行数不足! 期望 {expected_rows} 行, 实际 {controller.get_row_count()} 行")
        success = False
    
    if controller.get_column_count() < expected_cols:
        print(f"\n错误: 列数不足! 期望 {expected_cols} 列, 实际 {controller.get_column_count()} 列")
        success = False
    
    # 检查数据内容
    for i in range(expected_rows):
        for j in range(expected_cols):
            if i < len(data) and j < len(data[i]):
                expected_value = f"数据{i}_{j}"
                if data[i][j] != expected_value:
                    print(f"\n错误: 数据不匹配! 位置({i},{j}) 期望 '{expected_value}', 实际 '{data[i][j]}'")
                    success = False
    
    # 测试结果
    if success:
        print("\n✅ 测试通过: 粘贴功能正确扩展了表格大小并保存了数据")
    else:
        print("\n❌ 测试失败: 粘贴功能存在问题")
    
    # 保存测试文件
    file_path = controller.data_manager.current_file_path
    print(f"\n5. 测试表格已保存到: {file_path}")
    print(f"   文件是否存在: {os.path.exists(file_path) if file_path else False}")
    
    # 不显示窗口，直接退出
    app.quit()
    
    return success

if __name__ == "__main__":
    test_paste_functionality()