"""
财务管理Admin配置模块

本模块配置Django Admin后台的收入和支出管理界面。
包含彩色标签显示、总额统计、自定义列表显示等功能。
"""

# 导入Django Admin模块，用于注册和配置后台管理界面
from django.contrib import admin
# 导入format_html函数，用于在Admin列表中安全地渲染HTML内容
from django.utils.html import format_html
# 导入Sum聚合函数，用于计算总收入/总支出
from django.db.models import Sum
# 导入Income和Expense模型，用于在Admin中管理财务数据
from finance.models import Income, Expense


# ================================
# 收入Admin配置类
# ================================
# 使用@admin.register装饰器将IncomeAdmin注册到Admin后台
@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    """
    收入Admin配置类 - 支持总收入统计和彩色标签
    
    功能包括:
        - 自定义列表显示（绿色金额、彩色来源标签）
        - 列表页面显示总收入统计
        - 搜索和过滤功能
        - 字段分组布局
    """
    
    # list_display: 定义列表页面显示的字段
    list_display = (
        'date',              # 日期
        'amount_display',    # 自定义金额显示（绿色样式）
        'source_display',    # 自定义来源显示（彩色标签）
        'short_description'  # 自定义短描述（截断过长文本）
    )
    
    # ordering: 定义列表页面的默认排序方式
    # '-date'表示按日期降序排列（最新的在前面）
    ordering = ('-date',)
    
    # list_display_links: 定义哪些字段可以点击进入编辑页面
    list_display_links = ('date',)
    
    # list_per_page: 定义每页显示的记录数量
    list_per_page = 20
    
    # search_fields: 定义可搜索的字段
    search_fields = ['date', 'source', 'description']
    
    # list_filter: 定义右侧过滤器的字段
    list_filter = ('source', 'date')
    
    # fieldsets: 定义编辑页面的字段分组布局
    fieldsets = (
        ('收入详情', {'fields': ('date', 'amount', 'source', 'description')}),
    )

    def amount_display(self, obj):
        """
        自定义金额显示方法
        
        用于在列表页面以绿色粗体样式显示收入金额。
        
        参数:
            obj (Income): 收入对象实例
        
        返回:
            str: HTML格式的金额字符串
        """
        # 使用format_html渲染带样式的金额显示
        # style属性: color绿色（#28a745）、font-weight粗体、font-size14像素
        return format_html(
            '<span style="color:#28a745;font-weight:bold;font-size:14px;">￥{}</span>',
            obj.amount
        )
    
    # 设置列的显示名称
    amount_display.short_description = '金额'
    # 设置点击列标题时的排序字段
    amount_display.admin_order_field = 'amount'

    def source_display(self, obj):
        """
        自定义来源彩色显示方法
        
        用于在列表页面以不同颜色的标签显示收入来源。
        
        颜色对应关系:
            - Room(客房收入): 蓝色 #007bff
            - Food(餐饮收入): 绿色 #28a745
            - Other(其他收入): 灰色 #6c757d
        
        参数:
            obj (Income): 收入对象实例
        
        返回:
            str: HTML格式的来源标签
        """
        # 定义来源对应的颜色字典
        colors = {
            'Room': '#007bff',   # 客房收入 - 蓝色
            'Food': '#28a745',   # 餐饮收入 - 绿色
            'Other': '#6c757d'   # 其他收入 - 灰色
        }
        
        # 使用format_html渲染彩色标签
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;border-radius:3px;font-weight:bold;">{}</span>',
            colors.get(obj.source, '#000'),  # 获取对应颜色，默认黑色
            dict(obj.INCOME_SOURCES).get(obj.source, obj.source)  # 获取中文来源名称
        )
    
    # 设置列的显示名称
    source_display.short_description = '来源'

    def short_description(self, obj):
        """
        自定义短描述显示方法
        
        用于在列表页面显示截断的描述文本。
        如果描述超过50个字符，则截断并添加...
        
        参数:
            obj (Income): 收入对象实例
        
        返回:
            str: 截断后的描述文本
        """
        # 如果描述长度超过50个字符，截断并添加省略号
        if len(obj.description) > 50:
            return obj.description[:50] + '...'
        # 否则返回完整描述
        return obj.description
    
    # 设置列的显示名称
    short_description.short_description = '描述'

    def changelist_view(self, request, extra_context=None):
        """
        重写列表页面视图方法
        
        在列表页面添加总收入统计信息。
        
        参数:
            request: HTTP请求对象
            extra_context: 额外的模板上下文数据
        
        返回:
            HttpResponse: 列表页面的HTTP响应
        """
        # 使用aggregate()和Sum()计算所有收入的总和
        # aggregate()返回一个字典，Sum('amount')计算amount字段的总和
        total = Income.objects.aggregate(total=Sum('amount'))['total'] or 0
        
        # 初始化或更新extra_context字典
        extra_context = extra_context or {}
        # 添加总收入到上下文中，供模板使用
        extra_context['total_income'] = total
        
        # 调用父类的changelist_view方法
        return super().changelist_view(request, extra_context=extra_context)

    def save_model(self, request, obj, form, change):
        """
        重写模型保存方法
        
        在保存前执行模型的完整验证。
        
        参数:
            request: HTTP请求对象
            obj (Income): 要保存的收入对象
            form: 表单实例
            change (bool): True表示修改，False表示新建
        """
        # 调用模型的full_clean方法，执行所有验证
        obj.full_clean()
        # 调用父类的save_model方法完成保存
        super().save_model(request, obj, form, change)


