"""
酒店入住管理系统 - 应用配置
"""

from django.apps import AppConfig


class HotelManagementConfig(AppConfig):
    """酒店入住管理系统主应用配置类"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hotel_management'
    
    def ready(self):
        """应用准备就绪时导入自定义admin配置"""
        # 导入自定义admin配置，确保用户管理保护逻辑生效
        import hotel_management.admin
