"""
预订管理应用配置模块
定义reservations应用的基本配置信息
该应用是系统核心，负责处理客房预订的全生命周期
"""

# 从Django应用配置模块导入AppConfig基类
from django.apps import AppConfig


class ReservationsConfig(AppConfig):
    """
    预订管理应用配置类
    继承自Django的AppConfig，用于配置应用的元数据
    该应用管理预订业务，与房间、客户、财务模块联动
    """
    
    # 定义模型主键自动字段类型为BigAutoField（64位自增整数）
    # 这是Django 3.2+推荐的默认设置，支持更大的数据量
    default_auto_field = "django.db.models.BigAutoField"
    
    # 应用名称，必须与应用目录名一致
    # Django通过此名称在INSTALLED_APPS中识别应用
    name = "reservations"
