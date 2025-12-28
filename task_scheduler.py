# -*- coding: utf-8 -*-
"""
定时任务调度器
支持调度不同类型的爬虫任务
"""
import os
import sys
import json
import logging
import importlib
import subprocess
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from flask import Flask

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class TaskScheduler:
    """定时任务调度器"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.tasks = {}
        self.task_results = {}
        self.tasks_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tasks.json')
        self.logger = self._setup_logger()
        self._load_tasks()
        
    def _setup_logger(self):
        """设置日志记录器"""
        logger = logging.getLogger('TaskScheduler')
        logger.setLevel(logging.INFO)
        
        # 创建文件处理器
        file_handler = logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scheduler.log'),
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 创建格式化器
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
        
    def _load_tasks(self):
        """从文件加载任务配置"""
        if os.path.exists(self.tasks_file):
            try:
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    self.tasks = json.load(f)
                self.logger.info(f"已加载 {len(self.tasks)} 个任务配置")
            except Exception as e:
                self.logger.error(f"加载任务配置失败: {str(e)}")
                self.tasks = {}
        else:
            self.tasks = {}
            
    def _save_tasks(self):
        """保存任务配置到文件"""
        try:
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=2)
            self.logger.info("任务配置已保存")
        except Exception as e:
            self.logger.error(f"保存任务配置失败: {str(e)}")
            
    def add_task(self, task_id, task_config):
        """添加任务"""
        if task_id in self.tasks:
            self.logger.warning(f"任务 {task_id} 已存在，将被覆盖")
            
        self.tasks[task_id] = task_config
        self._save_tasks()
        
        # 如果调度器已启动，添加任务到调度器
        if self.scheduler.running:
            self._schedule_task(task_id, task_config)
            
        self.logger.info(f"已添加任务: {task_id}")
        return True
        
    def remove_task(self, task_id):
        """移除任务"""
        if task_id not in self.tasks:
            self.logger.warning(f"任务 {task_id} 不存在")
            return False
            
        # 从调度器中移除
        if self.scheduler.get_job(task_id):
            self.scheduler.remove_job(task_id)
            
        # 从配置中移除
        del self.tasks[task_id]
        self._save_tasks()
        
        self.logger.info(f"已移除任务: {task_id}")
        return True
        
    def _schedule_task(self, task_id, task_config):
        """将任务添加到调度器"""
        trigger_type = task_config.get('trigger_type', 'cron')
        
        try:
            if trigger_type == 'cron':
                # Cron表达式触发
                trigger = CronTrigger(
                    minute=task_config.get('minute', '*'),
                    hour=task_config.get('hour', '*'),
                    day=task_config.get('day', '*'),
                    month=task_config.get('month', '*'),
                    day_of_week=task_config.get('day_of_week', '*')
                )
            elif trigger_type == 'interval':
                # 间隔触发
                trigger = IntervalTrigger(
                    seconds=task_config.get('seconds', 0),
                    minutes=task_config.get('minutes', 0),
                    hours=task_config.get('hours', 0),
                    days=task_config.get('days', 0)
                )
            elif trigger_type == 'date':
                # 指定日期触发
                run_date = task_config.get('run_date')
                if not run_date:
                    self.logger.error(f"任务 {task_id} 缺少 run_date 参数")
                    return False
                trigger = DateTrigger(run_date=run_date)
            else:
                self.logger.error(f"任务 {task_id} 不支持的触发器类型: {trigger_type}")
                return False
                
            # 添加任务到调度器
            self.scheduler.add_job(
                func=self._execute_task,
                trigger=trigger,
                args=[task_id, task_config],
                id=task_id,
                replace_existing=True
            )
            
            self.logger.info(f"已调度任务: {task_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"调度任务 {task_id} 失败: {str(e)}")
            return False
            
    def _execute_task(self, task_id, task_config):
        """执行任务"""
        self.logger.info(f"开始执行任务: {task_id}")
        start_time = datetime.now()
        
        try:
            task_type = task_config.get('type', 'script')
            
            if task_type == 'script':
                # 执行Python脚本
                script_path = task_config.get('script_path')
                if not script_path or not os.path.exists(script_path):
                    raise Exception(f"脚本文件不存在: {script_path}")
                    
                # 使用subprocess执行脚本
                result = subprocess.run(
                    [sys.executable, script_path],
                    capture_output=True,
                    text=True,
                    encoding='utf-8'
                )
                
                if result.returncode != 0:
                    raise Exception(f"脚本执行失败: {result.stderr}")
                    
                output = result.stdout
                
            elif task_type == 'scrapy':
                # 执行Scrapy爬虫
                project_path = task_config.get('project_path')
                spider_name = task_config.get('spider_name')
                
                if not project_path or not spider_name:
                    raise Exception("Scrapy任务缺少 project_path 或 spider_name 参数")
                    
                # 切换到Scrapy项目目录
                original_dir = os.getcwd()
                os.chdir(project_path)
                
                try:
                    # 执行Scrapy命令
                    result = subprocess.run(
                        [sys.executable, '-m', 'scrapy', 'crawl', spider_name],
                        capture_output=True,
                        text=True,
                        encoding='utf-8'
                    )
                    
                    if result.returncode != 0:
                        raise Exception(f"Scrapy爬虫执行失败: {result.stderr}")
                        
                    output = result.stdout
                finally:
                    # 恢复原始目录
                    os.chdir(original_dir)
                    
            elif task_type == 'flask':
                # 调用Flask应用中的函数
                app_path = task_config.get('app_path')
                function_name = task_config.get('function_name')
                
                if not app_path or not function_name:
                    raise Exception("Flask任务缺少 app_path 或 function_name 参数")
                    
                # 动态导入模块
                module_name = os.path.splitext(os.path.basename(app_path))[0]
                spec = importlib.util.spec_from_file_location(module_name, app_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # 获取函数并执行
                if not hasattr(module, function_name):
                    raise Exception(f"模块 {module_name} 中不存在函数 {function_name}")
                    
                func = getattr(module, function_name)
                output = func()
                
            else:
                raise Exception(f"不支持的任务类型: {task_type}")
                
            # 记录任务执行结果
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.task_results[task_id] = {
                'status': 'success',
                'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
                'duration': f"{duration:.2f}秒",
                'output': output[:1000] if output else "",  # 限制输出长度
                'last_run': end_time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.logger.info(f"任务 {task_id} 执行成功，耗时 {duration:.2f}秒")
            
        except Exception as e:
            # 记录任务执行失败
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.task_results[task_id] = {
                'status': 'failed',
                'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
                'duration': f"{duration:.2f}秒",
                'error': str(e),
                'last_run': end_time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.logger.error(f"任务 {task_id} 执行失败: {str(e)}")
            
    def start(self):
        """启动调度器"""
        if not self.scheduler.running:
            # 添加所有已配置的任务
            for task_id, task_config in self.tasks.items():
                if task_config.get('enabled', True):  # 只添加启用的任务
                    self._schedule_task(task_id, task_config)
                    
            self.scheduler.start()
            self.logger.info("任务调度器已启动")
            
    def stop(self):
        """停止调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.logger.info("任务调度器已停止")
            
    def get_task_status(self, task_id=None):
        """获取任务状态"""
        if task_id:
            if task_id not in self.tasks:
                return None
                
            job = self.scheduler.get_job(task_id)
            task_config = self.tasks[task_id]
            task_result = self.task_results.get(task_id, {})
            
            return {
                'id': task_id,
                'config': task_config,
                'scheduled': job is not None,
                'next_run': job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job and job.next_run_time else None,
                'result': task_result
            }
        else:
            # 返回所有任务状态
            tasks_status = {}
            for tid in self.tasks:
                tasks_status[tid] = self.get_task_status(tid)
            return tasks_status
            
    def run_task_now(self, task_id):
        """立即运行指定任务"""
        if task_id not in self.tasks:
            self.logger.error(f"任务 {task_id} 不存在")
            return False
            
        task_config = self.tasks[task_id]
        self._execute_task(task_id, task_config)
        self.logger.info(f"已手动执行任务: {task_id}")
        return True
        
    def export_tasks(self, file_path=None):
        """导出任务配置"""
        if not file_path:
            file_path = f"tasks_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=2)
            self.logger.info(f"任务配置已导出到: {file_path}")
            return file_path
        except Exception as e:
            self.logger.error(f"导出任务配置失败: {str(e)}")
            return None
            
    def import_tasks(self, file_path, merge=False):
        """导入任务配置"""
        if not os.path.exists(file_path):
            self.logger.error(f"导入文件不存在: {file_path}")
            return False
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_tasks = json.load(f)
                
            if not merge:
                # 不合并，直接替换
                self.tasks = imported_tasks
            else:
                # 合并导入
                self.tasks.update(imported_tasks)
                
            self._save_tasks()
            
            # 如果调度器已运行，重新调度所有任务
            if self.scheduler.running:
                # 先移除所有任务
                for job in self.scheduler.get_jobs():
                    self.scheduler.remove_job(job.id)
                    
                # 重新添加所有任务
                for task_id, task_config in self.tasks.items():
                    if task_config.get('enabled', True):
                        self._schedule_task(task_id, task_config)
                        
            self.logger.info(f"已导入 {len(imported_tasks)} 个任务配置")
            return True
            
        except Exception as e:
            self.logger.error(f"导入任务配置失败: {str(e)}")
            return False


# 全局调度器实例
task_scheduler = TaskScheduler()