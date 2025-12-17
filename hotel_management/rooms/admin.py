"""房间管理Admin配置模块"""
from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from django.core.exceptions import ValidationError
from django import forms
from rooms.models import Room

class RoomAdminForm(forms.ModelForm):
    """房间管理表单类 - 验证有活跃订单的房间不允许修改"""
    class Meta:
        model = Room
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        if self.instance.pk:
            from reservations.models import Reservation
            active = Reservation.objects.filter(room=self.instance, status__in=['Booked', 'CheckedIn'])
            if active.exists():
                raise ValidationError(f'该房间存在{active.count()}个活跃订单，无法修改房间信息！')
        return cleaned_data


admin.site.site_header = '酒店入住管理系统'
admin.site.site_title = '酒店入住管理系统后台'
admin.site.index_title = '欢迎来到酒店入住管理系统后台'

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    """房间Admin配置类"""
    form = RoomAdminForm
    list_display = ('room_number', 'room_type', 'price_display', 'status_colored', 'picture_image', 'facilities', 'floor', 'capacity', 'description')
    ordering = ('-price',)
    list_display_links = ('room_number',)
    list_per_page = 20
    search_fields = ['room_number', 'room_type']
    actions = ['safe_delete_selected']
    fieldsets = (
        (None, {'fields': ('room_number', 'room_type', 'price', 'pictures')}),
        ('详细信息', {'fields': ('facilities', 'status', 'floor', 'capacity', 'description')})
    )

    def get_actions(self, request):
        """移除默认删除操作"""
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def save_model(self, request, obj, form, change):
        obj.full_clean()
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        """单个删除时检查活跃订单"""
        from reservations.models import Reservation
        active = Reservation.objects.filter(room=obj, status__in=['Booked', 'CheckedIn'])
        if active.exists():
            messages.error(request, f'无法删除房间「{obj.room_number}」，存在{active.count()}个活跃订单！')
            return
        super().delete_model(request, obj)
        messages.success(request, f'房间 {obj.room_number} 已删除')

    @admin.action(description='删除所选的房间')
    def safe_delete_selected(self, request, queryset):
        """批量安全删除，检查活跃订单"""
        from reservations.models import Reservation
        blocked = [
            r.room_number for r in queryset
            if Reservation.objects.filter(room=r, status__in=['Booked', 'CheckedIn']).exists()
        ]
        if blocked:
            messages.error(request, f'操作已取消！以下房间存在活跃订单：{", ".join(blocked)}')
            return
        count = queryset.count()
        for r in queryset:
            r.delete()
        messages.success(request, f'已成功删除 {count} 个房间')

    def price_display(self, obj):
        """绿色价格显示"""
        return format_html('<span style="color:#28a745;font-weight:bold;font-size:14px;">￥{}</span>', obj.price)
    price_display.short_description = '价格(元/晚)'
    price_display.admin_order_field = 'price'

    def status_colored(self, obj):
        """彩色状态标签"""
        colors = {
            'Available': '#28a745',
            'Booked': '#ffc107',
            'Occupied': '#dc3545',
            'Maintenance': '#6c757d'
        }
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;border-radius:3px;font-weight:bold;">{}</span>',
            colors.get(obj.status, '#000'),
            dict(obj.ROOM_STATUS).get(obj.status, obj.status)
        )
    status_colored.short_description = '状态'

    def picture_image(self, obj):
        """图片预览"""
        if obj.pictures:
            return format_html(
                '<a href="{0}" data-lightbox="room-{1}"><img src="{0}" width="100" height="100"/></a>',
                obj.pictures.url,
                obj.id
            )
        return None
    picture_image.short_description = '主图'

    class Media:
        js = ('https://cdn.jsdelivr.net/npm/lightbox2@2.11.3/dist/js/lightbox.min.js',)
        css = {
            'all': ('https://cdn.jsdelivr.net/npm/lightbox2@2.11.3/dist/css/lightbox.min.css',)
        }
