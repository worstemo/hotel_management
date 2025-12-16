"""预订管理模块 - 数据模型 | 系统核心模块"""
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from customers.models import Customer
from rooms.models import Room


class Reservation(models.Model):  # 定义预订模型类，继承自Django的Model基类，用于管理酒店预订业务
    """预订模型 - 管理预订全生命周期，自动处理金额计算、房间状态同步、财务联动"""
    
    # ================================
    # 预订状态常量定义
    # ================================
    # STATUS: 定义预订状态选项的元组，每个元素为(数据库存储值, 前端显示名称)
    # 状态流转: Booked(已预订) → CheckedIn(已入住) → CheckedOut(已离店)
    #          Booked(已预订) → Refunded(已退订)
    STATUS = (
        ('Booked', '已预订'),      # 预订已创建，等待客户入住
        ('CheckedIn', '已入住'),   # 客户已办理入住手续，正在使用房间
        ('CheckedOut', '已离店'),  # 客户已办理退房手续，预订订单完成
        ('Refunded', '已退订')     # 客户取消预订，系统已处理全额退款
    )

    # ================================
    # 外键关联字段
    # ================================
    # customer: 客户外键，建立与Customer模型的多对一关系（N:1）
    # 一个客户可以创建多个预订记录
    # on_delete=CASCADE: 当关联的客户被删除时，该客户的所有预订也会被级联删除
    # verbose_name: 在Django Admin后台界面中显示的字段名称
    customer = models.ForeignKey(
        Customer,                          # 关联的目标模型类
        on_delete=models.CASCADE,          # 删除策略：级联删除
        verbose_name='客户'                # Admin后台显示名称
    )
    
    # room: 房间外键，建立与Room模型的多对一关系（N:1）
    # 一个房间可以有多个预订记录（不同时间段）
    # on_delete=CASCADE: 当关联的房间被删除时，该房间的所有预订也会被级联删除
    room = models.ForeignKey(
        Room,                              # 关联的目标模型类
        on_delete=models.CASCADE,          # 删除策略：级联删除
        verbose_name='房间'                # Admin后台显示名称
    )
    
    # ================================
    # 日期字段
    # ================================
    # check_in_date: 入住日期字段，使用DateField存储日期（格式：YYYY-MM-DD）
    # 在clean()方法中会验证入住日期必须早于离店日期
    check_in_date = models.DateField(
        verbose_name='入住日期'            # Admin后台显示名称
    )
    
    # check_out_date: 离店日期字段，使用DateField存储日期（格式：YYYY-MM-DD）
    # 用于计算入住天数和自动计算付款金额
    check_out_date = models.DateField(
        verbose_name='离店日期'            # Admin后台显示名称
    )
    
    # ================================
    # 入住信息字段
    # ================================
    # number_of_guests: 入住人数字段，使用PositiveIntegerField存储正整数
    # validators: 验证器列表，确保人数在合理范围内（1-100人）
    # MinValueValidator(1): 最小值为1，至少要有1人入住
    # MaxValueValidator(100): 最大值为100，防止异常数据
    # 在clean()方法中还会额外验证人数不超过房间容量
    number_of_guests = models.PositiveIntegerField(
        verbose_name='入住人数',                      # Admin后台显示名称
        validators=[                                  # 字段级验证器列表
            MinValueValidator(1),                     # 最小值验证器：人数 >= 1
            MaxValueValidator(100)                    # 最大值验证器：人数 <= 100
        ]
    )
    
    # special_requests: 特殊要求字段，使用TextField存储长文本
    # blank=True: 表单验证时允许为空（非必填项）
    # 用于记录客户的特殊需求，如：需要加床、无烟房间、高楼层等
    special_requests = models.TextField(
        blank=True,                        # 允许表单提交时为空
        verbose_name='特殊要求'            # Admin后台显示名称
    )
    
    # ================================
    # 状态字段
    # ================================
    # status: 预订状态字段，使用CharField存储字符串
    # max_length=20: 最大长度20个字符，足以存储状态值
    # choices=STATUS: 限制可选值为预订义的STATUS元组，Admin界面显示为下拉框
    # default='Booked': 新建预订时默认状态为"已预订"
    status = models.CharField(
        max_length=20,                     # 字符串最大长度
        choices=STATUS,                    # 可选值限制为STATUS元组中的选项
        default='Booked',                  # 默认值：已预订状态
        verbose_name='预订状态'            # Admin后台显示名称
    )
    
    # ================================
    # 金额字段
    # ================================
    # paid_amount: 已付金额字段，使用DecimalField存储精确的十进制数
    # 使用Decimal而非Float是为了避免浮点数精度问题（金融计算必须精确）
    # max_digits=10: 总位数最多10位（含小数位），可存储最大99999999.99
    # decimal_places=2: 小数位数为2位，精确到分
    # default=0: 默认值为0，在clean()方法中自动计算
    # help_text: 表单帮助提示，说明金额计算方式
    # 金额计算公式: paid_amount = (check_out_date - check_in_date).days × room.price
    paid_amount = models.DecimalField(
        max_digits=10,                                    # 数字总位数（含整数和小数）
        decimal_places=2,                                 # 小数位数
        default=0,                                        # 默认值
        verbose_name='已付金额',                          # Admin后台显示名称
        help_text='天数×房价自动计算',                    # 表单字段的帮助提示文本
        validators=[MinValueValidator(Decimal('0.00'))]   # 验证器：金额不能为负数
    )
    
    # refund_amount: 退款金额字段，使用DecimalField存储
    # 当预订状态变为"已退订"(Refunded)时，_process_refund()方法会自动设置
    # 系统采用全额退款策略：refund_amount = paid_amount
    refund_amount = models.DecimalField(
        max_digits=10,                                    # 数字总位数（含整数和小数）
        decimal_places=2,                                 # 小数位数
        default=0,                                        # 默认值：未退款时为0
        verbose_name='退款金额',                          # Admin后台显示名称
        validators=[MinValueValidator(Decimal('0.00'))]   # 验证器：金额不能为负数
    )
    
    # ================================
    # 财务联动标记字段
    # ================================
    # income_recorded: 收入记录标志，使用BooleanField存储True/False
    # 用于标记该预订是否已在finance_income表中创建对应的收入记录
    # 作用：防止重复创建收入记录（幂等性保证）
    # 在_create_income_record()方法执行后会被设置为True
    income_recorded = models.BooleanField(
        default=False,                     # 默认值：未记录收入
        verbose_name='已记录收入'          # Admin后台显示名称
    )
    
    # refund_recorded: 退款记录标志，使用BooleanField存储True/False
    # 用于标记该预订是否已在finance_expense表中创建对应的退款记录
    # 作用：防止重复创建退款记录（幂等性保证）
    # 在_process_refund()方法执行后会被设置为True
    refund_recorded = models.BooleanField(
        default=False,                     # 默认值：未退款
        verbose_name='已退款'              # Admin后台显示名称
    )
    
    # ================================
    # 时间戳字段
    # ================================
    # created_at: 创建时间字段，使用DateTimeField存储日期时间
    # auto_now_add=True: 仅在对象首次创建(INSERT)时自动设置为当前时间
    # 之后无论如何更新对象，该字段值都不会改变
    # 用于记录预订的创建时间，便于审计和统计
    created_at = models.DateTimeField(
        auto_now_add=True,                 # 仅创建时自动设置当前时间
        verbose_name='创建时间'            # Admin后台显示名称
    )
    
    # updated_at: 更新时间字段，使用DateTimeField存储日期时间
    # auto_now=True: 每次保存对象(INSERT/UPDATE)时都自动更新为当前时间
    # 用于追踪预订的最后修改时间，便于审计
    updated_at = models.DateTimeField(
        auto_now=True,                     # 每次保存时自动更新为当前时间
        verbose_name='更新时间'            # Admin后台显示名称
    )

    def clean(self):  # 定义模型验证方法
        """
        模型验证方法
        执行业务逻辑验证,包括:
        1. 日期有效性检查
        2. 自动计算应付金额
        3. 入住人数检查
        4. 房间日期冲突检测
        """
        super().clean()  # 调用父类的clean方法，执行默认的数据验证
        
        # 检查入住日期和离店日期是否都已设置
        if self.check_in_date and self.check_out_date:
            # 验证入住日期必须早于离店日期
            if self.check_in_date >= self.check_out_date:
                # 如果日期无效，抛出ValidationError异常
                # 普通异常 → 程序崩溃，显示500错误页面
                # ValidationError → 页面友好提示，用户可以修改后重新提交
                raise ValidationError('入住日期必须早于离店日期')
            
            # 如果房间已选择，计算应付金额（使用room_id检查避免异常）
            if self.room_id:
                # 计算入住天数（离店日期 - 入住日期）
                days = (self.check_out_date - self.check_in_date).days
                # 计算应付金额 = 天数 × 房间价格，使用Decimal确保精确计算
                self.paid_amount = Decimal(str(days)) * self.room.price
        
        # 检查房间和人数是否都已设置（使用room_id检查避免异常）
        if self.room_id and self.number_of_guests:
            # 验证入住人数不能超过房间容量
            if self.number_of_guests > self.room.capacity:
                # 如果人数超过容量，抛出ValidationError异常
                raise ValidationError(
                    f'入住人数({self.number_of_guests})超过房间容量({self.room.capacity})'
                )
        

        # 日期冲突检测：防止同一房间在同一时间段被重复预订
        # 检查房间、入住日期、离店日期必须都已填写
        # 使用room_id而非room是为了避免在room未设置时访问room对象导致异常
        if self.room_id and self.check_in_date and self.check_out_date:
            
            # ----------------------------------------------------------
            # 第一步：查询数据库，找出该房间所有"活跃"的预订
            # ----------------------------------------------------------
            # Reservation.objects 是Django ORM的查询管理器
            # .filter() 相当于SQL的WHERE子句，用于筛选数据
            # 
            # 等价SQL: SELECT * FROM reservations_reservation 
            #          WHERE room_id = 当前房间ID 
            #          AND status IN ('Booked', 'CheckedIn')
            #
            conflict = Reservation.objects.filter(
                # 条件1：筛选同一个房间的预订
                room=self.room,
                
                # 条件2：只考虑"活跃"状态的预订（已预订 或 已入住）
                # status__in 是Django ORM的查询语法：
                #   - status 是字段名
                #   - __in 是查询操作符，表示"值在列表中"
                #   - 相当于SQL: status IN ('Booked', 'CheckedIn')
                # 已离店(CheckedOut)和已退订(Refunded)的预订不需要考虑
                status__in=['Booked', 'CheckedIn']
                
            # ----------------------------------------------------------
            # 第二步：在上一步结果中，进一步筛选出日期有重叠的预订
            # ----------------------------------------------------------
            ).filter(
                # Q对象用于构建复杂的查询条件，支持 &(与) 和 |(或) 操作
                # 
                # 日期重叠判断逻辑：
                # 如果 已有预订的入住日期 < 新预订的离店日期
                # 且   已有预订的离店日期 > 新预订的入住日期
                # 则说明两个时间段有重叠
                #
                # __lt 表示 less than (小于)，相当于SQL的 <
                # __gt 表示 greater than (大于)，相当于SQL的 >
                #
                # 等价SQL: AND check_in_date < '新预订离店日期' 
                #          AND check_out_date > '新预订入住日期'
                #
                Q(check_in_date__lt=self.check_out_date) &  # 已有订单的入住日期 < 当前订单的离店日期
                Q(check_out_date__gt=self.check_in_date)    # 已有订单的离店日期 > 当前订单的入住日期
            )
            
            # ----------------------------------------------------------
            # 第三步：如果要编辑现有预订，需要排除自己
            # ----------------------------------------------------------
            # 如果当前预订已存在（有主键pk），就从冲突结果中排除自己
            # self.pk 是当前预订的主键ID
            #   - 新建预订时 self.pk = None
            #   - 编辑预订时 self.pk = 预订ID（如1、2、3...）
            if self.pk:  # 如果是编辑现有预订（pk不为空）
                # .exclude() 是filter的反向操作，表示"排除"符合条件的记录
                # pk=self.pk 表示排除主键等于当前预订ID的记录
                # 等价SQL: AND id != 当前预订ID
                conflict = conflict.exclude(pk=self.pk)
            
            # ----------------------------------------------------------
            # 第四步：检查是否存在冲突，如果存在则阻止保存
            # ----------------------------------------------------------
            # .exists() 返回True或False，表示查询结果是否有数据
            if conflict.exists():  # 如果存在冲突的预订记录
                # 抛出验证错误，阻止保存，并在页面显示错误提示
                raise ValidationError(f'房间{self.room.room_number}该时段已被预订')

    def save(self, *args, **kwargs):  # 重写保存方法，接收任意位置参数和关键字参数
        """
        重写保存方法
        执行流程:
        1. 调用clean()进行数据验证
        2. 检查是否超期需自动离店
        3. 保存到数据库
        4. 同步房间状态
        5. 创建收入记录(如需)
        6. 处理退款(如需)
        """
        self.full_clean()  # 调用full_clean()方法，执行所有验证规则
        
        # 导入date类，用于获取今天的日期
        from datetime import date
        # 检查离店日期是否已过期且订单状态为已入住
        if self.check_out_date and self.check_out_date < date.today():
            # 如果当前状态是已入住
            if self.status == 'CheckedIn':
                # 自动将状态改为已离店
                self.status = 'CheckedOut'
        
        # 判断是否为新建预订（通过检查主键是否为None）
        is_new = self.pk is None
        # 初始化旧状态变量
        old_status = None
        
        # 如果不是新建预订（即编辑现有预订）
        if not is_new:
            try:
                # 从数据库中获取当前预订的旧状态
                old_status = Reservation.objects.get(pk=self.pk).status
            except Reservation.DoesNotExist:  # 如果预订不存在（理论上不应该发生）
                pass  # 忽略异常，继续执行
        
        # 调用父类的save方法，将数据保存到数据库
        super().save(*args, **kwargs)
        
        # 调用内部方法，同步更新房间状态
        self._update_room_status()
        
        # 如果有已付金额且尚未记录收入
        if self.paid_amount > 0 and not self.income_recorded:
            # 调用内部方法，创建收入记录
            self._create_income_record()
        
        # 如果不是新建订单 且 旧状态不是已退订 且 新状态是已退订
        if not is_new and old_status != 'Refunded' and self.status == 'Refunded':
            # 调用内部方法，处理退款
            self._process_refund()

    def _update_room_status(self):
        """
        同步房间状态方法（私有方法，方法名以_开头表示仅供类内部调用）
        
        【功能说明】
        根据该房间的所有预订状态，自动计算并更新房间的当前状态
        
        【状态优先级】（从高到低）
        1. 已入住(Occupied) - 只要有一个"已入住"的预订，房间就是"已入住"
        2. 已预订(Booked)   - 没有入住但有预订，房间就是"已预订"  
        3. 空闲(Available)  - 既没入住也没预订，房间就是"空闲"
        4. 维修中(Maintenance) - 特殊状态，系统不自动修改，需手动设置
        
        【调用时机】
        - 创建预订后
        - 修改预订状态后（入住、离店、退订）
        - 删除预订后
        """
        
        # ----------------------------------------------------------
        # 第一步：查询该房间的所有"活跃"预订
        # ----------------------------------------------------------
        # 查询条件：
        #   - room=self.room：筛选当前预订关联的房间
        #   - status__in=['Booked', 'CheckedIn']：只看"已预订"和"已入住"状态
        # 
        # "已离店"和"已退订"的预订不影响房间状态，所以不查询
        #
        # 等价SQL: SELECT * FROM reservations_reservation 
        #          WHERE room_id = 当前房间ID 
        #          AND status IN ('Booked', 'CheckedIn')
        active = Reservation.objects.filter(
            room=self.room,                      # 筛选当前房间的预订
            status__in=['Booked', 'CheckedIn']   # 只看活跃状态的预订
        )
        
        # ----------------------------------------------------------
        # 第二步：根据优先级判断房间应该是什么状态
        # ----------------------------------------------------------
        # 判断逻辑：
        #   如果有"已入住"的预订 → 房间状态 = 已入住
        #   否则如果有"已预订"的预订 → 房间状态 = 已预订
        #   否则 → 房间状态 = 空闲（除非原本是维修中）
        
        # 情况1：检查是否有"已入住"状态的预订
        # .filter(status='CheckedIn') 进一步筛选出已入住的预订
        # .exists() 返回True/False，表示是否存在符合条件的记录
        if active.filter(status='CheckedIn').exists():
            # 有客人正在住，房间状态应该是"已入住"(Occupied)
            new_status = 'Occupied'
            
        # 情况2：没有入住的，检查是否有"已预订"状态的预订
        elif active.filter(status='Booked').exists():
            # 有预订但还没入住，房间状态应该是"已预订"(Booked)
            new_status = 'Booked'
            
        # 情况3：既没有入住也没有预订
        else:
            # 使用三元表达式（Python的条件表达式）：
            # 格式：值1 if 条件 else 值2
            # 含义：如果条件为True返回值1，否则返回值2
            #
            # 这里的逻辑：
            # - 如果房间原本不是"维修中" → 设为"空闲"
            # - 如果房间原本是"维修中" → 保持"维修中"（不自动改变维修状态）
            new_status = 'Available' if self.room.status != 'Maintenance' else 'Maintenance'

        # ----------------------------------------------------------
        # 第三步：如果状态发生变化，则更新房间并保存到数据库
        # ----------------------------------------------------------
        # 只有当新状态和当前状态不同时才更新，避免不必要的数据库写操作
        if self.room.status != new_status:        # 如果状态有变化
            self.room.status = new_status         # 更新房间对象的status属性
            self.room.save()                      # 将变更保存到数据库

    def _create_income_record(self):  # 定义私有方法，用于创建收入记录
        """
        创建收入记录方法
        在财务系统中自动创建客房收入记录
        并将预订详情填充到描述字段
        """
        from finance.models import Income  # 导入Income模型，用于创建收入记录
        
        # 计算入住天数
        days = (self.check_out_date - self.check_in_date).days
        
        # 构建收入描述文本，包含预订的详细信息
        description = (
            f'预订号:{self.id} | '  # 预订ID
            f'客户:{self.customer.name} | '  # 客户姓名
            f'房间:{self.room.room_number} | '  # 房间号
            f'{self.check_in_date} 至 {self.check_out_date} (共{days}天) | '  # 入住日期范围和天数
            f'人数:{self.number_of_guests}'  # 入住人数
        )
        
        # 在财务系统中创建新的收入记录
        Income.objects.create(
            date=timezone.now().date(),  # 收入日期为当前日期
            amount=self.paid_amount,  # 收入金额为已付金额
            source='Room',  # 收入来源为客房
            description=description  # 收入描述
        )
        
        # 使用update方法将当前预订的income_recorded标记设为True（避免触发save方法）
        Reservation.objects.filter(pk=self.pk).update(income_recorded=True)

    def _process_refund(self):  # 定义私有方法，用于处理退款
        """
        退款处理方法
        执行流程:
        1. 计算退款金额(全额退款)
        2. 创建退款支出记录
        3. 标记原收入记录为已退款
        4. 更新预订退款标记
        """
        # 如果已经退款过或没有已付金额，直接返回
        if self.refund_recorded or self.paid_amount <= 0:
            return  # 结束方法执行
        
        # 导入Income和Expense模型，用于处理退款
        from finance.models import Income, Expense
        
        # 设置退款金额等于已付金额（全额退款）
        self.refund_amount = self.paid_amount
        # 计算入住天数
        days = (self.check_out_date - self.check_in_date).days
        
        # 构建退款描述文本，包含预订的详细信息
        description = (
            f'退款-预订号:{self.id} | '  # 预订ID
            f'客户:{self.customer.name} | '  # 客户姓名
            f'房间:{self.room.room_number} | '  # 房间号
            f'{self.check_in_date} 至 {self.check_out_date}({days}天) | '  # 入住日期范围和天数
            f'退款:￥{self.refund_amount}'  # 退款金额
        )
        
        # 在财务系统中创建新的支出记录（退款）
        Expense.objects.create(
            date=timezone.now().date(),  # 支出日期为当前日期
            amount=self.refund_amount,  # 支出金额为退款金额
            category='Other',  # 支出类别为其他
            description=description  # 支出描述
        )
        
        # 如果之前已记录过收入
        if self.income_recorded:
            # 查找对应的收入记录
            income = Income.objects.filter(
                source='Room',  # 收入来源为客房
                description__contains=f'预订号:{self.id}'  # 描述中包含当前预订号
            ).first()  # 获取第一条匹配的记录
            
            # 如果找到收入记录
            if income:
                # 在收入描述后追加退款标记
                income.description += f' | [已退订-退款￥{self.refund_amount}]'
                # 保存更新后的收入记录
                income.save()
        
        # 使用update方法更新预订的退款标记（避免触发save方法）
        Reservation.objects.filter(pk=self.pk).update(
            refund_recorded=True,  # 标记为已退款
            refund_amount=self.refund_amount  # 记录退款金额
        )

    def delete(self, *args, **kwargs):  # 重写删除方法，接收任意位置参数和关键字参数
        """
        重写删除方法
        删除预订时自动处理:
        1. 退款处理(如需)
        2. 标记收入记录为已删除
        3. 重新评估房间状态
        """
        # 保存房间引用，因为删除后self.room会变为None
        room = self.room
        
        # 只有退订状态的订单删除时才处理退款，已离店订单不退款
        # 如果有已付金额且尚未退款且状态为已退订
        if self.paid_amount > 0 and not self.refund_recorded and self.status == 'Refunded':
            # 调用内部方法处理退款
            self._process_refund()
        
        # 如果已记录过收入
        if self.income_recorded:
            # 导入Income模型
            from finance.models import Income
            # 查找对应的收入记录
            income = Income.objects.filter(
                source='Room',  # 收入来源为客房
                description__contains=f'预订号:{self.id}'  # 描述中包含当前预订号
            ).first()  # 获取第一条匹配的记录
            
            # 如果找到收入记录
            if income:
                # 在收入描述后追加删除标记
                income.description += ' | [预订已删除]'
                # 保存更新后的收入记录
                income.save()
        
        # 调用父类的delete方法，从数据库中删除预订记录
        super().delete(*args, **kwargs)

        # 查询该房间的所有"活跃"预订，查询条件：
        #   - room=room：筛选当前预订关联的房间
        #   - status__in=['Booked', 'CheckedIn']：只看"已预订"和"已入住"状态
        # 等价SQL: SELECT * FROM reservations_reservation
        #          WHERE room_id = 当前房间ID
        #          AND status IN ('Booked', 'CheckedIn')
        active = Reservation.objects.filter(
            room=room,  # 筛选当前房间的预订
            status__in=['Booked', 'CheckedIn']  # 只看活跃状态的预订
        )

        # 根据优先级判断房间应该是什么状态
        #   如果有"已入住"的预订 → 房间状态 = 已入住
        #   否则如果有"已预订"的预订 → 房间状态 = 已预订
        #   否则 → 房间状态 = 空闲（除非原本是维修中）

        # 情况1：检查是否有"已入住"状态的预订
        # .filter(status='CheckedIn') 进一步筛选出已入住的预订
        # .exists() 返回True/False，表示是否存在符合条件的记录
        if active.filter(status='CheckedIn').exists():
            # 有客人正在住，房间状态应该是"已入住"(Occupied)
            new_status = 'Occupied'

        # 情况2：没有入住的，检查是否有"已预订"状态的预订
        elif active.filter(status='Booked').exists():
            # 有预订但还没入住，房间状态应该是"已预订"(Booked)
            new_status = 'Booked'

        # 情况3：既没有入住也没有预订
        else:
            # 如果房间原本不是"维修中" → 设为"空闲"
            # 如果房间原本是"维修中" → 保持"维修中"（不自动改变维修状态）
            new_status = 'Available' if room.status != 'Maintenance' else 'Maintenance'

        # 如果状态发生变化，则更新房间并保存到数据库
        # 只有当新状态和当前状态不同时才更新，避免不必要的数据库写操作
        if room.status != new_status:  # 如果状态有变化
            room.status = new_status  # 更新房间对象的status属性
            room.save()

    def __str__(self):  # 定义模型对象的字符串表示方法
        # 返回格式化的字符串：预订号-客户姓名-房间号
        return f"预订号:{self.id}-{self.customer.name}-{self.room.room_number}"
    
    class Meta:  # 定义模型的元数据
        verbose_name = '预订'  # 在Admin后台显示的单数名称
        verbose_name_plural = '预订'  # 在Admin后台显示的复数名称
        ordering = ['-check_in_date']  # 默认排序方式：按入住日期降序排列
