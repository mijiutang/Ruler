#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置管理器
用于保存和加载应用程序配置
"""

import os
import json
from PyQt5.QtCore import QSettings

class ConfigManager:
    """配置管理器类"""
    
    def __init__(self):
        """初始化配置管理器"""
        # 使用QSettings保存配置
        self.settings = QSettings("Lingtrain", "TableEditor")
        
        # 确保配置目录存在
        self.config_dir = os.path.expanduser("~/.lingtrain_table_editor")
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        
        self.config_file = os.path.join(self.config_dir, "config.json")
    
    def save_theme(self, theme_name):
        """
        保存当前主题设置
        
        Args:
            theme_name (str): 主题名称
        """
        # 使用QSettings保存
        self.settings.setValue("theme", theme_name)
        
        # 同时保存到JSON文件作为备份
        config = self.load_config()
        config["theme"] = theme_name
        self._save_config_to_file(config)
    
    def load_theme(self):
        """
        加载保存的主题设置
        
        Returns:
            str: 主题名称，如果没有保存则返回默认值"default"
        """
        # 首先尝试从QSettings加载
        theme = self.settings.value("theme", "default")
        
        # 如果QSettings中没有，尝试从JSON文件加载
        if theme == "default":
            config = self.load_config()
            theme = config.get("theme", "default")
        
        return theme
    
    def load_config(self):
        """
        从文件加载配置
        
        Returns:
            dict: 配置字典
        """
        if not os.path.exists(self.config_file):
            return {}
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    
    def save_window_geometry(self, width, height, x=None, y=None):
        """
        保存窗口几何信息
        
        Args:
            width (int): 窗口宽度
            height (int): 窗口高度
            x (int, optional): 窗口X坐标
            y (int, optional): 窗口Y坐标
        """
        # 使用QSettings保存
        self.settings.setValue("window_width", width)
        self.settings.setValue("window_height", height)
        
        if x is not None:
            self.settings.setValue("window_x", x)
        if y is not None:
            self.settings.setValue("window_y", y)
        
        # 同时保存到JSON文件作为备份
        config = self.load_config()
        config["window"] = {
            "width": width,
            "height": height
        }
        
        if x is not None:
            config["window"]["x"] = x
        if y is not None:
            config["window"]["y"] = y
            
        self._save_config_to_file(config)
    
    def load_window_geometry(self):
        """
        加载窗口几何信息
        
        Returns:
            dict: 包含窗口几何信息的字典，如果没有保存则返回默认值
        """
        # 首先尝试从QSettings加载
        width = self.settings.value("window_width", 1000)
        height = self.settings.value("window_height", 700)
        x = self.settings.value("window_x")
        y = self.settings.value("window_y")
        
        # 如果QSettings中没有，尝试从JSON文件加载
        if width == 1000 and height == 700:
            config = self.load_config()
            window_config = config.get("window", {})
            width = window_config.get("width", 1000)
            height = window_config.get("height", 700)
            x = window_config.get("x")
            y = window_config.get("y")
        
        return {
            "width": int(width) if width else 1000,
            "height": int(height) if height else 700,
            "x": int(x) if x else None,
            "y": int(y) if y else None
        }
    
    def save_dock_state(self, dock_state):
        """
        保存停靠窗口状态
        
        Args:
            dock_state: 停靠窗口状态(QByteArray)
        """
        # 将QByteArray转换为Base64编码的字符串，以便JSON序列化
        import base64
        dock_state_str = base64.b64encode(dock_state).decode('utf-8')
        
        # 使用QSettings保存
        self.settings.setValue("dock_state", dock_state_str)
        
        # 同时保存到JSON文件作为备份
        config = self.load_config()
        config["dock_state"] = dock_state_str
        self._save_config_to_file(config)
    
    def load_dock_state(self):
        """
        加载停靠窗口状态
        
        Returns:
            QByteArray: 停停窗口状态
        """
        # 从QSettings加载
        dock_state_str = self.settings.value("dock_state", "")
        
        # 如果QSettings中没有，尝试从JSON文件加载
        if not dock_state_str:
            config = self.load_config()
            dock_state_str = config.get("dock_state", "")
        
        # 如果有保存的状态，将Base64字符串解码为QByteArray
        if dock_state_str:
            try:
                import base64
                from PyQt5.QtCore import QByteArray
                dock_state_bytes = base64.b64decode(dock_state_str)
                return QByteArray(dock_state_bytes)
            except Exception as e:
                print(f"加载停靠窗口状态失败: {e}")
                return None
        
        return None
    
    def _save_config_to_file(self, config):
        """
        保存配置到文件
        
        Args:
            config (dict): 配置字典
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except IOError:
            pass