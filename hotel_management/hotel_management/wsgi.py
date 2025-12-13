"""
WSGI配置文件

WSGI (Web Server Gateway Interface) 是Python Web应用的标准服务器网关接口
用于将Web服务器（如Nginx、Apache）与Django应用连接起来

用途：
1. 生产环境下使用Gunicorn、uWSGI等WSGI服务器部署
2. 同步请求处理，适合大多数Web应用场景
3. 成熟稳定，广泛支持

部署示例（使用Gunicorn）:
gunicorn hotel_management.wsgi:application --bind 0.0.0.0:8000

更多信息请参考:
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

# 导入操作系统接口模块，用于设置环境变量
import os

# 从Django核心WSGI模块导入应用获取函数
from django.core.wsgi import get_wsgi_application

# 设置Django配置模块的环境变量
# 指向项目的settings.py文件
# 如果环境变量中没有设置DJANGO_SETTINGS_MODULE，则使用默认值
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hotel_management.settings")

# 获取WSGI应用实例
# 该应用实例用于WSGI服务器调用
application = get_wsgi_application()
