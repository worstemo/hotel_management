"""员工管理模块 - 数据模型"""
from django.db import models
from django.core.validators import MinValueValidator, RegexValidator
from django.core.exceptions import ValidationError


# 手机号验证器
phone_validator = RegexValidator(
    regex=r'^1[3-9]\d{9}$',
    message='请输入有效的11位手机号'
)


class Employee(models.Model):
    """员工模型"""
    POSITION_CHOICES = (
        ('前台', '前台'),
        ('后厨', '后厨'),
        ('保洁', '保洁'),
        ('保安', '保安'),
        ('经理', '经理')
    )
    STATUS_CHOICES = (
        ('在职', '在职'),
        ('离职', '离职')
    )

    name = models.CharField(max_length=100, verbose_name='姓名')
    position = models.CharField(max_length=100, choices=POSITION_CHOICES, verbose_name='职位')
    phone = models.CharField(max_length=11, verbose_name='联系方式', validators=[phone_validator])
    email = models.EmailField(blank=True, verbose_name='邮箱')
    address = models.TextField(blank=True, verbose_name='地址')
    salary = models.PositiveIntegerField(verbose_name='工资', validators=[MinValueValidator(1)])
    hire_date = models.DateField(verbose_name='入职日期')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='在职', verbose_name='状态')

    def clean(self):
        super().clean()
        if self.salary is not None and self.salary <= 0:
            raise ValidationError({'salary': '工资必须为正整数'})

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = verbose_name_plural = '员工'
