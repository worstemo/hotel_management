"""员工管理应用配置模块"""

from django.apps import AppConfig


class EmployeesConfig(AppConfig):
    """员工管理应用配置类"""
    
    default_auto_field = "django.db.models.BigAutoField"
    name = "employees"
