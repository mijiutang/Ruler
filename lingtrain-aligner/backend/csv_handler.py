#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CSV文件处理模块
负责表格数据的CSV文件读写操作
"""

import csv
import os
from datetime import datetime

class CSVHandler:
    """CSV文件处理类"""
    
    def __init__(self, csv_dir="表格"):
        """
        初始化CSV处理器
        
        Args:
            csv_dir (str): CSV文件存储目录
        """
        self.csv_dir = csv_dir
        # 确保目录存在
        if not os.path.exists(csv_dir):
            os.makedirs(csv_dir)
    
    def save_table(self, table_name, data, overwrite=False):
        """
        保存表格数据到CSV文件
        
        Args:
            table_name (str): 表格名称
            data (list): 二维列表形式的表格数据
            overwrite (bool): 是否覆盖已存在的文件
            
        Returns:
            str: 保存的文件路径，失败返回None
        """
        if not data or len(data) == 0:
            return None
            
        try:
            # 先尝试使用原始文件名
            filename = f"{table_name}.csv"
            file_path = os.path.join(self.csv_dir, filename)
            
            # 如果文件已存在且不允许覆盖，则添加时间戳确保唯一性
            if os.path.exists(file_path) and not overwrite:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{table_name}_{timestamp}.csv"
                file_path = os.path.join(self.csv_dir, filename)
            
            # 写入CSV文件
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                # 写入数据
                for row in data:
                    writer.writerow(row)
            
            return file_path
            
        except Exception as e:
            print(f"保存CSV文件错误: {e}")
            return None
    
    def load_table(self, file_path):
        """
        从CSV文件加载表格数据
        
        Args:
            file_path (str): CSV文件路径
            
        Returns:
            tuple: (文件名, 二维列表数据)，失败返回(None, None)
        """
        try:
            if not os.path.exists(file_path):
                return None, None
                
            # 从文件路径获取文件名（不含扩展名）
            filename = os.path.splitext(os.path.basename(file_path))[0]
            
            # 读取CSV文件
            data = []
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    data.append(row)
            
            return filename, data
            
        except Exception as e:
            print(f"加载CSV文件错误: {e}")
            return None, None
    
    def get_all_tables(self):
        """
        获取所有CSV文件信息
        
        Returns:
            list: 包含文件信息的列表，每个元素为(文件名, 文件路径, 行数, 列数, 修改时间)元组
        """
        tables = []
        
        try:
            for filename in os.listdir(self.csv_dir):
                if filename.endswith('.csv'):
                    file_path = os.path.join(self.csv_dir, filename)
                    # 获取文件修改时间
                    mtime = os.path.getmtime(file_path)
                    mod_time = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                    
                    # 读取文件信息
                    rows = 0
                    cols = 0
                    try:
                        with open(file_path, 'r', encoding='utf-8') as csvfile:
                            reader = csv.reader(csvfile)
                            data = list(reader)
                            rows = len(data)
                            cols = len(data[0]) if data else 0
                    except:
                        pass
                    
                    tables.append((filename, file_path, rows, cols, mod_time))
                    
            # 按修改时间排序（最新的在前）
            tables.sort(key=lambda x: x[4], reverse=True)
            
        except Exception as e:
            print(f"获取CSV文件列表错误: {e}")
        
        return tables
    
    def delete_table(self, file_path):
        """
        删除CSV文件
        
        Args:
            file_path (str): 要删除的文件路径
            
        Returns:
            bool: 删除是否成功
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
            
        except Exception as e:
            print(f"删除CSV文件错误: {e}")
            return False