"""
酒店入住管理系统URL配置
定义项目的所有URL路由映射关系
"""

from django.conf import settings  # 导入Django设置配置，用于读取settings.py中的配置项
from django.conf.urls.static import static  # 导入static函数，用于处理静态文件和媒体文件URL
from django.contrib import admin  # 导入Django的admin模块
from django.urls import path, include  # 导入path和include函数，用于定义URL路由
from django.views.generic import RedirectView  # 导入重定向视图，用于将一个URL重定向到另一个URL
from django.contrib.auth.views import LogoutView  # 导入Django内置的登出视图
from .views import CustomLoginView  # 从当前应用导入自定义的登录视图


# 定义URL路由列表
urlpatterns = [
    # 访问根目录时自动重定向到/admin/
    path('', RedirectView.as_view(url='/admin/', permanent=True)),  # permanent=True表示永久重定向（301）
    # 自定义的管理员登录页面URL
    path('admin/login/', CustomLoginView.as_view(), name='admin_login'),  # 使用自定义登录视图
    # 管理员登出URL，登出后跳转到登录页
    path('admin/logout/', LogoutView.as_view(next_page='admin_login'), name='admin_logout'),  # next_page指定登出后跳转的页面
    # Django管理后台URL
    path('admin/', admin.site.urls),  # 所有以admin/开头的URL都由Django Admin处理
]

# 如果当前为开发模式，添加媒体文件URL配置
if settings.DEBUG:  # 判断是否为调试模式
    # 将媒体文件URL路由添加到urlpatterns中
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # MEDIA_URL是URL前缀，MEDIA_ROOT是文件存储目录
