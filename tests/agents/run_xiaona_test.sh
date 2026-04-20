#!/bin/bash
# 小娜Agent专利检索功能测试启动脚本

# 切换到项目根目录
cd "$(dirname "$0")/../.."

# 运行测试
python3 tests/agents/test_xiaona_patent_search.py "$@"
