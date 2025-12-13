"""
预订管理Admin配置模块

本模块配置Django Admin后台的预订管理界面。
包含表单验证、状态流转控制、批量操作、彩色状态标签等功能。
这是系统中最复杂的Admin配置，处理了预订的完整生命周期。
"""

# 导入Django Admin模块和messages消息模块
from django.contrib import admin, messages
# 导入format_html函数，用于在Admin列表中安全地渲染HTML内容
from django.utils.html import format_html
# 导入验证错误异常类
from django.core.exceptions import ValidationError
# 导入Django表单模块
from django import forms
# 导入Q对象，用于构建复杂的数据库查询条件
from django.db.models import Q
# 导入Reservation和Room模型
from reservations.models import Reservation
from rooms.models import Room


# ================================
# 预订管理表单类定义
# ================================
class ReservationAdminForm(forms.ModelForm):
    """
    预订管理表单类 - 控制预订状态流转和字段可编辑性
    
    核心功能:
        1. 新建预订时：只显示空闲房间，状态只能选择已预定或已入住
        2. 编辑预订时：根据当前状态限制可选状态和可编辑字段
        3. 防止已入住订单直接退款
    """
    
    class Meta:
        """表单元数据配置"""
        model = Reservation  # 关联的数据模型
        fields = '__all__'  # 包含所有字段

    def __init__(self, *args, **kwargs):
        """
        表单初始化方法
        
        根据是否为新建订单以及当前订单状态，
        动态调整表单字段的可选值和可编辑性。
        
        参数:
            *args: 位置参数
            **kwargs: 关键字参数
        """
        # 调用父类的__init__方法
        super().__init__(*args, **kwargs)
        
        # 判断是否为新建预订（无主键表示新建）
        if not self.instance.pk:
            # ===== 新建预订的配置 =====
            # 房间字段只显示空闲状态的房间
            self.fields['room'].queryset = Room.objects.filter(status='Available')
            # 设置房间字段的帮助文本
            self.fields['room'].help_text = '只显示空闲房间'
            # 新建时状态只能选择已预定或已入住
            self.fields['status'].choices = [
                ('Booked', '已预定'),
                ('CheckedIn', '已入住')
            ]
        else:
            # ===== 编辑预订的配置 =====
            # 房间字段显示空闲房间和当前订单关联的房间
            self.fields['room'].queryset = Room.objects.filter(
                Q(status='Available') |  # 空闲房间
                Q(id=self.instance.room.id)  # 或者当前订单关联的房间
            )
            
            # 定义不同状态的配置规则
            # 字典结构: 状态 -> (disabled, help_text, choices, disable_customer, disable_room)
            status_config = {
                'CheckedOut': (  # 已离店订单
                    True,  # 状态字段禁用
                    '已离店订单无法修改状态',  # 帮助文本
                    [('CheckedOut', '已离店')],  # 可选状态
                    False,  # 是否禁用客户字段
                    False   # 是否禁用房间字段
                ),
                'Refunded': (  # 已退订订单
                    True,  # 状态字段禁用
                    '已退订订单无法修改状态',  # 帮助文本
                    [('Refunded', '已退订')],  # 可选状态
                    False,  # 是否禁用客户字段
                    False   # 是否禁用房间字段
                ),
                'CheckedIn': (  # 已入住订单
                    False,  # 状态字段可编辑
                    '已入住订单只能办理离店，不支持退款',  # 帮助文本
                    [('CheckedIn', '已入住'), ('CheckedOut', '已离店')],  # 可选状态
                    True,   # 禁用客户字段
                    True    # 禁用房间字段
                ),
            }
            
            # 根据当前状态应用配置
            if self.instance.status in status_config:
                # 解构配置元组
                disabled, help_text, choices, disable_customer, disable_room = status_config[self.instance.status]
                # 应用配置到状态字段
                self.fields['status'].disabled = disabled
                self.fields['status'].help_text = help_text
                self.fields['status'].choices = choices
                # 根据配置禁用客户和房间字段
                if disable_customer:
                    self.fields['customer'].disabled = True
                if disable_room:
                    self.fields['room'].disabled = True
            else:
                # 默认配置（已预定状态）
                self.fields['status'].choices = [
                    ('Booked', '已预定'),
                    ('CheckedIn', '已入住'),
                    ('Refunded', '已退订')
                ]
                # 已预定状态不能修改房间
                self.fields['room'].disabled = True

    def clean(self):
        """
        表单整体验证方法
        
        实现业务规则验证:
            1. 已预定订单不能修改房间
            2. 已入住订单不能修改客户和房间
            3. 已入住订单不能直接退款
        
        返回:
            dict: 验证后的清洗数据
        
        异常:
            ValidationError: 当违反业务规则时抛出
        """
        # 调用父类的clean方法
        cleaned_data = super().clean()
        
        # 只在编辑现有订单时进行验证
        if self.instance.pk:
            # 获取数据库中的原始订单数据
            original = Reservation.objects.get(pk=self.instance.pk)
            
            if original.status == 'Booked':
                # 已预定状态：保持原有房间，不允许修改
                cleaned_data['room'] = original.room
            elif original.status == 'CheckedIn':
                # 已入住状态：保持原有客户和房间
                cleaned_data['customer'] = original.customer
                cleaned_data['room'] = original.room
                # 检查是否试图直接退款
                if cleaned_data.get('status') == 'Refunded':
                    raise ValidationError('已入住订单不支持退款，请先办理离店。')
        
        return cleaned_data


