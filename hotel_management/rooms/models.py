"""
房间管理模块 - 数据模型

本模块定义了房间（Room）模型，用于存储酒店房间的基本信息。
包含房间类型、价格、状态、设施等字段，以及房间号的正则表达式验证。
"""

# 导入Django的models模块，用于定义数据库模型
from django.db import models
# 导入最小值验证器和正则表达式验证器
from django.core.validators import MinValueValidator, RegexValidator
# 导入验证错误异常类
from django.core.exceptions import ValidationError


# ================================
# 房间号验证器定义
# ================================
# 创建房间号正则验证器，确保房间号为3位数字
#
# 正则表达式详解: r'^\d{3}$'
# ^     - 匹配字符串的开始位置
# \d    - 匹配任意一个数字字符（0-9）
# {3}   - 前面的元素必须出现恰好3次
# $     - 匹配字符串的结束位置
#
# 整体含义: 从开始到结束必须是恰好3位数字
#
# 示例匹配: 101、202、303、999
# 示例不匹配: 12（只有2位）、1234（有4位）、A01（包含字母）
room_number_validator = RegexValidator(
    regex=r'^\d{3}$',  # 匹配3位数字的正则表达式
    message='房间号必须是三位数字，如：101、202、303'  # 验证失败时的错误消息
)


# ================================
# 房间数据模型定义
# ================================
class Room(models.Model):
    """
    房间模型类 - 存储酒店房间的基本信息、类型、价格、状态等
    
    继承自Django的Model类，每个Room实例对应数据库中的一条房间记录。
    
    字段说明:
        room_number: 房间号（3位数字，唯一）
        room_type: 房间类型（单人间/双人间/套房/豪华间）
        price: 房间价格（正整数，单位：元/晚）
        facilities: 房间设施描述
        status: 房间状态（空闲/已预订/已入住/维修中）
        floor: 所在楼层
        capacity: 容纳人数
        description: 房间描述
        pictures: 房间主图
    """
    
    # 定义房间类型选项（元组列表）
    # 每个元组包含：（数据库存储值, 显示名称）
    ROOM_TYPES = (
        ('Single', '单人间'),   # 单人房间
        ('Double', '双人间'),   # 双人房间
        ('Suite', '套房'),       # 套房
        ('Deluxe', '豪华间')   # 豪华间
    )
    
    # 定义房间状态选项（元组列表）
    ROOM_STATUS = (
        ('Available', '空闲'),      # 可用状态
        ('Booked', '已预订'),       # 已被预订
        ('Occupied', '已入住'),     # 当前有客人入住
        ('Maintenance', '维修中')  # 正在维护中
    )

    # 房间号字段：使用CharField存储，最大长度3个字符
    # unique=True 确保每个房间号唯一
    room_number = models.CharField(
        max_length=3,  # 最大长度3个字符
        unique=True,  # 唯一约束，防止重复房间号
        verbose_name='房间号',  # Admin后台显示的字段名称
        validators=[room_number_validator]  # 使用正则验证器验证格式
    )
    
    # 房间类型字段：使用CharField存储，限制为预定义的选项
    # choices参数限制可选值，并在Admin中显示为下拉框
    room_type = models.CharField(
        max_length=50,  # 最大长度50个字符
        choices=ROOM_TYPES,  # 使用预定义的选项
        verbose_name='房间类型'  # Admin后台显示的字段名称
    )
    
    # 价格字段：使用PositiveIntegerField存储正整数
    # validators添加最小值验证，确保价格至少为1
    price = models.PositiveIntegerField(
        verbose_name='价格',  # Admin后台显示的字段名称
        validators=[MinValueValidator(1)]  # 最小值验证器，价格必须>=1
    )
    
    # 设施字段：使用TextField存储设施描述文本
    facilities = models.TextField(
        verbose_name='设施'  # Admin后台显示的字段名称
    )
    
    # 状态字段：使用CharField存储，限制为预定义的状态选项
    # default指定默认值为'Available'（空闲）
    status = models.CharField(
        max_length=20,  # 最大长度20个字符
        choices=ROOM_STATUS,  # 使用预定义的状态选项
        default='Available',  # 默认状态为空闲
        verbose_name='状态'  # Admin后台显示的字段名称
    )
    
    # 楼层字段：使用IntegerField存储整数
    floor = models.IntegerField(
        verbose_name='楼层'  # Admin后台显示的字段名称
    )
    
    # 容纳人数字段：使用IntegerField存储整数
    capacity = models.IntegerField(
        verbose_name='容纳人数'  # Admin后台显示的字段名称
    )
    
    # 描述字段：使用TextField存储长文本
    # blank=True 表示该字段可以为空
    description = models.TextField(
        blank=True,  # 允许为空
        verbose_name='描述'  # Admin后台显示的字段名称
    )
    
    # 图片字段：使用ImageField存储图片
    # upload_to指定上传目录（相对于MEDIA_ROOT）
    pictures = models.ImageField(
        upload_to='pictures/',  # 图片上传到MEDIA_ROOT/pictures/目录
        blank=True,  # 表单中允许为空
        null=True,  # 数据库中允许为NULL
        verbose_name='房间主图'  # Admin后台显示的字段名称
    )

    def clean(self):
        """
        模型验证方法
        
        在保存模型之前执行自定义验证逻辑。
        这里再次验证价格必须为正数（作为额外的安全检查）。
        
        异常:
            ValidationError: 当价格小于等于0时抛出
        """
        # 调用父类的clean方法，执行默认验证
        super().clean()
        
        # 检查价格是否为正数（双重保险，字段级验证器也会检查）
        if self.price is not None and self.price <= 0:
            # 抛出验证错误，错误信息关联到'price'字段
            raise ValidationError({'price': '价格必须为正整数'})

    def __str__(self):
        """
        定义模型对象的字符串表示
        
        当打印Room对象或在Admin后台显示时调用。
        返回房间号作为对象的字符串表示。
        
        返回:
            str: 房间号
        """
        return self.room_number

    class Meta:
        """
        模型的元数据配置类
        
        用于定义模型的额外属性，如显示名称等。
        """
        # 设置模型的单数和复数显示名称
        verbose_name = verbose_name_plural = '房间'
