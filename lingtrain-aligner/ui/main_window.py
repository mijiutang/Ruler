#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
表格编辑器主窗口UI
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QTableWidget, QPushButton, QMenuBar, QMenu, 
                            QAction, QMessageBox, QToolBar, QStatusBar, 
                            QInputDialog, QTableWidgetItem, QFileDialog, 
                            QDialog, QListWidget, QDialogButtonBox, QLabel, QApplication, QTextEdit, QStyledItemDelegate, QDockWidget)
from PyQt5.QtCore import Qt, QEvent, QSize
from PyQt5.QtGui import QKeySequence, QClipboard
import csv
import os

# 导入表浏览器
from ui.table_browser import TableBrowser

class CustomTextEdit(QTextEdit):
    """自定义文本编辑器，用于表格单元格编辑"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWordWrapMode(True)  # 启用自动换行
        self.setLineWrapMode(QTextEdit.WidgetWidth)  # 按控件宽度换行
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)  # 需要时显示滚动条
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setMinimumSize(100, 50)  # 设置最小尺寸
    
    def sizeHint(self):
        """返回推荐的编辑器大小"""
        # 根据内容计算合适的大小
        text = self.toPlainText()
        lines = text.split('\n')
        max_line_length = max(len(line) for line in lines) if lines else 0
        
        # 计算合适的宽度和高度
        width = max(100, min(300, max_line_length * 8))
        height = max(50, min(200, len(lines) * 20 + 20))
        
        return QSize(width, height)
    
    def keyPressEvent(self, event):
        """处理按键事件"""
        # 当按下Return键且没有按Ctrl/Shift时，完成编辑
        if event.key() == Qt.Key_Return and not (event.modifiers() & (Qt.ControlModifier | Qt.ShiftModifier)):
            # 发送编辑完成信号
            self.clearFocus()
            return
        
        # Ctrl+Return 插入换行
        if event.key() == Qt.Key_Return and event.modifiers() & Qt.ControlModifier:
            self.insertPlainText('\n')
            return
        
        # 其他按键交给父类处理
        super().keyPressEvent(event)


class CustomTextEditDelegate(QStyledItemDelegate):
    """自定义委托类，用于在表格单元格中使用CustomTextEdit"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def createEditor(self, parent, option, index):
        """创建编辑器"""
        editor = CustomTextEdit(parent)
        editor.setFrameStyle(QTextEdit.NoFrame)  # 移除边框，使其看起来更自然
        return editor
    
    def setEditorData(self, editor, index):
        """设置编辑器数据"""
        text = index.model().data(index, Qt.EditRole)
        if not text:
            text = index.model().data(index, Qt.DisplayRole)
        
        if text:
            editor.setPlainText(text)
    
    def setModelData(self, editor, model, index):
        """设置模型数据"""
        text = editor.toPlainText()
        model.setData(index, text, Qt.EditRole)
    
    def updateEditorGeometry(self, editor, option, index):
        """更新编辑器几何形状"""
        # 使用单元格的矩形区域
        editor.setGeometry(option.rect)
        
        # 如果文本很长，可以适当调整编辑器大小
        text = index.model().data(index, Qt.DisplayRole)
        if text and len(text) > 50:
            lines = text.split('\n')
            # 计算合适的高度
            height = max(option.rect.height(), min(200, len(lines) * 20 + 20))
            width = max(option.rect.width(), min(300, len(text) * 8))
            
            # 确保编辑器不会超出表格边界
            table = editor.parent().parent()
            if hasattr(table, 'viewport'):
                viewport_rect = table.viewport().rect()
                x = option.rect.x()
                y = option.rect.y()
                
                # 调整宽度
                if x + width > viewport_rect.width():
                    width = viewport_rect.width() - x
                
                # 调整高度
                if y + height > viewport_rect.height():
                    height = viewport_rect.height() - y
                
                editor.setGeometry(x, y, width, height)

