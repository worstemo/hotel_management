#!/usr/bin/env python
"""Django项目的命令行管理工具入口文件"""

import os
import sys


def main():
    """主函数 - 执行Django管理命令"""
    
    # 设置Django配置文件的环境变量
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hotel_management.settings")
    
    # 导入Django命令行执行器
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    # 执行命令
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
