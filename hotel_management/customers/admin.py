"""
客户管理Admin配置模块

本模块配置Django Admin后台的客户管理界面。
包含客户表单验证、列表显示、删除保护等功能。
"""

# 导入Django Admin模块，用于注册和配置后台管理界面
from django.contrib import admin
# 导入format_html函数，用于在Admin列表中安全地渲染HTML内容
from django.utils.html import format_html
# 导入messages模块，用于在Admin后台显示操作结果消息
from django.contrib import messages
# 导入验证错误异常类，用于在表单验证失败时抛出异常
from django.core.exceptions import ValidationError
# 导入Django表单模块，用于创建自定义表单
from django import forms
# 导入Customer模型，用于在Admin中管理客户数据
from customers.models import Customer


# ================================
# 客户管理表单类定义
# ================================
class CustomerAdminForm(forms.ModelForm):
    """
    客户管理表单类 - 用于验证客户信息的修改操作
    
    继承自Django的ModelForm类，自动根据Customer模型生成表单字段。
    重写clean方法添加业务逻辑验证：已入住客户不允许修改信息。
    """
    
    class Meta:
        """
        表单的元数据配置
        
        属性:
            model: 指定关联的模型为Customer
            fields: '__all__'表示包含模型的所有字段
        """
        model = Customer  # 关联的数据模型
        fields = '__all__'  # 包含所有字段

    def clean(self):
        """
        表单整体验证方法
        
        在所有字段验证完成后调用，用于执行跨字段的业务逻辑验证。
        
        业务规则:
            - 如果客户存在已入住的订单，则不允许修改客户信息
            - 这是为了保证入住期间数据的一致性
        
        返回:
            dict: 验证后的清洗数据
        
        异常:
            ValidationError: 当客户存在已入住订单时抛出
        """
        # 调用父类的clean方法，获取验证后的数据
        cleaned_data = super().clean()
        
        # 检查是否为编辑操作（而非新建）
        # self.instance.pk存在表示该对象已经存在于数据库中
        if self.instance.pk:
            # 延迟导入Reservation模型，避免循环导入问题
            from reservations.models import Reservation
            
            # 查询该客户的所有已入住订单
            checkedin = Reservation.objects.filter(
                customer=self.instance,  # 筛选当前客户
                status='CheckedIn'  # 状态为已入住
            )
            
            # 如果存在已入住订单，则不允许修改
            if checkedin.exists():
                # 抛出验证错误，阻止表单提交
                raise ValidationError(
                    f'该客户存在{checkedin.count()}个已入住订单，无法修改客户信息！请先办理离店。'
                )
        
        # 返回验证后的数据
        return cleaned_data


