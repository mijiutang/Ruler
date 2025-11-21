#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
表格操作命令类
实现撤回/重做功能的具体命令
"""

from utils.command_history import Command

class EditCellCommand(Command):
    """编辑单元格命令"""
    
    def __init__(self, table_controller, row, col, new_value, old_value=None):
        """
        初始化编辑单元格命令
        
        Args:
            table_controller: 表格控制器
            row: 行索引
            col: 列索引
            new_value: 新值
            old_value: 旧值，如果为None则从表格获取
        """
        self.table_controller = table_controller
        self.row = row
        self.col = col
        self.new_value = new_value
        self.old_value = old_value if old_value is not None else table_controller.get_data()[row][col]
        # 记录变化的单元格，用于增量更新
        self.changed_cells = [(row, col)]
    
    def execute(self):
        """执行命令"""
        self.table_controller.set_cell_data(self.row, self.col, self.new_value)
        # 返回变化的单元格，用于增量更新
        return self.changed_cells
    
    def undo(self):
        """撤回命令"""
        self.table_controller.set_cell_data(self.row, self.col, self.old_value)
        # 返回变化的单元格，用于增量更新
        return self.changed_cells
    
    def redo(self):
        """重做命令"""
        return self.execute()

class InsertRowCommand(Command):
    """插入行命令"""
    
    def __init__(self, table_controller, position=None):
        """
        初始化插入行命令
        
        Args:
            table_controller: 表格控制器
            position: 插入位置，如果为None则在末尾插入
        """
        self.table_controller = table_controller
        self.position = position if position is not None else table_controller.get_row_count()
        # 记录影响的区域，用于增量更新
        self.affected_area = None
    
    def execute(self):
        """执行命令"""
        # 插入行
        self.table_controller.add_row(self.position)
        # 记录影响的区域（从插入行到最后一行）
        self.affected_area = [(self.position, col) for col in range(self.table_controller.get_column_count())]
        # 返回影响的区域，用于增量更新
        return self.affected_area
    
    def undo(self):
        """撤回命令"""
        # 删除插入的行
        self.table_controller.delete_row(self.position)
        # 返回影响的区域，用于增量更新
        return self.affected_area
    
    def redo(self):
        """重做命令"""
        return self.execute()

class InsertColumnCommand(Command):
    """插入列命令"""
    
    def __init__(self, table_controller, position=None):
        """
        初始化插入列命令
        
        Args:
            table_controller: 表格控制器
            position: 插入位置，如果为None则在末尾插入
        """
        self.table_controller = table_controller
        self.position = position if position is not None else table_controller.get_column_count()
        # 记录影响的区域，用于增量更新
        self.affected_area = None
    
    def execute(self):
        """执行命令"""
        # 插入列
        self.table_controller.add_column(self.position)
        # 记录影响的区域（从插入列到最后一列）
        self.affected_area = [(row, self.position) for row in range(self.table_controller.get_row_count())]
        # 返回影响的区域，用于增量更新
        return self.affected_area
    
    def undo(self):
        """撤回命令"""
        # 删除插入的列
        self.table_controller.delete_column(self.position)
        # 返回影响的区域，用于增量更新
        return self.affected_area
    
    def redo(self):
        """重做命令"""
        return self.execute()

class DeleteRowCommand(Command):
    """删除行命令"""
    
    def __init__(self, table_controller, position):
        """
        初始化删除行命令
        
        Args:
            table_controller: 表格控制器
            position: 要删除的行索引
        """
        self.table_controller = table_controller
        self.position = position
        self.row_data = None  # 保存被删除行的数据
        # 记录影响的区域，用于增量更新
        self.affected_area = None
    
    def execute(self):
        """执行命令"""
        # 保存要删除的行数据
        self.row_data = self.table_controller.get_data()[self.position].copy()
        self.table_controller.delete_row(self.position)
        # 记录影响的区域（从删除行到最后一行）
        self.affected_area = [(row, col) for row in range(self.position, self.table_controller.get_row_count()+1) 
                             for col in range(self.table_controller.get_column_count())]
        # 返回影响的区域，用于增量更新
        return self.affected_area
    
    def undo(self):
        """撤回命令"""
        # 插入被删除的行
        self.table_controller.add_row(self.position)
        # 恢复数据
        for col, value in enumerate(self.row_data):
            self.table_controller.set_cell_data(self.position, col, value)
        # 返回影响的区域，用于增量更新
        return self.affected_area
    
    def redo(self):
        """重做命令"""
        return self.execute()

class DeleteColumnCommand(Command):
    """删除列命令"""
    
    def __init__(self, table_controller, position):
        """
        初始化删除列命令
        
        Args:
            table_controller: 表格控制器
            position: 要删除的列索引
        """
        self.table_controller = table_controller
        self.position = position
        self.column_data = []  # 保存被删除列的数据
        # 记录影响的区域，用于增量更新
        self.affected_area = None
    
    def execute(self):
        """执行命令"""
        # 保存要删除的列数据
        for row in range(self.table_controller.get_row_count()):
            self.column_data.append(self.table_controller.get_data()[row][self.position])
        self.table_controller.delete_column(self.position)
        # 记录影响的区域（从删除列到最后一列）
        self.affected_area = [(row, col) for row in range(self.table_controller.get_row_count()) 
                             for col in range(self.position, self.table_controller.get_column_count()+1)]
        # 返回影响的区域，用于增量更新
        return self.affected_area
    
    def undo(self):
        """撤回命令"""
        # 插入被删除的列
        self.table_controller.add_column(self.position)
        # 恢复数据
        for row, value in enumerate(self.column_data):
            self.table_controller.set_cell_data(row, self.position, value)
        # 返回影响的区域，用于增量更新
        return self.affected_area
    
    def redo(self):
        """重做命令"""
        return self.execute()

class PasteDataCommand(Command):
    """粘贴数据命令"""
    
    def __init__(self, table_controller, start_row, start_col, paste_data):
        """
        初始化粘贴数据命令
        
        Args:
            table_controller: 表格控制器
            start_row: 起始行
            start_col: 起始列
            paste_data: 要粘贴的数据（二维数组）
        """
        self.table_controller = table_controller
        self.start_row = start_row
        self.start_col = start_col
        self.paste_data = paste_data
        self.old_data = []  # 保存被覆盖的数据
    
    def execute(self):
        """执行命令"""
        # 保存被覆盖的数据
        for r, row_data in enumerate(self.paste_data):
            row = self.start_row + r
            old_row_data = []
            for c, cell_value in enumerate(row_data):
                col = self.start_col + c
                old_row_data.append(self.table_controller.get_data()[row][col])
                self.table_controller.set_cell_data(row, col, cell_value)
            self.old_data.append(old_row_data)
    
    def undo(self):
        """撤回命令"""
        # 恢复被覆盖的数据
        for r, row_data in enumerate(self.old_data):
            row = self.start_row + r
            for c, cell_value in enumerate(row_data):
                col = self.start_col + c
                self.table_controller.set_cell_data(row, col, cell_value)
    
    def redo(self):
        """重做命令"""
        self.execute()