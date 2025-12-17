"""酒店入住管理系统 - 自定义管理后台配置"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.contrib import messages


class CustomUserAdmin(BaseUserAdmin):
    """自定义用户管理后台"""
    
    def delete_model(self, request, obj):
        """删除单个用户前检查是否为当前登录用户"""
        if obj == request.user:
            messages.error(request, '无法删除自己的账户！请使用其他管理员账户进行操作。')
            return
        super().delete_model(request, obj)
        messages.success(request, f'用户 {obj.username} 已删除')
    
    def delete_queryset(self, request, queryset):
        """批量删除用户前检查是否包含当前登录用户"""
        if queryset.filter(id=request.user.id).exists():
            messages.error(request, '无法删除自己的账户！请从选择中移除当前登录用户。')
            return
        
        count = queryset.count()
        super().delete_queryset(request, queryset)
        messages.success(request, f'已成功删除 {count} 个用户')


# 注销并重新注册User模型以使用自定义管理类
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)