# ================================
# 支出Admin配置类
# ================================
# 使用@admin.register装饰器将ExpenseAdmin注册到Admin后台
@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    """
    支出Admin配置类 - 支持总支出统计和彩色标签
    
    功能包括:
        - 自定义列表显示（红色金额、彩色类别标签）
        - 列表页面显示总支出统计
        - 搜索功能
        - 字段分组布局
    """
    
    # list_display: 定义列表页面显示的字段
    list_display = (
        'date',              # 日期
        'amount_display',    # 自定义金额显示（红色样式）
        'category_display',  # 自定义类别显示（彩色标签）
        'description'        # 描述
    )
    
    # ordering: 定义列表页面的默认排序方式
    # '-date'表示按日期降序排列（最新的在前面）
    ordering = ('-date',)
    
    # list_display_links: 定义哪些字段可以点击进入编辑页面
    list_display_links = ('date',)
    
    # list_per_page: 定义每页显示的记录数量
    list_per_page = 20
    
    # search_fields: 定义可搜索的字段
    search_fields = ['date', 'category']
    
    # fieldsets: 定义编辑页面的字段分组布局
    fieldsets = (
        ('支出详情', {'fields': ('date', 'amount', 'category', 'description')}),
    )

    def amount_display(self, obj):
        """
        自定义金额显示方法
        
        用于在列表页面以红色粗体样式显示支出金额。
        红色表示支出，与收入的绿色形成对比。
        
        参数:
            obj (Expense): 支出对象实例
        
        返回:
            str: HTML格式的金额字符串
        """
        # 使用format_html渲染带样式的金额显示
        # style属性: color红色（#dc3545）、font-weight粗体、font-size14像素
        return format_html(
            '<span style="color:#dc3545;font-weight:bold;font-size:14px;">￥{}</span>',
            obj.amount
        )
    
    # 设置列的显示名称
    amount_display.short_description = '金额'
    # 设置点击列标题时的排序字段
    amount_display.admin_order_field = 'amount'

    def category_display(self, obj):
        """
        自定义类别彩色显示方法
        
        用于在列表页面以不同颜色的标签显示支出类别。
        
        颜色对应关系:
            - Salary(员工工资): 黄色 #ffc107
            - Maintenance(维修费用): 红色 #dc3545
            - Utilities(水电费): 青色 #17a2b8
            - Other(其他支出): 灰色 #6c757d
        
        参数:
            obj (Expense): 支出对象实例
        
        返回:
            str: HTML格式的类别标签
        """
        # 定义类别对应的颜色字典
        colors = {
            'Salary': '#ffc107',       # 员工工资 - 黄色
            'Maintenance': '#dc3545',  # 维修费用 - 红色
            'Utilities': '#17a2b8',    # 水电费 - 青色
            'Other': '#6c757d'         # 其他支出 - 灰色
        }
        
        # 使用format_html渲染彩色标签
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;border-radius:3px;font-weight:bold;">{}</span>',
            colors.get(obj.category, '#000'),  # 获取对应颜色，默认黑色
            dict(obj.EXPENSE_CATEGORIES).get(obj.category, obj.category)  # 获取中文类别名称
        )
    
    # 设置列的显示名称
    category_display.short_description = '类别'

    def changelist_view(self, request, extra_context=None):
        """
        重写列表页面视图方法
        
        在列表页面添加总支出统计信息。
        
        参数:
            request: HTTP请求对象
            extra_context: 额外的模板上下文数据
        
        返回:
            HttpResponse: 列表页面的HTTP响应
        """
        # 使用aggregate()和Sum()计算所有支出的总和
        total = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0
        
        # 初始化或更新extra_context字典
        extra_context = extra_context or {}
        # 添加总支出到上下文中，供模板使用
        extra_context['total_expense'] = total
        
        # 调用父类的changelist_view方法
        return super().changelist_view(request, extra_context=extra_context)

    def save_model(self, request, obj, form, change):
        """
        重写模型保存方法
        
        在保存前执行模型的完整验证。
        
        参数:
            request: HTTP请求对象
            obj (Expense): 要保存的支出对象
            form: 表单实例
            change (bool): True表示修改，False表示新建
        """
        # 调用模型的full_clean方法，执行所有验证
        obj.full_clean()
        # 调用父类的save_model方法完成保存
        super().save_model(request, obj, form, change)
