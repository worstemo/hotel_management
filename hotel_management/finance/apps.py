"""财务管理应用配置模块"""

from django.apps import AppConfig


class FinanceConfig(AppConfig):
    """财务管理应用配置类"""
    
    default_auto_field = "django.db.models.BigAutoField"
    name = "finance"
