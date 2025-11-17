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
from PyQt5.QtCore import Qt, QEvent, QSize, pyqtSignal
from PyQt5.QtGui import QKeySequence, QClipboard, QColor, QTextCursor
import csv
import os
import json

# 导入表浏览器
from ui.table_browser import TableBrowser

# 导入配置管理器
from utils.config_manager import ConfigManager

class CommentManager:
    """单元格批注管理类"""
    
    def __init__(self, file_path=None):
        """
        初始化批注管理器
        
        Args:
            file_path (str): 表格文件路径，用于生成批注文件路径，可以为None
        """
        self.base_file_path = file_path
        self.comments_file = self._get_comments_file_path()
        self.comments = {}
        if file_path:
            self.load_comments()
    
    def _get_comments_file_path(self):
        """获取批注文件路径"""
        # 如果有表格文件路径，则在其同目录下创建同名.json文件
        if self.base_file_path:
            base_dir = os.path.dirname(self.base_file_path)
            base_name = os.path.splitext(os.path.basename(self.base_file_path))[0]
            return os.path.join(base_dir, f"{base_name}_comments.json")
        # 否则使用默认路径
        return os.path.join(os.getcwd(), "default_comments.json")
    
    def _get_cell_key(self, row, col):
        """获取单元格键名"""
        return f"({row+1}:{col+1})"
    
    def load_comments(self, file_path=None):
        """从文件加载批注
        
        Args:
            file_path (str): 表格文件路径，如果提供则更新当前文件路径
        """
        if file_path:
            self.base_file_path = file_path
            self.comments_file = self._get_comments_file_path()
            
        try:
            if os.path.exists(self.comments_file):
                with open(self.comments_file, 'r', encoding='utf-8') as f:
                    loaded_comments = json.load(f)
                    
                # 兼容旧格式："单元格(行:列)" -> "(行:列)"
                self.comments = {}
                for key, value in loaded_comments.items():
                    if key.startswith("单元格("):
                        # 旧格式，转换为新格式
                        new_key = key.replace("单元格", "")
                        self.comments[new_key] = value
                    else:
                        # 新格式，直接使用
                        self.comments[key] = value
            else:
                self.comments = {}
        except Exception as e:
            print(f"加载批注文件失败: {e}")
            self.comments = {}
    
    def save_comments(self):
        """保存批注到文件"""
        try:
            if not self.comments_file:
                return False
                
            os.makedirs(os.path.dirname(self.comments_file), exist_ok=True)
            with open(self.comments_file, 'w', encoding='utf-8') as f:
                json.dump(self.comments, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存批注文件失败: {e}")
            return False
    
    def get_comment(self, row, col):
        """
        获取单元格批注
        
        Args:
            row (int): 行索引
            col (int): 列索引
            
        Returns:
            str: 批注内容，如果没有批注则返回空字符串
        """
        cell_key = self._get_cell_key(row, col)
        return self.comments.get(cell_key, "")
    
    def set_comment(self, row, col, comment):
        """
        设置单元格批注
        
        Args:
            row (int): 行索引
            col (int): 列索引
            comment (str): 批注内容，如果为空字符串则删除批注
        """
        cell_key = self._get_cell_key(row, col)
        
        if comment and comment.strip():
            self.comments[cell_key] = comment.strip()
        else:
            # 如果批注为空，则删除该批注
            self.comments.pop(cell_key, None)
        
        return self.save_comments()
    
    def has_comment(self, row, col):
        """
        检查单元格是否有批注
        
        Args:
            row (int): 行索引
            col (int): 列索引
            
        Returns:
            bool: 是否有批注
        """
        cell_key = self._get_cell_key(row, col)
        return cell_key in self.comments and bool(self.comments[cell_key].strip())
    
    def get_all_comments(self):
        """获取所有批注"""
        return self.comments.copy()

class CommentDockWidget(QDockWidget):
    """批注停靠窗口类"""
    
    # 定义信号
    comment_updated = pyqtSignal(int, int, str)  # 行, 列, 批注内容
    
    def __init__(self, parent=None):
        """
        初始化批注停靠窗口
        
        Args:
            parent: 父窗口
        """
        super().__init__("单元格批注", parent)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.current_cell = None  # 当前选中的单元格 (row, col)
        self.comment_manager = None  # 批注管理器
        
        # 创建界面
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面"""
        # 创建主部件
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        
        # 批注编辑器
        self.comment_edit = QTextEdit()
        self.comment_edit.setPlaceholderText("在此输入批注内容...")
        layout.addWidget(self.comment_edit)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 保存按钮
        self.save_button = QPushButton("保存批注")
        self.save_button.clicked.connect(self.save_comment)
        button_layout.addWidget(self.save_button)
        
        # 删除按钮
        self.delete_button = QPushButton("删除批注")
        self.delete_button.clicked.connect(self.delete_comment)
        button_layout.addWidget(self.delete_button)
        
        layout.addLayout(button_layout)
        
        # 设置主部件
        self.setWidget(main_widget)
        
        # 初始状态下禁用编辑器
        self.comment_edit.setEnabled(False)
        self.save_button.setEnabled(False)
        self.delete_button.setEnabled(False)
    
    def set_comment_manager(self, comment_manager):
        """
        设置批注管理器
        
        Args:
            comment_manager (CommentManager): 批注管理器实例
        """
        self.comment_manager = comment_manager
    
    def set_current_cell(self, row, col):
        """
        设置当前选中的单元格
        
        Args:
            row (int): 行索引
            col (int): 列索引
        """
        self.current_cell = (row, col)
        
        # 启用编辑器
        self.comment_edit.setEnabled(True)
        self.save_button.setEnabled(True)
        self.delete_button.setEnabled(True)
        
        # 加载当前单元格的批注
        if self.comment_manager:
            comment = self.comment_manager.get_comment(row, col)
            self.comment_edit.setPlainText(comment)
        else:
            self.comment_edit.clear()
    
    def clear_current_cell(self):
        """清除当前单元格"""
        self.current_cell = None
        self.comment_edit.clear()
        
        # 禁用编辑器
        self.comment_edit.setEnabled(False)
        self.save_button.setEnabled(False)
        self.delete_button.setEnabled(False)
    
    def load_comment(self, row, col):
        """
        加载指定单元格的批注
        
        Args:
            row (int): 行索引
            col (int): 列索引
        """
        self.set_current_cell(row, col)
    
    def clear_display(self):
        """清空显示"""
        self.clear_current_cell()
    
    def save_comment(self):
        """保存批注"""
        if self.current_cell and self.comment_manager:
            row, col = self.current_cell
            comment = self.comment_edit.toPlainText()
            
            if self.comment_manager.set_comment(row, col, comment):
                # 保存成功
                # 获取主窗口并显示状态消息
                main_window = self.parent()
                while main_window and not isinstance(main_window, QMainWindow):
                    main_window = main_window.parent()
                
                if main_window:
                    main_window.statusBar().showMessage(f"已保存单元格({row+1}:{col+1})的批注", 3000)
                
                # 发出信号
                self.comment_updated.emit(row, col, comment)
            else:
                # 保存失败
                QMessageBox.warning(self, "保存失败", "无法保存批注，请检查文件权限。")
    
    def delete_comment(self):
        """删除批注"""
        if self.current_cell and self.comment_manager:
            row, col = self.current_cell
            
            reply = QMessageBox.question(
                self, "确认删除", 
                f"确定要删除单元格({row+1}:{col+1})的批注吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                if self.comment_manager.set_comment(row, col, ""):
                    # 删除成功
                    self.comment_edit.clear()
                    
                    # 获取主窗口并显示状态消息
                    main_window = self.parent()
                    while main_window and not isinstance(main_window, QMainWindow):
                        main_window = main_window.parent()
                    
                    if main_window:
                        main_window.statusBar().showMessage(f"已删除单元格({row+1}:{col+1})的批注", 3000)
                    
                    # 发出信号
                    self.comment_updated.emit(row, col, "")
                else:
                    # 删除失败
                    QMessageBox.warning(self, "删除失败", "无法删除批注，请检查文件权限。")

class CustomTextEdit(QTextEdit):
    """自定义文本编辑器，用于表格单元格编辑"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWordWrapMode(True)  # 启用自动换行
        self.setLineWrapMode(QTextEdit.WidgetWidth)  # 按控件宽度换行
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)  # 需要时显示滚动条
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setMinimumSize(100, 50)  # 设置最小尺寸
        self.row_index = None  # 存储当前编辑的行索引
        self.col_index = None  # 存储当前编辑的列索引
    
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
        
        # 如果按下Ctrl+Shift+C，执行复制到首列功能
        if event.key() == Qt.Key_C and event.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier):
            self.copy_to_first_column()
            return
        
        # 其他按键交给父类处理
        super().keyPressEvent(event)
    
    def mousePressEvent(self, event):
        """处理鼠标按键事件"""
        # 检查是否是鼠标侧键（XButton1或XButton2）
        if event.button() == Qt.XButton1 or event.button() == Qt.XButton2:
            # 执行复制到首列功能
            self.copy_to_first_column()
            return
        
        super().mousePressEvent(event)
    
    def contextMenuEvent(self, event):
        """处理右键菜单事件"""
        # 获取默认的右键菜单
        menu = self.createStandardContextMenu()
        
        # 添加分隔线
        menu.addSeparator()
        
        # 添加"复制到首列"动作
        copy_to_first_col_action = menu.addAction("复制到首列")
        copy_to_first_col_action.triggered.connect(self.copy_to_first_column)
        
        # 添加"剪切到下一行"动作
        cut_to_next_row_action = menu.addAction("剪切到下一行")
        cut_to_next_row_action.triggered.connect(self.cut_to_next_row)
        
        # 显示菜单
        menu.exec_(event.globalPos())
    
    def copy_to_first_column(self):
        """复制选中文本到同行的第一列，如果该列已有内容则添加到下一行（换行）"""
        # 获取选中的文本
        selected_text = self.textCursor().selectedText()
        
        if not selected_text:
            # 如果没有选中文本，获取全部文本
            selected_text = self.toPlainText()
        
        if selected_text and self.row_index is not None:
            # 获取父表格
            table = self.parent().parent()
            
            # 确保第一列存在
            if table.columnCount() < 1:
                table.setColumnCount(1)
            
            # 获取或创建第一列的单元格项
            first_col_item = table.item(self.row_index, 0)
            if not first_col_item:
                first_col_item = QTableWidgetItem()
                table.setItem(self.row_index, 0, first_col_item)
                # 设置为空，这样后续代码会直接添加文本
                first_col_item.setText("")
            
            # 获取当前首列的内容
            current_text = first_col_item.text()
            
            # 如果首列已有内容，添加换行符后再添加新文本
            if current_text.strip():
                new_text = current_text + "\n" + selected_text
            else:
                # 如果首列为空，直接添加文本
                new_text = selected_text
            
            # 设置文本到第一列
            first_col_item.setText(new_text)
            
            # 如果有控制器，也更新控制器中的数据
            main_window = table.parent().parent()
            if hasattr(main_window, 'controller'):
                main_window.controller.set_cell_data(self.row_index, 0, new_text)
            
            # 调整行高以适应多行文本
            table.resizeRowToContents(self.row_index)
            
            # 显示状态消息
            if hasattr(main_window, 'statusBar'):
                if current_text.strip():
                    main_window.statusBar().showMessage(f"已复制文本到第{self.row_index + 1}行首列的下一行", 3000)
                else:
                    main_window.statusBar().showMessage(f"已复制文本到第{self.row_index + 1}行的首列", 3000)
    
    def cut_to_next_row(self):
        """将光标后的文本剪切到下一行的单元格中，并创建新行"""
        # 获取当前文本光标
        cursor = self.textCursor()
        
        # 获取光标位置到文本末尾的内容
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        text_after_cursor = cursor.selectedText()
        
        if text_after_cursor and self.row_index is not None and self.col_index is not None:
            # 获取父表格
            table = self.parent().parent()
            
            # 获取当前单元格的全部文本
            full_text = self.toPlainText()
            
            # 获取光标位置之前的内容（保留在原单元格）
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
            cursor.setPosition(self.textCursor().position(), QTextCursor.KeepAnchor)
            text_before_cursor = cursor.selectedText()
            
            # 更新当前单元格为光标前的内容
            self.setPlainText(text_before_cursor)
            
            # 获取当前行和列
            current_row = self.row_index
            current_col = self.col_index
            
            # 在当前行之后插入新行
            new_row_index = current_row + 1
            table.insertRow(new_row_index)
            
            # 确保新行有足够的列
            if table.columnCount() <= current_col:
                table.setColumnCount(current_col + 1)
            
            # 创建新单元格项并设置文本
            new_item = QTableWidgetItem(text_after_cursor)
            table.setItem(new_row_index, current_col, new_item)
            
            # 获取主窗口
            main_window = table.parent().parent()
            
            # 更新控制器中的数据
            if hasattr(main_window, 'controller'):
                # 更新当前单元格
                main_window.controller.set_cell_data(current_row, current_col, text_before_cursor)
                # 更新新单元格
                main_window.controller.set_cell_data(new_row_index, current_col, text_after_cursor)
            
            # 调整行高以适应内容
            table.resizeRowToContents(current_row)
            table.resizeRowToContents(new_row_index)
            
            # 显示状态消息
            if hasattr(main_window, 'statusBar'):
                main_window.statusBar().showMessage(f"已将文本剪切到第{new_row_index + 1}行第{current_col + 1}列", 3000)


