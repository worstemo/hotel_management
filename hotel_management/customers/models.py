"""
客户管理模块 - 数据模型

本模块定义了客户（Customer）模型，用于存储酒店客户的基本信息。
包含手机号和身份证号的正则表达式验证功能。
"""

# 导入Django的models模块，用于定义数据库模型
from django.db import models
# 导入正则表达式验证器，用于创建自定义字段验证规则
from django.core.validators import RegexValidator
# 导入验证错误异常类，用于在验证失败时抛出异常
from django.core.exceptions import ValidationError
# 导入Python内置的正则表达式模块，用于模式匹配
import re


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
# 身份证号验证函数
# ================================
def validate_id_number(value):
    """
    验证18位身份证号格式的自定义验证函数
    
    参数:
        value (str): 需要验证的身份证号字符串
    
    异常:
        ValidationError: 当身份证号格式不正确时抛出
    
    身份证号码结构（18位）:
        - 第1-6位：地址码（省市区代码）
        - 第7-14位：出生日期码（YYYYMMDD）
        - 第15-17位：顺序码（其中第17位奇数为男，偶数为女）
        - 第18位：校验码（0-9或X）
    """
    # 定义18位身份证号的正则表达式模式
    # 
    # 正则表达式详解: r'^[1-9]\d{5}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]$'
    #
    # ^           - 匹配字符串开始位置
    # [1-9]       - 第1位：1-9的数字（地址码首位不能为0）
    # \d{5}       - 第2-6位：5位任意数字（组成6位地址码）
    # (19|20)     - 第7-8位：年份前两位，只能是19或20（表示1900-2099年）
    # \d{2}       - 第9-10位：年份后两位，任意两位数字
    # (0[1-9]|1[0-2])  - 第11-12位：月份
    #                    0[1-9] 表示01-09月
    #                    1[0-2] 表示10-12月
    # (0[1-9]|[12]\d|3[01]) - 第13-14位：日期
    #                         0[1-9]  表示01-09日
    #                         [12]\d  表示10-29日（[12]匹配1或2，\d匹配任意数字）
    #                         3[01]   表示30-31日
    # \d{3}       - 第15-17位：顺序码，3位任意数字
    # [\dXx]      - 第18位：校验码，可以是数字0-9或字母X（大小写均可）
    # $           - 匹配字符串结束位置
    #
    # 示例匹配: 110101199003076512、320106200112250019、44010019850101123X
    # 示例不匹配: 011010199003076512（首位为0）、11010119900376512（月份13无效）
    pattern = r'^[1-9]\d{5}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]$'
    
    # 使用re.match()函数检查身份证号是否匹配正则表达式
    # re.match()从字符串开头开始匹配，返回Match对象或None
    if not re.match(pattern, value):
        # 如果不匹配，抛出验证错误异常
        raise ValidationError('请输入有效的18位身份证号')


# ================================
# 客户数据模型定义
# ================================
class Customer(models.Model):
    """
    客户模型类 - 存储酒店客户的基本信息
    
    继承自Django的Model类，每个Customer实例对应数据库中的一条客户记录。
    
    字段说明:
        name: 客户姓名（必填）
        id_number: 身份证号（必填，唯一，18位）
        phone: 联系电话（必填，11位手机号）
        email: 电子邮箱（选填）
        address: 住址（选填）
    """
    
    # 姓名字段：使用CharField存储，最大长度100个字符
    # verbose_name用于在Admin后台显示中文名称
    name = models.CharField(
        max_length=100,  # 最大长度100个字符
        verbose_name='姓名'  # Admin后台显示的字段名称
    )
    
    # 身份证号字段：使用CharField存储，最大长度18个字符
    # unique=True 确保数据库中不会有重复的身份证号
    # validators 指定使用validate_id_number函数进行验证
    id_number = models.CharField(
        max_length=18,  # 身份证号固定18位
        unique=True,  # 唯一约束，防止重复注册
        verbose_name='身份证号',  # Admin后台显示的字段名称
        validators=[validate_id_number]  # 使用自定义验证函数验证格式
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

    def __str__(self):
        """
        定义模型对象的字符串表示
        
        当打印Customer对象或在Admin后台显示时，会调用此方法。
        返回客户的姓名作为对象的字符串表示。
        
        返回:
            str: 客户姓名
        """
        return self.name

    class Meta:
        """
        模型的元数据配置类
        
        用于定义模型的一些额外属性，如数据库表名、排序方式、显示名称等。
        """
        # verbose_name: 单数形式的模型名称，用于Admin后台显示
        # verbose_name_plural: 复数形式的模型名称
        # 中文环境下通常设置为相同值
        verbose_name = verbose_name_plural = '客户'