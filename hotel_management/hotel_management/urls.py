"""
酒店入住管理系统URL配置
定义项目的所有URL路由映射关系

【什么是URL路由？】
URL路由就是把用户访问的网址（URL）对应到具体的处理程序（视图）

举例：
  用户访问 http://localhost:8000/admin/
  Django会根据这个文件的配置，找到对应的处理程序

【URL匹配流程】
用户请求URL → Django从上到下匹配urlpatterns → 找到匹配项 → 执行对应的视图

【本项目的URL结构】
 http://localhost:8000/           → 自动跳转到 /admin/
 http://localhost:8000/admin/      → Django Admin 后台首页
 http://localhost:8000/admin/login/ → 自定义登录页面
 http://localhost:8000/admin/logout/→ 登出，返回登录页
"""

# ================================================================
# 导入模块
# ================================================================

# 导入Django设置配置，用于读取settings.py中的配置项
# 例如：settings.DEBUG（是否调试模式）、settings.MEDIA_URL（媒体文件URL前缀）
from django.conf import settings

# 导入static函数，用于在开发模式下处理媒体文件（如房间图片）的URL
# 生产环境中，媒体文件由Nginx等Web服务器处理，不需要这个
from django.conf.urls.static import static

# 导入Django的admin模块，提供后台管理功能
# admin.site.urls 包含了所有Admin后台的URL路由
from django.contrib import admin

# path: 定义单个URL路由的函数
# include: 用于引入其他应用的URL配置（本项目未使用）
from django.urls import path, include

# RedirectView: Django内置的重定向视图
# 用于将一个URL自动跳转到另一个URL
from django.views.generic import RedirectView

# LogoutView: Django内置的登出视图
# 处理用户点击"退出登录"按钮的逻辑
from django.contrib.auth.views import LogoutView

# 从当前目录的views.py导入自定义的登录视图
# . 表示当前目录（hotel_management/）
from .views import CustomLoginView


# ================================================================
# URL路由配置列表
# ================================================================
#
# 【path() 函数的参数说明】
# path(路由规则, 视图, name=路由名称)
#   - 路由规则: URL的匹配模式（如 'admin/'）
#   - 视图: 匹配成功后执行的视图函数或类
#   - name: 路由的名称，用于在代码中反向引用URL
#
# 【.as_view() 方法】
# 类视图（Class-Based View）需要调用 as_view() 转换为可调用的视图函数
# 因为Django的URL路由期望的是一个函数，而不是类
#
urlpatterns = [
    # ----------------------------------------------------------
    # 路由1: 根目录重定向
    # ----------------------------------------------------------
    # 当用户访问 http://localhost:8000/ 时
    # 自动跳转到 http://localhost:8000/admin/
    #
    # 为什么需要这个？
    # 因为本项目使用Django Admin作为主界面，用户直接访问根目录应该进入后台
    #
    # permanent=True 表示永久重定向（HTTP 301）
    #   - 301: 永久重定向，浏览器会缓存这个跳转
    #   - 302: 临时重定向，浏览器不会缓存
    path('', RedirectView.as_view(url='/admin/', permanent=True)),
    
    # ----------------------------------------------------------
    # 路由2: 自定义登录页面
    # ----------------------------------------------------------
    # 当用户访问 http://localhost:8000/admin/login/ 时
    # 使用我们自定义的登录视图（CustomLoginView）
    #
    # 为什么要自定义？
    # Django Admin默认的登录页面比较简陋
    # 自定义登录视图可以：
    #   - 使用更美观的登录界面（SimpleUI风格）
    #   - 添加验证码、记住我等功能
    #   - 自定义登录逻辑
    #
    # name='admin_login' 给这个路由起名字
    # 在代码或模板中可以用 {% url 'admin_login' %} 获取这个URL
    path('admin/login/', CustomLoginView.as_view(), name='admin_login'),
    
    # ----------------------------------------------------------
    # 路由3: 登出页面
    # ----------------------------------------------------------
    # 当用户点击"退出登录"时访问此URL
    # 使用Django内置的LogoutView处理登出逻辑
    #
    # next_page='admin_login' 指定登出后跳转到哪个页面
    # 这里使用路由名称（不是URL），Django会自动解析为 /admin/login/
    path('admin/logout/', LogoutView.as_view(next_page='admin_login'), name='admin_logout'),
    
    # ----------------------------------------------------------
    # 路由4: Django Admin后台（核心路由）
    # ----------------------------------------------------------
    # 这是Django Admin的核心路由
    # 所有以 admin/ 开头的URL都会交给 admin.site.urls 处理
    #
    # 例如：
    #   /admin/                    → 后台首页
    #   /admin/reservations/       → 预订管理列表
    #   /admin/rooms/room/         → 房间管理列表
    #   /admin/customers/customer/ → 客户管理列表
    #
    # 这些子路由是Django Admin根据注册的Model自动生成的
    path('admin/', admin.site.urls),
]

# ================================================================
# 开发模式下的媒体文件配置
# ================================================================
#
# 【什么是媒体文件？】
# 媒体文件是用户上传的文件，如房间图片
# 存储在 MEDIA_ROOT 目录下（settings.py中配置）
#
# 【为什么需要这个配置？】
# 在开发模式下，Django的开发服务器（runserver）需要知道如何处理媒体文件URL
# 这个配置告诉Django：
#   当URL以 /media/ 开头时，去 MEDIA_ROOT 目录找对应的文件
#
# 【生产环境怎么办？】
# 生产环境中，DEBUG=False，这段代码不会执行
# 媒体文件由Nginx等Web服务器直接处理，性能更好
#
if settings.DEBUG:  # 只在调试模式（开发环境）下执行
    # static() 函数返回一个URL路由
    # MEDIA_URL = '/media/'（URL前缀）
    # MEDIA_ROOT = BASE_DIR / 'media'（文件存储目录）
    #
    # 效果：访问 /media/rooms/101.jpg 会返回 media/rooms/101.jpg 文件
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
