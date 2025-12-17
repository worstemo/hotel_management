"""
酒店入住管理系统 - Django配置文件

本文件包含项目的核心配置。
"""

# 导入模块
import os
from pathlib import Path
import socket


# 基础路径配置
BASE_DIR = Path(__file__).resolve().parent.parent


# 安全配置
SECRET_KEY = "django-insecure-%dhmv-tm%^_prz&mwv+3ge^v-uj4zcr5c9f86at5xkkf7i^uk9"

# 环境判断
IS_PRODUCTION = os.environ.get('DJANGO_ENV') == 'production'

# DEBUG模式开关
DEBUG = not IS_PRODUCTION

# 允许访问的主机列表
ALLOWED_HOSTS = [
    '117.72.39.127',      # 服务器公网IP
    'localhost',           # 本地开发
    '127.0.0.1',          # 本地开发
    '*',                   # 允许所有，开发方便
]


# 应用注册配置
INSTALLED_APPS = [
    'simpleui',  # SimpleUI管理后台美化插件
    "django.contrib.admin",  # Django管理后台
    "django.contrib.auth",  # Django认证系统
    "django.contrib.contenttypes",  # 内容类型框架
    "django.contrib.sessions",  # 会话框架
    "django.contrib.messages",  # 消息框架
    "django.contrib.staticfiles",  # 静态文件管理
    "rooms",  # 房间管理应用
    "customers",  # 客户管理应用
    "reservations",  # 预订管理应用
    "finance",  # 财务管理应用
    "employees",  # 员工管理应用
]


# 中间件配置
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",  # 安全相关中间件
    "django.contrib.sessions.middleware.SessionMiddleware",  # 会话处理中间件
    "django.middleware.common.CommonMiddleware",  # 通用中间件
    "django.middleware.csrf.CsrfViewMiddleware",  # CSRF保护中间件
    "django.contrib.auth.middleware.AuthenticationMiddleware",  # 认证中间件
    "django.contrib.messages.middleware.MessageMiddleware",  # 消息中间件
    "django.middleware.clickjacking.XFrameOptionsMiddleware",  # 点击劫持保护
]


# URL配置
ROOT_URLCONF = "hotel_management.urls"


# 模板配置
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",  # 使用Django模板引擎
    "DIRS": [os.path.join(BASE_DIR, 'templates')],  # 自定义模板目录
    "APP_DIRS": True,  # 允许在应用目录中查找模板
    "OPTIONS": {
        "context_processors": [  # 上下文处理器列表
            "django.template.context_processors.debug",  # 调试信息处理器
            "django.template.context_processors.request",  # 请求对象处理器
            "django.contrib.auth.context_processors.auth",  # 认证信息处理器
            "django.contrib.messages.context_processors.messages",  # 消息处理器
        ],
    },
}]


# WSGI配置
WSGI_APPLICATION = "hotel_management.wsgi.application"


# 数据库配置
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',  # 数据库引擎：MySQL
        'NAME': 'hotel_management_db',  # 数据库名称
        'USER': 'root',  # 数据库用户名
        'PASSWORD': 'Admin@123' if IS_PRODUCTION else 'admin',  # 服务器密码 / 本地密码
        'HOST': 'localhost',  # 数据库主机地址
        'PORT': '3306',  # 数据库端口
    }
}


# 密码验证配置
AUTH_PASSWORD_VALIDATORS = [
    # 检查密码与用户属性的相似度
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    # 检查密码最小长度
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    # 检查是否为常见密码
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    # 检查是否为纯数字密码
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# 国际化配置
LANGUAGE_CODE = 'zh-hans'  # 默认语言代码，使用简体中文
TIME_ZONE = 'Asia/Shanghai'  # 默认时区，使用上海时区
USE_I18N = True  # 是否启用国际化
USE_L10N = True  # 是否启用本地化


# 静态文件和媒体文件配置
STATIC_URL = '/static/'  # 静态文件的URL前缀
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]  # 额外的静态文件目录
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # 静态文件收集目录
MEDIA_URL = '/media/'  # 媒体文件的URL前缀
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  # 媒体文件的存储目录


# 其他Django配置
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"  # 默认的自动主键字段类型


# SimpleUI配置
SIMPLEUI_LOGO = '/static/img/logo.png'  # 后台左上角的Logo图片路径
SIMPLEUI_HOME_INFO = False  # 是否显示首页的系统信息
SIMPLEUI_ANALYSIS = False  # 是否开启统计分析功能
SIMPLEUI_DEFAULT_THEME = 'admin.lte.css'  # 默认主题
SIMPLEUI_HOME = True  # 是否显示首页
SIMPLEUI_HOME_QUICK = True  # 是否显示快捷操作卡片
SIMPLEUI_HOME_ACTION = True  # 是否显示操作历史

SIMPLEUI_CONFIG = {
    'system_keep': False,  # 不保留系统默认菜单
    'menu_display': ['酒店管理', '财务管理', '员工管理', '系统管理'],  # 菜单显示顺序
    'dynamic': False,  # 不使用动态菜单
    'menus': [  # 自定义菜单配置
        {
            # 酒店管理菜单组
            'app': 'auth',
            'name': '酒店管理',
            'icon': 'fas fa-user-shield',
            'models': [  # 子菜单列表
                {'name': '房间管理', 'icon': 'fa fa-th-list', 'url': 'rooms/room/'},
                {'name': '顾客管理', 'icon': 'fa fa-th-list', 'url': 'customers/customer/'},
                {'name': '预订管理', 'icon': 'fa fa-th-list', 'url': 'reservations/reservation/'}
            ]
        },
        {
            # 财务管理菜单组
            'name': '财务管理',
            'icon': 'fa fa-th-list',
            'models': [
                {'name': '收入管理', 'icon': 'fa fa-user', 'url': 'finance/income/'},
                {'name': '支出管理', 'icon': 'fa fa-user', 'url': 'finance/expense/'}
            ]
        },
        {
            # 员工管理菜单组
            'name': '员工管理',
            'icon': 'fa fa-th-list',
            'models': [
                {'name': '员工管理', 'icon': 'fa fa-user', 'url': 'employees/employee/'}
            ]
        },
        {
            # 系统管理菜单组
            'name': '系统管理',
            'icon': 'fa fa-th-list',
            'models': [
                {'name': '管理员管理', 'icon': 'fa fa-user', 'url': 'auth/user/'}
            ]
        },
    ]
}


# 登录配置
LOGIN_URL = 'admin_login'  # 登录页面的URL名称
LOGIN_REDIRECT_URL = 'admin:index'  # 登录成功后的跳转URL