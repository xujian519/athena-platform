#!/bin/bash
# Patent Downloader MCP Server 启动脚本

cd "$(dirname "$0")"
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
exec .venv/bin/python -c "
import sys
sys.path.insert(0, 'src')
from patent_downloader.mcp_server import start_mcp_server
start_mcp_server()
"
