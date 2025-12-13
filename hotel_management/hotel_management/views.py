"""
酒店入住管理系统 - 自定义视图模块

本模块定义了系统的自定义视图，包括：
- 自定义登录视图（CustomLoginView）

该模块替代了Django Admin默认的登录页面，
提供更美观的用户界面和自定义的错误提示。
"""

# 导入Django认证相关的函数
# authenticate: 用于验证用户名和密码
# login: 用于将用户登录到会话中
from django.contrib.auth import authenticate, login

# 导入快捷函数
# render: 用于渲染模板并返回HTTP响应
# redirect: 用于重定向到其他URL
from django.shortcuts import render, redirect

# 导入基于类的视图基类
# View是Django所有基于类的视图的父类
from django.views import View


# ================================
# 自定义登录视图类
# ================================
class CustomLoginView(View):
    """
    自定义登录视图类 - 处理用户登录逻辑
    
    继承自Django的View类，实现GET和POST两种请求方式：
    - GET请求：显示登录页面
    - POST请求：处理登录表单提交
    
    属性:
        template_name: 登录页面使用的模板文件名
    
    业务流程:
        1. GET请求时，检查用户是否已登录，已登录则跳转到后台首页
        2. POST请求时，验证用户名和密码，验证成功则登录并跳转
        3. 验证失败则显示错误消息
    """
    
    # 登录页面模板文件名
    # 该模板文件位于templates/custom_login.html
    template_name = 'custom_login.html'

    def get(self, request):
        """
        处理GET请求 - 显示登录页面
        
        如果用户已经登录，则直接跳转到后台首页。
        否则渲染并显示登录页面。
        
        参数:
            request: HTTP请求对象，包含用户信息、请求数据等
        
        返回:
            HttpResponse: HTTP响应对象
                - 已登录：重定向到'admin:index'
                - 未登录：渲染登录页面
        """
        # 检查用户是否已认证（已登录）
        # request.user.is_authenticated返回True表示用户已登录
        if request.user.is_authenticated:
            # 已登录用户直接跳转到管理后台首页
            # 'admin:index'是Django Admin首页的URL名称
            return redirect('admin:index')
        
        # 未登录用户显示登录页面
        # render()函数将请求对象和模板结合，返回渲染后的HTML
        return render(request, self.template_name)

    def post(self, request):
        """
        处理POST请求 - 验证登录信息
        
        从请求中获取用户名和密码，进行身份验证。
        验证成功则登录并跳转，失败则显示错误消息。
        
        参数:
            request: HTTP请求对象，包含表单数据
                - request.POST.get('username'): 用户名
                - request.POST.get('password'): 密码
        
        返回:
            HttpResponse: HTTP响应对象
                - 登录成功：重定向到'admin:index'
                - 登录失败：渲染登录页面并显示错误消息
        """
        # 使用Django的authenticate函数验证用户
        # 该函数检查用户名和密码是否匹配数据库中的用户
        # request.POST.get()方法安全地获取表单数据，不存在时返回None
        user = authenticate(
            request,
            username=request.POST.get('username'),  # 从POST数据中获取用户名
            password=request.POST.get('password')   # 从POST数据中获取密码
        )
        
        # 检查验证结果
        # 如果验证成功，authenticate返回User对象
        # 如果验证失败，返回None
        if user is not None:
            # 验证成功：将用户登录到当前会话
            # login()函数在会话中记录用户信息，设置认证Cookie
            login(request, user)
            # 重定向到管理后台首页
            return redirect('admin:index')
        
        # 验证失败：重新渲染登录页面，并传递错误消息
        # 通过context字典传递错误消息到模板
        return render(
            request,
            self.template_name,
            {'error_message': '用户名或密码错误！'}  # 错误消息，模板中可通过{{ error_message }}显示
        )
