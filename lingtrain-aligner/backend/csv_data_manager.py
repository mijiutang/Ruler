#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CSV表格数据管理模块
负责表格数据的存储和管理，支持CSV文件存储
实现内存与磁盘文件的实时同步
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
        # 添加同步锁，防止并发修改
        self._sync_lock = False
        # 添加批量更新机制
        self._batch_mode = False
        self._pending_changes = False
        # 内存优化：添加内存缓存标志，避免频繁磁盘读取
        self._memory_cache_valid = True
    
    def get_data(self):
        """获取表格数据，优先使用内存缓存"""
        # 如果内存缓存有效，直接返回内存中的数据
        if self._memory_cache_valid:
            return self.data
            
        # 只有在内存缓存无效时才从磁盘文件读取最新数据
        if self.current_file_path and os.path.exists(self.current_file_path):
            # 从磁盘文件读取最新数据
            _, data = self.csv_handler.load_table(self.current_file_path)
            if data is not None:
                self.data = data
                self.rows = len(data)
                self.cols = max(len(row) for row in data) if self.rows > 0 else 0
                # 标记内存缓存有效
                self._memory_cache_valid = True
        return self.data
    
    def set_data(self, data):
        """
        设置表格数据并立即同步到磁盘文件
        
        Args:
            data (list): 新的表格数据
        """
        if data and len(data) > 0:
            self.rows = len(data)
            # 计算所有行中的最大列数，而不仅仅是第一行
            self.cols = max(len(row) for row in data) if self.rows > 0 else 0
            # 确保所有行都有相同的列数，补齐空字符串
            self.data = []
            for row in data:
                # 如果当前行的列数少于最大列数，补齐空字符串
                if len(row) < self.cols:
                    row = row + ["" for _ in range(self.cols - len(row))]
                self.data.append(row)
            
            # 标记内存缓存有效
            self._memory_cache_valid = True
            
            # 立即同步到磁盘文件
            self._sync_to_disk()
    
    def get_cell_data(self, row, col):
        """
        获取指定单元格数据，优先使用内存缓存
        
        Args:
            row (int): 行索引
            col (int): 列索引
            
        Returns:
            str: 单元格数据
        """
        # 直接使用内存中的数据，不进行磁盘读取
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.data[row][col]
        return ""
    
    def set_cell_data(self, row, col, value):
        """
        设置指定单元格数据并立即同步到磁盘文件
        
        Args:
            row (int): 行索引
            col (int): 列索引
            value (str): 单元格值
        """
        # 直接使用内存中的数据，不进行磁盘读取
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.data[row][col] = value
            
            # 如果不是批量模式，立即同步到磁盘文件
            if not self._batch_mode:
                self._sync_to_disk()
            else:
                # 批量模式下，只标记有待处理的更改
                self._pending_changes = True
    
    def start_batch_update(self):
        """开始批量更新模式，暂停磁盘同步"""
        self._batch_mode = True
        self._pending_changes = False
    
    def end_batch_update(self):
        """结束批量更新模式，同步所有待处理的更改到磁盘"""
        if self._batch_mode and self._pending_changes:
            self._sync_to_disk()
            self._pending_changes = False
        self._batch_mode = False
    
    def add_row(self, position=None):
        """
        添加新行并立即同步到磁盘文件
        
        Args:
            position (int, optional): 添加位置，默认在末尾添加
        """
        # 直接使用内存中的数据，不进行磁盘读取
        if position is None or position >= self.rows:
            # 在末尾添加
            self.data.append(["" for _ in range(self.cols)])
            self.rows += 1
        else:
            # 在指定位置插入
            self.data.insert(position, ["" for _ in range(self.cols)])
            self.rows += 1
        
        # 立即同步到磁盘文件
        self._sync_to_disk()
    
    def add_column(self, position=None):
        """
        添加新列并立即同步到磁盘文件
        
        Args:
            position (int, optional): 添加位置，默认在末尾添加
        """
        # 直接使用内存中的数据，不进行磁盘读取
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
        
        # 立即同步到磁盘文件
        self._sync_to_disk()
    
    def delete_row(self, position):
        """
        删除指定行并立即同步到磁盘文件
        
        Args:
            position (int): 要删除的行索引
            
        Returns:
            bool: 删除是否成功
        """
        # 直接使用内存中的数据，不进行磁盘读取
        # 检查行索引有效性以及至少保留一行
        if 0 <= position < self.rows and self.rows > 1:
            # 删除指定行
            self.data.pop(position)
            # 更新行数
            self.rows -= 1
            
            # 立即同步到磁盘文件
            self._sync_to_disk()
            return True
        return False
    
    def delete_column(self, position):
        """
        删除指定列并立即同步到磁盘文件
        
        Args:
            position (int): 要删除的列索引
            
        Returns:
            bool: 删除是否成功
        """
        # 直接使用内存中的数据，不进行磁盘读取
        # 检查列索引有效性以及至少保留一列
        if 0 <= position < self.cols and self.cols > 1:
            # 遍历每一行，删除指定位置的列
            for row in self.data:
                # 确保要删除的列索引在当前行范围内
                if position < len(row):
                    row.pop(position)
            
            # 更新列数
            self.cols -= 1
            
            # 立即同步到磁盘文件
            self._sync_to_disk()
            return True
        return False
    
    def get_row_count(self):
        """获取行数，使用内存缓存"""
        return self.rows
    
    def get_column_count(self):
        """获取列数，使用内存缓存"""
        return self.cols
    
    def _sync_to_disk(self):
        """内部方法：将当前数据同步到磁盘文件"""
        if self._sync_lock or not self.current_file_path:
            return
            
        try:
            # 设置同步锁，防止递归同步
            self._sync_lock = True
            # 保存到磁盘文件
            self.csv_handler.save_table(self.current_table_name, self.data, overwrite=True)
        except Exception as e:
            print(f"同步到磁盘失败: {e}")
        finally:
            # 释放同步锁
            self._sync_lock = False
    
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
            # 直接设置数据，不调用set_data避免立即同步到磁盘
            if data and len(data) > 0:
                self.rows = len(data)
                # 计算所有行中的最大列数，而不仅仅是第一行
                self.cols = max(len(row) for row in data) if self.rows > 0 else 0
                # 确保所有行都有相同的列数，补齐空字符串
                self.data = []
                for row in data:
                    # 如果当前行的列数少于最大列数，补齐空字符串
                    if len(row) < self.cols:
                        row = row + ["" for _ in range(self.cols - len(row))]
                    self.data.append(row)
            else:
                self.data = []
                self.rows = 0
                self.cols = 0
                
            self.current_file_path = file_path
            self.current_table_name = name
            # 标记内存缓存有效
            self._memory_cache_valid = True
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
        result = self.csv_handler.delete_table(file_path)
        # 如果删除的是当前文件，清除当前文件信息
        if result and self.current_file_path == file_path:
            self.current_file_path = None
            self.current_table_name = None
            self.data = []
            self.rows = 0
            self.cols = 0
        return result
    
    def new_table(self, rows=10, cols=4, table_name=None):
        """
        创建新表格并立即保存到磁盘
        
        Args:
            rows (int): 行数，默认为10
            cols (int): 列数，默认为4
            table_name (str, optional): 表格名称
        """
        self.rows = rows
        self.cols = cols
        self.data = [["" for _ in range(cols)] for _ in range(rows)]
        
        # 如果提供了表格名称，立即保存到磁盘
        if table_name:
            self.current_table_name = table_name
            self.save_to_csv(table_name, overwrite=True)
    
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
    
    def refresh_from_disk(self):
        """
        强制从磁盘刷新数据，使内存缓存无效
        
        Returns:
            bool: 刷新是否成功
        """
        if self.current_file_path and os.path.exists(self.current_file_path):
            # 标记内存缓存无效
            self._memory_cache_valid = False
            # 调用get_data会从磁盘读取最新数据
            self.get_data()
            return True
        return False