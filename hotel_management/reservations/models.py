"""预订管理模块 - 数据模型"""
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from customers.models import Customer
from rooms.models import Room


class Reservation(models.Model):
    """预订模型 - 管理预订全生命周期"""
    STATUS = (
        ('Booked', '已预订'),
        ('CheckedIn', '已入住'),
        ('CheckedOut', '已离店'),
        ('Refunded', '已退订')
    )

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name='客户')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, verbose_name='房间')
    check_in_date = models.DateField(verbose_name='入住日期')
    check_out_date = models.DateField(verbose_name='离店日期')
    number_of_guests = models.PositiveIntegerField(verbose_name='入住人数', validators=[MinValueValidator(1), MaxValueValidator(100)])
    special_requests = models.TextField(blank=True, verbose_name='特殊要求')
    status = models.CharField(max_length=20, choices=STATUS, default='Booked', verbose_name='预订状态')
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='已付金额', help_text='天数×房价自动计算', validators=[MinValueValidator(Decimal('0.00'))])
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='退款金额', validators=[MinValueValidator(Decimal('0.00'))])
    income_recorded = models.BooleanField(default=False, verbose_name='已记录收入')
    refund_recorded = models.BooleanField(default=False, verbose_name='已退款')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    def clean(self):
        super().clean()
        if self.check_in_date and self.check_out_date:
            if self.check_in_date >= self.check_out_date:
                raise ValidationError('入住日期必须早于离店日期')
            if self.room_id:
                days = (self.check_out_date - self.check_in_date).days
                self.paid_amount = Decimal(str(days)) * self.room.price
        if self.room_id and self.number_of_guests:
            if self.number_of_guests > self.room.capacity:
                raise ValidationError(f'入住人数({self.number_of_guests})超过房间容量({self.room.capacity})')
        if self.room_id and self.check_in_date and self.check_out_date:
            conflict = Reservation.objects.filter(room=self.room, status__in=['Booked', 'CheckedIn']).filter(
                Q(check_in_date__lt=self.check_out_date) & Q(check_out_date__gt=self.check_in_date)
            )
            if self.pk:
                conflict = conflict.exclude(pk=self.pk)
            if conflict.exists():
                raise ValidationError(f'房间{self.room.room_number}该时段已被预订')

    def save(self, *args, **kwargs):
        self.full_clean()
        from datetime import date
        if self.check_out_date and self.check_out_date < date.today():
            if self.status == 'CheckedIn':
                self.status = 'CheckedOut'
        is_new = self.pk is None
        old_status = None
        if not is_new:
            try:
                old_status = Reservation.objects.get(pk=self.pk).status
            except Reservation.DoesNotExist:
                pass
        super().save(*args, **kwargs)
        self._update_room_status()
        if self.paid_amount > 0 and not self.income_recorded:
            self._create_income_record()
        if not is_new and old_status != 'Refunded' and self.status == 'Refunded':
            self._process_refund()

    def _update_room_status(self):
        """同步房间状态"""
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

    def _create_income_record(self):
        """创建收入记录"""
        from finance.models import Income
        days = (self.check_out_date - self.check_in_date).days
        description = (f'预订号:{self.id} | 客户:{self.customer.name} | 房间:{self.room.room_number} | '
                      f'{self.check_in_date} 至 {self.check_out_date} (共{days}天) | 人数:{self.number_of_guests}')
        Income.objects.create(date=timezone.now().date(), amount=self.paid_amount, source='Room', description=description)
        Reservation.objects.filter(pk=self.pk).update(income_recorded=True)

    def _process_refund(self):
        """处理退款"""
        if self.refund_recorded or self.paid_amount <= 0:
            return
        from finance.models import Income, Expense
        self.refund_amount = self.paid_amount
        days = (self.check_out_date - self.check_in_date).days
        description = (f'退款-预订号:{self.id} | 客户:{self.customer.name} | 房间:{self.room.room_number} | '
                      f'{self.check_in_date} 至 {self.check_out_date}({days}天) | 退款:￥{self.refund_amount}')
        Expense.objects.create(date=timezone.now().date(), amount=self.refund_amount, category='Other', description=description)
        if self.income_recorded:
            income = Income.objects.filter(source='Room', description__contains=f'预订号:{self.id}').first()
            if income:
                income.description += f' | [已退订-退款￥{self.refund_amount}]'
                income.save()
        Reservation.objects.filter(pk=self.pk).update(refund_recorded=True, refund_amount=self.refund_amount)

    def delete(self, *args, **kwargs):
        """删除预订并处理退款"""
        room = self.room
        if self.paid_amount > 0 and not self.refund_recorded and self.status == 'Refunded':
            self._process_refund()
        if self.income_recorded:
            from finance.models import Income
            income = Income.objects.filter(source='Room', description__contains=f'预订号:{self.id}').first()
            if income:
                income.description += ' | [预订已删除]'
                income.save()
        super().delete(*args, **kwargs)
        active = Reservation.objects.filter(room=room, status__in=['Booked', 'CheckedIn'])
        if active.filter(status='CheckedIn').exists():
            new_status = 'Occupied'
        elif active.filter(status='Booked').exists():
            new_status = 'Booked'
        else:
            new_status = 'Available' if room.status != 'Maintenance' else 'Maintenance'
        if room.status != new_status:
            room.status = new_status
            room.save()

    def __str__(self):
        return f"预订号:{self.id}-{self.customer.name}-{self.room.room_number}"
    
    class Meta:
        verbose_name = '预订'
        verbose_name_plural = '预订'
        ordering = ['-check_in_date']
