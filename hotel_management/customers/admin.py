"""客户管理Admin配置模块"""
from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from django.core.exceptions import ValidationError
from django import forms
from customers.models import Customer

class CustomerAdminForm(forms.ModelForm):
    """客户管理表单类 - 验证已入住客户不允许修改"""
    class Meta:
        model = Customer
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        if self.instance.pk:
            from reservations.models import Reservation
            checkedin = Reservation.objects.filter(customer=self.instance, status='CheckedIn')
            if checkedin.exists():
                raise ValidationError(f'该客户存在{checkedin.count()}个已入住订单，无法修改客户信息！请先办理离店。')
        return cleaned_data

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """客户Admin配置类"""
    form = CustomerAdminForm
    list_display = ('name', 'id_number', 'phone', 'email_display', 'address')
    ordering = ('-name',)
    list_display_links = ('name', 'id_number')
    list_per_page = 20
    search_fields = ['name', 'id_number', 'phone']
    list_filter = ('name',)
    actions = ['safe_delete_selected']
    fieldsets = (
        (None, {'fields': ('name', 'id_number', 'phone')}),
        ('详细信息', {'fields': ('email', 'address')})
    )

    def get_actions(self, request):
        """移除默认删除操作，替换为安全删除"""
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def email_display(self, obj):
        """自定义邮箱显示"""
        if obj.email:
            return format_html('<span style="color:#007bff;">{}</span>', obj.email)
        return '-'
    email_display.short_description = '邮箱'
    email_display.admin_order_field = 'email'

    def delete_model(self, request, obj):
        """单个删除时检查活跃订单"""
        from reservations.models import Reservation
        active = Reservation.objects.filter(customer=obj, status__in=['Booked', 'CheckedIn'])
        if active.exists():
            messages.error(request, f'无法删除客户「{obj.name}」，存在{active.count()}个活跃订单！')
            return
        super().delete_model(request, obj)
        messages.success(request, f'客户 {obj.name} 已删除')

    @admin.action(description='删除所选的 客户')
    def safe_delete_selected(self, request, queryset):
        """批量安全删除，检查活跃订单"""
        from reservations.models import Reservation
        blocked = [
            c.name for c in queryset
            if Reservation.objects.filter(customer=c, status__in=['Booked', 'CheckedIn']).exists()
        ]
        if blocked:
            messages.error(request, f'操作已取消！以下客户存在活跃订单：{", ".join(blocked)}')
            return
        count = queryset.count()
        for c in queryset:
            c.delete()
        messages.success(request, f'已成功删除 {count} 个客户')
