"""
房间管理Admin配置模块

本模块配置Django Admin后台的房间管理界面。
包含房间表单验证、列表显示、彩色状态标签、删除保护等功能。
同时设置了Admin后台的网站标题。
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
# 导入Room模型，用于在Admin中管理房间数据
from rooms.models import Room


# ================================
# 房间管理表单类定义
# ================================
class RoomAdminForm(forms.ModelForm):
    """
    房间管理表单类 - 用于验证房间信息的修改操作
    
    继承自Django的ModelForm类，自动根据Room模型生成表单字段。
    重写clean方法添加业务逻辑验证：有活跃订单的房间不允许修改。
    """
    
    class Meta:
        """
        表单的元数据配置
        
        属性:
            model: 指定关联的模型为Room
            fields: '__all__'表示包含模型的所有字段
        """
        model = Room  # 关联的数据模型
        fields = '__all__'  # 包含所有字段

    def clean(self):
        """
        表单整体验证方法
        
        在所有字段验证完成后调用，用于执行跨字段的业务逻辑验证。
        
        业务规则:
            - 如果房间存在活跃订单（已预定或已入住），则不允许修改房间信息
            - 这是为了保证订单关联数据的一致性
        
        返回:
            dict: 验证后的清洗数据
        
        异常:
            ValidationError: 当房间存在活跃订单时抛出
        """
        # 调用父类的clean方法，获取验证后的数据
        cleaned_data = super().clean()
        
        # 检查是否为编辑操作（而非新建）
        # self.instance.pk存在表示该对象已经存在于数据库中
        if self.instance.pk:
            # 延迟导入Reservation模型，避免循环导入问题
            from reservations.models import Reservation
            
            # 查询该房间的所有活跃订单（已预定或已入住）
            active = Reservation.objects.filter(
                room=self.instance,  # 筛选当前房间
                status__in=['Booked', 'CheckedIn']  # 状态为已预定或已入住
            )
            
            # 如果存在活跃订单，则不允许修改
            if active.exists():
                # 抛出验证错误，阻止表单提交
                raise ValidationError(
                    f'该房间存在{active.count()}个活跃订单，无法修改房间信息！'
                )
        
        # 返回验证后的数据
        return cleaned_data


# ================================
# Admin后台全局配置
# ================================
# 设置Admin后台页面的头部标题（显示在每个页面的左上角）
admin.site.site_header = '酒店入住管理系统'
# 设置Admin后台的网站标题（显示在浏览器标签页）
admin.site.site_title = '酒店入住管理系统后台'
# 设置Admin后台首页的标题
admin.site.index_title = '欢迎来到酒店入住管理系统后台'


# ================================
# 房间Admin配置类
# ================================
# 使用@admin.register装饰器将RoomAdmin注册到Admin后台
@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    """
    房间Admin配置类 - 定义Admin后台的房间管理界面
    
    功能包括:
        - 自定义列表显示字段（包括彩色状态标签、价格样式等）
        - 删除保护机制（有活跃订单的房间不能删除）
        - 自定义批量操作
        - 图片预览功能
        - 第三方lightbox图片插件集成
    """
    
    # 指定使用自定义的表单类
    form = RoomAdminForm
    
    # list_display: 定义列表页面显示的字段
    # 可以是模型字段名称，也可以是自定义方法名称
    list_display = (
        'room_number',      # 房间号
        'room_type',        # 房间类型
        'price_display',    # 自定义价格显示（绿色样式）
        'status_colored',   # 自定义状态显示（彩色标签）
        'picture_image',    # 自定义图片预览
        'facilities',       # 设施
        'floor',           # 楼层
        'capacity',        # 容纳人数
        'description'      # 描述
    )
    
    # ordering: 定义列表页面的默认排序方式
    # '-price'表示按价格降序排列
    ordering = ('-price',)
    
    # list_display_links: 定义哪些字段可以点击进入编辑页面
    list_display_links = ('room_number',)
    
    # list_per_page: 定义每页显示的记录数量
    list_per_page = 20
    
    # search_fields: 定义可搜索的字段
    search_fields = ['room_number', 'room_type']
    
    # actions: 定义可用的批量操作
    actions = ['safe_delete_selected']
    
    # fieldsets: 定义编辑页面的字段分组布局
    fieldsets = (
        (None, {'fields': ('room_number', 'room_type', 'price', 'pictures')}),  # 基本信息组
        ('详细信息', {'fields': ('facilities', 'status', 'floor', 'capacity', 'description')})  # 详细信息组
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
        
        # 移除Django默认的删除操作
        if 'delete_selected' in actions:
            del actions['delete_selected']
        
        # 返回修改后的操作列表
        return actions

    def save_model(self, request, obj, form, change):
        """
        重写模型保存方法
        
        在保存前执行模型的完整验证。
        
        参数:
            request: HTTP请求对象
            obj (Room): 要保存的房间对象
            form: 表单实例
            change (bool): True表示修改，False表示新建
        """
        # 调用模型的full_clean方法，执行所有验证
        obj.full_clean()
        # 调用父类的save_model方法完成保存
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        """
        重写单个对象删除方法
        
        在删除房间前检查是否存在活跃订单。
        如果存在已预定或已入住的订单，则拒绝删除。
        
        参数:
            request: HTTP请求对象
            obj (Room): 要删除的房间对象
        """
        # 延迟导入Reservation模型
        from reservations.models import Reservation
        
        # 查询该房间的活跃订单（已预定或已入住）
        active = Reservation.objects.filter(
            room=obj,  # 筛选当前房间
            status__in=['Booked', 'CheckedIn']  # 状态为已预定或已入住
        )
        
        # 如果存在活跃订单，显示错误消息并返回
        if active.exists():
            messages.error(
                request,
                f'无法删除房间「{obj.room_number}」，存在{active.count()}个活跃订单！'
            )
            return  # 不执行删除操作
        
        # 调用父类方法执行实际删除
        super().delete_model(request, obj)
        # 显示成功消息
        messages.success(request, f'房间 {obj.room_number} 已删除')

    @admin.action(description='删除所选的 房间')
    def safe_delete_selected(self, request, queryset):
        """
        安全批量删除房间的操作方法
        
        在删除前检查所有选中的房间是否存在活跃订单。
        如果任何一个房间有活跃订单，则取消整个操作。
        
        装饰器说明:
            @admin.action(description='...')设置操作在Admin界面的显示名称
        
        参数:
            request: HTTP请求对象
            queryset: 选中的房间查询集
        """
        # 延迟导入Reservation模型
        from reservations.models import Reservation
        
        # 遍历选中的房间，找出有活跃订单的房间号
        blocked = [
            r.room_number  # 提取房间号
            for r in queryset  # 遍历所有选中的房间
            if Reservation.objects.filter(
                room=r,
                status__in=['Booked', 'CheckedIn']
            ).exists()
        ]
        
        # 如果存在被阻止删除的房间，显示错误消息并返回
        if blocked:
            messages.error(
                request,
                f'操作已取消！以下房间存在活跃订单：{", ".join(blocked)}'
            )
            return  # 不执行删除操作
        
        # 记录要删除的房间数量
        count = queryset.count()
        
        # 遍历并删除每个房间
        for r in queryset:
            r.delete()  # 调用对象的delete方法
        
        # 显示成功消息
        messages.success(request, f'已成功删除 {count} 个房间')

    def price_display(self, obj):
        """
        自定义价格显示方法
        
        用于在列表页面以绿色粗体样式显示价格。
        
        参数:
            obj (Room): 房间对象实例
        
        返回:
            str: HTML格式的价格字符串
        """
        # 使用format_html渲染带样式的价格显示
        # style属性: color绿色、font-weight粗体、font-size14像素
        return format_html(
            '<span style="color:#28a745;font-weight:bold;font-size:14px;">￥{}</span>',
            obj.price
        )
    
    # 设置列的显示名称
    price_display.short_description = '价格(元/晚)'
    # 设置点击列标题时的排序字段
    price_display.admin_order_field = 'price'

    def status_colored(self, obj):
        """
        自定义状态彩色显示方法
        
        用于在列表页面以不同颜色的标签显示房间状态。
        
        颜色对应关系:
            - Available(空闲): 绿色 #28a745
            - Booked(已预订): 黄色 #ffc107
            - Occupied(已入住): 红色 #dc3545
            - Maintenance(维修中): 灰色 #6c757d
        
        参数:
            obj (Room): 房间对象实例
        
        返回:
            str: HTML格式的状态标签
        """
        # 定义状态对应的颜色字典
        colors = {
            'Available': '#28a745',    # 空闲 - 绿色
            'Booked': '#ffc107',       # 已预订 - 黄色
            'Occupied': '#dc3545',     # 已入住 - 红色
            'Maintenance': '#6c757d'   # 维修中 - 灰色
        }
        
        # 使用format_html渲染彩色状态标签
        # style属性: 背景色、白色文字、内边距、圆角、粗体
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;border-radius:3px;font-weight:bold;">{}</span>',
            colors.get(obj.status, '#000'),  # 获取对应颜色，默认黑色
            dict(obj.ROOM_STATUS).get(obj.status, obj.status)  # 获取中文状态名称
        )
    
    # 设置列的显示名称
    status_colored.short_description = '状态'

    def picture_image(self, obj):
        """
        自定义图片预览显示方法
        
        用于在列表页面显示房间主图的缩略图。
        点击图片可以使用lightbox插件查看大图。
        
        参数:
            obj (Room): 房间对象实例
        
        返回:
            str: HTML格式的图片链接，或None
        """
        # 检查是否有图片
        if obj.pictures:
            # 使用format_html渲染可点击的图片
            # data-lightbox属性用于lightbox插件分组
            # 图片尺寸固定为100x100像素
            return format_html(
                '<a href="{0}" data-lightbox="room-{1}"><img src="{0}" width="100" height="100"/></a>',
                obj.pictures.url,  # 图片URL
                obj.id  # 房间ID（用于lightbox分组）
            )
        # 如果没有图片，返回None
        return None
    
    # 设置列的显示名称
    picture_image.short_description = '主图'

    class Media:
        """
        Admin媒体文件配置类
        
        用于在Admin页面加载额外的JavaScript和CSS文件。
        这里加载了lightbox2插件，用于图片放大浏览。
        """
        # 导入的JavaScript文件（lightbox插件）
        # 使用CDN加载，版本2.11.3
        js = ('https://cdn.jsdelivr.net/npm/lightbox2@2.11.3/dist/js/lightbox.min.js',)
        
        # 导入的CSS文件（lightbox样式）
        # 'all'表示所有媒体类型都使用这个样式
        css = {
            'all': ('https://cdn.jsdelivr.net/npm/lightbox2@2.11.3/dist/css/lightbox.min.css',)
        }
