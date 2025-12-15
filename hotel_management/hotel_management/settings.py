"""
酒店入住管理系统 - Django配置文件

本文件包含项目的所有核心配置，包括：
- 数据库连接配置
- 应用注册
- 中间件配置
- 静态文件和媒体文件配置
- SimpleUI管理后台美化配置
- 国际化和时区配置
"""

# 导入操作系统模块，用于文件路径操作
import os
# 导入pathlib模块，用于跨平台路径处理
from pathlib import Path
# 导入socket模块，用于获取主机名判断运行环境
import socket


# ================================
# 基础路径配置
# ================================
# BASE_DIR: 项目的根目录路径
# __file__ 表示当前文件(settings.py)的路径
# .resolve() 解析为绝对路径
# .parent 获取父目录，两次.parent回到项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent


# ================================
# 安全配置
# ================================
# SECRET_KEY: Django的密钥，用于加密签名、会话等
# 生产环境中应该使用环境变量来存储，不要硬编码
SECRET_KEY = "django-insecure-%dhmv-tm%^_prz&mwv+3ge^v-uj4zcr5c9f86at5xkkf7i^uk9"

# ================================
# 环境判断
# ================================
# 通过环境变量 DJANGO_ENV 判断当前运行环境
# 服务器上设置 DJANGO_ENV=production
# 本地开发时不设置或设置为 development
IS_PRODUCTION = os.environ.get('DJANGO_ENV') == 'production'

# DEBUG: 调试模式开关
# 本地开发时 DEBUG=True，显示详细错误信息
# 服务器上 DEBUG=False，隐藏详细错误信息
DEBUG = not IS_PRODUCTION

# ALLOWED_HOSTS: 允许访问的主机列表
# 同时包含本地和服务器地址，两边都能正常运行
ALLOWED_HOSTS = [
    '117.72.39.127',      # 服务器公网IP
    'localhost',           # 本地开发
    '127.0.0.1',          # 本地开发
    '*',                   # 允许所有，开发方便，生产环境需要删除
]
''

# ================================
# 应用注册配置
# ================================
# INSTALLED_APPS: 已安装的应用列表
# 顺序很重要，SimpleUI必须在django.contrib.admin之前
INSTALLED_APPS = [
    'simpleui',  # SimpleUI管理后台美化插件（必须在admin之前）
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


# ================================
# 中间件配置
# ================================
# MIDDLEWARE: 中间件列表，处理请求和响应的钩子
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",  # 安全相关的中间件
    "django.contrib.sessions.middleware.SessionMiddleware",  # 会话处理中间件
    "django.middleware.common.CommonMiddleware",  # 通用中间件（如URL重写）
    "django.middleware.csrf.CsrfViewMiddleware",  # CSRF保护中间件
    "django.contrib.auth.middleware.AuthenticationMiddleware",  # 认证中间件
    "django.contrib.messages.middleware.MessageMiddleware",  # 消息中间件
    "django.middleware.clickjacking.XFrameOptionsMiddleware",  # 点击劫持保护
]


# ================================
# URL配置
# ================================
# ROOT_URLCONF: 根URL配置模块的路径
ROOT_URLCONF = "hotel_management.urls"


# ================================
# 模板配置
# ================================
# TEMPLATES: 模板引擎配置列表
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


# ================================
# WSGI配置
# ================================
# WSGI_APPLICATION: WSGI应用的路径
WSGI_APPLICATION = "hotel_management.wsgi.application"


# ================================
# 数据库配置
# ================================
# DATABASES: 数据库连接配置字典
# 根据运行环境自动选择不同的数据库密码
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


# ================================
# 密码验证配置
# ================================
# AUTH_PASSWORD_VALIDATORS: 密码验证器列表
AUTH_PASSWORD_VALIDATORS = [
    # 检查密码与用户属性的相似度
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    # 检查密码最小长度（默认8位）
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    # 检查是否为常见密码
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    # 检查是否为纯数字密码
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ================================
# 国际化配置
# ================================
# LANGUAGE_CODE: 默认语言代码，使用简体中文
LANGUAGE_CODE = 'zh-hans'

# TIME_ZONE: 默认时区，使用上海时区（东八区）
TIME_ZONE = 'Asia/Shanghai'

# USE_I18N: 是否启用国际化（翻译功能）
USE_I18N = True

# USE_L10N: 是否启用本地化（日期/数字格式）
USE_L10N = True


# ================================
# 静态文件和媒体文件配置
# ================================
# STATIC_URL: 静态文件的URL前缀
STATIC_URL = '/static/'

# STATICFILES_DIRS: 额外的静态文件目录
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# STATIC_ROOT: 静态文件收集目录（生产环境使用）
# 执行 python manage.py collectstatic 时，静态文件会被复制到这个目录
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# MEDIA_URL: 媒体文件（用户上传）的URL前缀
MEDIA_URL = '/media/'

# MEDIA_ROOT: 媒体文件的存储目录
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# ================================
# 其他Django配置
# ================================
# DEFAULT_AUTO_FIELD: 默认的自动主键字段类型
# BigAutoField支持更大的ID范围
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ================================
# SimpleUI配置
# ================================
# SimpleUI是一个Django Admin后台美化插件
# 官方文档: https://simpleui.72wo.com/docs/simpleui/

# SIMPLEUI_LOGO: 后台左上角的Logo图片路径
SIMPLEUI_LOGO = '/static/img/logo.png'

# SIMPLEUI_HOME_INFO: 是否显示首页的系统信息
SIMPLEUI_HOME_INFO = False

# SIMPLEUI_ANALYSIS: 是否开启统计分析功能
SIMPLEUI_ANALYSIS = False

# SIMPLEUI_DEFAULT_THEME: 默认主题
# admin.lte.css是AdminLTE风格的主题
SIMPLEUI_DEFAULT_THEME = 'admin.lte.css'

# SIMPLEUI_HOME: 是否显示首页
SIMPLEUI_HOME = True

# SIMPLEUI_HOME_QUICK: 是否显示快捷操作卡片
SIMPLEUI_HOME_QUICK = True

# SIMPLEUI_HOME_ACTION: 是否显示操作历史
SIMPLEUI_HOME_ACTION = True

# SIMPLEUI_CONFIG: 自定义菜单配置
SIMPLEUI_CONFIG = {
    'system_keep': False,  # 不保留系统默认菜单
    'menu_display': ['酒店管理', '财务管理', '员工管理', '系统管理'],  # 菜单显示顺序
    'dynamic': False,  # 不使用动态菜单
    'menus': [  # 自定义菜单配置
        {
            # 酒店管理菜单组
            'app': 'auth',  # 关联的应用
            'name': '酒店管理',  # 菜单名称
            'icon': 'fas fa-user-shield',  # 菜单图标（Font Awesome）
            'models': [  # 子菜单列表
                {'name': '房间管理', 'icon': 'fa fa-th-list', 'url': 'rooms/room/'},
                {'name': '顾客管理', 'icon': 'fa fa-th-list', 'url': 'customers/customer/'},
                {'name': '预定管理', 'icon': 'fa fa-th-list', 'url': 'reservations/reservation/'}
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


# ================================
# 登录配置
# ================================
# LOGIN_URL: 登录页面的URL名称
LOGIN_URL = 'admin_login'

# LOGIN_REDIRECT_URL: 登录成功后的跳转URL
LOGIN_REDIRECT_URL = 'admin:index'
