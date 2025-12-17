"""房间管理模块 - 数据模型"""
from django.db import models
from django.core.validators import MinValueValidator, RegexValidator
from django.core.exceptions import ValidationError


# 房间号验证器
room_number_validator = RegexValidator(
    regex=r'^\d{3}$',
    message='房间号必须是三位数字'
)

class Room(models.Model):
    """房间模型"""
    ROOM_TYPES = (
        ('Single', '单人间'),
        ('Double', '双人间'),
        ('Suite', '套房'),
        ('Deluxe', '豪华间')
    )
    ROOM_STATUS = (
        ('Available', '空闲'),
        ('Booked', '已预订'),
        ('Occupied', '已入住'),
        ('Maintenance', '维修中')
    )

    room_number = models.CharField(max_length=3, unique=True, verbose_name='房间号', validators=[room_number_validator])
    room_type = models.CharField(max_length=50, choices=ROOM_TYPES, verbose_name='房间类型')
    price = models.PositiveIntegerField(verbose_name='价格', validators=[MinValueValidator(1)])
    facilities = models.TextField(verbose_name='设施')
    status = models.CharField(max_length=20, choices=ROOM_STATUS, default='Available', verbose_name='状态')
    floor = models.IntegerField(verbose_name='楼层')
    capacity = models.IntegerField(verbose_name='容纳人数')
    description = models.TextField(blank=True, verbose_name='描述')
    pictures = models.ImageField(upload_to='pictures/', blank=True, null=True, verbose_name='房间主图')

    def clean(self):
        super().clean()
        if self.price is not None and self.price <= 0:
            raise ValidationError({'price': '价格必须为正整数'})

    def __str__(self):
        return self.room_number

    class Meta:
        verbose_name = verbose_name_plural = '房间'
