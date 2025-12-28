#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
定时任务管理系统启动脚本
"""

import os
import sys
import logging
from task_manager_app import app

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('task_manager.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """主函数"""
    try:
        logger.info("启动定时任务管理系统...")
        
        # 确保导出目录存在
        os.makedirs('exports', exist_ok=True)
        
        # 启动Flask应用
        logger.info("Web界面启动成功，访问 http://localhost:5000")
        app.run(host='0.0.0.0', port=5000, debug=True)
        
    except Exception as e:
        logger.error(f"启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()