class TableListDialog(QDialog):
    """表格列表对话框"""
    
    def __init__(self, tables, parent=None):
        """
        初始化表格列表对话框
        
        Args:
            tables (list): 表格信息列表
            parent: 父窗口
        """
        super().__init__(parent)
        self.tables = tables
        self.selected_table_id = None
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("选择表格")
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)
        
        layout = QVBoxLayout(self)
        
        # 添加标签
        label = QLabel("请选择要加载的表格:")
        layout.addWidget(label)
        
        # 创建列表控件
        self.list_widget = QListWidget()
        for table in self.tables:
            # 支持两种格式:
            # 数据库模式: (id, name, rows, cols, updated_at)
            # CSV模式: (filename, file_path, rows, cols, mod_time)
            if len(table) >= 5:
                if isinstance(table[0], int):  # 数据库模式
                    table_id, name, rows, cols, updated_at = table
                    item_text = f"{name} ({rows}行 x {cols}列) - {updated_at}"
                    self.list_widget.addItem(item_text)
                    # 存储表格ID
                    self.list_widget.item(self.list_widget.count() - 1).setData(Qt.UserRole, table_id)
                else:  # CSV模式
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
                    
                    item_text = f"{table_name} ({rows}行 x {cols}列) - {mod_time}"
                    self.list_widget.addItem(item_text)
                    # 存储文件路径
                    self.list_widget.item(self.list_widget.count() - 1).setData(Qt.UserRole, file_path)
        
        layout.addWidget(self.list_widget)
        
        # 添加按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_selected_table_id(self):
        """获取选中的表格ID或文件路径"""
        current_item = self.list_widget.currentItem()
        if current_item:
            return current_item.data(Qt.UserRole)
        return None

