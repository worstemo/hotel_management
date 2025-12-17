"""财务管理模块 - 数据模型"""
from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError

class Income(models.Model):
    """收入模型"""
    INCOME_SOURCES = (
        ('Room', '客房收入'),
        ('Food', '餐饮收入'),
        ('Other', '其他收入')
    )

    date = models.DateField(verbose_name='日期')
    amount = models.PositiveIntegerField(verbose_name='金额', validators=[MinValueValidator(1)])
    source = models.CharField(max_length=50, choices=INCOME_SOURCES, verbose_name='收入来源')
    description = models.TextField(blank=True, verbose_name='描述')

    def clean(self):
        super().clean()
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({'amount': '金额必须为正整数'})

    def __str__(self):
        return f"{self.date} - {self.source}: {self.amount}"

    class Meta:
        verbose_name = verbose_name_plural = '收入'

class Expense(models.Model):
    """支出模型"""
    EXPENSE_CATEGORIES = (
        ('Salary', '员工工资'),
        ('Maintenance', '维修费用'),
        ('Utilities', '水电费'),
        ('Other', '其他支出')
    )

    date = models.DateField(verbose_name='日期')
    amount = models.PositiveIntegerField(verbose_name='金额', validators=[MinValueValidator(1)])
    category = models.CharField(max_length=50, choices=EXPENSE_CATEGORIES, verbose_name='支出类别')
    description = models.TextField(blank=True, verbose_name='描述')

    def clean(self):
        super().clean()
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({'amount': '金额必须为正整数'})

    def __str__(self):
        return f"{self.date}-{self.category}:{self.amount}"

    class Meta:
        verbose_name = verbose_name_plural = '支出'