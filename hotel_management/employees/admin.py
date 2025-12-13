"""
员工管理Admin配置模块

本模块配置Django Admin后台的员工管理界面。
包含列表显示、字段分组、搜索等功能。
"""

# 导入Django Admin模块，用于注册和配置后台管理界面
from django.contrib import admin
# 导入Employee模型，用于在Admin中管理员工数据
from employees.models import Employee


# ================================
# 员工Admin配置类
# ================================
# 使用@admin.register装饰器将EmployeeAdmin注册到Admin后台
# 这是一种简洁的注册方式，等价于 admin.site.register(Employee, EmployeeAdmin)
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    """
    员工Admin配置类 - 定义Admin后台的员工管理界面
    
    功能包括:
        - 自定义列表显示字段
        - 字段分组布局
        - 搜索功能
        - 完整性验证
    """
    
    # list_display: 定义列表页面显示的字段
    # 显示员工的所有主要信息
    list_display = (
        'name',       # 姓名
        'position',   # 职位
        'phone',      # 联系电话
        'email',      # 邮箱
        'address',    # 地址
        'salary',     # 工资
        'hire_date',  # 入职日期
        'status'      # 在职状态
    )
    
    # ordering: 定义列表页面的默认排序方式
    # '-name'表示按姓名降序排列
    ordering = ('-name',)
    
    # list_display_links: 定义哪些字段可以点击进入编辑页面
    list_display_links = ('name',)
    
    # list_per_page: 定义每页显示的记录数量
    list_per_page = 20
    
    # search_fields: 定义可搜索的字段
    # 用户可以通过姓名、职位、电话搜索员工
    search_fields = ['name', 'position', 'phone']
    
    # fieldsets: 定义编辑页面的字段分组布局
    # 每个元组包含：（组名称，{配置字典}）
    # None表示没有组名称（默认组）
    fieldsets = (
        # 基本信息组：显示姓名、职位、联系电话
        (None, {'fields': ('name', 'position', 'phone')}),
        # 详细信息组：显示邮箱、地址、工资、入职日期、状态
        ('详细信息', {'fields': ('email', 'address', 'salary', 'hire_date', 'status')})
    )

    def save_model(self, request, obj, form, change):
        """
        重写模型保存方法
        
        在保存前执行模型的完整验证，确保数据的有效性。
        
        参数:
            request: HTTP请求对象，包含当前用户信息等
            obj (Employee): 要保存的员工对象
            form: 表单实例，包含用户提交的数据
            change (bool): True表示修改现有记录，False表示新建记录
        """
        # 调用模型的full_clean方法，执行所有字段验证和模型级验证
        obj.full_clean()
        # 调用父类的save_model方法完成实际的数据库保存操作
        super().save_model(request, obj, form, change)
