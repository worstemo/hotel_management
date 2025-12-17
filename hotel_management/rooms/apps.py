"""房间管理应用配置模块"""

from django.apps import AppConfig


class RoomsConfig(AppConfig):
    """房间管理应用配置类"""
    
    default_auto_field = "django.db.models.BigAutoField"
    name = "rooms"
