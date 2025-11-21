#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
命令历史管理器
实现撤回/重做功能
"""

from abc import ABC, abstractmethod
from typing import List

class Command(ABC):
    """抽象命令基类"""
    
    @abstractmethod
    def execute(self):
        """执行命令"""
        pass
    
    @abstractmethod
    def undo(self):
        """撤回命令"""
        pass
    
    @abstractmethod
    def redo(self):
        """重做命令"""
        pass

class CommandHistory:
    """命令历史管理器"""
    
    def __init__(self):
        """初始化命令历史管理器"""
        self.undo_stack: List[Command] = []  # 撤回栈
        self.redo_stack: List[Command] = []  # 重做栈
        self.max_history = 100  # 最大历史记录数
    
    def execute_command(self, command: Command):
        """
        执行命令并添加到历史记录
        
        Args:
            command: 要执行的命令
            
        Returns:
            list: 变化的单元格列表，用于增量更新
        """
        changed_cells = command.execute()
        self.undo_stack.append(command)
        self.redo_stack.clear()  # 执行新命令后清空重做栈
        
        # 限制历史记录数量
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)
        # 返回变化的单元格，用于增量更新
        return changed_cells if hasattr(command, 'changed_cells') else None
    
    def undo(self):
        """
        撤回上一个命令
        
        Returns:
            list: 变化的单元格列表，用于增量更新
        """
        if not self.undo_stack:
            return None
        
        command = self.undo_stack.pop()
        changed_cells = command.undo()
        self.redo_stack.append(command)
        # 返回变化的单元格，用于增量更新
        return changed_cells if hasattr(command, 'changed_cells') else None
    
    def redo(self):
        """
        重做上一个撤回的命令
        
        Returns:
            list: 变化的单元格列表，用于增量更新
        """
        if not self.redo_stack:
            return None
        
        command = self.redo_stack.pop()
        changed_cells = command.redo()
        self.undo_stack.append(command)
        # 返回变化的单元格，用于增量更新
        return changed_cells if hasattr(command, 'changed_cells') else None
    
    def can_undo(self):
        """
        检查是否可以撤回
        
        Returns:
            bool: 是否可以撤回
        """
        return len(self.undo_stack) > 0
    
    def can_redo(self):
        """
        检查是否可以重做
        
        Returns:
            bool: 是否可以重做
        """
        return len(self.redo_stack) > 0
    
    def clear(self):
        """清空历史记录"""
        self.undo_stack.clear()
        self.redo_stack.clear()