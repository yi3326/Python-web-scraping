# -*- coding: utf-8 -*-
"""
任务配置管理模块
提供任务配置的导入导出功能
"""
import os
import json
import datetime
from typing import Dict, List, Any, Optional

class TaskConfigManager:
    """任务配置管理器"""
    
    def __init__(self, config_dir: str = None):
        """
        初始化任务配置管理器
        
        Args:
            config_dir: 配置文件目录，默认为当前目录下的configs文件夹
        """
        if config_dir is None:
            self.config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'configs')
        else:
            self.config_dir = config_dir
            
        # 确保配置目录存在
        os.makedirs(self.config_dir, exist_ok=True)
        
        # 默认配置文件路径
        self.default_config_file = os.path.join(self.config_dir, 'default_tasks.json')
        self.custom_config_file = os.path.join(self.config_dir, 'custom_tasks.json')
        
        # 初始化默认配置
        self._init_default_config()
        
    def _init_default_config(self):
        """初始化默认任务配置"""
        if not os.path.exists(self.default_config_file):
            default_tasks = {
                "qsbk_daily": {
                    "name": "糗事百科每日爬取",
                    "description": "每天早上8点爬取糗事百科最新内容",
                    "type": "script",
                    "script_path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "QSBK.py"),
                    "trigger_type": "cron",
                    "hour": "8",
                    "minute": "0",
                    "enabled": True,
                    "params": {
                        "pages": 3
                    }
                },
                "douban_weekly": {
                    "name": "豆瓣每周爬取",
                    "description": "每周一早上9点爬取豆瓣内容",
                    "type": "script",
                    "script_path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "DouBan", "DouBan.py"),
                    "trigger_type": "cron",
                    "day_of_week": "1",
                    "hour": "9",
                    "minute": "0",
                    "enabled": True
                },
                "xiaohua_daily": {
                    "name": "小花图片每日爬取",
                    "description": "每天下午2点爬取小花图片",
                    "type": "scrapy",
                    "project_path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "XiaoHua"),
                    "spider_name": "XiaoHua",
                    "trigger_type": "cron",
                    "hour": "14",
                    "minute": "0",
                    "enabled": True
                }
            }
            
            with open(self.default_config_file, 'w', encoding='utf-8') as f:
                json.dump(default_tasks, f, ensure_ascii=False, indent=2)
                
    def get_default_tasks(self) -> Dict[str, Any]:
        """获取默认任务配置"""
        try:
            with open(self.default_config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"读取默认任务配置失败: {str(e)}")
            return {}
            
    def get_custom_tasks(self) -> Dict[str, Any]:
        """获取自定义任务配置"""
        if not os.path.exists(self.custom_config_file):
            return {}
            
        try:
            with open(self.custom_config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"读取自定义任务配置失败: {str(e)}")
            return {}
            
    def save_custom_tasks(self, tasks: Dict[str, Any]) -> bool:
        """保存自定义任务配置"""
        try:
            with open(self.custom_config_file, 'w', encoding='utf-8') as f:
                json.dump(tasks, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存自定义任务配置失败: {str(e)}")
            return False
            
    def export_tasks(self, tasks: Dict[str, Any], file_path: str = None) -> Optional[str]:
        """
        导出任务配置到文件
        
        Args:
            tasks: 要导出的任务配置
            file_path: 导出文件路径，如果不指定则自动生成
            
        Returns:
            导出文件的路径，失败返回None
        """
        if file_path is None:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = os.path.join(self.config_dir, f"tasks_export_{timestamp}.json")
            
        try:
            # 添加导出元数据
            export_data = {
                "export_time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "export_version": "1.0",
                "tasks": tasks
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
                
            print(f"任务配置已导出到: {file_path}")
            return file_path
        except Exception as e:
            print(f"导出任务配置失败: {str(e)}")
            return None
            
    def import_tasks(self, file_path: str, merge: bool = True) -> Optional[Dict[str, Any]]:
        """
        从文件导入任务配置
        
        Args:
            file_path: 导入文件路径
            merge: 是否与现有配置合并，False则完全替换
            
        Returns:
            导入的任务配置，失败返回None
        """
        if not os.path.exists(file_path):
            print(f"导入文件不存在: {file_path}")
            return None
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
                
            # 检查是否是导出格式的文件
            if "tasks" in import_data:
                tasks = import_data["tasks"]
                export_info = {
                    "export_time": import_data.get("export_time", "未知"),
                    "export_version": import_data.get("export_version", "未知")
                }
                print(f"导入文件信息 - 导出时间: {export_info['export_time']}, 版本: {export_info['export_version']}")
            else:
                # 直接是任务配置
                tasks = import_data
                
            if merge:
                # 与现有配置合并
                custom_tasks = self.get_custom_tasks()
                custom_tasks.update(tasks)
                self.save_custom_tasks(custom_tasks)
                print(f"已合并导入 {len(tasks)} 个任务配置")
            else:
                # 完全替换
                self.save_custom_tasks(tasks)
                print(f"已替换导入 {len(tasks)} 个任务配置")
                
            return tasks
        except Exception as e:
            print(f"导入任务配置失败: {str(e)}")
            return None
            
    def validate_task_config(self, task_config: Dict[str, Any]) -> List[str]:
        """
        验证任务配置的有效性
        
        Args:
            task_config: 任务配置
            
        Returns:
            错误信息列表，空列表表示验证通过
        """
        errors = []
        
        # 检查必需字段
        if "name" not in task_config:
            errors.append("缺少任务名称 (name)")
            
        if "type" not in task_config:
            errors.append("缺少任务类型 (type)")
        elif task_config["type"] not in ["script", "scrapy", "flask"]:
            errors.append(f"不支持的任务类型: {task_config['type']}")
            
        if "trigger_type" not in task_config:
            errors.append("缺少触发器类型 (trigger_type)")
        elif task_config["trigger_type"] not in ["cron", "interval", "date"]:
            errors.append(f"不支持的触发器类型: {task_config['trigger_type']}")
            
        # 根据任务类型检查特定字段
        if task_config.get("type") == "script":
            if "script_path" not in task_config:
                errors.append("脚本类型任务缺少脚本路径 (script_path)")
            elif not os.path.exists(task_config.get("script_path", "")):
                errors.append(f"脚本文件不存在: {task_config.get('script_path', '')}")
                
        elif task_config.get("type") == "scrapy":
            if "project_path" not in task_config:
                errors.append("Scrapy类型任务缺少项目路径 (project_path)")
            elif not os.path.exists(task_config.get("project_path", "")):
                errors.append(f"Scrapy项目路径不存在: {task_config.get('project_path', '')}")
                
            if "spider_name" not in task_config:
                errors.append("Scrapy类型任务缺少爬虫名称 (spider_name)")
                
        elif task_config.get("type") == "flask":
            if "app_path" not in task_config:
                errors.append("Flask类型任务缺少应用路径 (app_path)")
            elif not os.path.exists(task_config.get("app_path", "")):
                errors.append(f"Flask应用文件不存在: {task_config.get('app_path', '')}")
                
            if "function_name" not in task_config:
                errors.append("Flask类型任务缺少函数名称 (function_name)")
                
        # 根据触发器类型检查特定字段
        trigger_type = task_config.get("trigger_type")
        if trigger_type == "date":
            if "run_date" not in task_config:
                errors.append("日期触发器缺少运行日期 (run_date)")
                
        return errors
        
    def create_task_template(self, task_type: str) -> Dict[str, Any]:
        """
        创建任务配置模板
        
        Args:
            task_type: 任务类型 (script, scrapy, flask)
            
        Returns:
            任务配置模板
        """
        base_template = {
            "name": "新任务",
            "description": "任务描述",
            "enabled": True,
            "trigger_type": "cron"
        }
        
        if task_type == "script":
            return {
                **base_template,
                "type": "script",
                "script_path": "path/to/script.py",
                "minute": "0",
                "hour": "0"
            }
        elif task_type == "scrapy":
            return {
                **base_template,
                "type": "scrapy",
                "project_path": "path/to/scrapy/project",
                "spider_name": "spider_name",
                "minute": "0",
                "hour": "0"
            }
        elif task_type == "flask":
            return {
                **base_template,
                "type": "flask",
                "app_path": "path/to/app.py",
                "function_name": "function_name",
                "minute": "0",
                "hour": "0"
            }
        else:
            return base_template