# 定时任务管理系统

这是一个基于Flask和APScheduler的定时任务管理系统，专为Python爬虫项目设计，支持Python脚本、Scrapy爬虫和Flask应用的定时执行。

## 功能特点

- 📅 **灵活的调度器**：支持Cron表达式、间隔执行和指定日期三种触发方式
- 🕷️ **多类型任务支持**：支持Python脚本、Scrapy爬虫和Flask应用三种任务类型
- 📥 **任务导入导出**：支持JSON格式的任务配置导入导出，方便备份和迁移
- 🌐 **友好的Web界面**：基于Bootstrap的响应式界面，操作简单直观
- 📊 **执行历史记录**：记录任务执行历史，方便排查问题
- ⚡ **实时任务控制**：支持立即执行、暂停、恢复任务操作

## 安装与配置

### 1. 安装依赖

```bash
pip install flask apscheduler
```

### 2. 启动系统

```bash
python run_task_manager.py
```

启动后访问 http://localhost:5000 即可使用Web界面管理定时任务。

## 使用说明

### 创建任务

1. 点击"新建任务"按钮
2. 填写任务基本信息：
   - 任务名称：唯一标识符
   - 任务描述：可选的任务说明
   - 任务类型：选择Python脚本、Scrapy爬虫或Flask应用
   - 启用状态：是否立即启用任务

3. 根据任务类型配置相应参数：
   - **Python脚本**：脚本路径（相对于项目根目录）
   - **Scrapy爬虫**：项目路径和爬虫名称
   - **Flask应用**：应用路径和函数名称

4. 配置触发器：
   - **Cron表达式**：设置分钟、小时、日、月、星期
   - **间隔执行**：设置秒、分钟、小时的间隔
   - **指定日期**：设置具体的执行日期和时间

5. 点击"创建任务"保存

### 管理任务

在任务列表页面，您可以：

- 查看所有任务的状态和下次执行时间
- 立即执行任务
- 编辑任务配置
- 暂停/恢复任务
- 删除任务
- 查看任务详情和执行历史

### 导入导出任务

#### 导出任务

1. 点击"导出任务"按钮
2. 选择要导出的任务
3. 设置文件名（可选）
4. 选择是否包含已禁用的任务
5. 点击"下载文件"获取JSON格式的任务配置

#### 导入任务

1. 点击"导入任务"按钮
2. 选择JSON格式的任务配置文件
3. 选择是否覆盖已存在的任务
4. 预览文件内容
5. 确认导入

## 任务配置示例

### Python脚本任务

```json
{
  "id": "daily_qsbk",
  "config": {
    "name": "每日糗事百科爬取",
    "description": "每天早上8点爬取糗事百科最新内容",
    "type": "script",
    "enabled": true,
    "trigger_type": "cron",
    "minute": "0",
    "hour": "8",
    "day": "*",
    "month": "*",
    "day_of_week": "*",
    "script_path": "QSBK.py"
  }
}
```

### Scrapy爬虫任务

```json
{
  "id": "weekly_xiaohua",
  "config": {
    "name": "每周笑话图片爬取",
    "description": "每周一早上9点爬取笑话图片",
    "type": "scrapy",
    "enabled": true,
    "trigger_type": "cron",
    "minute": "0",
    "hour": "9",
    "day": "*",
    "month": "*",
    "day_of_week": "0",
    "project_path": "XiaoHua",
    "spider_name": "xiaohua"
  }
}
```

### Flask应用任务

```json
{
  "id": "hourly_data_sync",
  "config": {
    "name": "每小时数据同步",
    "description": "每小时同步一次数据",
    "type": "flask",
    "enabled": true,
    "trigger_type": "interval",
    "seconds": 0,
    "minutes": 0,
    "hours": 1,
    "app_path": "server.py",
    "function_name": "sync_data"
  }
}
```

## 项目结构

```
d:\Python-web-scraping\
├── task_manager_app.py      # Flask应用主文件
├── task_scheduler.py        # 任务调度器核心模块
├── task_config_manager.py   # 任务配置管理模块
├── run_task_manager.py      # 启动脚本
├── templates/               # HTML模板目录
│   ├── base.html           # 基础模板
│   ├── tasks.html          # 任务列表页面
│   ├── task_form.html      # 任务表单页面
│   ├── task_detail.html    # 任务详情页面
│   ├── import_tasks.html   # 任务导入页面
│   └── export_tasks.html   # 任务导出页面
├── static/                 # 静态资源目录
├── exports/                # 导出文件目录
└── task_manager.log        # 日志文件
```

## 注意事项

1. 确保Python脚本、Scrapy项目和Flask应用的路径正确
2. 任务执行时会记录日志，可通过日志排查问题
3. 导入任务时会验证配置格式，格式错误的任务会被跳过
4. 系统会自动创建必要的目录（如exports目录）
5. 建议定期导出任务配置作为备份

## 常见问题

### Q: 任务执行失败怎么办？

A: 查看任务详情页面的执行历史，可以看到具体的错误信息。也可以查看task_manager.log日志文件获取更详细的错误信息。

### Q: 如何修改已存在的任务？

A: 在任务列表页面点击任务的"编辑"按钮，或者点击任务名称进入详情页面后点击"编辑"按钮。

### Q: 任务可以同时运行多个实例吗？

A: 不可以，同一个任务同时只能有一个实例在运行。如果任务正在执行，再次点击"立即执行"会提示任务正在运行。

### Q: 如何备份所有任务配置？

A: 使用"导出任务"功能，选择所有任务并导出为JSON文件。建议定期备份以防数据丢失。

## 技术栈

- **后端框架**：Flask
- **任务调度**：APScheduler
- **前端框架**：Bootstrap 5
- **前端交互**：jQuery
- **图标库**：Font Awesome