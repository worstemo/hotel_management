"""
员工管理应用配置模块
定义employees应用的基本配置信息
该应用负责管理酒店员工信息
"""

# 从Django应用配置模块导入AppConfig基类
from django.apps import AppConfig


class EmployeesConfig(AppConfig):
    """
    员工管理应用配置类
    继承自Django的AppConfig，用于配置应用的元数据
    该应用管理员工的基本信息、职位和薪资
    """
    
    # 定义模型主键自动字段类型为BigAutoField（64位自增整数）
    # 这是Django 3.2+推荐的默认设置，支持更大的数据量
    default_auto_field = "django.db.models.BigAutoField"
    
    # 应用名称，必须与应用目录名一致
    # Django通过此名称在INSTALLED_APPS中识别应用
    name = "employees"