# ================================
# 客户Admin配置类
# ================================
# 使用@admin.register装饰器将CustomerAdmin注册到Admin后台
# 这是一种简洁的注册方式，等价于 admin.site.register(Customer, CustomerAdmin)
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """
    客户Admin配置类 - 定义Admin后台的客户管理界面
    
    功能包括:
        - 自定义列表显示字段
        - 删除保护机制（有活跃订单的客户不能删除）
        - 自定义批量操作
        - 字段分组显示
    """
    
    # 指定使用自定义的表单类
    form = CustomerAdminForm
    
    # list_display: 定义列表页面显示的字段
    # 可以是模型字段名称，也可以是自定义方法名称
    list_display = ('name', 'id_number', 'phone', 'email_display', 'address')
    
    # ordering: 定义列表页面的默认排序方式
    # '-name'表示按姓名降序排列，去掉负号则为升序
    ordering = ('-name',)
    
    # list_display_links: 定义哪些字段可以点击进入编辑页面
    list_display_links = ('name', 'id_number')
    
    # list_per_page: 定义每页显示的记录数量
    list_per_page = 20
    
    # search_fields: 定义可搜索的字段
    # 用户可以通过姓名、身份证号、电话搜索客户
    search_fields = ['name', 'id_number', 'phone']
    
    # list_filter: 定义右侧过滤器的字段
    list_filter = ('name',)
    
    # actions: 定义可用的批量操作
    actions = ['safe_delete_selected']
    
    # fieldsets: 定义编辑页面的字段分组布局
    # 每个元组包含：（组名称，{配置字典}）
    # None表示没有组名称（默认组）
    fieldsets = (
        (None, {'fields': ('name', 'id_number', 'phone')}),  # 基本信息组
        ('详细信息', {'fields': ('email', 'address')})  # 详细信息组
    )

    def get_actions(self, request):
        """
        重写获取操作列表的方法
        
        移除Django默认的'delete_selected'操作，
        替换为带有安全检查的自定义删除操作。
        
        参数:
            request: HTTP请求对象
        
        返回:
            dict: 可用的操作字典
        """
        # 调用父类方法获取默认操作列表
        actions = super().get_actions(request)
        
        # 移除Django默认的删除操作（不带安全检查）
        if 'delete_selected' in actions:
            del actions['delete_selected']
        
        # 返回修改后的操作列表
        return actions

    def email_display(self, obj):
        """
        自定义邮箱显示方法
        
        用于在列表页面以蓝色样式显示邮箱地址。
        如果邮箱为空，则显示'-'。
        
        参数:
            obj (Customer): 客户对象实例
        
        返回:
            str: HTML格式的邮箱字符串或'-'
        """
        # 如果邮箱存在，使用format_html渲染蓝色样式
        # format_html会自动转义特殊字符，防止XSS攻击
        if obj.email:
            return format_html('<span style="color:#007bff;">{}</span>', obj.email)
        # 如果邮箱为空，返回'-'
        return '-'
    
    # 设置列的显示名称
    email_display.short_description = '邮箱'
    # 设置点击列标题时的排序字段
    email_display.admin_order_field = 'email'

    def delete_model(self, request, obj):
        """
        重写单个对象删除方法
        
        在删除客户前检查是否存在活跃订单。
        如果存在已预定或已入住的订单，则拒绝删除。
        
        参数:
            request: HTTP请求对象
            obj (Customer): 要删除的客户对象
        """
        # 延迟导入Reservation模型
        from reservations.models import Reservation
        
        # 查询该客户的活跃订单（已预定或已入住）
        active = Reservation.objects.filter(
            customer=obj,  # 筛选当前客户
            status__in=['Booked', 'CheckedIn']  # 状态为已预定或已入住
        )
        
        # 如果存在活跃订单，显示错误消息并返回
        if active.exists():
            messages.error(
                request, 
                f'无法删除客户「{obj.name}」，存在{active.count()}个活跃订单！'
            )
            return  # 不执行删除操作
        
        # 调用父类方法执行实际删除
        super().delete_model(request, obj)
        # 显示成功消息
        messages.success(request, f'客户 {obj.name} 已删除')

    @admin.action(description='删除所选的 客户')
    def safe_delete_selected(self, request, queryset):
        """
        安全批量删除客户的操作方法
        
        在删除前检查所有选中的客户是否存在活跃订单。
        如果任何一个客户有活跃订单，则取消整个操作。
        
        装饰器说明:
            @admin.action(description='...')设置操作在Admin界面的显示名称
        
        参数:
            request: HTTP请求对象
            queryset: 选中的客户查询集
        """
        # 延迟导入Reservation模型
        from reservations.models import Reservation
        
        # 遍历选中的客户，找出有活跃订单的客户名称
        # 使用列表推导式进行筛选
        blocked = [
            c.name  # 提取客户姓名
            for c in queryset  # 遍历所有选中的客户
            if Reservation.objects.filter(  # 检查是否存在活跃订单
                customer=c, 
                status__in=['Booked', 'CheckedIn']
            ).exists()
        ]
        
        # 如果存在被阻止删除的客户，显示错误消息并返回
        if blocked:
            messages.error(
                request, 
                f'操作已取消！以下客户存在活跃订单：{", ".join(blocked)}'
            )
            return  # 不执行删除操作
        
        # 记录要删除的客户数量
        count = queryset.count()
        
        # 遍历并删除每个客户
        for c in queryset:
            c.delete()  # 调用对象的delete方法
        
        # 显示成功消息
        messages.success(request, f'已成功删除 {count} 个客户')
