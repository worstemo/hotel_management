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
# 
# 【什么是 ModelForm？】
# ModelForm 是 Django 提供的表单类，可以根据模型（Model）自动生成表单字段
# 它会自动处理数据验证、保存到数据库等操作
# 
# 【为什么需要自定义表单？】
# 默认的 ModelForm 会显示所有字段且都可编辑
# 但我们需要根据预订状态动态控制：
#   - 哪些房间可以选择
#   - 哪些状态可以切换
#   - 哪些字段可以修改
#
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
#
# 【什么是 ModelAdmin？】
# ModelAdmin 是 Django Admin 的核心类，用于配置模型在后台的显示和行为
# 通过继承 ModelAdmin 并设置各种属性，可以自定义：
#   - 列表页面显示哪些字段
#   - 编辑页面的布局
#   - 搜索、过滤、排序功能
#   - 批量操作按钮
#   - 保存和删除的行为
#
# 【@admin.register 装饰器】
# 这是 Django 提供的快捷方式，用于将 Admin 类注册到后台
# 等价于：admin.site.register(Reservation, ReservationAdmin)
#
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
    
    # ================================================================
    # 基本配置属性
    # ================================================================
    
    # ----------------------------------------------------------
    # form: 指定使用的表单类
    # ----------------------------------------------------------
    # 默认情况下，Django 会根据模型自动生成表单
    # 这里指定使用我们自定义的 ReservationAdminForm
    # 这样就可以控制字段的可选值、禁用状态等
    form = ReservationAdminForm
    
    # ----------------------------------------------------------
    # list_display: 列表页面显示的字段/方法
    # ----------------------------------------------------------
    # 这个元组定义了列表页面表格的列
    # 可以是：
    #   1. 模型字段名（如 'id', 'customer'）
    #   2. 自定义方法名（如 'status_colored'，方法需要在下面定义）
    #
    # 【效果】打开预订列表页面时，会看到这些列：
    # | 预订号 | 客户 | 房间 | 房间状态 | 入住日期 | ... | 预订状态 | 创建时间 |
    list_display = (
        'id',                   # 预订号（模型的主键字段）
        'customer',             # 客户（外键字段，会显示 Customer 的 __str__ 返回值）
        'room',                 # 房间（外键字段，会显示 Room 的 __str__ 返回值）
        'get_room_status',      # 房间状态（自定义方法，显示彩色状态）
        'check_in_date',        # 入住日期（日期字段）
        'check_out_date',       # 离店日期（日期字段）
        'number_of_guests',     # 入住人数（整数字段）
        'paid_amount_display',  # 已付金额（自定义方法，绿色显示）
        'refund_amount_display',# 退款金额（自定义方法，红色显示）
        'income_recorded',      # 是否已记录收入（布尔字段，显示√或×）
        'refund_recorded',      # 是否已退款（布尔字段）
        'status_colored',       # 预订状态（自定义方法，彩色标签）
        'created_at'            # 创建时间（日期时间字段）
    )
    
    # ----------------------------------------------------------
    # ordering: 默认排序方式
    # ----------------------------------------------------------
    # 定义列表页面的默认排序
    # '-check_in_date' 中的 '-' 表示降序（最新的在前面）
    # 没有 '-' 表示升序
    ordering = ('-check_in_date',)
    
    # ----------------------------------------------------------
    # list_display_links: 可点击进入编辑页面的字段
    # ----------------------------------------------------------
    # 默认情况下，第一列是可点击的链接
    # 这里设置 customer 和 room 列可以点击进入编辑页面
    list_display_links = ('customer', 'room')
    
    # ----------------------------------------------------------
    # list_per_page: 每页显示的记录数
    # ----------------------------------------------------------
    # 列表页面的分页设置，每页显示20条记录
    list_per_page = 20
    
    # ----------------------------------------------------------
    # search_fields: 可搜索的字段
    # ----------------------------------------------------------
    # 定义搜索框可以搜索哪些字段
    # '__' 语法用于跨关系搜索（访问关联模型的字段）
    #   - 'customer__name'：搜索客户的姓名
    #   - 'room__room_number'：搜索房间号
    #   - 'id'：搜索预订号
    #
    # 【效果】在搜索框输入"张三"，会搜索客户姓名包含"张三"的预订
    search_fields = ['customer__name', 'room__room_number', 'id']
    
    # ----------------------------------------------------------
    # list_filter: 右侧过滤器
    # ----------------------------------------------------------
    # 定义列表页面右侧的过滤器选项
    # 可以按这些字段快速筛选数据
    #   - 'status'：按预订状态过滤（已预定/已入住/已离店/已退订）
    #   - 'check_in_date'：按入住日期过滤（今天/过去7天/本月/今年）
    #   - 'room__room_type'：按房间类型过滤（单人间/双人间/套房/豪华间）
    list_filter = ('status', 'check_in_date', 'room__room_type')
    
    # ----------------------------------------------------------
    # readonly_fields: 只读字段
    # ----------------------------------------------------------
    # 这些字段在编辑页面显示但不可修改
    # 通常用于系统自动生成的字段，防止用户手动修改
    readonly_fields = (
        'created_at',              # 创建时间（自动生成）
        'updated_at',              # 更新时间（自动更新）
        'income_recorded',         # 收入记录标志（系统自动设置）
        'refund_recorded',         # 退款记录标志（系统自动设置）
        'refund_amount',           # 退款金额（系统自动计算）
        'estimated_amount_display' # 预计金额显示（自定义只读字段）
    )
    
    # ----------------------------------------------------------
    # actions: 批量操作按钮
    # ----------------------------------------------------------
    # 定义列表页面上方的批量操作下拉菜单
    # 这些是下面定义的方法名，用户勾选多个记录后可以执行这些操作
    actions = ['make_checkin', 'make_checkout', 'cancel_reservations', 'safe_delete_selected']
    
    # ----------------------------------------------------------
    # fieldsets: 编辑页面的字段分组布局
    # ----------------------------------------------------------
    # 定义编辑页面的字段如何分组显示
    # 格式：((组名, {配置}), (组名, {配置}), ...)
    #   - 组名为 None 表示不显示组标题
    #   - 'fields': 该组包含的字段
    #   - 'description': 组的说明文字
    #
    # 【效果】编辑页面会分成三个区域：基本信息、详细信息、退款信息
    fieldsets = (
        # 第一组：基本信息（无标题）
        (None, {
            'fields': ('customer', 'room', 'check_in_date', 'check_out_date')
        }),
        # 第二组：详细信息
        ('详细信息', {
            'fields': (
                'number_of_guests', 'special_requests', 'status',
                'estimated_amount_display', 'income_recorded',
                'created_at', 'updated_at'
            )
        }),
        # 第三组：退款信息（带说明文字）
        ('退款信息', {
            'fields': ('refund_amount', 'refund_recorded'),
            'description': '取消预订后将自动全额退款'  # 显示在组标题下方的提示文字
        }),
    )

    # ================================================================
    # 重写的 Admin 方法
    # ================================================================

    def get_actions(self, request):
        """
        重写获取操作列表的方法
        
        【为什么要重写？】
        Django Admin 默认有一个"删除所选"操作，但它不会执行我们的删除保护逻辑
        所以我们移除默认的删除操作，替换为自定义的 safe_delete_selected
        
        参数:
            request: HTTP请求对象（包含用户信息等）
        
        返回:
            dict: 可用的操作字典 {操作名: (方法, 操作名, 描述)}
        """
        # 调用父类方法获取默认操作列表
        actions = super().get_actions(request)
        # 移除 Django 默认的删除操作
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    # ================================================================
    # 自定义显示方法（用于 list_display 和 readonly_fields）
    # ================================================================
    #
    # 【自定义显示方法的规则】
    # 1. 方法接收 self 和 obj 参数，obj 是当前行的模型对象
    # 2. 返回要显示的内容（可以是 HTML）
    # 3. 使用 format_html() 安全地渲染 HTML
    # 4. 设置 .short_description 属性作为列标题
    # 5. 设置 .admin_order_field 属性允许按该列排序
    #

    def estimated_amount_display(self, obj):
        """
        自定义预计金额显示方法（用于编辑页面的只读字段）
        
        【功能】
        在编辑页面显示预计金额，新建时显示"保存后自动计算"
        
        参数:
            obj (Reservation): 当前预订对象
        
        返回:
            str: HTML格式的金额或提示信息
        """
        # 如果是已存在的订单且有已付金额
        if obj.pk and obj.paid_amount > 0:
            # 返回绿色粗体的金额
            # format_html() 安全地渲染 HTML，防止 XSS 攻击
            # {} 是占位符，会被后面的参数替换
            return format_html(
                '<span style="color:#28a745;font-weight:bold;font-size:15px;">￥{}</span>',
                obj.paid_amount
            )
        # 如果是新建订单（还没有 pk）
        if not obj.pk:
            # 显示灰色斜体的提示文本
            return format_html(
                '<span style="color:#6c757d;font-style:italic;">保存后自动计算</span>'
            )
        return '￥0.00'
    
    # .short_description 设置该字段在页面上显示的标题
    estimated_amount_display.short_description = '预计金额'

    def paid_amount_display(self, obj):
        """
        自定义已付金额显示方法（用于列表页面）
        
        【功能】
        在列表页面以绿色粗体样式显示已付金额
        
        参数:
            obj (Reservation): 当前预订对象
        
        返回:
            str: HTML格式的金额字符串
        """
        if obj.paid_amount > 0:
            # 绿色(#28a745)表示收入/正数金额
            return format_html(
                '<span style="color:#28a745;font-weight:bold;">￥{}</span>',
                obj.paid_amount
            )
        return '￥0.00'
    
    paid_amount_display.short_description = '已付金额'  # 列标题
    # .admin_order_field 指定点击列标题时按哪个字段排序
    # 这样用户点击"已付金额"列标题时，会按 paid_amount 字段排序
    paid_amount_display.admin_order_field = 'paid_amount'

    def refund_amount_display(self, obj):
        """
        自定义退款金额显示方法（用于列表页面）

        【功能】
        在列表页面以红色粗体样式显示退款金额
        退款金额为0时显示 '-'

        参数:
            obj (Reservation): 当前预订对象

        返回:
            str: HTML格式的金额字符串或'-'
        """
        if obj.refund_amount > 0:
            # 红色(#dc3545)表示支出/退款金额
            return format_html(
                '<span style="color:#dc3545;font-weight:bold;">￥{}</span>',
                obj.refund_amount
            )
        return '-'  # 没有退款时显示横线
    
    refund_amount_display.short_description = '退款金额'
    refund_amount_display.admin_order_field = 'refund_amount'

    def get_room_status(self, obj):
        """
        自定义房间状态显示方法（用于列表页面）
        
        【功能】
        以不同颜色显示关联房间的当前状态
        这样用户可以快速看到房间是空闲还是已占用
        
        参数:
            obj (Reservation): 当前预订对象
        
        返回:
            str: HTML格式的彩色状态文本
        """
        # 定义状态 → 颜色的映射字典
        colors = {
            'Available': '#28a745',    # 空闲 - 绿色（可预订）
            'Booked': '#ffc107',       # 已预订 - 黄色（等待入住）
            'Occupied': '#dc3545',     # 已入住 - 红色（使用中）
            'Maintenance': '#6c757d'   # 维修中 - 灰色（不可用）
        }
        # format_html 的第一个参数是模板，{} 会被后面的参数依次替换
        # obj.room.status 获取房间的状态值（如 'Available'）
        # dict(obj.room.ROOM_STATUS) 将元组转为字典，用于获取中文名称
        return format_html(
            '<span style="color:{};font-weight:bold;">{}</span>',
            colors.get(obj.room.status, '#000'),  # 获取颜色，默认黑色
            dict(obj.room.ROOM_STATUS).get(obj.room.status, obj.room.status)  # 获取中文名称
        )
    
    get_room_status.short_description = '房间状态'

    def status_colored(self, obj):
        """
        自定义预订状态彩色显示方法（用于列表页面）
        
        【功能】
        以不同颜色的圆角标签显示预订状态
        这是列表页面最右侧的状态列
        
        颜色对应关系:
            - Booked(已预定): 蓝色 - 表示等待中
            - CheckedIn(已入住): 绿色 - 表示进行中
            - CheckedOut(已离店): 灰色 - 表示已完成
            - Refunded(已退订): 红色 - 表示已取消
        
        参数:
            obj (Reservation): 当前预订对象
        
        返回:
            str: HTML格式的彩色状态标签
        """
        colors = {
            'Booked': '#007bff',     # 已预定 - 蓝色
            'CheckedIn': '#28a745',  # 已入住 - 绿色
            'CheckedOut': '#6c757d', # 已离店 - 灰色
            'Refunded': '#dc3545'    # 已退订 - 红色
        }
        # 创建一个带背景色的圆角标签
        # padding: 内边距，border-radius: 圆角
        return format_html(
            '<span style="background:{};color:white;padding:5px 12px;border-radius:4px;">{}</span>',
            colors.get(obj.status, '#000'),
            dict(obj.STATUS).get(obj.status, obj.status)  # 获取中文状态名
        )
    
    status_colored.short_description = '预订状态'

    # ================================================================
    # 批量操作方法（用于 actions）
    # ================================================================
    #
    # 【批量操作的规则】
    # 1. 使用 @admin.action(description='操作名称') 装饰器
    # 2. 方法接收 self, request, queryset 三个参数
    # 3. queryset 是用户勾选的记录的查询集
    # 4. 使用 messages 模块显示操作结果
    #

    @admin.action(description='批量办理入住')
    def make_checkin(self, request, queryset):
        """
        批量办理入住的操作方法
        
        【功能】
        将选中的"已预定"订单状态改为"已入住"
        其他状态的订单会被忽略
        
        参数:
            request: HTTP请求对象
            queryset: 用户勾选的预订记录查询集
        """
        # ----------------------------------------------------------
        # 遍历选中的订单，只处理状态为 Booked 的
        # ----------------------------------------------------------
        # 这是一个较复杂的 Python 写法，分解说明：
        # 
        # sum(...) 计算总数
        # for r in queryset 遍历所有选中的记录
        # if r.status == 'Booked' 只处理已预定的订单
        # and (...) 后面是一个元组表达式，执行多个操作
        #   setattr(r, 'status', 'CheckedIn') 设置状态为已入住
        #   r.save() 保存到数据库（会触发模型的 save 方法，自动更新房间状态）
        #   True 最后返回 True
        # [-1] 取元组最后一个元素（True）
        #
        # 【简化理解】相当于：
        # updated = 0
        # for r in queryset:
        #     if r.status == 'Booked':
        #         r.status = 'CheckedIn'
        #         r.save()
        #         updated += 1
        #
        updated = sum(
            1 for r in queryset 
            if r.status == 'Booked' and (
                setattr(r, 'status', 'CheckedIn'),
                r.save(),
                True
            )[-1]
        )
        # 显示成功消息（绿色提示框）
        if updated:
            messages.success(request, f'成功办理{updated}个入住')

    @admin.action(description='批量办理离店')
    def make_checkout(self, request, queryset):
        """
        批量办理离店的操作方法
        
        【功能】
        将选中的"已入住"订单状态改为"已离店"
        其他状态的订单会被忽略
        
        参数:
            request: HTTP请求对象
            queryset: 用户勾选的预订记录查询集
        """
        # 只处理状态为 CheckedIn 的订单
        updated = sum(
            1 for r in queryset 
            if r.status == 'CheckedIn' and (
                setattr(r, 'status', 'CheckedOut'),
                r.save(),  # 保存会触发房间状态更新为 Available
                True
            )[-1]
        )
        if updated:
            messages.success(request, f'成功办理{updated}个离店')

    @admin.action(description='批量退订(自动退款)')
    def cancel_reservations(self, request, queryset):
        """
        批量退订的操作方法
        
        【功能】
        将选中的"已预定"订单状态改为"已退订"
        系统会自动处理全额退款（创建 Expense 记录）
        
        【限制】
        已入住订单不允许退订，必须先办理离店
        
        参数:
            request: HTTP请求对象
            queryset: 用户勾选的预订记录查询集
        """
        # ----------------------------------------------------------
        # 第一步：检查是否有已入住订单（不允许退款）
        # ----------------------------------------------------------
        checkedin_count = queryset.filter(status='CheckedIn').count()
        if checkedin_count > 0:
            # 显示错误消息（红色提示框），中断操作
            messages.error(
                request,
                f'操作已取消！{checkedin_count}个已入住订单不支持退款，请先办理离店。'
            )
            return  # 直接返回，不执行后续操作
        
        # ----------------------------------------------------------
        # 第二步：处理已预定订单的退订
        # ----------------------------------------------------------
        updated = 0  # 退订数量
        total = 0    # 总退款金额
        
        # 只处理已预定状态的订单
        for r in queryset.filter(status='Booked'):
            r.status = 'Refunded'  # 设置状态为已退订
            r.save()  # 保存会触发模型的 _process_refund() 方法，自动创建退款记录
            updated += 1
            
            # refresh_from_db() 重新从数据库读取数据
            # 因为 _process_refund() 使用 update() 更新数据库
            # 当前对象的 refund_amount 可能还是旧值，需要刷新
            r.refresh_from_db()
            
            # 累加退款金额
            total += r.refund_amount if r.refund_recorded else 0
        
        # ----------------------------------------------------------
        # 第三步：显示操作结果
        # ----------------------------------------------------------
        if updated:
            messages.success(request, f'成功退订{updated}个，总退款:￥{total}')
        else:
            # 如果没有处理任何订单，显示警告消息（黄色提示框）
            messages.warning(request, '没有可退订的订单（只有已预定订单可退订）')

    @admin.action(description='删除订单')
    def safe_delete_selected(self, request, queryset):
        """
        安全删除预订的操作方法
        
        【功能】
        删除选中的预订记录，但有保护机制：
        活跃订单（已预定或已入住）不允许删除
        
        【为什么需要安全删除？】
        - 已预定订单：客户可能还会来入住，不能随便删
        - 已入住订单：客户正在住，绝对不能删
        - 已离店/已退订：业务已完成，可以删除历史记录
        
        参数:
            request: HTTP请求对象
            queryset: 用户勾选的预订记录查询集
        """
        # ----------------------------------------------------------
        # 第一步：检查是否有活跃订单
        # ----------------------------------------------------------
        # status__in 是 Django ORM 的查询语法
        # 相当于 SQL: WHERE status IN ('Booked', 'CheckedIn')
        active = queryset.filter(status__in=['Booked', 'CheckedIn'])
        if active.exists():  # 如果存在活跃订单
            messages.error(
                request,
                f'操作已取消！无法删除 {active.count()} 个活跃订单！请先将状态改为已离店或已退订。'
            )
            return
        
        # ----------------------------------------------------------
        # 第二步：执行删除
        # ----------------------------------------------------------
        count = 0  # 删除数量
        total = 0  # 总退款金额
        
        for obj in queryset:
            # 如果是退订订单且有已付金额且未退款，累加退款金额
            if obj.status == 'Refunded' and obj.paid_amount > 0 and not obj.refund_recorded:
                total += obj.paid_amount
            obj.delete()  # 删除订单（会触发模型的 delete() 方法）
            count += 1
        
        # ----------------------------------------------------------
        # 第三步：显示操作结果
        # ----------------------------------------------------------
        msg = f'已成功删除 {count} 个预订'
        if total > 0:
            msg += f'，总退款：￥{total}'
        messages.success(request, msg)

    # ================================================================
    # 重写的保存和删除方法
    # ================================================================

    def save_model(self, request, obj, form, change):
        """
        重写模型保存方法
        
        【什么时候调用？】
        用户在编辑页面点击"保存"按钮后，Django 调用此方法
        
        【参数说明】
            request: HTTP请求对象（包含当前用户等信息）
            obj: 要保存的预订对象（已填充表单数据）
            form: 表单实例
            change: 布尔值，True=修改现有记录，False=新建记录
        """
        try:
            obj.save()  # 调用模型的 save() 方法保存到数据库
            
            # 新建订单时显示已付金额（提示用户金额是多少）
            if not change and obj.paid_amount > 0:
                # messages.info 显示蓝色信息提示框
                messages.info(request, f'已付金额:￥{obj.paid_amount}')
            
            # 退订时显示退款信息
            if obj.status == 'Refunded' and obj.refund_recorded:
                # messages.warning 显示黄色警告提示框
                messages.warning(request, f'已退订，退款:￥{obj.refund_amount}')
                
        except ValidationError as e:
            # 如果保存过程中发生验证错误，显示错误消息
            messages.error(request, f'保存失败:{e}')
            raise  # 重新抛出异常，阻止保存

    def delete_model(self, request, obj):
        """
        重写单个对象删除方法
        
        【什么时候调用？】
        用户在编辑页面点击"删除"按钮后，Django 调用此方法
        （与批量删除 safe_delete_selected 不同，这是单个删除）
        
        【参数说明】
            request: HTTP请求对象
            obj: 要删除的预订对象
        """
        # ----------------------------------------------------------
        # 删除保护：检查是否为活跃订单
        # ----------------------------------------------------------
        if obj.status in ['Booked', 'CheckedIn']:
            messages.error(
                request,
                f'无法删除活跃订单（预订号{obj.id}）！请先将状态改为已离店或已退订。'
            )
            return  # 直接返回，不执行删除
        
        # ----------------------------------------------------------
        # 保存删除前的信息（删除后就获取不到了）
        # ----------------------------------------------------------
        room_number = obj.room.room_number
        has_income = obj.income_recorded
        will_refund = obj.status == 'Refunded' and obj.paid_amount > 0 and not obj.refund_recorded
        refund_amount = obj.paid_amount if will_refund else 0
        
        # ----------------------------------------------------------
        # 执行删除
        # ----------------------------------------------------------
        obj.delete()  # 调用模型的 delete() 方法，会自动更新房间状态
        
        # ----------------------------------------------------------
        # 显示操作结果
        # ----------------------------------------------------------
        messages.success(request, f'预订已删除，房间{room_number}状态已更新')
        if has_income:
            messages.info(request, '收入记录已标记为"已删除"')
        if refund_amount > 0:
            messages.warning(request, f'已创建退款记录：￥{refund_amount}')
