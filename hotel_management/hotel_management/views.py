"""
酒店入住管理系统 - 自定义视图模块

本模块定义了系统的自定义视图，包括：
- 自定义登录视图（CustomLoginView）
"""

from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.views import View


class CustomLoginView(View):
    """
    自定义登录视图类 - 处理用户登录逻辑
    """
    
    template_name = 'custom_login.html'

    def get(self, request):
        """
        处理GET请求 - 显示登录页面
        """
        if request.user.is_authenticated:
            return redirect('admin:index')
        
        return render(request, self.template_name)

    def post(self, request):
        """
        处理POST请求 - 验证登录信息
        """
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password')
        )
        
        if user is not None:
            login(request, user)
            return redirect('admin:index')
        
        return render(
            request,
            self.template_name,
            {'error_message': '用户名或密码错误！'}
        )
