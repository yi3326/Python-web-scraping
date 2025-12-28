# -*- coding: utf-8 -*-
"""
定时任务管理Web应用
提供Web界面管理定时任务的导入导出功能
"""
import os
import json
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from werkzeug.utils import secure_filename
from task_scheduler import task_scheduler
from task_config_manager import TaskConfigManager

# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上传文件大小为16MB

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 初始化任务配置管理器
config_manager = TaskConfigManager()

@app.route('/')
def index():
    """主页 - 显示所有任务"""
    tasks_status = task_scheduler.get_task_status()
    return render_template('tasks.html', tasks=tasks_status)

@app.route('/api/tasks', methods=['GET'])
def api_get_tasks():
    """获取所有任务状态API"""
    tasks = task_scheduler.get_task_status()
    return jsonify(tasks)

@app.route('/api/tasks/<task_id>', methods=['GET'])
def api_get_task(task_id):
    """获取指定任务状态API"""
    task = task_scheduler.get_task_status(task_id)
    if task is None:
        return jsonify({'error': '任务不存在'}), 404
    return jsonify(task)

@app.route('/api/tasks', methods=['POST'])
def api_add_task():
    """添加任务API"""
    task_data = request.json
    if not task_data or 'id' not in task_data or 'config' not in task_data:
        return jsonify({'error': '请求数据格式错误'}), 400
        
    task_id = task_data['id']
    task_config = task_data['config']
    
    # 验证任务配置
    errors = config_manager.validate_task_config(task_config)
    if errors:
        return jsonify({'error': '任务配置无效', 'details': errors}), 400
        
    # 添加任务
    if task_scheduler.add_task(task_id, task_config):
        return jsonify({'success': True, 'message': f'任务 {task_id} 添加成功'})
    else:
        return jsonify({'error': '添加任务失败'}), 500

@app.route('/api/tasks/<task_id>', methods=['PUT'])
def api_update_task(task_id):
    """更新任务API"""
    task_config = request.json
    if not task_config:
        return jsonify({'error': '请求数据格式错误'}), 400
        
    # 验证任务配置
    errors = config_manager.validate_task_config(task_config)
    if errors:
        return jsonify({'error': '任务配置无效', 'details': errors}), 400
        
    # 更新任务
    if task_scheduler.add_task(task_id, task_config):
        return jsonify({'success': True, 'message': f'任务 {task_id} 更新成功'})
    else:
        return jsonify({'error': '更新任务失败'}), 500

@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def api_delete_task(task_id):
    """删除任务API"""
    if task_scheduler.remove_task(task_id):
        return jsonify({'success': True, 'message': f'任务 {task_id} 删除成功'})
    else:
        return jsonify({'error': '删除任务失败'}), 500

@app.route('/api/tasks/<task_id>/run', methods=['POST'])
def api_run_task(task_id):
    """立即运行任务API"""
    if task_scheduler.run_task_now(task_id):
        return jsonify({'success': True, 'message': f'任务 {task_id} 已开始执行'})
    else:
        return jsonify({'error': '执行任务失败'}), 500

@app.route('/api/tasks/export', methods=['GET'])
def api_export_tasks():
    """导出任务配置API"""
    # 获取当前所有任务配置
    tasks = task_scheduler.tasks
    
    # 导出任务配置
    file_path = config_manager.export_tasks(tasks)
    if file_path:
        return send_file(file_path, as_attachment=True)
    else:
        return jsonify({'error': '导出任务配置失败'}), 500

@app.route('/api/tasks/import', methods=['POST'])
def api_import_tasks():
    """导入任务配置API"""
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
        
    # 保存上传的文件
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    # 获取合并选项
    merge = request.form.get('merge', 'true').lower() == 'true'
    
    # 导入任务配置
    tasks = config_manager.import_tasks(file_path, merge)
    
    # 删除临时文件
    os.remove(file_path)
    
    if tasks is not None:
        # 更新调度器中的任务
        for task_id, task_config in tasks.items():
            task_scheduler.add_task(task_id, task_config)
            
        return jsonify({'success': True, 'message': f'成功导入 {len(tasks)} 个任务配置'})
    else:
        return jsonify({'error': '导入任务配置失败'}), 500

@app.route('/api/templates/<task_type>')
def api_get_template(task_type):
    """获取任务配置模板API"""
    template = config_manager.create_task_template(task_type)
    return jsonify(template)

@app.route('/tasks/new')
def new_task():
    """新建任务页面"""
    task_type = request.args.get('type', 'script')
    template = config_manager.create_task_template(task_type)
    return render_template('task_form.html', task=None, template=template, edit=False)

@app.route('/tasks/<task_id>/edit')
def edit_task(task_id):
    """编辑任务页面"""
    task = task_scheduler.get_task_status(task_id)
    if task is None:
        return redirect(url_for('index'))
    return render_template('task_form.html', task=task, template=None, edit=True)

@app.route('/tasks/import')
def import_tasks():
    """导入任务页面"""
    return render_template('import_tasks.html')

@app.route('/tasks/export')
def export_tasks():
    """导出任务页面"""
    tasks = task_scheduler.tasks
    return render_template('export_tasks.html', tasks=tasks)

if __name__ == '__main__':
    # 启动任务调度器
    task_scheduler.start()
    
    try:
        # 启动Flask应用
        app.run(host='0.0.0.0', port=5001, debug=True)
    finally:
        # 停止任务调度器
        task_scheduler.stop()