"""
预订管理Admin配置模块
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
    
    【状态流转规则】
    新建 → 只能选择"已预定"或"已入住"
    已预定 → 可改为"已入住"或"已退订"
    已入住 → 只能改为"已离店"（不能直接退款）
    已离店/已退订 → 不能修改状态
    """
    
    class Meta:
        """
        表单元数据配置类
        
        这个内部类告诉 Django：
        - 这个表单对应哪个模型
        - 包含哪些字段
        """
        model = Reservation  # 关联的数据模型是 Reservation（预订）
        fields = '__all__'   # '__all__' 表示包含模型的所有字段

    def __init__(self, *args, **kwargs):
        """
        表单初始化方法（构造函数）
        
        【什么时候调用？】
        每次打开"添加预订"或"编辑预订"页面时，Django 会创建表单对象
        创建时会自动调用这个 __init__ 方法
        
        【做什么？】
        根据是新建还是编辑，以及当前订单状态，动态调整表单的行为
        
        参数:
            *args: 位置参数（Python语法，接收任意数量的位置参数）
            **kwargs: 关键字参数（Python语法，接收任意数量的关键字参数）
            这两个参数会传递给父类，包含表单的初始数据等信息
        """
        # ----------------------------------------------------------
        # 调用父类的 __init__ 方法
        # ----------------------------------------------------------
        # super() 获取父类（forms.ModelForm）
        # 必须先调用父类的初始化方法，让表单完成基本的初始化工作
        # 之后 self.fields 字典才会被创建，我们才能修改字段配置
        super().__init__(*args, **kwargs)
        
        # ----------------------------------------------------------
        # 判断是新建预订还是编辑预订
        # ----------------------------------------------------------
        # self.instance 是当前表单关联的模型对象
        # self.instance.pk 是主键（Primary Key）
        #   - 新建时：pk = None（还没保存到数据库，没有主键）
        #   - 编辑时：pk = 1, 2, 3...（已存在的记录有主键）
        #
        if not self.instance.pk:
            # =====================================================
            # 【新建预订】的表单配置
            # =====================================================
            
            # ----- 配置房间下拉框 -----
            # self.fields['room'] 获取表单中的房间字段
            # .queryset 设置下拉框的选项来源（从数据库查询哪些房间）
            # Room.objects.filter(status='Available') 只查询状态为"空闲"的房间
            # 
            # 效果：新建预订时，房间下拉框只显示空闲的房间，已入住/已预订的房间不会出现
            self.fields['room'].queryset = Room.objects.filter(status='Available')
            
            # 设置帮助文本，会显示在字段下方，提示用户
            self.fields['room'].help_text = '只显示空闲房间'
            
            # ----- 配置状态下拉框 -----
            # .choices 设置下拉框的可选项
            # 格式：[(值1, 显示文本1), (值2, 显示文本2), ...]
            # 新建时只能选择"已预定"或"已入住"（不能直接选择已离店或已退订）
            self.fields['status'].choices = [
                ('Booked', '已预定'),      # 元组：(存入数据库的值, 页面显示的文本)
                ('CheckedIn', '已入住')
            ]
            
        else:
            # =====================================================
            # 【编辑预订】的表单配置
            # =====================================================
            
            # ----- 配置房间下拉框 -----
            # 编辑时，房间下拉框显示：
            #   1. 所有空闲房间（可以换房）
            #   2. 当前订单已关联的房间（必须包含，否则显示会出错）
            #
            # Q() 是 Django 的查询对象，用于构建复杂查询条件
            # Q(status='Available') | Q(id=self.instance.room.id)
            # | 表示"或"，即：状态为空闲 或者 是当前订单的房间
            self.fields['room'].queryset = Room.objects.filter(
                Q(status='Available') |           # 空闲房间
                Q(id=self.instance.room.id)       # 或者当前订单关联的房间
            )
            
            # ----- 根据当前状态配置表单行为 -----
            # 不同状态的订单，表单行为不同
            # 使用字典存储每种状态的配置规则，便于维护
            #
            # 字典结构：
            # {
            #     状态值: (状态字段是否禁用, 帮助文本, 可选状态列表, 是否禁用客户字段, 是否禁用房间字段)
            # }
            status_config = {
                # ----- 已离店订单的配置 -----
                'CheckedOut': (
                    True,                          # disabled=True：状态下拉框变灰，不可点击
                    '已离店订单无法修改状态',       # 帮助文本提示
                    [('CheckedOut', '已离店')],    # 下拉框只显示"已离店"一个选项
                    True,                         # 客户字段禁用
                    True                          # 房间字段禁用
                ),
                # ----- 已退订订单的配置 -----
                'Refunded': (
                    True,                          # 状态字段禁用
                    '已退订订单无法修改状态',       # 帮助文本提示
                    [('Refunded', '已退订')],      # 只能显示已退订
                    True,                         # 客户字段禁用
                    True                          # 房间字段禁用
                ),
                # ----- 已入住订单的配置 -----
                'CheckedIn': (
                    False,                         # 状态字段可编辑（需要改为已离店）
                    '已入住订单只能办理离店，不支持退款',  # 提示不能退款
                    [('CheckedIn', '已入住'), ('CheckedOut', '已离店')],  # 只能选这两个
                    True,                          # 禁用客户字段（入住后不能换客户）
                    True                           # 禁用房间字段（入住后不能换房）
                ),
            }
            
            # ----- 应用配置规则 -----
            # self.instance.status 是当前订单的状态
            # 检查当前状态是否在配置字典中
            if self.instance.status in status_config:
                # 从字典中取出配置元组，并解构赋值给5个变量
                # 这是 Python 的元组解包语法
                disabled, help_text, choices, disable_customer, disable_room = status_config[self.instance.status]
                
                # 应用配置到状态字段
                self.fields['status'].disabled = disabled      # 设置是否禁用
                self.fields['status'].help_text = help_text    # 设置帮助文本
                self.fields['status'].choices = choices        # 设置可选项
                
                # 根据配置禁用客户和房间字段
                if disable_customer:
                    self.fields['customer'].disabled = True    # 客户下拉框变灰不可选
                if disable_room:
                    self.fields['room'].disabled = True        # 房间下拉框变灰不可选
                    
            else:
                # ----- 默认配置（已预定状态 Booked）-----
                # 如果状态不在配置字典中，说明是"已预定"状态
                self.fields['status'].choices = [
                    ('Booked', '已预定'),
                    ('CheckedIn', '已入住'),    # 可以办理入住
                    ('Refunded', '已退订')      # 可以退订
                ]
                # 已预定状态不能修改房间
                self.fields['customer'].disabled = True
                self.fields['room'].disabled = True

    def clean(self):
        """
        表单整体验证方法
        
        【什么时候调用？】
        用户点击"保存"按钮后，Django 会调用这个方法进行数据验证
        
        【与模型的 clean() 有什么区别？】
        - 模型的 clean()：验证数据是否符合业务规则（如日期冲突）
        - 表单的 clean()：验证用户输入是否符合表单规则（如状态流转）
        
        【执行顺序】
        表单 clean() → 模型 clean() → 保存到数据库
        
        返回:
            dict: 验证后的清洗数据（cleaned_data）
        
        异常:
            ValidationError: 当违反业务规则时抛出，阻止保存
        """
        # 调用父类的 clean 方法，获取已验证的数据
        # cleaned_data 是一个字典，包含所有字段的值
        # 例如：{'customer': <Customer对象>, 'room': <Room对象>, 'status': 'Booked', ...}
        cleaned_data = super().clean()
        
        # ----------------------------------------------------------
        # 只在编辑现有订单时进行验证（新建订单不需要这些规则）
        # ----------------------------------------------------------
        if self.instance.pk:
            # 从数据库重新查询原始订单数据
            # 因为 self.instance 可能已经被表单数据修改了
            # 我们需要知道修改前的状态是什么
            original = Reservation.objects.get(pk=self.instance.pk)
            
            # ----- 规则1：已预定订单不能修改房间 -----
            if original.status == 'Booked':
                # 强制使用原来的房间，忽略用户的修改
                # 即使用户在前端修改了房间，这里也会被覆盖回原值
                cleaned_data['room'] = original.room
                
            # ----- 规则2：已入住订单不能修改客户和房间 -----
            elif original.status == 'CheckedIn':
                # 强制使用原来的客户和房间
                cleaned_data['customer'] = original.customer
                cleaned_data['room'] = original.room
                
                # ----- 规则3：已入住订单不能直接退款 -----
                # 业务逻辑：客人已经住了，不能直接退款
                # 必须先办理离店（CheckedOut），然后再做其他处理
                if cleaned_data.get('status') == 'Refunded':
                    # raise ValidationError 会阻止保存，并在页面显示错误信息
                    raise ValidationError('已入住订单不支持退款，请先办理离店。')
        
        # 返回验证后的数据，Django 会用这些数据保存到数据库
        return cleaned_data


