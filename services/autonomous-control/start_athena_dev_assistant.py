#!/usr/bin/env python3
"""
启动Athena开发助手
Start Athena Development Assistant
"""

import os
import sys
from pathlib import Path

# 添加路径
current_dir = Path(__file__).parent
sys.path.append(str(current_dir / "athena_dev_assistant"))

# 设置环境变量
os.environ["PYTHONPATH"] = str(Path(__file__).parent.parent.parent)

# 导入并启动
from athena_dev_main import main

if __name__ == "__main__":
    print("🏛️  启动Athena开发助手...")
    print("💖 爸爸的专利专业助手\n")
    import asyncio
    asyncio.run(main())
