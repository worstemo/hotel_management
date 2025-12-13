"""
员工管理模块 - 数据模型

本模块定义了员工（Employee）模型，用于存储酒店员工的基本信息。
包含员工姓名、职位、联系方式、薪资、入职日期、状态等字段。
"""

# 导入Django的models模块，用于定义数据库模型
from django.db import models
# 导入最小值验证器和正则表达式验证器
from django.core.validators import MinValueValidator, RegexValidator
# 导入验证错误异常类
from django.core.exceptions import ValidationError


# ================================
# 手机号验证器定义
# ================================
# 创建手机号正则验证器，使用RegexValidator类
#
# 正则表达式详解: r'^1[3-9]\d{9}$'
# ^       - 匹配字符串的开始位置
# 1       - 第一位必须是数字1（中国大陆手机号都以1开头）
# [3-9]   - 第二位必须是3到9之间的数字（目前中国手机号段为13x-19x）
# \d{9}   - 后面必须跟随恰好9位数字（\d表示任意数字，{9}表示重复9次）
# $       - 匹配字符串的结束位置
#
# 示例匹配: 13812345678、15987654321、18666666666
# 示例不匹配: 12345678901（第二位不在3-9范围）、1381234567（只有10位）
phone_validator = RegexValidator(
    regex=r'^1[3-9]\d{9}$',  # 匹配11位手机号的正则表达式
    message='请输入有效的11位手机号'  # 验证失败时显示的错误消息
)


# ================================
# 员工数据模型定义
# ================================
class Employee(models.Model):
    """
    员工模型类 - 存储酒店员工的基本信息、职位、薪资等
    
    继承自Django的Model类，每个Employee实例对应数据库中的一条员工记录。
    
    字段说明:
        name: 员工姓名（必填）
        position: 职位（前台/后厨/保洁/保安/经理）
        phone: 联系电话（11位手机号）
        email: 电子邮箱（选填）
        address: 地址（选填）
        salary: 工资（正整数）
        hire_date: 入职日期
        status: 在职状态（在职/离职）
    """
    
    # 定义职位选项（元组列表）
    # 每个元组包含：（数据库存储值, 显示名称）
    POSITION_CHOICES = (
        ('前台', '前台'),   # 前台接待人员
        ('后厨', '后厨'),   # 后厨工作人员
        ('保洁', '保洁'),   # 保洁人员
        ('保安', '保安'),   # 安保人员
        ('经理', '经理')    # 管理人员
    )
    
    # 定义在职状态选项（元组列表）
    STATUS_CHOICES = (
        ('在职', '在职'),   # 当前在职
        ('离职', '离职')    # 已经离职
    )

    # 姓名字段：使用CharField存储，最大长度100个字符
    name = models.CharField(
        max_length=100,  # 最大长度100个字符
        verbose_name='姓名'  # Admin后台显示的字段名称
    )
    
    # 职位字段：使用CharField存储，限制为预定义的选项
    # choices参数限制可选值，并在Admin中显示为下拉框
    position = models.CharField(
        max_length=100,  # 最大长度100个字符
        choices=POSITION_CHOICES,  # 使用预定义的职位选项
        verbose_name='职位'  # Admin后台显示的字段名称
    )
    
    # 联系电话字段：使用CharField存储，最大长度11个字符
    # validators 指定使用phone_validator正则验证器进行验证
    phone = models.CharField(
        max_length=11,  # 手机号固定11位
        verbose_name='联系方式',  # Admin后台显示的字段名称
        validators=[phone_validator]  # 使用正则验证器验证手机号格式
    )
    
    # 邮箱字段：使用Django内置的EmailField，自动验证邮箱格式
    # blank=True 表示该字段在表单中可以为空（不是必填项）
    email = models.EmailField(
        blank=True,  # 允许为空
        verbose_name='邮箱'  # Admin后台显示的字段名称
    )
    
    # 地址字段：使用TextField存储长文本
    # blank=True 表示该字段可以为空
    address = models.TextField(
        blank=True,  # 允许为空
        verbose_name='地址'  # Admin后台显示的字段名称
    )
    
    # 工资字段：使用PositiveIntegerField存储正整数
    # validators添加最小值验证，确保工资至少为1
    salary = models.PositiveIntegerField(
        verbose_name='工资',  # Admin后台显示的字段名称
        validators=[MinValueValidator(1)]  # 最小值验证器，工资必须>=1
    )
    
    # 入职日期字段：使用DateField存储日期
    hire_date = models.DateField(
        verbose_name='入职日期'  # Admin后台显示的字段名称
    )
    
    # 状态字段：使用CharField存储，限制为预定义的状态选项
    # default指定默认值为'在职'
    status = models.CharField(
        max_length=20,  # 最大长度20个字符
        choices=STATUS_CHOICES,  # 使用预定义的状态选项
        default='在职',  # 默认状态为在职
        verbose_name='状态'  # Admin后台显示的字段名称
    )

    def clean(self):
        """
        模型验证方法
        
        在保存模型之前执行自定义验证逻辑。
        这里再次验证工资必须为正数（作为额外的安全检查）。
        
        异常:
            ValidationError: 当工资小于等于0时抛出
        """
        # 调用父类的clean方法，执行默认验证
        super().clean()
        
        # 检查工资是否为正数（双重保险，字段级验证器也会检查）
        if self.salary is not None and self.salary <= 0:
            # 抛出验证错误，错误信息关联到'salary'字段
            raise ValidationError({'salary': '工资必须为正整数'})

    def __str__(self):
        """
        定义模型对象的字符串表示
        
        当打印Employee对象或在Admin后台显示时调用。
        返回员工姓名作为对象的字符串表示。
        
        返回:
            str: 员工姓名
        """
        return self.name

    class Meta:
        """
        模型的元数据配置类
        
        用于定义模型的额外属性，如显示名称等。
        """
        # 设置模型的单数和复数显示名称
        verbose_name = verbose_name_plural = '员工'