# ================================
# 预订Admin配置类
# ================================
# 使用@admin.register装饰器将ReservationAdmin注册到Admin后台
@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    """
    预订Admin配置类 - 定义Admin后台的预订管理界面
    
    功能包括:
        - 完整的列表显示（包含彩色状态标签、金额显示等）
        - 批量操作（入住、离店、退订、删除）
        - 字段分组和只读字段配置
        - 自定义表单验证
        - 删除保护机制
    """
    
    # 指定使用自定义的表单类
    form = ReservationAdminForm
    
    # list_display: 定义列表页面显示的字段
    # 包含模型字段和自定义方法
    list_display = (
        'id',                   # 预订号
        'customer',             # 客户
        'room',                 # 房间
        'get_room_status',      # 自定义房间状态显示
        'check_in_date',        # 入住日期
        'check_out_date',       # 离店日期
        'number_of_guests',     # 入住人数
        'paid_amount_display',  # 自定义已付金额显示
        'refund_amount_display',# 自定义退款金额显示
        'income_recorded',      # 是否已记录收入
        'refund_recorded',      # 是否已退款
        'status_colored',       # 自定义彩色状态显示
        'created_at'            # 创建时间
    )
    
    # ordering: 定义列表页面的默认排序方式
    # '-check_in_date'表示按入住日期降序排列
    ordering = ('-check_in_date',)
    
    # list_display_links: 定义哪些字段可以点击进入编辑页面
    list_display_links = ('customer', 'room')
    
    # list_per_page: 定义每页显示的记录数量
    list_per_page = 20
    
    # search_fields: 定义可搜索的字段
    # '__'语法用于跨关系搜索
    search_fields = ['customer__name', 'room__room_number', 'id']
    
    # list_filter: 定义右侧过滤器的字段
    list_filter = ('status', 'check_in_date', 'room__room_type')
    
    # readonly_fields: 定义只读字段（不可编辑）
    readonly_fields = (
        'created_at',              # 创建时间
        'updated_at',              # 更新时间
        'income_recorded',         # 收入记录标志
        'refund_recorded',         # 退款记录标志
        'refund_amount',           # 退款金额
        'estimated_amount_display' # 预计金额显示
    )
    
    # actions: 定义可用的批量操作
    actions = ['make_checkin', 'make_checkout', 'cancel_reservations', 'safe_delete_selected']
    
    # fieldsets: 定义编辑页面的字段分组布局
    fieldsets = (
        # 基本信息组
        (None, {'fields': ('customer', 'room', 'check_in_date', 'check_out_date')}),
        # 详细信息组
        ('详细信息', {
            'fields': (
                'number_of_guests', 'special_requests', 'status',
                'estimated_amount_display', 'income_recorded',
                'created_at', 'updated_at'
            )
        }),
        # 退款信息组（带说明文本）
        ('退款信息', {
            'fields': ('refund_amount', 'refund_recorded'),
            'description': '取消预订后将自动全额退款'
        }),
    )

    def get_actions(self, request):
        """
        重写获取操作列表的方法
        
        移除Django默认的删除操作，使用自定义的安全删除操作。
        
        参数:
            request: HTTP请求对象
        
        返回:
            dict: 可用的操作字典
        """
        # 调用父类方法获取默认操作列表
        actions = super().get_actions(request)
        # 移除默认的删除操作
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def estimated_amount_display(self, obj):
        """
        自定义预计金额显示方法
        
        在编辑页面显示预计金额，新建订单时显示提示文本。
        
        参数:
            obj (Reservation): 预订对象实例
        
        返回:
            str: HTML格式的金额或提示信息
        """
        # 如果是已存在的订单且有已付金额
        if obj.pk and obj.paid_amount > 0:
            # 显示绿色粗体的金额
            return format_html(
                '<span style="color:#28a745;font-weight:bold;font-size:15px;">￥{}</span>',
                obj.paid_amount
            )
        # 如果是新建订单，显示提示文本
        if not obj.pk:
            return format_html(
                '<span style="color:#6c757d;font-style:italic;">保存后自动计算</span>'
            )
        return '￥0.00'
    
    # 设置列的显示名称
    estimated_amount_display.short_description = '预计金额'

    def paid_amount_display(self, obj):
        """
        自定义已付金额显示方法
        
        在列表页面以绿色粗体样式显示已付金额。
        
        参数:
            obj (Reservation): 预订对象实例
        
        返回:
            str: HTML格式的金额字符串
        """
        if obj.paid_amount > 0:
            return format_html(
                '<span style="color:#28a745;font-weight:bold;">￥{}</span>',
                obj.paid_amount
            )
        return '￥0.00'
    
    paid_amount_display.short_description = '已付金额'
    paid_amount_display.admin_order_field = 'paid_amount'

    def refund_amount_display(self, obj):
        """
        自定义退款金额显示方法
        
        在列表页面以红色粗体样式显示退款金额。
        
        参数:
            obj (Reservation): 预订对象实例
        
        返回:
            str: HTML格式的金额字符串或'-'
        """
        if obj.refund_amount > 0:
            return format_html(
                '<span style="color:#dc3545;font-weight:bold;">￥{}</span>',
                obj.refund_amount
            )
        return '-'
    
    refund_amount_display.short_description = '退款金额'
    refund_amount_display.admin_order_field = 'refund_amount'

    def get_room_status(self, obj):
        """
        自定义房间状态显示方法
        
        以不同颜色显示关联房间的当前状态。
        
        参数:
            obj (Reservation): 预订对象实例
        
        返回:
            str: HTML格式的状态文本
        """
        # 定义状态对应的颜色字典
        colors = {
            'Available': '#28a745',    # 空闲 - 绿色
            'Booked': '#ffc107',       # 已预订 - 黄色
            'Occupied': '#dc3545',     # 已入住 - 红色
            'Maintenance': '#6c757d'   # 维修中 - 灰色
        }
        return format_html(
            '<span style="color:{};font-weight:bold;">{}</span>',
            colors.get(obj.room.status, '#000'),
            dict(obj.room.ROOM_STATUS).get(obj.room.status, obj.room.status)
        )
    
    get_room_status.short_description = '房间状态'

    def status_colored(self, obj):
        """
        自定义预订状态彩色显示方法
        
        以不同颜色的标签显示预订状态。
        
        颜色对应关系:
            - Booked(已预定): 蓝色 #007bff
            - CheckedIn(已入住): 绿色 #28a745
            - CheckedOut(已离店): 灰色 #6c757d
            - Refunded(已退订): 红色 #dc3545
        
        参数:
            obj (Reservation): 预订对象实例
        
        返回:
            str: HTML格式的状态标签
        """
        colors = {
            'Booked': '#007bff',     # 已预定 - 蓝色
            'CheckedIn': '#28a745',  # 已入住 - 绿色
            'CheckedOut': '#6c757d', # 已离店 - 灰色
            'Refunded': '#dc3545'    # 已退订 - 红色
        }
        return format_html(
            '<span style="background:{};color:white;padding:5px 12px;border-radius:4px;">{}</span>',
            colors.get(obj.status, '#000'),
            dict(obj.STATUS).get(obj.status, obj.status)
        )
    
    status_colored.short_description = '预订状态'

    @admin.action(description='批量办理入住')
    def make_checkin(self, request, queryset):
        """
        批量办理入住的操作方法
        
        将选中的已预定订单状态改为已入住。
        
        参数:
            request: HTTP请求对象
            queryset: 选中的预订查询集
        """
        # 使用生成器表达式和sum()统计成功处理的数量
        # 只处理状态为Booked的订单
        updated = sum(
            1 for r in queryset 
            if r.status == 'Booked' and (  # 只处理已预定订单
                setattr(r, 'status', 'CheckedIn'),  # 设置状态为已入住
                r.save(),  # 保存更改
                True  # 返回True以便计数
            )[-1]
        )
        # 显示成功消息
        if updated:
            messages.success(request, f'成功办理{updated}个入住')

    @admin.action(description='批量办理离店')
    def make_checkout(self, request, queryset):
        """
        批量办理离店的操作方法
        
        将选中的已入住订单状态改为已离店。
        
        参数:
            request: HTTP请求对象
            queryset: 选中的预订查询集
        """
        # 只处理状态为CheckedIn的订单
        updated = sum(
            1 for r in queryset 
            if r.status == 'CheckedIn' and (
                setattr(r, 'status', 'CheckedOut'),
                r.save(),
                True
            )[-1]
        )
        if updated:
            messages.success(request, f'成功办理{updated}个离店')

    @admin.action(description='批量退订(自动退款)')
    def cancel_reservations(self, request, queryset):
        """
        批量退订的操作方法
        
        将选中的已预定订单状态改为已退订，自动处理退款。
        已入住订单不允许退订。
        
        参数:
            request: HTTP请求对象
            queryset: 选中的预订查询集
        """
        # 检查是否有已入住订单
        checkedin_count = queryset.filter(status='CheckedIn').count()
        if checkedin_count > 0:
            messages.error(
                request,
                f'操作已取消！{checkedin_count}个已入住订单不支持退款，请先办理离店。'
            )
            return
        
        # 统计处理结果
        updated = 0  # 退订数量
        total = 0    # 总退款金额
        
        # 只处理已预定状态的订单
        for r in queryset.filter(status='Booked'):
            r.status = 'Refunded'  # 设置状态为已退订
            r.save()  # 保存会触发模型的退款逻辑
            updated += 1
            # 重新从数据库获取最新数据（因为_process_refund使用update更新数据库）
            r.refresh_from_db()
            # 累加退款金额
            total += r.refund_amount if r.refund_recorded else 0
        
        # 显示操作结果
        if updated:
            messages.success(request, f'成功退订{updated}个，总退款:￥{total}')
        else:
            messages.warning(request, '没有可退订的订单（只有已预定订单可退订）')

    @admin.action(description='删除订单')
    def safe_delete_selected(self, request, queryset):
        """
        安全删除预订的操作方法
        
        检查活跃订单后执行删除。
        活跃订单（已预定或已入住）不允许删除。
        
        参数:
            request: HTTP请求对象
            queryset: 选中的预订查询集
        """
        # 检查是否有活跃订单
        active = queryset.filter(status__in=['Booked', 'CheckedIn'])
        if active.exists():
            messages.error(
                request,
                f'操作已取消！无法删除 {active.count()} 个活跃订单！请先将状态改为已离店或已退订。'
            )
            return
        
        count = 0  # 删除数量
        total = 0  # 总退款金额
        
        for obj in queryset:
            # 如果是退订订单且有已付金额且未退款，累加退款金额
            if obj.status == 'Refunded' and obj.paid_amount > 0 and not obj.refund_recorded:
                total += obj.paid_amount
            obj.delete()  # 删除订单（会触发模型的delete方法）
            count += 1
        
        # 构建成功消息
        msg = f'已成功删除 {count} 个预订'
        if total > 0:
            msg += f'，总退款：￥{total}'
        messages.success(request, msg)

    def save_model(self, request, obj, form, change):
        """
        重写模型保存方法
        
        在保存后显示相关提示信息。
        
        参数:
            request: HTTP请求对象
            obj (Reservation): 要保存的预订对象
            form: 表单实例
            change (bool): True表示修改，False表示新建
        """
        try:
            obj.save()  # 保存订单
            
            # 新建订单时显示已付金额
            if not change and obj.paid_amount > 0:
                messages.info(request, f'已付金额:￥{obj.paid_amount}')
            
            # 退订时显示退款信息
            if obj.status == 'Refunded' and obj.refund_recorded:
                messages.warning(request, f'已退订，退款:￥{obj.refund_amount}')
                
        except ValidationError as e:
            messages.error(request, f'保存失败:{e}')
            raise

    def delete_model(self, request, obj):
        """
        重写单个对象删除方法
        
        检查活跃状态后执行删除，并显示相关操作结果。
        
        参数:
            request: HTTP请求对象
            obj (Reservation): 要删除的预订对象
        """
        # 检查是否为活跃订单
        if obj.status in ['Booked', 'CheckedIn']:
            messages.error(
                request,
                f'无法删除活跃订单（预订号{obj.id}）！请先将状态改为已离店或已退订。'
            )
            return
        
        # 保存删除前的信息
        room_number = obj.room.room_number
        has_income = obj.income_recorded
        will_refund = obj.status == 'Refunded' and obj.paid_amount > 0 and not obj.refund_recorded
        refund_amount = obj.paid_amount if will_refund else 0
        
        # 执行删除
        obj.delete()
        
        # 显示操作结果
        messages.success(request, f'预订已删除，房间{room_number}状态已更新')
        if has_income:
            messages.info(request, '收入记录已标记为"已删除"')
        if refund_amount > 0:
            messages.warning(request, f'已创建退款记录：￥{refund_amount}')