class CustomTextEditDelegate(QStyledItemDelegate):
    """自定义委托类，用于在表格单元格中使用CustomTextEdit"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def createEditor(self, parent, option, index):
        """创建编辑器"""
        editor = CustomTextEdit(parent)
        editor.setFrameStyle(QTextEdit.NoFrame)  # 移除边框，使其看起来更自然
        
        # 设置行和列索引
        editor.row_index = index.row()
        editor.col_index = index.column()
        
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
        
        # 初始化配置管理器
        self.config_manager = ConfigManager()
        
        self.init_ui()
        self.setup_connections()
        self.update_window_title()
        self.setup_table_properties()
        
        # 加载保存的主题
        saved_theme = self.config_manager.load_theme()
        self.change_theme(saved_theme)
        
        # 加载保存的窗口大小和位置
        window_geometry = self.config_manager.load_window_geometry()
        self.resize(window_geometry["width"], window_geometry["height"])
        
        # 如果有保存的位置，设置窗口位置
        if window_geometry["x"] is not None and window_geometry["y"] is not None:
            self.move(window_geometry["x"], window_geometry["y"])
        
        # 安装事件过滤器以处理表格的键盘事件
        self.table.installEventFilter(self)
        # 初始化时禁用保存按钮
        self.update_save_button_state()
        
        # 延迟加载停靠窗口状态，确保所有停靠窗口都已创建
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(100, self.restore_dock_state)
    
    def restore_dock_state(self):
        """恢复停靠窗口状态"""
        dock_state = self.config_manager.load_dock_state()
        if dock_state:
            self.restoreState(dock_state)
    
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
        
        # 创建批注管理器
        self.comment_manager = CommentManager()
        
        # 创建批注停靠窗口
        self.create_comment_dock()
        
        # 设置停靠窗口默认状态
        self.addDockWidget(Qt.RightDockWidgetArea, self.table_browser_dock)
        self.table_browser_dock.show()
        
        self.addDockWidget(Qt.RightDockWidgetArea, self.comment_widget)
        self.comment_widget.show()
        
        # 设置停靠窗口选项卡式排列
        self.tabifyDockWidget(self.table_browser_dock, self.comment_widget)
        self.table_browser_dock.raise_()
        
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
        toolbar.setObjectName("main_toolbar")
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
        
        # 刷新表格按钮
        refresh_action = QAction("刷新", self)
        refresh_action.triggered.connect(self.refresh_table)
        toolbar.addAction(refresh_action)
    
    def create_comment_dock(self):
        """创建批注停靠窗口"""
        # 直接创建批注停靠窗口实例（它本身就是QDockWidget）
        self.comment_widget = CommentDockWidget(self)
        self.comment_widget.setObjectName("comment_widget_dock")
        
        # 设置批注管理器
        self.comment_widget.set_comment_manager(self.comment_manager)
        
        # 连接信号和槽
        self.comment_widget.comment_updated.connect(self.on_comment_updated)
        
        # 连接表格选择变化信号
        self.table.itemSelectionChanged.connect(self.on_table_selection_changed)
    
    def on_table_selection_changed(self):
        """表格选择变化事件处理"""
        # 获取当前选中的单元格
        selected_items = self.table.selectedItems()
        if selected_items:
            item = selected_items[0]
            row = item.row()
            col = item.column()
            
            # 更新批注窗口显示当前单元格的批注
            self.comment_widget.load_comment(row, col)
            
            # 加载当前表格的批注文件
            if hasattr(self.controller, 'current_table_path') and self.controller.current_table_path:
                self.comment_manager.load_comments(self.controller.current_table_path)
        else:
            # 没有选中单元格时，清空批注窗口
            self.comment_widget.clear_display()
    
    def on_comment_updated(self, row, col, comment):
        """批注更新事件处理"""
        # 保存当前表格的批注文件
        if hasattr(self.controller, 'current_table_path') and self.controller.current_table_path:
            self.comment_manager.save_comments()
        
        # 更新状态栏
        if comment:
            self.statusBar().showMessage(f"已更新单元格({row+1}:{col+1})的批注")
        else:
            self.statusBar().showMessage(f"已删除单元格({row+1}:{col+1})的批注")
        
        # 标记有批注的单元格
        self.update_comment_indicators()
    
    def update_comment_indicators(self):
        """更新批注指示器"""
        # 遍历所有单元格，为有批注的单元格添加背景色
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                comment = self.comment_manager.get_comment(row, col)
                
                # 获取单元格项
                item = self.table.item(row, col)
                if not item:
                    item = QTableWidgetItem()
                    self.table.setItem(row, col, item)
                
                # 如果有批注，设置浅黄色背景
                if comment:
                    item.setBackground(QColor(255, 255, 200))  # 浅黄色
                else:
                    # 恢复默认背景色
                    item.setBackground(QColor(255, 255, 255))  # 白色
    
    def create_table_browser(self):
        self.table_browser_dock = QDockWidget("表浏览器", self)
        self.table_browser_dock.setObjectName("table_browser_dock")
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
        """加载选中的表格 - 内存优化版本，减少不必要的数据同步"""
        # 只在数据确实被修改时才同步到磁盘
        if self.controller.is_modified:
            self.controller.save_table()
        
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
            
            # 加载对应的批注文件
            if hasattr(self.controller, 'current_table_path') and self.controller.current_table_path:
                self.comment_manager.load_comments(self.controller.current_table_path)
                self.update_comment_indicators()
            
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
        
        # 批注窗口显示/隐藏选项
        self.toggle_comment_dock_action = QAction("单元格批注", self)
        self.toggle_comment_dock_action.setCheckable(True)
        self.toggle_comment_dock_action.setChecked(True)  # 默认显示
        self.toggle_comment_dock_action.triggered.connect(self.toggle_comment_dock)
        view_menu.addAction(self.toggle_comment_dock_action)
        
        # 主题菜单
        theme_menu = menubar.addMenu("主题")
        
        # 默认白色主题
        default_theme_action = QAction("默认白色", self)
        default_theme_action.triggered.connect(lambda: self.change_theme("default"))
        theme_menu.addAction(default_theme_action)
        
        # 桃粉主题
        pink_theme_action = QAction("桃粉", self)
        pink_theme_action.triggered.connect(lambda: self.change_theme("pink"))
        theme_menu.addAction(pink_theme_action)
        
        # 淡紫主题
        purple_theme_action = QAction("淡紫", self)
        purple_theme_action.triggered.connect(lambda: self.change_theme("purple"))
        theme_menu.addAction(purple_theme_action)
        
        # 草绿主题
        green_theme_action = QAction("草绿", self)
        green_theme_action.triggered.connect(lambda: self.change_theme("green"))
        theme_menu.addAction(green_theme_action)
        
        # 天蓝主题
        blue_theme_action = QAction("天蓝", self)
        blue_theme_action.triggered.connect(lambda: self.change_theme("blue"))
        theme_menu.addAction(blue_theme_action)
    
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
        """单元格内容变化事件处理 - 优化版本，减少磁盘同步频率"""
        value = self.table.item(row, col).text() if self.table.item(row, col) else ""
        self.controller.set_cell_data(row, col, value)
        
        # 只对当前修改的行进行行高调整，而不是所有行
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
                cols, ok_cols = QInputDialog.getInt(self, "新建表格", "请输入列数:", 4, 1, 1000)
                if ok_cols:
                    # 创建指定尺寸的表格并保存到CSV文件
                    self.controller.new_table(rows, cols, table_name)
                    # 更新UI
                    self.update_table()  # 更新表格显示
                    self.update_window_title()
                    self.statusBar().showMessage(f"已新建并保存{rows}×{cols}表格: {table_name}")
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
        """更新表格显示 - 内存优化版本，支持大型表格"""
        data = self.controller.get_table_data()
        if data is not None:
            rows = len(data)
            cols = len(data[0]) if rows > 0 else 0
            
            # 先清空表格
            self.table.clear()
            
            # 重新设置行列数
            self.table.setRowCount(rows)
            self.table.setColumnCount(cols)
            
            # 暂时禁用表格更新以提高性能
            self.table.setUpdatesEnabled(False)
            
            # 批量创建和设置单元格项
            items = []
            for i in range(rows):
                for j in range(cols):
                    item = QTableWidgetItem(str(data[i][j]))
                    items.append((i, j, item))
            
            # 批量设置单元格项
            for i, j, item in items:
                self.table.setItem(i, j, item)
            
            # 重新启用表格更新
            self.table.setUpdatesEnabled(True)
            
            # 对于大型表格，延迟调整行高以提高性能
            if rows > 1000:
                # 对于大型表格，只调整当前可见区域的行高
                visible_row_start = self.table.rowAt(self.table.viewport().y())
                visible_row_end = self.table.rowAt(self.table.viewport().y() + self.table.viewport().height())
                if visible_row_end == -1:  # 如果没有行在底部，设置为最后一行
                    visible_row_end = self.table.rowCount() - 1
                
                # 只调整可见区域的行高
                for row in range(visible_row_start, visible_row_end + 1):
                    self.table.resizeRowToContents(row)
                
                # 设置滚动事件处理，在用户滚动时动态调整行高
                if not hasattr(self, '_scroll_connection'):
                    self._scroll_connection = self.table.verticalScrollBar().valueChanged.connect(
                        self._adjust_visible_rows_height
                    )
            else:
                # 对于小型表格，调整所有行高
                for row in range(rows):
                    self.table.resizeRowToContents(row)
            
            # 设置列宽为Stretch模式，确保列宽适应窗口
            header = self.table.horizontalHeader()
            for col in range(cols):
                header.setSectionResizeMode(col, header.Stretch)
                
            # 更新批注指示器
            if hasattr(self, 'comment_manager'):
                self.update_comment_indicators()
        else:
            # 如果没有数据，清空表格
            self.table.clear()
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
    
    def _adjust_visible_rows_height(self):
        """调整当前可见区域的行高 - 优化版本"""
        # 检查表格是否已初始化
        if not hasattr(self, 'table') or self.table.rowCount() == 0:
            return
            
        visible_row_start = self.table.rowAt(self.table.viewport().y())
        visible_row_end = self.table.rowAt(self.table.viewport().y() + self.table.viewport().height())
        if visible_row_end == -1:  # 如果没有行在底部，设置为最后一行
            visible_row_end = self.table.rowCount() - 1
        
        # 只调整可见区域的行高
        for row in range(visible_row_start, visible_row_end + 1):
            self.table.resizeRowToContents(row)
    
    def get_table(self):
        """获取表格控件"""
        return self.table
    
    def refresh_table(self):
        """刷新当前表格数据"""
        if self.controller.current_table_id is not None:
            # 强制从磁盘刷新数据
            if self.controller.refresh_from_disk():
                self.update_table()
                self.statusBar().showMessage(f"已刷新表格: {self.controller.current_table_name}", 3000)
            else:
                QMessageBox.warning(self, "错误", f"无法刷新表格: {self.controller.current_table_name}")
        else:
            QMessageBox.information(self, "提示", "没有打开的表格可刷新")
    
    def on_paste(self):
        """粘贴事件处理 - 优化版本，支持大量数据粘贴"""
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
        
        # 开始批量更新模式，暂停磁盘同步
        self.controller.start_batch_update()
        
        try:
            # 确保表格有足够的行和列
            max_rows = current_row + len(paste_data)
            max_cols = current_col + max(len(row) for row in paste_data) if paste_data else 0
            
            # 检查并扩展数据管理器的行数和列数
            current_data_rows = self.controller.get_row_count()
            current_data_cols = self.controller.get_column_count()
            
            # 如果需要更多行，一次性添加所有需要的行到数据管理器
            if max_rows > current_data_rows:
                rows_to_add = max_rows - current_data_rows
                # 直接操作数据管理器，避免逐行添加的开销
                data = self.controller.data_manager.get_data()
                for _ in range(rows_to_add):
                    data.append([''] * current_data_cols)
                self.controller.data_manager.set_data(data)
            
            # 如果需要更多列，一次性添加所有需要的列到数据管理器
            if max_cols > current_data_cols:
                cols_to_add = max_cols - current_data_cols
                # 直接操作数据管理器，避免逐列添加的开销
                data = self.controller.data_manager.get_data()
                for row in data:
                    row.extend([''] * cols_to_add)
                self.controller.data_manager.set_data(data)
            
            # 确保UI表格也有足够的行和列
            if max_rows > self.table.rowCount():
                self.table.setRowCount(max_rows)
            
            if max_cols > self.table.columnCount():
                self.table.setColumnCount(max_cols)
            
            # 暂时禁用表格更新以提高性能
            self.table.setUpdatesEnabled(False)
            
            # 批量设置数据到表格中
            items_to_set = []
            for i, row_data in enumerate(paste_data):
                for j, cell_data in enumerate(row_data):
                    row = current_row + i
                    col = current_col + j
                    items_to_set.append((row, col, cell_data))
            
            # 批量创建和设置单元格项
            for row, col, cell_data in items_to_set:
                # 获取或创建单元格项
                item = self.table.item(row, col)
                if not item:
                    item = QTableWidgetItem()
                    self.table.setItem(row, col, item)
                
                # 设置单元格文本
                item.setText(cell_data)
            
            # 批量更新数据管理器中的数据
            data = self.controller.data_manager.get_data()
            for row, col, cell_data in items_to_set:
                data[row][col] = cell_data
            
            # 一次性更新数据管理器，避免频繁同步到磁盘
            self.controller.data_manager.set_data(data)
            
            # 重新启用表格更新
            self.table.setUpdatesEnabled(True)
            
            # 只对粘贴的行进行行高调整，且只调整可见区域
            visible_row_start = self.table.rowAt(self.table.viewport().y())
            visible_row_end = self.table.rowAt(self.table.viewport().y() + self.table.viewport().height())
            if visible_row_end == -1:  # 如果没有行在底部，设置为最后一行
                visible_row_end = self.table.rowCount() - 1
            
            # 只调整可见区域的行高
            for row in range(max(current_row, visible_row_start), min(current_row + len(paste_data), visible_row_end + 1)):
                self.table.resizeRowToContents(row)
            
            # 设置所有列为Stretch模式，确保列宽适应窗口
            header = self.table.horizontalHeader()
            for col in range(self.table.columnCount()):
                header.setSectionResizeMode(col, header.Stretch)
            
            self.statusBar().showMessage(f"已粘贴 {len(paste_data)} 行数据")
        finally:
            # 结束批量更新模式，同步所有待处理的更改到磁盘
            self.controller.end_batch_update()
    
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
    
    def toggle_comment_dock(self):
        """切换批注窗口显示/隐藏"""
        if self.comment_widget.isVisible():
            self.comment_widget.hide()
            self.toggle_comment_dock_action.setChecked(False)
        else:
            self.comment_widget.show()
            self.toggle_comment_dock_action.setChecked(True)
    
    def closeEvent(self, event):
        """窗口关闭事件处理"""
        # 保存当前窗口大小和位置
        geometry = self.geometry()
        self.config_manager.save_window_geometry(
            width=geometry.width(),
            height=geometry.height(),
            x=geometry.x(),
            y=geometry.y()
        )
        
        # 保存停靠窗口状态
        dock_state = self.saveState()
        self.config_manager.save_dock_state(dock_state)
        
        # 调用父类的关闭事件处理方法
        super().closeEvent(event)
    
    def change_theme(self, theme_name):
        """切换应用主题"""
        # 定义不同主题的颜色方案
        themes = {
            "default": {
                "background": "#ffffff",
                "alternate": "#f9f9f9",
                "grid": "#e0e0e0",
                "text": "#000000",
                "header": "#f0f0f0",
                "selected_border": "#0078d7"
            },
            "pink": {
                "background": "#fff5f5",
                "alternate": "#ffe0e6",
                "grid": "#ffb6c1",
                "text": "#333333",
                "header": "#ffccd5",
                "selected_border": "#ff69b4"
            },
            "purple": {
                "background": "#f8f5ff",
                "alternate": "#ede6f5",
                "grid": "#d8bfd8",
                "text": "#333333",
                "header": "#e6e0fa",
                "selected_border": "#9370db"
            },
            "green": {
                "background": "#f5fff5",
                "alternate": "#e6ffe6",
                "grid": "#90ee90",
                "text": "#333333",
                "header": "#d4ffd4",
                "selected_border": "#32cd32"
            },
            "blue": {
                "background": "#f5f9ff",
                "alternate": "#e6f2ff",
                "grid": "#add8e6",
                "text": "#333333",
                "header": "#d4e7ff",
                "selected_border": "#4682b4"
            }
        }
        
        # 获取当前主题的颜色方案
        if theme_name not in themes:
            theme_name = "default"
        colors = themes[theme_name]
        
        # 应用主题样式到整个应用程序
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {colors["background"]};
            }}
            
            QTableWidget {{
                background-color: {colors["background"]};
                alternate-background-color: {colors["alternate"]};
                gridline-color: {colors["grid"]};
                color: {colors["text"]};
                selection-background-color: transparent;
                selection-color: {colors["text"]};
            }}
            
            QTableWidget::item:selected {{
                border: 2px solid {colors["selected_border"]};
                background-color: transparent;
            }}
            
            QTableWidget::item:focus {{
                border: 2px solid {colors["selected_border"]};
                background-color: transparent;
            }}
            
            QTableWidget::item {{
                padding: 5px;
            }}
            
            QHeaderView::section {{
                background-color: {colors["header"]};
                color: {colors["text"]};
                padding: 5px;
                border: 1px solid {colors["grid"]};
                font-weight: bold;
            }}
            
            QMenuBar {{
                background-color: {colors["header"]};
                color: {colors["text"]};
            }}
            
            QMenuBar::item {{
                background-color: transparent;
                padding: 5px 10px;
            }}
            
            QMenuBar::item:selected {{
                background-color: {colors["alternate"]};
            }}
            
            QMenu {{
                background-color: {colors["background"]};
                color: {colors["text"]};
                border: 1px solid {colors["grid"]};
            }}
            
            QMenu::item:selected {{
                background-color: {colors["alternate"]};
            }}
            
            QToolBar {{
                background-color: {colors["header"]};
                border: 1px solid {colors["grid"]};
            }}
            
            QStatusBar {{
                background-color: {colors["header"]};
                color: {colors["text"]};
            }}
            
            QDockWidget {{
                background-color: {colors["background"]};
                color: {colors["text"]};
                border: 1px solid {colors["grid"]};
            }}
            
            QDockWidget::title {{
                background-color: {colors["header"]};
                padding: 5px;
            }}
            
            QListWidget {{
                background-color: {colors["background"]};
                alternate-background-color: {colors["alternate"]};
                color: {colors["text"]};
                border: 1px solid {colors["grid"]};
            }}
            
            QListWidget::item:selected {{
                background-color: {colors["alternate"]};
                color: {colors["text"]};
            }}
        """)
        
        # 保存当前主题设置
        self.config_manager.save_theme(theme_name)
        
        # 更新状态栏消息
        theme_names = {
            "default": "默认白色",
            "pink": "桃粉",
            "purple": "淡紫",
            "green": "草绿",
            "blue": "天蓝"
        }
        
        self.statusBar().showMessage(f"已切换到{theme_names.get(theme_name, '默认')}主题", 3000)