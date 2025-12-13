"""
财务管理模块 - 数据模型

本模块定义了收入（Income）和支出（Expense）两个模型，
用于记录酒店的财务数据，包括各类收入和支出记录。
"""

# 导入Django的models模块，用于定义数据库模型
from django.db import models
# 导入最小值验证器，用于确保金额字段的有效性
from django.core.validators import MinValueValidator
# 导入验证错误异常类，用于在验证失败时抛出异常
from django.core.exceptions import ValidationError


# ================================
# 收入数据模型定义
# ================================
class Income(models.Model):
    """
    收入模型类 - 记录酒店所有收入，包括客房收入、餐饮收入等
    
    继承自Django的Model类，每个Income实例对应数据库中的一条收入记录。
    
    字段说明:
        date: 收入日期
        amount: 收入金额（正整数）
        source: 收入来源（客房/餐饮/其他）
        description: 收入描述（选填）
    
    与预订系统的关联:
        当预订创建时，系统会自动创建客房收入记录，
        并在描述字段中记录预订详情。
    """
    
    # 定义收入来源选项（元组列表）
    # 每个元组包含：（数据库存储值, 显示名称）
    INCOME_SOURCES = (
        ('Room', '客房收入'),   # 客房入住收入
        ('Food', '餐饮收入'),   # 餐饮服务收入
        ('Other', '其他收入')  # 其他类型收入
    )

    # 日期字段：使用DateField存储日期
    date = models.DateField(
        verbose_name='日期'  # Admin后台显示的字段名称
    )
    
    # 金额字段：使用PositiveIntegerField存储正整数
    # validators添加最小值验证，确保金额至少为1
    amount = models.PositiveIntegerField(
        verbose_name='金额',  # Admin后台显示的字段名称
        validators=[MinValueValidator(1)]  # 最小值验证器，金额必须>=1
    )
    
    # 来源字段：使用CharField存储，限制为预定义的选项
    # choices参数限制可选值，并在Admin中显示为下拉框
    source = models.CharField(
        max_length=50,  # 最大长度50个字符
        choices=INCOME_SOURCES,  # 使用预定义的收入来源选项
        verbose_name='收入来源'  # Admin后台显示的字段名称
    )
    
    # 描述字段：使用TextField存储长文本
    # blank=True 表示该字段可以为空
    description = models.TextField(
        blank=True,  # 允许为空
        verbose_name='描述'  # Admin后台显示的字段名称
    )

    def clean(self):
        """
        模型验证方法
        
        在保存模型之前执行自定义验证逻辑。
        这里再次验证金额必须为正数（作为额外的安全检查）。
        
        异常:
            ValidationError: 当金额小于等于0时抛出
        """
        # 调用父类的clean方法，执行默认验证
        super().clean()
        
        # 检查金额是否为正数（双重保险，字段级验证器也会检查）
        if self.amount is not None and self.amount <= 0:
            # 抛出验证错误，错误信息关联到'amount'字段
            raise ValidationError({'amount': '金额必须为正整数'})

    def __str__(self):
        """
        定义模型对象的字符串表示
        
        当打印Income对象或在Admin后台显示时调用。
        返回格式化的字符串：日期-来源:金额
        
        返回:
            str: 格式化的收入信息
        """
        return f"{self.date}-{self.source}:{self.amount}"

    class Meta:
        """
        模型的元数据配置类
        
        用于定义模型的额外属性，如显示名称等。
        """
        # 设置模型的单数和复数显示名称
        verbose_name = verbose_name_plural = '收入'


# ================================
# 支出数据模型定义
# ================================
class Expense(models.Model):
    """
    支出模型类 - 记录酒店所有支出，包括工资、维修、水电等
    
    继承自Django的Model类，每个Expense实例对应数据库中的一条支出记录。
    
    字段说明:
        date: 支出日期
        amount: 支出金额（正整数）
        category: 支出类别（工资/维修/水电/其他）
        description: 支出描述（选填）
    
    与预订系统的关联:
        当预订退款时，系统会自动创建支出记录（类别为'其他'），
        并在描述字段中记录退款详情。
    """
    
    # 定义支出类别选项（元组列表）
    # 每个元组包含：（数据库存储值, 显示名称）
    EXPENSE_CATEGORIES = (
        ('Salary', '员工工资'),      # 员工薪资支出
        ('Maintenance', '维修费用'),  # 设备维修支出
        ('Utilities', '水电费'),       # 水电费用支出
        ('Other', '其他支出')        # 其他类型支出（包括退款）
    )

    # 日期字段：使用DateField存储日期
    date = models.DateField(
        verbose_name='日期'  # Admin后台显示的字段名称
    )
    
    # 金额字段：使用PositiveIntegerField存储正整数
    # validators添加最小值验证，确保金额至少为1
    amount = models.PositiveIntegerField(
        verbose_name='金额',  # Admin后台显示的字段名称
        validators=[MinValueValidator(1)]  # 最小值验证器，金额必须>=1
    )
    
    # 类别字段：使用CharField存储，限制为预定义的选项
    # choices参数限制可选值，并在Admin中显示为下拉框
    category = models.CharField(
        max_length=50,  # 最大长度50个字符
        choices=EXPENSE_CATEGORIES,  # 使用预定义的支出类别选项
        verbose_name='支出类别'  # Admin后台显示的字段名称
    )
    
    # 描述字段：使用TextField存储长文本
    # blank=True 表示该字段可以为空
    description = models.TextField(
        blank=True,  # 允许为空
        verbose_name='描述'  # Admin后台显示的字段名称
    )

    def clean(self):
        """
        模型验证方法
        
        在保存模型之前执行自定义验证逻辑。
        这里再次验证金额必须为正数（作为额外的安全检查）。
        
        异常:
            ValidationError: 当金额小于等于0时抛出
        """
        # 调用父类的clean方法，执行默认验证
        super().clean()
        
        # 检查金额是否为正数（双重保险，字段级验证器也会检查）
        if self.amount is not None and self.amount <= 0:
            # 抛出验证错误，错误信息关联到'amount'字段
            raise ValidationError({'amount': '金额必须为正整数'})

    def __str__(self):
        """
        定义模型对象的字符串表示
        
        当打印Expense对象或在Admin后台显示时调用。
        返回格式化的字符串：日期-类别:金额
        
        返回:
            str: 格式化的支出信息
        """
        return f"{self.date}-{self.category}:{self.amount}"

    class Meta:
        """
        模型的元数据配置类
        
        用于定义模型的额外属性，如显示名称等。
        """
        # 设置模型的单数和复数显示名称
        verbose_name = verbose_name_plural = '支出'