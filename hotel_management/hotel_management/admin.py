"""
酒店入住管理系统 - 自定义管理后台配置
包含自定义的用户管理，防止管理员删除自己
"""

from django.contrib import admin  # 从Django导入admin模块，用于管理后台功能
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin  # 导入Django内置的UserAdmin，并重命名为BaseUserAdmin
from django.contrib.auth.models import User  # 导入Django内置的User模型
from django.contrib import messages  # 导入消息框架，用于显示提示信息


# ========== 自定义用户管理后台 ==========
class CustomUserAdmin(BaseUserAdmin):  # 定义自定义用户管理类，继承自BaseUserAdmin
    """
    自定义用户管理后台
    继承Django内置的UserAdmin，添加删除保护逻辑
    防止管理员删除自己的账户
    """
    
    def delete_model(self, request, obj):
        """删除单个用户前检查是否为当前登录用户"""
        # 判断要删除的用户是否为当前登录的用户
        if obj == request.user:
            # 如果是自己，显示错误消息并直接返回，不执行删除
            messages.error(request, '无法删除自己的账户！请使用其他管理员账户进行操作。')
            return  # 直接返回，不执行后续代码
        # 如果不是自己，调用父类的delete_model方法执行删除
        super().delete_model(request, obj)
        # 显示成功消息
        messages.success(request, f'用户 {obj.username} 已删除')
    
    def delete_queryset(self, request, queryset):
        """批量删除用户前检查是否包含当前登录用户"""
        # 检查待删除的用户集合中是否包含当前登录用户
        if queryset.filter(id=request.user.id).exists():
            # 如果包含当前用户，显示错误消息并直接返回
            messages.error(request, '无法删除自己的账户！请从选择中移除当前登录用户。')
            return  # 直接返回，不执行后续代码
        
        # 获取待删除的用户数量
        count = queryset.count()
        # 调用父类的delete_queryset方法执行批量删除
        super().delete_queryset(request, queryset)
        # 显示成功消息
        messages.success(request, f'已成功删除 {count} 个用户')


# ========== 注册自定义用户管理 ==========
# 先注销Django默认的User管理
admin.site.unregister(User)  # 从Django Admin中移除默认的User模型管理
# 注册自定义的User管理
admin.site.register(User, CustomUserAdmin)  # 使用自定义的CustomUserAdmin管理User模型
