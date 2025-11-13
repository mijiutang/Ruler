"""
图像处理模块 - 负责所有图像处理逻辑
包括图片加载、裁剪、拼接等功能
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
import os


class ImageProcessor:
    """图像处理类，负责所有图像相关的操作"""
    
    def __init__(self):
        """初始化图像处理器"""
        self.current_image = None
        self.original_image = None
        self.stitched_image = None
    
    def load_image(self, file_path: str) -> bool:
        """
        加载图片
        
        Args:
            file_path: 图片文件路径
            
        Returns:
            bool: 加载成功返回True，失败返回False
        """
        try:
            if not os.path.exists(file_path):
                return False
                
            # 使用OpenCV加载图片 - 处理中文路径问题
            # 先用numpy读取文件，再用OpenCV解码
            with open(file_path, 'rb') as f:
                file_data = np.frombuffer(f.read(), dtype=np.uint8)
            image = cv2.imdecode(file_data, cv2.IMREAD_COLOR)
            
            if image is None:
                return False
                
            # 转换为RGB格式（OpenCV默认是BGR）
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            self.current_image = image.copy()
            self.original_image = image.copy()
            return True
        except Exception as e:
            print(f"加载图片失败: {e}")
            return False
    
    def get_image_size(self) -> Optional[Tuple[int, int]]:
        """
        获取当前图片尺寸
        
        Returns:
            Tuple[int, int]: (宽度, 高度)，如果没有图片则返回None
        """
        if self.current_image is None:
            return None
        height, width = self.current_image.shape[:2]
        return (width, height)
    
    def crop_image(self, x: int, y: int, width: int, height: int) -> bool:
        """
        裁剪图片
        
        Args:
            x: 起始x坐标
            y: 起始y坐标
            width: 裁剪宽度
            height: 裁剪高度
            
        Returns:
            bool: 裁剪成功返回True，失败返回False
        """
        try:
            if self.current_image is None:
                return False
                
            img_height, img_width = self.current_image.shape[:2]
            
            # 确保裁剪区域在图片范围内
            x = max(0, min(x, img_width - 1))
            y = max(0, min(y, img_height - 1))
            width = min(width, img_width - x)
            height = min(height, img_height - y)
            
            if width <= 0 or height <= 0:
                return False
                
            # 裁剪图片
            cropped = self.current_image[y:y+height, x:x+width]
            return True
        except Exception as e:
            print(f"裁剪图片失败: {e}")
            return False
    
    def reset_to_original(self):
        """重置为原始图片"""
        if self.original_image is not None:
            self.current_image = self.original_image.copy()
    
    def save_image(self, file_path: str, image_type: str = "current") -> bool:
        """
        保存图片
        
        Args:
            file_path: 保存路径
            image_type: 要保存的图片类型 ("current", "stitched")
            
        Returns:
            bool: 保存成功返回True，失败返回False
        """
        try:
            if image_type == "current" and self.current_image is not None:
                image = self.current_image
            elif image_type == "stitched" and self.stitched_image is not None:
                image = self.stitched_image
            else:
                return False
                
            # 转换为BGR格式供OpenCV保存
            image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            # 处理中文路径问题 - 先编码再写入
            success, encoded_img = cv2.imencode('.jpg', image_bgr)
            if success:
                with open(file_path, 'wb') as f:
                    f.write(encoded_img)
                return True
            return False
        except Exception as e:
            print(f"保存图片失败: {e}")
            return False
    
    def stitch_images_horizontal(self, images: List[np.ndarray], spacing: int = 10) -> bool:
        """
        水平拼接图片
        
        Args:
            images: 要拼接的图片列表
            spacing: 图片之间的间距
            
        Returns:
            bool: 拼接成功返回True，失败返回False
        """
        try:
            if not images:
                return False
                
            # 计算拼接后的尺寸
            max_height = max(img.shape[0] for img in images)
            total_width = sum(img.shape[1] for img in images) + spacing * (len(images) - 1)
            
            # 创建空白画布
            stitched = np.ones((max_height, total_width, 3), dtype=np.uint8) * 255
            
            # 逐个放置图片
            x_offset = 0
            for img in images:
                h, w = img.shape[:2]
                # 居中放置
                y_offset = (max_height - h) // 2
                stitched[y_offset:y_offset+h, x_offset:x_offset+w] = img
                x_offset += w + spacing
                
            self.stitched_image = stitched
            return True
        except Exception as e:
            print(f"水平拼接图片失败: {e}")
            return False
    
    def stitch_images_vertical(self, images: List[np.ndarray], spacing: int = 10) -> bool:
        """
        垂直拼接图片
        
        Args:
            images: 要拼接的图片列表
            spacing: 图片之间的间距
            
        Returns:
            bool: 拼接成功返回True，失败返回False
        """
        try:
            if not images:
                return False
                
            # 计算拼接后的尺寸
            max_width = max(img.shape[1] for img in images)
            total_height = sum(img.shape[0] for img in images) + spacing * (len(images) - 1)
            
            # 创建空白画布
            stitched = np.ones((total_height, max_width, 3), dtype=np.uint8) * 255
            
            # 逐个放置图片
            y_offset = 0
            for img in images:
                h, w = img.shape[:2]
                # 居中放置
                x_offset = (max_width - w) // 2
                stitched[y_offset:y_offset+h, x_offset:x_offset+w] = img
                y_offset += h + spacing
                
            self.stitched_image = stitched
            return True
        except Exception as e:
            print(f"垂直拼接图片失败: {e}")
            return False
    

    
    def get_current_image(self) -> Optional[np.ndarray]:
        """获取当前图片"""
        if self.current_image is None:
            return None
        return self.current_image.copy()
    
    def get_stitched_image(self) -> Optional[np.ndarray]:
        """获取拼接后的图片"""
        if self.stitched_image is None:
            return None
        return self.stitched_image.copy()