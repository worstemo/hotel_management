"""预订管理模块 - 数据模型 | 系统核心模块"""
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from customers.models import Customer
from rooms.models import Room


class Reservation(models.Model):
    """预订模型 - 管理预订全生命周期，自动处理金额计算、房间状态同步、财务联动"""
    STATUS = (('Booked', '已预定'), ('CheckedIn', '已入住'), ('CheckedOut', '已离店'), ('Refunded', '已退订'))

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name='客户')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, verbose_name='房间')
    check_in_date = models.DateField(verbose_name='入住日期')
    check_out_date = models.DateField(verbose_name='离店日期')
    number_of_guests = models.PositiveIntegerField(verbose_name='入住人数', validators=[MinValueValidator(1), MaxValueValidator(100)])
    special_requests = models.TextField(blank=True, verbose_name='特殊要求')
    status = models.CharField(max_length=20, choices=STATUS, default='Booked', verbose_name='预订状态')
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='已付金额',
                                       help_text='天数×房价自动计算', validators=[MinValueValidator(Decimal('0.00'))])
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='退款金额',
                                         validators=[MinValueValidator(Decimal('0.00'))])
    income_recorded = models.BooleanField(default=False, verbose_name='已记录收入')
    refund_recorded = models.BooleanField(default=False, verbose_name='已退款')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

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
                raise ValidationError('入住日期必须早于离店日期')
            
            # 如果房间已选择，计算应付金额（使用room_id检查避免异常）
            if self.room_id:
                # 计算入住天数（离店日期 - 入住日期）
                days = (self.check_out_date - self.check_in_date).days
                # 计算应付金额 = 天数 × 房间价格，使用Decimal确保精确计算
                self.paid_amount = Decimal(str(days)) * self.room.price
        
        # 检查入住人数是否已设置
        if self.number_of_guests:
            # 验证人数必须在1-100之间
            if self.number_of_guests < 1 or self.number_of_guests > 100:
                # 如果人数无效，抛出ValidationError异常
                raise ValidationError('入住人数必须在1-100之间')
        
        # 检查房间和人数是否都已设置（使用room_id检查避免异常）
        if self.room_id and self.number_of_guests:
            # 验证入住人数不能超过房间容量
            if self.number_of_guests > self.room.capacity:
                # 如果人数超过容量，抛出ValidationError异常
                raise ValidationError(
                    f'人数({self.number_of_guests})超过房间容量({self.room.capacity})'
                )
        
        # 检查房间、入住日期和离店日期是否都已设置（使用room_id检查避免异常）
        if self.room_id and self.check_in_date and self.check_out_date:
            # 查询该房间在相同时段内的冲突预订
            conflict = Reservation.objects.filter(
                room=self.room,  # 筛选同一房间
                status__in=['Booked', 'CheckedIn']  # 只考虑已预定和已入住的订单
            ).filter(
                # 使用Q对象构建复杂查询：检查日期是否有重叠
                Q(check_in_date__lt=self.check_out_date) &  # 现有订单的入住日期早于当前订单的离店日期
                Q(check_out_date__gt=self.check_in_date)  # 现有订单的离店日期晚于当前订单的入住日期
            )
            
            # 如果是编辑现有预订（而非新建），排除自己
            if self.pk:
                # 从冲突查询中排除当前预订本身
                conflict = conflict.exclude(pk=self.pk)
            
            # 如果存在冲突预订
            if conflict.exists():
                # 抛出ValidationError异常，提示该时段已被预订
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
        """同步房间状态：已入住 > 已预订 > 空闲，维修中保持不变"""
        active = Reservation.objects.filter(room=self.room, status__in=['Booked', 'CheckedIn'])
        if active.filter(status='CheckedIn').exists():
            new_status = 'Occupied'
        elif active.filter(status='Booked').exists():
            new_status = 'Booked'
        else:
            new_status = 'Available' if self.room.status != 'Maintenance' else 'Maintenance'
        
        if self.room.status != new_status:
            self.room.status = new_status
            self.room.save()

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
            f'预订号:{self.id}|'  # 预订ID
            f'客户:{self.customer.name}|'  # 客户姓名
            f'房间:{self.room.room_number}|'  # 房间号
            f'{self.check_in_date}至{self.check_out_date}({days}天)|'  # 入住日期范围和天数
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
            f'退款-预订号:{self.id}|'  # 预订ID
            f'客户:{self.customer.name}|'  # 客户姓名
            f'房间:{self.room.room_number}|'  # 房间号
            f'{self.check_in_date}至{self.check_out_date}({days}天)|'  # 入住日期范围和天数
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
                income.description += f'|[已退订-退款￥{self.refund_amount}]'
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
                income.description += '|[预订已删除]'
                # 保存更新后的收入记录
                income.save()
        
        # 调用父类的delete方法，从数据库中删除预订记录
        super().delete(*args, **kwargs)
        
        # 查询该房间的所有活跃预订（已预定或已入住）
        active = Reservation.objects.filter(
            room=room,  # 筛选当前房间
            status__in=['Booked', 'CheckedIn']  # 状态为已预定或已入住
        )
        
        # 如果存在已入住的订单
        if active.filter(status='CheckedIn').exists():
            # 房间状态设为已入住
            new_status = 'Occupied'
        # 否则，如果存在已预定的订单
        elif active.filter(status='Booked').exists():
            # 房间状态设为已预订
            new_status = 'Booked'
        # 否则，没有活跃订单
        else:
            # 如果房间当前不是维修中状态
            if room.status != 'Maintenance':
                # 房间状态设为空闲
                new_status = 'Available'
            else:  # 如果房间是维修中状态
                # 保持维修中状态不变
                new_status = 'Maintenance'
        
        # 如果房间当前状态与新状态不同
        if room.status != new_status:
            # 更新房间状态
            room.status = new_status
            # 保存房间对象到数据库
            room.save()

    def __str__(self):  # 定义模型对象的字符串表示方法
        # 返回格式化的字符串：预订号-客户姓名-房间号
        return f"预订号:{self.id}-{self.customer.name}-{self.room.room_number}"
    
    class Meta:  # 定义模型的元数据
        verbose_name = '预订'  # 在Admin后台显示的单数名称
        verbose_name_plural = '预订'  # 在Admin后台显示的复数名称
        ordering = ['-check_in_date']  # 默认排序方式：按入住日期降序排列
