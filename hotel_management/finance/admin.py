"""财务管理Admin配置模块"""
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from finance.models import Income, Expense

@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    """收入Admin配置类"""
    list_display = ('date', 'amount_display', 'source_display', 'short_description')
    ordering = ('-date',)
    list_display_links = ('date',)
    list_per_page = 20
    search_fields = ['date', 'source', 'description']
    list_filter = ('source', 'date')
    fieldsets = (
        ('收入详情', {'fields': ('date', 'amount', 'source', 'description')}),
    )

    def amount_display(self, obj):
        """绿色金额显示"""
        return format_html('<span style="color:#28a745;font-weight:bold;font-size:14px;">￥{}</span>', obj.amount)
    amount_display.short_description = '金额'
    amount_display.admin_order_field = 'amount'

    def source_display(self, obj):
        """彩色来源标签"""
        colors = {
            'Room': '#007bff',
            'Food': '#28a745',
            'Other': '#6c757d'
        }
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;border-radius:3px;font-weight:bold;">{}</span>',
            colors.get(obj.source, '#000'),
            dict(obj.INCOME_SOURCES).get(obj.source, obj.source)
        )
    source_display.short_description = '来源'

    def short_description(self, obj):
        """截断描述显示"""
        if len(obj.description) > 50:
            return obj.description[:50] + '...'
        return obj.description
    short_description.short_description = '描述'

    def changelist_view(self, request, extra_context=None):
        """总收入统计"""
        total = Income.objects.aggregate(total=Sum('amount'))['total'] or 0
        extra_context = extra_context or {}
        extra_context['total_income'] = total
        return super().changelist_view(request, extra_context=extra_context)

    def save_model(self, request, obj, form, change):
        obj.full_clean()
        super().save_model(request, obj, form, change)

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    """支出Admin配置类"""
    list_display = ('date', 'amount_display', 'category_display', 'description')
    ordering = ('-date',)
    list_display_links = ('date',)
    list_per_page = 20
    search_fields = ['date', 'category']
    fieldsets = (
        ('支出详情', {'fields': ('date', 'amount', 'category', 'description')}),
    )

    def amount_display(self, obj):
        """红色金额显示"""
        return format_html('<span style="color:#dc3545;font-weight:bold;font-size:14px;">￥{}</span>', obj.amount)
    amount_display.short_description = '金额'
    amount_display.admin_order_field = 'amount'

    def category_display(self, obj):
        """彩色类别标签"""
        colors = {
            'Salary': '#ffc107',
            'Maintenance': '#dc3545',
            'Utilities': '#17a2b8',
            'Other': '#6c757d'
        }
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;border-radius:3px;font-weight:bold;">{}</span>',
            colors.get(obj.category, '#000'),
            dict(obj.EXPENSE_CATEGORIES).get(obj.category, obj.category)
        )
    category_display.short_description = '类别'

    def changelist_view(self, request, extra_context=None):
        """总支出统计"""
        total = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0
        extra_context = extra_context or {}
        extra_context['total_expense'] = total
        return super().changelist_view(request, extra_context=extra_context)

    def save_model(self, request, obj, form, change):
        obj.full_clean()
        super().save_model(request, obj, form, change)