# ================================
# 预订Admin配置类
# ================================

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    """
    预订Admin配置类 - 定义Admin后台的预订管理界面

    """

    form = ReservationAdminForm

    list_display = (
        'id',
        'customer',
        'room',
        'get_room_status',
        'check_in_date',
        'check_out_date',
        'number_of_guests',
        'paid_amount_display',
        'refund_amount_display',
        'income_recorded',
        'refund_recorded',
        'status_colored',
        'created_at'
    )
    

    ordering = ('-check_in_date',)

    list_display_links = ('customer', 'room')

    list_per_page = 20

    search_fields = ['customer__name', 'room__room_number', 'id']

    list_filter = ('status', 'check_in_date', 'room__room_type')

    readonly_fields = (
        'created_at',
        'updated_at',
        'income_recorded',
        'refund_recorded',
        'refund_amount',
        'estimated_amount_display'
    )

    actions = ['make_checkin', 'make_checkout', 'cancel_reservations', 'safe_delete_selected']
    

    fieldsets = (

        (None, {
            'fields': ('customer', 'room', 'check_in_date', 'check_out_date')
        }),

        ('详细信息', {
            'fields': (
                'number_of_guests', 'special_requests', 'status',
                'estimated_amount_display', 'income_recorded',
                'created_at', 'updated_at'
            )
        }),

        ('退款信息', {
            'fields': ('refund_amount', 'refund_recorded'),
            'description': '取消预订后将自动全额退款'
        }),
    )

    def get_actions(self, request):
        """
        重写获取操作列表的方法
        """
        # 调用父类方法获取默认操作列表
        actions = super().get_actions(request)
        # 移除 Django 默认的删除操作
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def estimated_amount_display(self, obj):
        """
        自定义预计金额显示方法（用于编辑页面的只读字段）
        """
        if obj.pk and obj.paid_amount > 0:
            return format_html(
                '<span style="color:#28a745;font-weight:bold;font-size:15px;">￥{}</span>',
                obj.paid_amount
            )
        if not obj.pk:
            return format_html(
                '<span style="color:#6c757d;font-style:italic;">保存后自动计算</span>'
            )
        return '￥0.00'

    estimated_amount_display.short_description = '预计金额'

    def paid_amount_display(self, obj):
        """
        自定义已付金额显示方法（用于列表页面）
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
        自定义退款金额显示方法（用于列表页面）
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
        自定义房间状态显示方法（用于列表页面）
        """
        # 定义状态 → 颜色的映射字典
        colors = {
            'Available': '#28a745',
            'Booked': '#ffc107',
            'Occupied': '#dc3545',
            'Maintenance': '#6c757d'
        }
        return format_html(
            '<span style="color:{};font-weight:bold;">{}</span>',
            colors.get(obj.room.status, '#000'),
            dict(obj.room.ROOM_STATUS).get(obj.room.status, obj.room.status)  # 获取中文名称
        )
    
    get_room_status.short_description = '房间状态'

    def status_colored(self, obj):
        """
        自定义预订状态彩色显示方法（用于列表页面）
        """
        colors = {
            'Booked': '#007bff',
            'CheckedIn': '#28a745',
            'CheckedOut': '#6c757d',
            'Refunded': '#dc3545'
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
        """
        updated = sum(
            1 for r in queryset 
            if r.status == 'Booked' and (
                setattr(r, 'status', 'CheckedIn'),
                r.save(),
                True
            )[-1]
        )

        if updated:
            messages.success(request, f'成功办理{updated}个入住')

    @admin.action(description='批量办理离店')
    def make_checkout(self, request, queryset):
        """
        批量办理离店的操作方法
        """

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
        """
        checkedin_count = queryset.filter(status='CheckedIn').count()
        if checkedin_count > 0:

            messages.error(
                request,
                f'操作已取消！{checkedin_count}个已入住订单不支持退款，请先办理离店。'
            )
            return

        updated = 0
        total = 0
        
        # 只处理已预定状态的订单
        for r in queryset.filter(status='Booked'):
            r.status = 'Refunded'
            r.save()
            updated += 1

            r.refresh_from_db()

            total += r.refund_amount if r.refund_recorded else 0

        if updated:
            messages.success(request, f'成功退订{updated}个，总退款:￥{total}')
        else:
            messages.warning(request, '没有可退订的订单（只有已预定订单可退订）')

    @admin.action(description='删除订单')
    def safe_delete_selected(self, request, queryset):
        """
        安全删除预订的操作方法
        """
        active = queryset.filter(status__in=['Booked', 'CheckedIn'])
        if active.exists():  # 如果存在活跃订单
            messages.error(
                request,
                f'操作已取消！无法删除 {active.count()} 个活跃订单！请先将状态改为已离店或已退订。'
            )
            return

        count = 0
        total = 0
        
        for obj in queryset:

            if obj.status == 'Refunded' and obj.paid_amount > 0 and not obj.refund_recorded:
                total += obj.paid_amount
            obj.delete()
            count += 1

        msg = f'已成功删除 {count} 个预订'
        if total > 0:
            msg += f'，总退款：￥{total}'
        messages.success(request, msg)


    def save_model(self, request, obj, form, change):
        """
        重写模型保存方法
        """
        try:
            obj.save()

            if not change and obj.paid_amount > 0:
                messages.info(request, f'已付金额:￥{obj.paid_amount}')

            if obj.status == 'Refunded' and obj.refund_recorded:
                messages.warning(request, f'已退订，退款:￥{obj.refund_amount}')
                
        except ValidationError as e:
            messages.error(request, f'保存失败:{e}')
            raise

    def delete_model(self, request, obj):
        """
        重写单个对象删除方法
        """
        if obj.status in ['Booked', 'CheckedIn']:
            messages.error(
                request,
                f'无法删除活跃订单（预订号{obj.id}）！请先将状态改为已离店或已退订。'
            )
            return

        room_number = obj.room.room_number
        has_income = obj.income_recorded
        will_refund = obj.status == 'Refunded' and obj.paid_amount > 0 and not obj.refund_recorded
        refund_amount = obj.paid_amount if will_refund else 0
        

        obj.delete()
        messages.success(request, f'预订已删除，房间{room_number}状态已更新')
        if has_income:
            messages.info(request, '收入记录已标记为"已删除"')
        if refund_amount > 0:
            messages.warning(request, f'已创建退款记录：￥{refund_amount}')
