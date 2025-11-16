#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CSV表格数据管理模块
负责表格数据的存储和管理，支持CSV文件存储
"""

from backend.csv_handler import CSVHandler
import time
import os

class CSVTableDataManager:
    """CSV表格数据管理类"""
    
    def __init__(self, rows=0, cols=0):
        """
        初始化表格数据
        
        Args:
            rows (int): 初始行数，默认为0表示空表格
            cols (int): 初始列数，默认为0表示空表格
        """
        self.rows = rows
        self.cols = cols
        # 只有当行列数都大于0时才创建数据
        if rows > 0 and cols > 0:
            self.data = [["" for _ in range(cols)] for _ in range(rows)]
        else:
            self.data = []
        self.current_file_path = None
        self.current_table_name = None
        self.csv_handler = CSVHandler()
    
    def get_data(self):
        """获取表格数据"""
        return self.data
    
    def set_data(self, data):
        """
        设置表格数据
        
        Args:
            data (list): 新的表格数据
        """
        if data and len(data) > 0:
            self.rows = len(data)
            self.cols = len(data[0]) if data[0] else 0
            self.data = data
    
    def get_cell_data(self, row, col):
        """
        获取指定单元格数据
        
        Args:
            row (int): 行索引
            col (int): 列索引
            
        Returns:
            str: 单元格数据
        """
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.data[row][col]
        return ""
    
    def set_cell_data(self, row, col, value):
        """
        设置指定单元格数据
        
        Args:
            row (int): 行索引
            col (int): 列索引
            value (str): 单元格值
        """
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.data[row][col] = value
    
    def add_row(self, position=None):
        """
        添加新行
        
        Args:
            position (int, optional): 添加位置，默认在末尾添加
        """
        if position is None or position >= self.rows:
            # 在末尾添加
            self.data.append(["" for _ in range(self.cols)])
            self.rows += 1
        else:
            # 在指定位置插入
            self.data.insert(position, ["" for _ in range(self.cols)])
            self.rows += 1
    
    def add_column(self, position=None):
        """
        添加新列
        
        Args:
            position (int, optional): 添加位置，默认在末尾添加
        """
        if position is None or position >= self.cols:
            # 在末尾添加
            for row in self.data:
                row.append("")
            self.cols += 1
        else:
            # 在指定位置插入
            for row in self.data:
                row.insert(position, "")
            self.cols += 1
    
    def delete_row(self, position):
        """
        删除指定行
        
        Args:
            position (int): 要删除的行索引
            
        Returns:
            bool: 删除是否成功
        """
        # 检查行索引有效性以及至少保留一行
        if 0 <= position < self.rows and self.rows > 1:
            # 删除指定行
            self.data.pop(position)
            # 更新行数
            self.rows -= 1
            return True
        return False
    
    def delete_column(self, position):
        """
        删除指定列
        
        Args:
            position (int): 要删除的列索引
            
        Returns:
            bool: 删除是否成功
        """
        # 检查列索引有效性以及至少保留一列
        if 0 <= position < self.cols and self.cols > 1:
            # 遍历每一行，删除指定位置的列
            for row in self.data:
                # 确保要删除的列索引在当前行范围内
                if position < len(row):
                    row.pop(position)
            
            # 更新列数
            self.cols -= 1
            return True
        return False
    
    def get_row_count(self):
        """获取行数"""
        return self.rows
    
    def get_column_count(self):
        """获取列数"""
        return self.cols
    
    # CSV文件相关方法
    def save_to_csv(self, table_name=None, overwrite=False):
        """
        保存当前表格数据到CSV文件
        
        Args:
            table_name (str, optional): 表格名称，如果未提供则使用当前名称
            overwrite (bool): 是否覆盖已存在的文件
            
        Returns:
            str: 保存的文件路径，失败返回None
        """
        name = table_name or self.current_table_name or f"表格_{int(time.time())}"
        
        file_path = self.csv_handler.save_table(name, self.data, overwrite)
        if file_path:
            self.current_file_path = file_path
            self.current_table_name = name
        return file_path
    
    def load_from_csv(self, file_path):
        """
        从CSV文件加载表格数据
        
        Args:
            file_path (str): CSV文件路径
            
        Returns:
            bool: 加载是否成功
        """
        name, data = self.csv_handler.load_table(file_path)
        if data is not None:
            self.set_data(data)
            self.current_file_path = file_path
            self.current_table_name = name
            return True
        return False
    
    def get_all_tables(self):
        """
        获取所有CSV文件信息
        
        Returns:
            list: 包含文件信息的列表
        """
        return self.csv_handler.get_all_tables()
    
    def delete_from_csv(self, file_path):
        """
        从CSV文件系统删除表格
        
        Args:
            file_path (str): 要删除的文件路径
            
        Returns:
            bool: 删除是否成功
        """
        return self.csv_handler.delete_table(file_path)
    
    def new_table(self, rows=10, cols=10):
        """
        创建新表格，清除当前数据
        
        Args:
            rows (int): 行数，默认为10
            cols (int): 列数，默认为10
        """
        self.rows = rows
        self.cols = cols
        self.data = [["" for _ in range(cols)] for _ in range(rows)]
        self.current_file_path = None
        self.current_table_name = None
    
    def get_current_table_info(self):
        """
        获取当前表格信息
        
        Returns:
            dict: 包含当前表格信息的字典
        """
        return {
            'file_path': self.current_file_path,
            'name': self.current_table_name,
            'rows': self.rows,
            'cols': self.cols
        }