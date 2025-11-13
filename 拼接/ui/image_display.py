import sys
import os
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QPixmap, QImage, QPen
from PyQt5.QtCore import Qt, QPoint, QRect, pyqtSignal


class ImageDisplayWidget(QWidget):
    """图片显示控件，支持鼠标选择区域"""
    
    selection_changed = pyqtSignal(int, int, int, int)  # 选择区域变化信号
    
    def __init__(self):
        super().__init__()
        self.image = None
        self.pixmap = None
        self.selection_rect = None
        self.is_selecting = False
        self.start_pos = None
        self.scale_factor = 1.0
        # 添加裁剪模式属性：None表示普通选择，"vertical"表示竖向裁剪，"horizontal"表示横向裁剪
        self.crop_mode = None
        self.mouse_pos = None  # 鼠标位置
        
        self.setMinimumSize(400, 300)
        self.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        # 设置鼠标追踪，以便在鼠标移动时也能触发事件
        self.setMouseTracking(True)
    
    def set_image(self, image):
        """设置要显示的图片"""
        if image is None:
            self.image = None
            self.pixmap = None
            self.update()
            return
            
        # 将numpy数组转换为QPixmap
        height, width, channel = image.shape
        bytes_per_line = 3 * width
        q_image = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888)
        self.pixmap = QPixmap.fromImage(q_image)
        self.image = image
        
        # 计算缩放因子以适应控件大小（无论图片大小如何都进行缩放）
        if self.width() > 0 and self.height() > 0 and self.pixmap.width() > 0 and self.pixmap.height() > 0:
            # 计算宽度和高度的缩放比例
            width_ratio = self.width() / self.pixmap.width()
            height_ratio = self.height() / self.pixmap.height()
            
            # 取较小的比例以确保图片完整显示，并留一些边距
            self.scale_factor = min(width_ratio, height_ratio) * 0.9
        else:
            self.scale_factor = 1.0
            
        # 清除之前的选择
        self.selection_rect = None
        self.update()
    
    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        # 当窗口大小改变时，重新计算图片的缩放因子
        if self.pixmap:
            if self.width() > 0 and self.height() > 0 and self.pixmap.width() > 0 and self.pixmap.height() > 0:
                # 计算宽度和高度的缩放比例
                width_ratio = self.width() / self.pixmap.width()
                height_ratio = self.height() / self.pixmap.height()
                
                # 取较小的比例以确保图片完整显示，并留一些边距
                self.scale_factor = min(width_ratio, height_ratio) * 0.9
            else:
                self.scale_factor = 1.0
            self.update()
    
    def get_scaled_image_size(self):
        """获取缩放后的图片尺寸"""
        if not self.pixmap:
            return 0, 0
            
        return int(self.pixmap.width() * self.scale_factor), int(self.pixmap.height() * self.scale_factor)
    
    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制背景
        painter.fillRect(self.rect(), Qt.lightGray)
        
        if self.pixmap:
            # 获取图片显示区域
            image_rect = self.get_image_rect()
            
            # 绘制图片 - 使用预计算的缩放因子
            scaled_pixmap = self.pixmap.scaled(
                image_rect.width(), image_rect.height(),
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            painter.drawPixmap(image_rect, scaled_pixmap)
            
            # 根据裁剪模式绘制虚线指示器
            if self.crop_mode == "vertical" and image_rect:
                # 竖向裁剪模式 - 绘制跟随鼠标的垂直虚线
                pen = QPen(Qt.red, 1, Qt.DashLine)
                painter.setPen(pen)
                # 如果有鼠标位置，使用鼠标位置，否则使用中间位置
                if self.mouse_pos and image_rect.contains(self.mouse_pos):
                    line_x = self.mouse_pos.x()
                else:
                    line_x = image_rect.x() + image_rect.width() // 2
                painter.drawLine(line_x, image_rect.y(), line_x, image_rect.y() + image_rect.height())
            elif self.crop_mode == "horizontal" and image_rect:
                # 横向裁剪模式 - 绘制跟随鼠标的水平虚线
                pen = QPen(Qt.red, 1, Qt.DashLine)
                painter.setPen(pen)
                # 如果有鼠标位置，使用鼠标位置，否则使用中间位置
                if self.mouse_pos and image_rect.contains(self.mouse_pos):
                    line_y = self.mouse_pos.y()
                else:
                    line_y = image_rect.y() + image_rect.height() // 2
                painter.drawLine(image_rect.x(), line_y, image_rect.x() + image_rect.width(), line_y)
            

    
    def get_image_rect(self):
        """获取图片在控件中的显示区域"""
        if not self.pixmap:
            return None
            
        # 获取缩放后的图片尺寸
        scaled_width, scaled_height = self.get_scaled_image_size()
        
        # 计算图片居中显示的位置
        x = (self.width() - scaled_width) // 2
        y = (self.height() - scaled_height) // 2
        
        return QRect(x, y, scaled_width, scaled_height)
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.RightButton and self.crop_mode:
            # 右键退出裁剪模式
            self.set_crop_mode(None)
            # 通过父窗口访问状态栏
            parent = self.parent()
            if parent and hasattr(parent, 'statusBar'):
                parent.statusBar().showMessage("已退出裁剪模式")
            return
            
        if event.button() == Qt.LeftButton and self.pixmap:
            # 如果处于裁剪模式，执行裁剪操作
            if self.crop_mode in ["vertical", "horizontal"]:
                # 调用裁剪方法
                self.perform_crop_at_position(self.crop_mode, event.pos(), self.get_image_rect())
                return
                
            # 普通模式下左键点击的占位符功能
            # TODO: 在这里添加左键点击的具体功能实现
            print("左键点击占位符 - 在这里添加具体功能")
            # 可以通过parent调用主窗口的方法
            parent = self.parent()
            if parent and hasattr(parent, 'on_left_click_placeholder'):
                parent.on_left_click_placeholder(event.pos())
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        # 如果处于裁剪模式，跟踪鼠标位置并更新显示
        if self.crop_mode in ["vertical", "horizontal"]:
            self.mouse_pos = event.pos()
            self.update()
            return
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        # 如果处于裁剪模式，则不进行手动选择
        if self.crop_mode in ["vertical", "horizontal"]:
            return
            
        # 普通模式下不执行任何操作，因为我们已经用占位符替换了左键点击功能
        pass
    
    def clear_selection(self):
        """清除选择区域"""
        self.selection_rect = None
        self.update()
    
    def set_crop_mode(self, mode):
        """设置裁剪模式"""
        self.crop_mode = mode
        self.update()
    
    def perform_crop_at_position(self, crop_mode, pos):
        """在指定位置执行裁剪操作"""
        if not crop_mode or not self.pixmap:
            return
            
        # 获取图片显示区域
        image_rect = self.get_image_rect()
        
        # 检查点击位置是否在图片区域内
        if not image_rect or not image_rect.contains(pos):
            return
            
        # 通知主窗口执行裁剪，传递位置和图片矩形用于坐标转换
        parent = self.parent()
        if parent and hasattr(parent, 'perform_crop_at_position'):
            parent.perform_crop_at_position(crop_mode, pos, image_rect)