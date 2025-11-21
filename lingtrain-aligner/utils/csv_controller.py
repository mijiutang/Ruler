#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CSV表格控制器模块
负责协调UI和数据管理层之间的交互，使用CSV存储方式
"""

from backend.csv_data_manager import CSVTableDataManager
from utils.command_history import CommandHistory
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
        self.command_history = CommandHistory()  # 命令历史管理器
    
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
    
    def start_batch_update(self):
        """开始批量更新模式，暂停磁盘同步"""
        self.data_manager.start_batch_update()
    
    def end_batch_update(self):
        """结束批量更新模式，同步所有待处理的更改到磁盘"""
        self.data_manager.end_batch_update()
    
    def set_cell_data(self, row, col, value, use_command=True):
        """
        设置单元格数据
        
        Args:
            row (int): 行索引
            col (int): 列索引
            value (str): 单元格值
            use_command (bool): 是否使用命令模式，默认为True
        """
        old_value = self.data_manager.get_cell_data(row, col)
        if old_value != value:
            if use_command and self.main_window:
                # 使用命令模式
                from utils.table_commands import EditCellCommand
                command = EditCellCommand(self.data_manager, row, col, value, old_value)
                self.execute_command(command)
            else:
                # 直接设置数据
                self.data_manager.set_cell_data(row, col, value)
                self.is_modified = True
    
    def add_row(self, position=None, use_command=True):
        """
        添加新行
        
        Args:
            position (int, optional): 添加位置，默认在末尾添加
            use_command (bool): 是否使用命令模式，默认为True
        """
        if use_command and self.main_window:
            # 使用命令模式
            from utils.table_commands import InsertRowCommand
            command = InsertRowCommand(self.data_manager, position)
            self.execute_command(command)
        else:
            # 直接添加行
            self.data_manager.add_row(position)
            self.is_modified = True
    
    def add_column(self, position=None, use_command=True):
        """
        添加新列
        
        Args:
            position (int, optional): 添加位置，默认在末尾添加
            use_command (bool): 是否使用命令模式，默认为True
        """
        if use_command and self.main_window:
            # 使用命令模式
            from utils.table_commands import InsertColumnCommand
            command = InsertColumnCommand(self.data_manager, position)
            self.execute_command(command)
        else:
            # 直接添加列
            self.data_manager.add_column(position)
            self.is_modified = True
    
    def delete_row(self, position, use_command=True):
        """
        删除指定行
        
        Args:
            position (int): 要删除的行索引
            use_command (bool): 是否使用命令模式，默认为True
            
        Returns:
            bool: 删除是否成功
        """
        if use_command and self.main_window:
            # 使用命令模式
            from utils.table_commands import DeleteRowCommand
            command = DeleteRowCommand(self.data_manager, position)
            self.execute_command(command)
            return True
        else:
            # 直接删除行
            result = self.data_manager.delete_row(position)
            if result:
                self.is_modified = True
            return result
    
    def delete_column(self, position, use_command=True):
        """
        删除指定列
        
        Args:
            position (int): 要删除的列索引
            use_command (bool): 是否使用命令模式，默认为True
            
        Returns:
            bool: 删除是否成功
        """
        if use_command and self.main_window:
            # 使用命令模式
            from utils.table_commands import DeleteColumnCommand
            command = DeleteColumnCommand(self.data_manager, position)
            self.execute_command(command)
            return True
        else:
            # 直接删除列
            result = self.data_manager.delete_column(position)
            if result:
                self.is_modified = True
            return result
    
    def get_row_count(self):
        """获取行数"""
        return self.data_manager.get_row_count()
    
    def get_column_count(self):
        """获取列数"""
        return self.data_manager.get_column_count()
    
    def new_table(self, rows=10, cols=4, table_name=None):
        """
        创建新表格
        
        Args:
            rows (int): 行数，默认为10
            cols (int): 列数，默认为4
            table_name (str, optional): 表格名称，如果未提供则使用默认名称
        """
        self.data_manager.new_table(rows, cols, table_name)
        self.is_modified = False
        # 数据管理器已实现实时同步，无需额外操作
    
    def save_table(self):
        """
        保存当前表格
        
        Returns:
            str: 表格名称
        """
        # 如果没有当前文件路径，则生成一个默认名称
        if not self.data_manager.current_table_name:
            # 生成默认名称
            default_name = f"表格_{self.data_manager.rows}×{self.data_manager.cols}"
            self.data_manager.current_table_name = default_name
        
        # 实际保存文件
        result = self.data_manager.save_to_csv(overwrite=True)
        self.is_modified = False
        return self.data_manager.current_table_name
    
    def save_table_as(self, table_name):
        """
        另存为表格
        
        Args:
            table_name (str): 表格名称
            
        Returns:
            str: 表格名称
        """
        # 实际保存文件
        result = self.data_manager.save_to_csv(table_name, overwrite=False)
        self.is_modified = False
        return table_name
    
    def load_table(self, table_id):
        """
        加载表格 - 内存优化版本
        
        Args:
            table_id: 可以是表格ID(int)或文件路径(str)
            
        Returns:
            bool: 加载是否成功
        """
        if isinstance(table_id, int):
            # 通过ID加载表格
            table_info = self.data_manager.get_table_info_by_id(table_id)
            if not table_info:
                return False
            
            file_path = table_info['file_path']
            table_name = table_info['name']
        else:
            # 通过文件路径加载表格
            file_path = table_id
            table_name = os.path.basename(file_path)
        
        # 加载表格数据
        if self.data_manager.load_from_csv(file_path):
            self.current_table_id = table_id
            self.current_table_name = table_name
            self.is_modified = False  # 重置修改状态
            return True
        
        return False
    
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
    
    def refresh_from_disk(self):
        """强制从磁盘刷新数据，使内存缓存无效"""
        return self.data_manager.refresh_from_disk()
    
    def _update_ui(self, changed_cells=None):
        """更新UI"""
        if self.main_window:
            # 如果有变化的单元格，使用增量更新；否则使用完整更新
            if changed_cells:
                self.main_window.update_table(incremental=True, changed_cells=changed_cells)
            else:
                self.main_window.update_table()
    
    def undo(self):
        """
        撤回上一个操作
        
        Returns:
            list: 变化的单元格列表，用于增量更新
        """
        # 执行撤回并获取变化的单元格
        changed_cells = self.command_history.undo()
        # 如果不在批量更新模式，更新UI
        if not hasattr(self, '_batch_update_mode') or not self._batch_update_mode:
            self._update_ui(changed_cells)
        # 返回变化的单元格，用于增量更新
        return changed_cells
    
    def redo(self):
        """
        重做上一个撤回的操作
        
        Returns:
            list: 变化的单元格列表，用于增量更新
        """
        # 执行重做并获取变化的单元格
        changed_cells = self.command_history.redo()
        # 如果不在批量更新模式，更新UI
        if not hasattr(self, '_batch_update_mode') or not self._batch_update_mode:
            self._update_ui(changed_cells)
        # 返回变化的单元格，用于增量更新
        return changed_cells
    
    def can_undo(self):
        """
        检查是否可以撤回
        
        Returns:
            bool: 是否可以撤回
        """
        return self.command_history.can_undo()
    
    def can_redo(self):
        """
        检查是否可以重做
        
        Returns:
            bool: 是否可以重做
        """
        return self.command_history.can_redo()
    
    def get_dirty_cells(self):
        """
        获取所有修改过的单元格坐标
        
        Returns:
            set: 修改过的单元格坐标集合 {(row, col), ...}
        """
        return self.data_manager.get_dirty_cells()
    
    def clear_dirty_cells(self):
        """清空脏数据集合"""
        self.data_manager.clear_dirty_cells()
    
    def get_hot_cells(self, threshold=5):
        """
        获取访问次数超过阈值的单元格坐标
        
        Args:
            threshold (int): 访问次数阈值，默认为5
            
        Returns:
            list: 访问次数超过阈值的单元格坐标列表 [(row, col, count), ...]
        """
        return self.data_manager.get_hot_cells(threshold)
    
    def execute_command(self, command):
        """
        执行命令并添加到历史记录
        
        Args:
            command: 要执行的命令
            
        Returns:
            list: 变化的单元格列表，用于增量更新
        """
        # 执行命令并获取变化的单元格
        changed_cells = self.command_history.execute_command(command)
        # 只有在非批量更新模式下才立即更新UI
        if not hasattr(self, '_batch_update_mode') or not self._batch_update_mode:
            self._update_ui(changed_cells)
        self.is_modified = True
        # 返回变化的单元格，用于增量更新
        return changed_cells
    
    def start_batch_update(self):
        """开始批量更新模式，暂停UI更新"""
        self._batch_update_mode = True
        self.data_manager.start_batch_update()
    
    def end_batch_update(self, update_ui=True):
        """结束批量更新模式，恢复UI更新
        
        Args:
            update_ui (bool): 是否在结束时更新UI，默认为True
        """
        self._batch_update_mode = False
        self.data_manager.end_batch_update()
        if update_ui:
            self._update_ui()