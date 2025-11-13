"""
主界面模块 - 负责用户界面和交互
"""

import sys
import os
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                            QMessageBox, QScrollArea, QSplitter, QGroupBox,
                            QRadioButton, QButtonGroup, QSlider, QSpinBox,
                            QComboBox, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QFont

# 添加后端模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
from image_processor import ImageProcessor
from ui.image_display import ImageDisplayWidget


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.image_processor = ImageProcessor()
        self.current_files = []
        self.cropped_files = []
        # 坐标记录相关属性
        self.crop_coordinates = []  # 存储裁剪坐标
        self.coordinates_display = None  # 显示坐标信息的标签
        
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("图片裁剪与拼接工具")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中央控件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧控制面板
        left_panel = self.create_control_panel()
        splitter.addWidget(left_panel)
        
        # 右侧图片显示区域
        right_panel = self.create_display_panel()
        splitter.addWidget(right_panel)
        
        # 设置分割器比例
        splitter.setSizes([300, 900])
        
        # 状态栏
        self.statusBar().showMessage("就绪")
    
    def create_control_panel(self):
        """创建控制面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 文件操作组
        file_group = QGroupBox("文件操作")
        file_layout = QVBoxLayout(file_group)
        
        self.load_btn = QPushButton("加载图片")
        self.load_btn.clicked.connect(self.load_image)
        file_layout.addWidget(self.load_btn)
        
        self.save_btn = QPushButton("保存当前图片")
        self.save_btn.clicked.connect(self.save_current_image)
        file_layout.addWidget(self.save_btn)
        
        layout.addWidget(file_group)
        
        # 裁剪操作组
        crop_group = QGroupBox("裁剪操作")
        crop_layout = QVBoxLayout(crop_group)
        
        # 添加垂直和水平裁剪按钮
        crop_direction_layout = QHBoxLayout()
        self.vertical_crop_btn = QPushButton("垂直裁剪")
        self.vertical_crop_btn.clicked.connect(self.crop_vertical)
        self.vertical_crop_btn.setEnabled(False)
        self.horizontal_crop_btn = QPushButton("水平裁剪")
        self.horizontal_crop_btn.clicked.connect(self.crop_horizontal)
        self.horizontal_crop_btn.setEnabled(False)
        crop_direction_layout.addWidget(self.vertical_crop_btn)
        crop_direction_layout.addWidget(self.horizontal_crop_btn)
        crop_layout.addLayout(crop_direction_layout)
        
        self.reset_btn = QPushButton("重置为原图")
        self.reset_btn.clicked.connect(self.reset_image)
        self.reset_btn.setEnabled(False)
        crop_layout.addWidget(self.reset_btn)
        
        layout.addWidget(crop_group)
        
        # 拼接操作组
        stitch_group = QGroupBox("拼接操作")
        stitch_layout = QVBoxLayout(stitch_group)
        
        # 拼接方向选择
        direction_layout = QHBoxLayout()
        self.horizontal_radio = QRadioButton("水平拼接")
        self.horizontal_radio.setChecked(True)
        self.vertical_radio = QRadioButton("垂直拼接")
        direction_layout.addWidget(self.horizontal_radio)
        direction_layout.addWidget(self.vertical_radio)
        stitch_layout.addLayout(direction_layout)
        
        # 间距设置
        spacing_layout = QHBoxLayout()
        spacing_layout.addWidget(QLabel("间距:"))
        self.spacing_spinbox = QSpinBox()
        self.spacing_spinbox.setRange(0, 100)
        self.spacing_spinbox.setValue(10)
        spacing_layout.addWidget(self.spacing_spinbox)
        stitch_layout.addLayout(spacing_layout)
        
        self.stitch_btn = QPushButton("拼接裁剪图片")
        self.stitch_btn.clicked.connect(self.stitch_images)
        self.stitch_btn.setEnabled(False)
        stitch_layout.addWidget(self.stitch_btn)
        
        self.save_stitched_btn = QPushButton("保存拼接图片")
        self.save_stitched_btn.clicked.connect(self.save_stitched_image)
        self.save_stitched_btn.setEnabled(False)
        stitch_layout.addWidget(self.save_stitched_btn)
        
        layout.addWidget(stitch_group)
        
        # 添加弹性空间
        layout.addStretch()
        
        return panel
    
    def create_display_panel(self):
        """创建图片显示面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 创建标签页
        self.tab_widget = QComboBox()
        self.tab_widget.addItems(["原始图片", "裁剪图片", "拼接图片"])
        self.tab_widget.currentTextChanged.connect(self.switch_display)
        layout.addWidget(self.tab_widget)
        
        # 创建图片显示区域
        self.image_display = ImageDisplayWidget()
        self.image_display.selection_changed.connect(self.on_selection_changed)
        
        # 添加滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.image_display)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        # 信息显示
        self.info_label = QLabel("请加载图片")
        layout.addWidget(self.info_label)
        
        # 坐标信息显示
        self.coordinates_display = QLabel("坐标信息: 无")
        self.coordinates_display.setWordWrap(True)
        layout.addWidget(self.coordinates_display)
        
        return panel
    
    def load_image(self):
        """加载图片"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "", 
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.tiff);;所有文件 (*)"
        )
        
        if file_path:
            if self.image_processor.load_image(file_path):
                self.current_files.append(file_path)
                self.image_display.set_image(self.image_processor.get_current_image())
                self.update_info()
                self.vertical_crop_btn.setEnabled(True)
                self.horizontal_crop_btn.setEnabled(True)
                self.reset_btn.setEnabled(True)
                self.statusBar().showMessage(f"已加载: {os.path.basename(file_path)}")
            else:
                QMessageBox.warning(self, "错误", "无法加载图片")
    
    def save_current_image(self):
        """保存当前图片"""
        if not self.image_processor.get_current_image():
            QMessageBox.warning(self, "警告", "没有可保存的图片")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存图片", "", 
            "图片文件 (*.png *.jpg *.jpeg *.bmp);;所有文件 (*)"
        )
        
        if file_path:
            if self.image_processor.save_image(file_path, "current"):
                self.statusBar().showMessage(f"已保存: {os.path.basename(file_path)}")
            else:
                QMessageBox.warning(self, "错误", "保存失败")
    
    def crop_selected_area(self):
        """裁剪选中的区域"""
        if not hasattr(self, 'last_selection'):
            QMessageBox.warning(self, "警告", "请先选择要裁剪的区域")
            return
            
        x, y, width, height = self.last_selection
        if self.image_processor.crop_image(x, y, width, height):
            # 启用拼接按钮
            self.stitch_btn.setEnabled(True)
            
            self.statusBar().showMessage(f"已裁剪区域: ({x},{y}) {width}x{height}")
        else:
            QMessageBox.warning(self, "错误", "裁剪失败")
    
    def reset_image(self):
        """重置为原图"""
        self.image_processor.reset_to_original()
        self.image_display.set_image(self.image_processor.get_current_image())
        self.image_display.clear_selection()
        # 重置后重新启用裁剪按钮
        self.vertical_crop_btn.setEnabled(True)
        self.horizontal_crop_btn.setEnabled(True)
        self.statusBar().showMessage("已重置为原图")
    
    def stitch_images(self):
        """拼接裁剪的图片"""
        # 移除了与裁剪图片列表相关的功能
        QMessageBox.information(self, "提示", "此功能已被移除")
    
    def save_stitched_image(self):
        """保存拼接的图片"""
        if not self.image_processor.get_stitched_image():
            QMessageBox.warning(self, "警告", "没有可保存的拼接图片")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存拼接图片", "", 
            "图片文件 (*.png *.jpg *.jpeg *.bmp);;所有文件 (*)"
        )
        
        if file_path:
            if self.image_processor.save_image(file_path, "stitched"):
                self.statusBar().showMessage(f"已保存: {os.path.basename(file_path)}")
            else:
                QMessageBox.warning(self, "错误", "保存失败")
    

    
    def switch_display(self, display_type):
        """切换显示内容"""
        if display_type == "原始图片":
            self.image_display.set_image(self.image_processor.get_current_image())
        elif display_type == "拼接图片":
            self.image_display.set_image(self.image_processor.get_stitched_image())
    
    def on_selection_changed(self, x, y, width, height):
        """选择区域变化时的处理"""
        self.last_selection = (x, y, width, height)
        self.statusBar().showMessage(f"选择区域: ({x},{y}) {width}x{height}")
    
    def update_info(self):
        """更新信息显示"""
        size = self.image_processor.get_image_size()
        if size:
            self.info_label.setText(f"图片尺寸: {size[0]} x {size[1]}")
        else:
            self.info_label.setText("无图片")
    
    def on_left_click_placeholder(self, pos):
        """左键点击占位符方法"""
        # TODO: 在这里添加左键点击的具体功能实现
        print(f"左键点击位置: {pos.x()}, {pos.y()}")
        self.statusBar().showMessage(f"左键点击位置: ({pos.x()}, {pos.y()})")
    
    def crop_vertical(self):
        """垂直裁剪 - 将图片从中间分成左右两部分"""
        # 设置裁剪模式为垂直
        self.image_display.set_crop_mode("vertical")
        # 不再自动裁剪，等待用户点击
        self.statusBar().showMessage("请在图片上点击确定垂直裁剪位置，右键退出裁剪模式")
    
    def crop_horizontal(self):
        """水平裁剪 - 将图片从中间分成上下两部分"""
        # 设置裁剪模式为水平
        self.image_display.set_crop_mode("horizontal")
        # 不再自动裁剪，等待用户点击
        self.statusBar().showMessage("请在图片上点击确定水平裁剪位置，右键退出裁剪模式")
    
    def perform_crop_at_position(self, crop_mode, pos, image_rect):
        """在指定位置执行裁剪操作"""
        # 重置裁剪模式
        self.image_display.set_crop_mode(None)
        
        # 获取当前图片尺寸
        size = self.image_processor.get_image_size()
        if not size:
            QMessageBox.warning(self, "警告", "没有可裁剪的图片")
            return
        
        width, height = size
        
        # 将显示坐标转换为原始图片坐标
        x_ratio = (pos.x() - image_rect.x()) / image_rect.width()
        y_ratio = (pos.y() - image_rect.y()) / image_rect.height()
        
        if crop_mode == "vertical":
            # 竖向裁剪 - 只记录坐标而不执行实际裁剪
            crop_x = int(x_ratio * width)
            
            # 确保裁剪位置在有效范围内
            crop_x = max(1, min(crop_x, width - 1))
            
            # 记录坐标信息
            coord_info = {
                "mode": "vertical",
                "click_position": {"x": pos.x(), "y": pos.y()},
                "image_coordinates": {"x": crop_x},
                "image_size": {"width": width, "height": height},
                "left_image": {"x": 0, "y": 0, "width": crop_x, "height": height},
                "right_image": {"x": crop_x, "y": 0, "width": width - crop_x, "height": height}
            }
            
            # 添加到坐标记录列表
            self.crop_coordinates.append(coord_info)
            
            # 更新UI显示
            self.update_coordinates_display()
            
            # 保存到JSON文件
            self.save_coordinates_to_json()
            
            self.statusBar().showMessage(f"已记录垂直裁剪坐标: x={crop_x}")
                
        elif crop_mode == "horizontal":
            # 横向裁剪 - 只记录坐标而不执行实际裁剪
            crop_y = int(y_ratio * height)
            
            # 确保裁剪位置在有效范围内
            crop_y = max(1, min(crop_y, height - 1))
            
            # 记录坐标信息
            coord_info = {
                "mode": "horizontal",
                "click_position": {"x": pos.x(), "y": pos.y()},
                "image_coordinates": {"y": crop_y},
                "image_size": {"width": width, "height": height},
                "top_image": {"x": 0, "y": 0, "width": width, "height": crop_y},
                "bottom_image": {"x": 0, "y": crop_y, "width": width, "height": height - crop_y}
            }
            
            # 添加到坐标记录列表
            self.crop_coordinates.append(coord_info)
            
            # 更新UI显示
            self.update_coordinates_display()
            
            # 保存到JSON文件
            self.save_coordinates_to_json()
            
            self.statusBar().showMessage(f"已记录水平裁剪坐标: y={crop_y}")
    
    def update_coordinates_display(self):
        """更新坐标信息显示"""
        if not self.crop_coordinates:
            self.coordinates_display.setText("坐标信息: 无")
            return
            
        # 显示最新的5条记录
        latest_coords = self.crop_coordinates[-5:]
        display_text = "坐标信息:\n"
        for i, coord in enumerate(latest_coords, 1):
            if coord["mode"] == "vertical":
                display_text += f"{len(self.crop_coordinates)-5+i}. 垂直裁剪 @ x={coord['image_coordinates']['x']}\n"
            else:
                display_text += f"{len(self.crop_coordinates)-5+i}. 水平裁剪 @ y={coord['image_coordinates']['y']}\n"
                
        self.coordinates_display.setText(display_text)
    
    def save_coordinates_to_json(self):
        """保存坐标信息到JSON文件"""
        try:
            with open("crop_coordinates.json", "w", encoding="utf-8") as f:
                json.dump(self.crop_coordinates, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存坐标到JSON文件失败: {e}")