class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self, controller):
        """
        初始化主窗口
        
        Args:
            controller: 表格控制器
        """
        super().__init__()
        self.controller = controller
        self.controller.set_main_window(self)
        self.save_action = None  # 保存动作引用
        self.init_ui()
        self.setup_connections()
        self.update_window_title()
        self.setup_table_properties()
        # 安装事件过滤器以处理表格的键盘事件
        self.table.installEventFilter(self)
        # 初始化时禁用保存按钮
        self.update_save_button_state()
    
    def eventFilter(self, obj, event):
        """事件过滤器，用于处理表格的键盘事件"""
        # 检查事件是否来自表格并且是按键事件
        if obj == self.table and event.type() == QEvent.KeyPress:
            # 检查是否按下了Delete键
            if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
                # 获取当前选中的单元格
                selected_ranges = self.table.selectedRanges()
                if selected_ranges:
                    # 处理每个选中的范围
                    for range_ in selected_ranges:
                        top_row = range_.topRow()
                        bottom_row = range_.bottomRow()
                        left_col = range_.leftColumn()
                        right_col = range_.rightColumn()
                        
                        # 清除选中范围内所有单元格的内容
                        for row in range(top_row, bottom_row + 1):
                            for col in range(left_col, right_col + 1):
                                item = self.table.item(row, col)
                                if item:
                                    item.setText("")
                                    # 通知控制器数据已更改
                                    self.controller.set_cell_data(row, col, "")
                                else:
                                    # 如果单元格不存在，创建一个新的空单元格
                                    item = QTableWidgetItem("")
                                    self.table.setItem(row, col, item)
                                    # 通知控制器数据已更改
                                    self.controller.set_cell_data(row, col, "")
                    
                    # 显示状态消息
                    self.statusBar().showMessage("已清除选中单元格的内容")
                    return True  # 事件已被处理
        
        # 对于其他事件，调用父类的事件过滤器
        return super().eventFilter(obj, event)
    
    def init_ui(self):
        """初始化用户界面"""
        # 设置窗口标题和大小
        self.setWindowTitle("表格编辑器")
        
        # 设置窗口位置和大小
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建工具栏
        self.create_toolbar()
        
        # 创建表格
        self.table = QTableWidget()
        # 获取控制器中的表格尺寸信息
        table_info = self.controller.get_current_table_info()
        rows = table_info.get('rows', 0)
        cols = table_info.get('cols', 0)
        # 只有当行列数都大于0时才设置表格行列数
        if rows > 0 and cols > 0:
            self.table.setRowCount(rows)
            self.table.setColumnCount(cols)
        main_layout.addWidget(self.table)
        
        # 创建表浏览器停靠窗口
        self.create_table_browser()
        
        # 设置停靠窗口默认状态
        self.addDockWidget(Qt.RightDockWidgetArea, self.table_browser_dock)
        self.table_browser_dock.show()
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建状态栏
        self.statusBar().showMessage("就绪")
        
    def setup_table_properties(self):
        """设置表格属性，包括文字换行、自适应行高和列宽"""
        # 设置文字自动换行
        self.table.setWordWrap(True)
        
        # 设置表格自适应列宽 - 使用Stretch模式确保列宽适应窗口
        header = self.table.horizontalHeader()
        for i in range(self.table.columnCount()):
            header.setSectionResizeMode(i, header.Stretch)
        
        # 设置表格自适应行高
        self.table.verticalHeader().setSectionResizeMode(0)  # 先设置为固定模式
        
        # 设置选择行为
        self.table.setSelectionBehavior(QTableWidget.SelectItems)
        
        # 设置网格线
        self.table.setShowGrid(True)
        
        # 设置行高和列宽调整策略
        self.table.horizontalHeader().setStretchLastSection(True)
        
        # 禁用拖放功能
        self.table.setDragEnabled(False)
        self.table.setAcceptDrops(False)
        self.table.setDropIndicatorShown(False)
        
        # 设置编辑触发器为单击、双击或按键
        self.table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed | QTableWidget.SelectedClicked | QTableWidget.AnyKeyPressed)
        
        # 设置自定义委托，使用CustomTextEdit进行单元格编辑
        self.table.setItemDelegate(CustomTextEditDelegate(self.table))
        
        # 设置默认字体
        from PyQt5.QtGui import QFont
        font = QFont("Arial", 12)
        self.table.setFont(font)
        
        # 设置粘贴快捷键
        self.paste_action = QAction("粘贴", self)
        self.paste_action.setShortcut(QKeySequence.Paste)
        self.paste_action.triggered.connect(self.on_paste)
        self.addAction(self.paste_action)
    
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # 添加工具栏按钮
        add_row_action = QAction("添加行", self)
        add_row_action.triggered.connect(self.on_add_row)
        toolbar.addAction(add_row_action)
        
        add_col_action = QAction("添加列", self)
        add_col_action.triggered.connect(self.on_add_column)
        toolbar.addAction(add_col_action)
        

        
        toolbar.addSeparator()
        
        # 保存功能已废弃，不再添加到工具栏
        pass
        
        load_action = QAction("加载", self)
        load_action.triggered.connect(self.on_load)
        toolbar.addAction(load_action)
    
    def create_table_browser(self):
        """创建表浏览器停靠窗口"""
        # 创建停靠窗口
        self.table_browser_dock = QDockWidget("表浏览器", self)
        self.table_browser_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        
        # 创建表浏览器实例
        self.table_browser = TableBrowser(self.controller)
        
        # 将表浏览器设置为停靠窗口的小部件
        self.table_browser_dock.setWidget(self.table_browser)
        
        # 连接信号和槽
        self.table_browser.table_selected.connect(self.load_selected_table)
        self.table_browser.refresh_requested.connect(self.refresh_table_list)
        
        # 连接停靠窗口的停靠区域变化信号
        self.table_browser_dock.dockLocationChanged.connect(self.on_dock_location_changed)
    
    def load_selected_table(self, table_id):
        """加载选中的表格"""
        # 检查table_id是整数（数据库模式）还是字符串（CSV文件路径）
        if isinstance(table_id, int):
            # 数据库模式
            success = self.controller.load_table(table_id)
        else:
            # CSV模式，table_id实际上是文件路径
            success = self.controller.load_table(table_id)
            
        if success:
            table_info = self.controller.get_current_table_info()
            self.update_window_title()
            self.update_table()
            self.statusBar().showMessage(f"已加载表格: {table_info['name']}")
            # 更新保存按钮状态
            self.update_save_button_state()
        else:
            QMessageBox.warning(self, "错误", "加载表格失败")
    
    def refresh_table_list(self):
        """刷新表格列表"""
        self.table_browser.load_tables()
        self.statusBar().showMessage("表格列表已刷新")
    
    def on_dock_location_changed(self, area):
        """停靠窗口位置变化事件处理"""
        # 不再保存停靠窗口的位置状态
        pass
    
    def create_menu_bar(self):
        """创建菜单栏"""
        from PyQt5.QtGui import QFont
        from PyQt5.QtWidgets import QFontDialog
        
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        new_action = QAction("新建", self)
        new_action.triggered.connect(self.on_new)
        file_menu.addAction(new_action)
        
        # 保存和另存为功能已废弃，不再添加到文件菜单
        pass
        
        load_action = QAction("加载", self)
        load_action.triggered.connect(self.on_load)
        file_menu.addAction(load_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu("编辑")
        
        add_row_action = QAction("添加行", self)
        add_row_action.triggered.connect(self.on_add_row)
        edit_menu.addAction(add_row_action)
        
        add_col_action = QAction("添加列", self)
        add_col_action.triggered.connect(self.on_add_column)
        edit_menu.addAction(add_col_action)
        
        edit_menu.addSeparator()
        
        # 字体菜单
        font_action = QAction("字体设置", self)
        font_action.triggered.connect(self.on_font_settings)
        edit_menu.addAction(font_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图")
        
        # 表浏览器显示/隐藏选项
        self.toggle_dock_action = QAction("表浏览器", self)
        self.toggle_dock_action.setCheckable(True)
        self.toggle_dock_action.setChecked(True)  # 默认显示
        self.toggle_dock_action.triggered.connect(self.toggle_table_browser)
        view_menu.addAction(self.toggle_dock_action)
    
    def setup_connections(self):
        """设置信号和槽连接"""
        # 表格内容变化事件
        self.table.cellChanged.connect(self.on_cell_changed)
    
    def update_save_button_state(self):
        """更新保存按钮状态（已废弃，保留空实现以避免程序崩溃）"""
        pass
    
    def on_add_row(self):
        """添加行事件处理"""
        self.controller.add_row()
        self.statusBar().showMessage("已添加新行")
    
    def on_add_column(self):
        """添加列事件处理"""
        self.controller.add_column()
        
        # 为新添加的列设置Stretch模式
        header = self.table.horizontalHeader()
        new_col_index = self.table.columnCount() - 1
        header.setSectionResizeMode(new_col_index, header.Stretch)
        
        self.statusBar().showMessage("已添加新列")
    

    
    def on_cell_changed(self, row, col):
        """单元格内容变化事件处理"""
        value = self.table.item(row, col).text() if self.table.item(row, col) else ""
        self.controller.set_cell_data(row, col, value)
        
        # 自动调整行高
        self.table.resizeRowToContents(row)
        
        # 更新保存按钮状态
        self.update_save_button_state()
    
    def on_new(self):
        """新建表格"""
        from PyQt5.QtWidgets import QInputDialog, QMessageBox
        
        # 弹出对话框让用户输入文件名
        table_name, ok = QInputDialog.getText(self, "新建表格", "请输入表格名称:")
        if ok and table_name:
            # 弹出对话框让用户输入行数
            rows, ok_rows = QInputDialog.getInt(self, "新建表格", "请输入行数:", 10, 1, 1000)
            if ok_rows:
                # 弹出对话框让用户输入列数
                cols, ok_cols = QInputDialog.getInt(self, "新建表格", "请输入列数:", 10, 1, 1000)
                if ok_cols:
                    # 创建指定尺寸的表格
                    self.controller.new_table(rows, cols)
                    # 不实际保存文件，只更新UI
                    self.controller.current_table_name = table_name
                    self.update_table()  # 更新表格显示
                    self.update_window_title()
                    self.statusBar().showMessage(f"已新建{rows}*{cols}表格: {table_name}")
                else:
                    # 用户取消了列数输入
                    self.statusBar().showMessage("已取消创建表格")
            else:
                # 用户取消了行数输入
                self.statusBar().showMessage("已取消创建表格")
        elif ok:
            # 用户输入了空名称
            self.statusBar().showMessage("表格名称不能为空")
    
    def on_save(self):
        """保存表格到已打开的CSV文件（已废弃，保留空实现以避免程序崩溃）"""
        self.statusBar().showMessage("已禁用保存功能，数据实时同步到CSV文件")
    
    def on_save_as(self):
        """另存为表格（已废弃，保留空实现以避免程序崩溃）"""
        self.statusBar().showMessage("已禁用另存为功能，数据实时同步到CSV文件")
    
    def on_load(self):
        """加载表格"""
        tables = self.controller.get_all_tables()
        if not tables:
            QMessageBox.information(self, "信息", "没有找到保存的表格")
            return
            
        dialog = TableListDialog(tables, self)
        if dialog.exec_() == QDialog.Accepted:
            table_id = dialog.get_selected_table_id()
            if table_id is not None:
                success = self.controller.load_table(table_id)
                if success:
                    table_info = self.controller.get_current_table_info()
                    self.update_window_title()
                    self.statusBar().showMessage(f"已加载表格: {table_info['name']}")
                else:
                    QMessageBox.warning(self, "错误", "加载表格失败")
    
    def on_resize_table(self):
        """自适应表格大小"""
        # 自适应所有行高
        for row in range(self.table.rowCount()):
            self.table.resizeRowToContents(row)
        
        # 设置所有列为Stretch模式，确保列宽适应窗口
        header = self.table.horizontalHeader()
        for col in range(self.table.columnCount()):
            header.setSectionResizeMode(col, header.Stretch)
        
        self.statusBar().showMessage("已调整表格大小")
    
    def update_window_title(self):
        """更新窗口标题"""
        table_info = self.controller.get_current_table_info()
        if 'name' in table_info and table_info['name']:
            title = f"表格编辑器 - {table_info['name']}"
        else:
            title = "表格编辑器"
        if 'is_modified' in table_info and table_info['is_modified']:
            title += " *"
        self.setWindowTitle(title)
    
    def update_table(self):
        """更新表格显示"""
        data = self.controller.get_table_data()
        if data is not None:
            rows = len(data)
            cols = len(data[0]) if rows > 0 else 0
            
            # 先清空表格
            self.table.clear()
            
            # 重新设置行列数
            self.table.setRowCount(rows)
            self.table.setColumnCount(cols)
            
            # 填充数据
            for i in range(rows):
                for j in range(cols):
                    item = QTableWidgetItem(str(data[i][j]))
                    self.table.setItem(i, j, item)
            
            # 自动调整行高
            for row in range(rows):
                self.table.resizeRowToContents(row)
            
            # 设置列宽为Stretch模式，确保列宽适应窗口
            header = self.table.horizontalHeader()
            for col in range(cols):
                header.setSectionResizeMode(col, header.Stretch)
        else:
            # 如果没有数据，清空表格
            self.table.clear()
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
    
    def get_table(self):
        """获取表格控件"""
        return self.table
    
    def on_paste(self):
        """粘贴事件处理"""
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        
        if not text:
            return
        
        # 获取当前选中的单元格
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            # 如果没有选中单元格，从当前光标位置开始粘贴
            current_row = self.table.currentRow()
            current_col = self.table.currentColumn()
            if current_row < 0 or current_col < 0:
                # 如果没有当前单元格，从(0,0)开始
                current_row = 0
                current_col = 0
        else:
            # 如果有选中的单元格，从选中区域的左上角开始粘贴
            range_ = selected_ranges[0]
            current_row = range_.topRow()
            current_col = range_.leftColumn()
        
        # 分割剪贴板文本为行和列
        rows = text.split('\n')
        if not rows or not rows[0]:
            return
        
        # 移除空行
        rows = [row for row in rows if row.strip()]
        
        # 解析每行的列数据
        paste_data = []
        for row in rows:
            # 使用制表符分割列
            cols = row.split('\t')
            paste_data.append(cols)
        
        # 确保表格有足够的行和列
        max_rows = current_row + len(paste_data)
        max_cols = current_col + max(len(row) for row in paste_data) if paste_data else 0
        
        if max_rows > self.table.rowCount():
            self.table.setRowCount(max_rows)
        
        if max_cols > self.table.columnCount():
            self.table.setColumnCount(max_cols)
        
        # 将数据粘贴到表格中
        for i, row_data in enumerate(paste_data):
            for j, cell_data in enumerate(row_data):
                row = current_row + i
                col = current_col + j
                
                # 获取或创建单元格项
                item = self.table.item(row, col)
                if not item:
                    item = QTableWidgetItem()
                    self.table.setItem(row, col, item)
                
                # 设置单元格文本
                item.setText(cell_data)
                # 通知控制器数据已更改
                self.controller.set_cell_data(row, col, cell_data)
        
        # 自动调整行高
        for row in range(current_row, current_row + len(paste_data)):
            self.table.resizeRowToContents(row)
        
        # 设置所有列为Stretch模式，确保列宽适应窗口
        header = self.table.horizontalHeader()
        for col in range(self.table.columnCount()):
            header.setSectionResizeMode(col, header.Stretch)
        
        self.statusBar().showMessage(f"已粘贴 {len(paste_data)} 行数据")
    
    def on_font_settings(self):
        """字体设置事件处理"""
        from PyQt5.QtGui import QFont
        from PyQt5.QtWidgets import QFontDialog
        
        # 获取当前字体
        current_font = self.table.font()
        
        # 显示字体选择对话框
        font, ok = QFontDialog.getFont(current_font, self)
        if ok:
            # 设置表格字体
            self.table.setFont(font)
            
            # 更新所有单元格的字体
            for row in range(self.table.rowCount()):
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item:
                        item.setFont(font)
            
            # 显示状态消息
            self.statusBar().showMessage(f"已设置字体: {font.family()}, 大小: {font.pointSize()}")
    
    def toggle_table_browser(self):
        """切换表浏览器显示/隐藏"""
        if self.table_browser_dock.isVisible():
            self.table_browser_dock.hide()
            self.toggle_dock_action.setChecked(False)
        else:
            self.table_browser_dock.show()
            self.toggle_dock_action.setChecked(True)
    
    def closeEvent(self, event):
        """窗口关闭事件处理"""
        # 调用父类的关闭事件处理方法
        super().closeEvent(event)