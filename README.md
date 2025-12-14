# 酒店入住管理系统

> 计算机科学与技术2班 第5组 - 软件工程 & Python 期末大作业

## 项目简介

酒店入住管理系统是一个基于 **Python Django 4.2** 框架开发的酒店后台管理系统，采用 **Django Admin + SimpleUI** 作为管理界面。系统专为中小型酒店设计，提供完整的酒店运营管理功能。

## 功能特性

### 核心功能模块

| 模块 | 功能说明 |
|------|----------|
| 🏨 房间管理 | 房间信息维护、状态管理、图片上传 |
| 👥 客户管理 | 客户档案录入与管理 |
| 📅 预订管理 | 预订创建、入住办理、退房办理、退订处理 |
| 💰 财务管理 | 收入支出记录、自动财务联动 |
| 👔 员工管理 | 员工信息与工资管理 |

### 系统亮点

- **业务自动化**: 预订创建时自动计算金额、自动记录收入、自动同步房间状态
- **智能退款**: 退订时自动创建全额退款记录
- **删除保护**: 有活跃订单的房间/客户无法删除
- **数据校验**: 日期冲突检测、人数容量校验、金额非负验证
- **批量操作**: 支持批量入住、批量退房、批量退订

## 技术栈

| 组件 | 版本/说明 |
|------|-----------|
| Python | 3.9+ |
| Django | 4.2 |
| MySQL | 8.0+ |
| django-simpleui | Admin界面美化 |
| Pillow | 图片处理 |
| PyMySQL/mysqlclient | MySQL驱动 |

## 项目结构

```
酒店入住管理系统/
├── hotel_management/           # Django项目目录
│   ├── manage.py               # Django管理脚本
│   ├── requirements.txt        # 依赖包列表
│   ├── hotel_management/       # 项目配置
│   │   ├── settings.py         # 全局配置
│   │   ├── urls.py             # URL路由
│   │   └── views.py            # 自定义视图
│   ├── rooms/                  # 房间管理应用
│   ├── customers/              # 客户管理应用
│   ├── reservations/           # 预订管理应用（核心）
│   ├── finance/                # 财务管理应用
│   ├── employees/              # 员工管理应用
│   └── templates/              # 模板目录
├── hotel_management_db.sql     # 数据库初始化脚本
├── 项目介绍文档.md                # 项目详细介绍
├── 项目运行文档.md                # 运行环境配置指南
├── 酒店入住管理系统开发文档.md    # 技术开发文档
├── 酒店入住管理系统项目分工表.md  # 团队分工说明
└── 服务器部署文档.md             # 生产环境部署指南
```

## 快速开始

### 1. 环境准备

确保已安装：
- Python 3.9+
- MySQL 8.0+

### 2. 安装依赖

```bash
cd hotel_management
pip install -r requirements.txt
```

### 3. 配置数据库

修改 `hotel_management/settings.py` 中的数据库配置：

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'hotel_management_db',
        'USER': 'root',
        'PASSWORD': '你的数据库密码',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

### 4. 创建数据库

```bash
mysql -u root -p -e "CREATE DATABASE hotel_management_db CHARACTER SET utf8mb4;"
```

或直接导入提供的SQL文件：

```bash
mysql -u root -p < hotel_management_db.sql
```

### 5. 执行数据库迁移

```bash
python manage.py migrate
```

### 6. 创建管理员账户

```bash
python manage.py createsuperuser
```

### 7. 启动开发服务器

```bash
python manage.py runserver
```

### 8. 访问系统

打开浏览器访问：http://127.0.0.1:8000/admin/

## 系统截图

系统采用 SimpleUI 主题，提供现代化的管理界面，包含：
- 酒店管理（房间、顾客、预订）
- 财务管理（收入、支出）
- 员工管理
- 系统管理

## 业务流程

### 预订入住流程

```
添加客户 → 创建预订 → 办理入住 → 办理退房
              ↓
        系统自动：
        • 计算金额
        • 更新房间状态
        • 创建收入记录
```

### 退订流程

```
预订状态改为「已退订」
        ↓
   系统自动：
   • 创建全额退款记录
   • 更新房间状态为「空闲」
```

## 相关文档

- [项目介绍文档](项目介绍文档.md) - 功能模块详解
- [项目运行文档](项目运行文档.md) - 环境配置指南
- [酒店入住管理系统开发文档](酒店入住管理系统开发文档.md) - 技术实现详解
- [服务器部署文档](服务器部署文档.md) - 生产环境部署

## 团队成员

**计算机科学与技术2班 第5组**

详见 [酒店入住管理系统项目分工表](酒店入住管理系统项目分工表.md)

## 许可证

本项目为课程作业，仅供学习交流使用。
