"""
酒店入住管理系统URL配置
定义项目的所有URL路由映射关系
"""

# 导入模块
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView
from django.contrib.auth.views import LogoutView
from .views import CustomLoginView


urlpatterns = [
    # 根目录重定向到/admin/
    path('', RedirectView.as_view(url='/admin/', permanent=True)),
    
    # 自定义登录页面
    path('admin/login/', CustomLoginView.as_view(), name='admin_login'),
    
    # 登出页面
    path('admin/logout/', LogoutView.as_view(next_page='admin_login'), name='admin_logout'),
    
    # Django Admin后台
    path('admin/', admin.site.urls),
]

# 开发模式下的媒体文件配置
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
