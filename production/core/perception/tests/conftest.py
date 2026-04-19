#!/usr/bin/env python3
"""
测试配置文件
Test Configuration

负责设置测试环境，包括Python路径、共享fixtures等
"""

from __future__ import annotations
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "config"))
sys.path.insert(0, str(project_root / "core"))

import asyncio
import shutil
import tempfile
from collections.abc import Generator

import pytest


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """创建事件循环的fixture"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """创建临时目录的fixture"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # 清理临时目录
    if temp_path.exists():
        shutil.rmtree(temp_path)


@pytest.fixture
def sample_image_path(temp_dir: Path) -> Path:
    """创建示例图像文件的fixture"""
    import numpy as np
    from PIL import Image

    # 创建一个简单的测试图像
    img_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    img = Image.fromarray(img_array)
    img_path = temp_dir / "test_image.jpg"
    img.save(img_path)

    return img_path


@pytest.fixture
def sample_text_file(temp_dir: Path) -> Path:
    """创建示例文本文件的fixture"""
    text_path = temp_dir / "test_text.txt"
    text_path.write_text("这是一段测试文本\nThis is a test text.", encoding="utf-8")
    return text_path


# 共享的测试配置
TEST_CONFIG = {
    "max_retries": 3,
    "timeout": 5.0,
    "test_data_dir": Path(__file__).parent / "test_data",
}


@pytest.fixture(scope="session")
def test_config() -> dict:
    """返回测试配置"""
    return TEST_CONFIG
