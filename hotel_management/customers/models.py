"""客户管理模块 - 数据模型"""

from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
import re
from datetime import datetime


# 手机号验证器
phone_validator = RegexValidator(
    regex=r'^1[3-9]\d{9}$',
    message='请输入有效的11位手机号'
)


def validate_id_number(value):
    """验证18位身份证号格式"""
    pattern = r'^[1-9]\d{5}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]$'
    if not re.match(pattern, value):
        raise ValidationError('请输入有效的18位身份证号')
    
    # 验证出生日期有效性
    year, month, day = int(value[6:10]), int(value[10:12]), int(value[12:14])
    try:
        datetime(year, month, day)
    except ValueError:
        raise ValidationError('身份证号中的出生日期无效')


class Customer(models.Model):
    """客户模型"""
    name = models.CharField(max_length=100, verbose_name='姓名')
    id_number = models.CharField(
        max_length=18, unique=True, verbose_name='身份证号',
        validators=[validate_id_number]
    )
    phone = models.CharField(
        max_length=11, verbose_name='联系方式',
        validators=[phone_validator]
    )
    email = models.EmailField(blank=True, verbose_name='邮箱')
    address = models.TextField(blank=True, verbose_name='地址')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = verbose_name_plural = '客户'