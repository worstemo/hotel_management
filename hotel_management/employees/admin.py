"""员工管理Admin配置模块"""
from django.contrib import admin
from employees.models import Employee

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    """员工Admin配置类"""
    list_display = ('name', 'position', 'phone', 'email', 'address', 'salary', 'hire_date', 'status')
    ordering = ('-name',)
    list_display_links = ('name',)
    list_per_page = 20
    search_fields = ['name', 'position', 'phone']
    fieldsets = (
        (None, {'fields': ('name', 'position', 'phone')}),
        ('详细信息', {'fields': ('email', 'address', 'salary', 'hire_date', 'status')})
    )

    def save_model(self, request, obj, form, change):
        obj.full_clean()
        super().save_model(request, obj, form, change)
