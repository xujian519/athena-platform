# App包初始化
__version__ = '1.0.0'

import logging

from .models import *
from .service import video_service

__all__ = [
    'video_service',
    '__version__'
]