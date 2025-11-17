#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试CSV文件同步功能
验证内存数据与磁盘文件的一致性
"""

import os
import sys
import time

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.csv_data_manager import CSVTableDataManager
from utils.csv_controller import CSVTableController

def test_data_sync():
    """测试数据同步功能"""
    print("=== 测试CSV文件同步功能 ===")
    
    # 创建测试表格名称
    test_table_name = "同步测试表格"
    
    # 1. 测试新建表格并立即保存
    print("\n1. 测试新建表格并立即保存")
    controller = CSVTableController(5, 3)
    print(f"创建表格: 5行3列")
    controller.new_table(5, 3, test_table_name)
    print(f"表格信息: {controller.get_current_table_info()}")
    
    # 检查文件是否存在
    file_path = controller.data_manager.current_file_path
    print(f"文件路径: {file_path}")
    print(f"文件是否存在: {os.path.exists(file_path) if file_path else False}")
    
    # 2. 测试修改单元格数据
    print("\n2. 测试修改单元格数据")
    controller.set_cell_data(0, 0, "测试1")
    controller.set_cell_data(1, 1, "测试2")
    controller.set_cell_data(2, 2, "测试3")
    
    # 从磁盘重新加载数据，验证是否同步
    new_controller = CSVTableController()
    new_controller.load_table(file_path)
    data = new_controller.get_data()
    print(f"修改后从磁盘读取的数据:")
    for i, row in enumerate(data):
        print(f"  行{i}: {row}")
    
    # 3. 测试添加行和列
    print("\n3. 测试添加行和列")
    controller.add_row()
    controller.add_column()
    controller.set_cell_data(5, 3, "新增数据")
    
    # 从磁盘重新加载数据，验证是否同步
    new_controller.load_table(file_path)
    data = new_controller.get_data()
    print(f"添加行列后从磁盘读取的数据:")
    for i, row in enumerate(data):
        print(f"  行{i}: {row}")
    
    # 4. 测试删除行和列
    print("\n4. 测试删除行和列")
    controller.delete_row(0)
    controller.delete_column(0)
    
    # 从磁盘重新加载数据，验证是否同步
    new_controller.load_table(file_path)
    data = new_controller.get_data()
    print(f"删除行列后从磁盘读取的数据:")
    for i, row in enumerate(data):
        print(f"  行{i}: {row}")
    
    # 5. 测试另存为
    print("\n5. 测试另存为")
    new_table_name = "另存为测试表格"
    controller.save_table_as(new_table_name)
    # 获取另存为后的文件路径
    new_file_path = controller.data_manager.current_file_path
    print(f"另存为文件路径: {new_file_path}")
    print(f"另存为文件是否存在: {os.path.exists(new_file_path) if new_file_path else False}")
    
    # 验证另存为的文件内容
    another_controller = CSVTableController()
    another_controller.load_table(new_file_path)
    data = another_controller.get_data()
    print(f"另存为文件的内容:")
    for i, row in enumerate(data):
        print(f"  行{i}: {row}")
    
    # 6. 测试删除表格
    print("\n6. 测试删除表格")
    delete_result = controller.delete_table(file_path)
    print(f"删除原表格结果: {delete_result}")
    print(f"原表格文件是否还存在: {os.path.exists(file_path) if file_path else False}")
    
    delete_result2 = another_controller.delete_table(new_file_path)
    print(f"删除另存为表格结果: {delete_result2}")
    print(f"另存为表格文件是否还存在: {os.path.exists(new_file_path) if new_file_path else False}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_data_sync()