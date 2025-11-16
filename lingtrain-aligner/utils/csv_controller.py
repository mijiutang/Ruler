#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CSV表格控制器模块
负责协调UI和数据管理层之间的交互，使用CSV存储方式
"""

from backend.csv_data_manager import CSVTableDataManager
import os

class CSVTableController:
    """CSV表格控制器类"""
    
    def __init__(self, rows=None, cols=None):
        """
        初始化控制器
        
        Args:
            rows (int, optional): 初始行数，默认为None表示不创建默认表格
            cols (int, optional): 初始列数，默认为None表示不创建默认表格
        """
        # 如果没有指定行列数，则创建一个空的数据管理器
        if rows is None or cols is None:
            self.data_manager = CSVTableDataManager(0, 0)
        else:
            self.data_manager = CSVTableDataManager(rows, cols)
        self.is_modified = False  # 标记数据是否被修改
        self.main_window = None  # 添加主窗口引用
    
    def set_main_window(self, main_window):
        """
        设置主窗口引用
        
        Args:
            main_window: 主窗口对象
        """
        self.main_window = main_window
    
    def get_data(self):
        """获取表格数据"""
        return self.data_manager.get_data()
    
    def set_cell_data(self, row, col, value):
        """
        设置单元格数据，并实时同步到CSV文件
        
        Args:
            row (int): 行索引
            col (int): 列索引
            value (str): 单元格值
        """
        old_value = self.data_manager.get_cell_data(row, col)
        if old_value != value:
            self.data_manager.set_cell_data(row, col, value)
            self.is_modified = True
            # 实时同步到CSV文件
            if self.data_manager.current_file_path:
                try:
                    self.data_manager.save_to_csv(overwrite=True)
                except Exception as e:
                    print(f"实时同步失败: {e}")
    
    def add_row(self, position=None):
        """
        添加新行，并实时同步到CSV文件
        
        Args:
            position (int, optional): 添加位置，默认在末尾添加
        """
        self.data_manager.add_row(position)
        self.is_modified = True
        # 实时同步到CSV文件
        if self.data_manager.current_file_path:
            try:
                self.data_manager.save_to_csv(overwrite=True)
            except Exception as e:
                print(f"实时同步失败: {e}")
    
    def add_column(self, position=None):
        """
        添加新列，并实时同步到CSV文件
        
        Args:
            position (int, optional): 添加位置，默认在末尾添加
        """
        self.data_manager.add_column(position)
        self.is_modified = True
        # 实时同步到CSV文件
        if self.data_manager.current_file_path:
            try:
                self.data_manager.save_to_csv(overwrite=True)
            except Exception as e:
                print(f"实时同步失败: {e}")
    
    def delete_row(self, position):
        """
        删除指定行，并实时同步到CSV文件
        
        Args:
            position (int): 要删除的行索引
            
        Returns:
            bool: 删除是否成功
        """
        result = self.data_manager.delete_row(position)
        if result:
            self.is_modified = True
            # 实时同步到CSV文件
            if self.data_manager.current_file_path:
                try:
                    self.data_manager.save_to_csv(overwrite=True)
                except Exception as e:
                    print(f"实时同步失败: {e}")
        return result
    
    def delete_column(self, position):
        """
        删除指定列，并实时同步到CSV文件
        
        Args:
            position (int): 要删除的列索引
            
        Returns:
            bool: 删除是否成功
        """
        result = self.data_manager.delete_column(position)
        if result:
            self.is_modified = True
            # 实时同步到CSV文件
            if self.data_manager.current_file_path:
                try:
                    self.data_manager.save_to_csv(overwrite=True)
                except Exception as e:
                    print(f"实时同步失败: {e}")
        return result
    
    def get_row_count(self):
        """获取行数"""
        return self.data_manager.get_row_count()
    
    def get_column_count(self):
        """获取列数"""
        return self.data_manager.get_column_count()
    
    def new_table(self, rows=10, cols=10):
        """
        创建新表格，并实时同步到CSV文件
        
        Args:
            rows (int): 行数，默认为10
            cols (int): 列数，默认为10
        """
        self.data_manager.new_table(rows, cols)
        self.is_modified = False
        # 实时同步到CSV文件
        if self.data_manager.current_file_path:
            try:
                self.data_manager.save_to_csv(overwrite=True)
            except Exception as e:
                print(f"实时同步失败: {e}")
    
    def save_table(self):
        """
        保存当前表格（仅更新UI，不实际保存文件）
        
        Returns:
            str: 表格名称
        """
        # 如果没有当前文件路径，则生成一个默认名称
        if not self.data_manager.current_table_name:
            # 生成默认名称
            default_name = f"表格_{self.data_manager.rows}x{self.data_manager.cols}"
            self.data_manager.current_table_name = default_name
        
        # 不实际保存文件，只返回表格名称
        result = self.data_manager.current_table_name
        self.is_modified = False
        return result
    
    def save_table_as(self, table_name):
        """
        另存为表格（仅更新UI，不实际保存文件）
        
        Args:
            table_name (str): 表格名称
            
        Returns:
            str: 表格名称
        """
        # 不实际保存文件，只更新表格名称
        self.data_manager.current_table_name = table_name
        result = table_name
        self.is_modified = False
        return result
    
    def load_table(self, file_path):
        """
        从CSV文件加载表格，并建立实时同步
        
        Args:
            file_path (str): CSV文件路径
            
        Returns:
            bool: 加载是否成功
        """
        result = self.data_manager.load_from_csv(file_path)
        if result:
            self.is_modified = False
        return result
    
    def get_all_tables(self):
        """
        获取所有CSV表格信息
        
        Returns:
            list: 包含表格信息的列表
        """
        return self.data_manager.get_all_tables()
    
    def delete_table(self, file_path):
        """
        删除指定的CSV表格
        
        Args:
            file_path (str): 要删除的文件路径
            
        Returns:
            bool: 删除是否成功
        """
        return self.data_manager.delete_from_csv(file_path)
    
    def get_table_data(self):
        """
        获取表格数据
        
        Returns:
            list: 二维列表形式的表格数据
        """
        return self.data_manager.get_data()
    
    def get_current_table_info(self):
        """
        获取当前表格信息
        
        Returns:
            dict: 包含当前表格信息的字典
        """
        # 检查是否有CSV文件存在
        tables = self.data_manager.csv_handler.get_all_tables()
        
        # 如果没有任何CSV文件且当前没有数据，则返回0行0列
        if not tables and (self.data_manager.rows == 0 or self.data_manager.cols == 0):
            info = {
                'rows': 0,
                'cols': 0,
                'current_file_path': self.data_manager.current_file_path,
                'current_table_name': self.data_manager.current_table_name
            }
        else:
            info = self.data_manager.get_current_table_info()
        info['is_modified'] = self.is_modified
        return info
    
    def _update_ui(self):
        """更新UI显示"""
        if self.main_window:
            self.main_window.update_table()