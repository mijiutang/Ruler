#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
表浏览器Docker窗口
用于显示CSV文件中的所有表格，并支持切换表格
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QListWidget, QLabel, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal


class TableBrowser(QWidget):
    """表浏览器Docker窗口类"""
    
    # 定义信号，当用户选择切换表格时发出
    table_selected = pyqtSignal(str)  # 参数为文件路径
    refresh_requested = pyqtSignal()  # 请求刷新表格列表
    
    def __init__(self, controller, parent=None):
        """
        初始化表浏览器
        
        Args:
            controller: 表格控制器
            parent: 父窗口
        """
        super().__init__(parent)
        self.controller = controller
        self.parent_window = parent
        self.init_ui()
        self.load_tables()
        
    def init_ui(self):
        """初始化用户界面"""
        # 设置窗口标题
        self.setWindowTitle("表浏览器")
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # 创建表格列表
        self.table_list = QListWidget()
        self.table_list.itemClicked.connect(self.on_table_selected)
        main_layout.addWidget(self.table_list)
        
        # 创建按钮布局
        button_layout = QHBoxLayout()
        
        # 刷新按钮
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.clicked.connect(self.load_tables)
        button_layout.addWidget(self.refresh_button)
        
        main_layout.addLayout(button_layout)
        
        # 设置尺寸
        self.setMinimumWidth(150)  # 缩小最小宽度让窗口更窄
        self.setMaximumWidth(200)  # 设置最大宽度防止过宽
        self.setMinimumHeight(200)
        self.resize(150, 300)  # 设置默认尺寸
        
    def load_tables(self):
        """加载所有表格"""
        # 清空列表
        self.table_list.clear()
        
        # 获取所有表格
        tables = self.controller.get_all_tables()
        
        # 添加到列表中
        for table in tables:
            # CSV模式: (filename, file_path, rows, cols, mod_time)
            if len(table) == 5:
                filename, file_path, rows, cols, mod_time = table
                # 从文件名中提取表格名称（去掉时间戳和扩展名）
                table_name = filename.replace(".csv", "")
                if "_" in table_name:
                    # 尝试去除时间戳部分
                    parts = table_name.split("_")
                    if len(parts) > 2 and parts[-2].isdigit() and parts[-1].isdigit():
                        table_name = "_".join(parts[:-2])
                    elif len(parts) > 1 and parts[-1].replace("_", "").isdigit():
                        table_name = "_".join(parts[:-1])
                
                item_text = f"{table_name} ({rows}行 x {cols}列)"
                self.table_list.addItem(item_text)
                # 存储文件路径作为用户数据
                self.table_list.item(self.table_list.count() - 1).setData(Qt.UserRole, file_path)
            
        # 注意：当没有表格时，不清除当前显示的表格内容
        # 这样可以保持新建的空白表格在界面上显示
            
    def on_table_selected(self, item):
        """当用户选择表格时触发"""
        file_path = item.data(Qt.UserRole)
        if file_path:
            # 发出信号通知主窗口切换表格
            self.table_selected.emit(file_path)
        
    def refresh_tables(self):
        """刷新表格列表"""
        self.load_tables()