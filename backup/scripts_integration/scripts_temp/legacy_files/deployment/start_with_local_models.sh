#!/bin/bash
# 使用本地模型启动脚本
# Start with local models

echo "🚀 启动Athena工作平台（使用本地模型）"
echo "========================================"

# 设置环境变量
source /Users/xujian/Athena工作平台/scripts/setup_model_environment.sh

# 导入本地模型配置到环境
export PYTHONPATH="/Users/xujian/Athena工作平台:$PYTHONPATH"

# 创建别名方便使用
alias athena="python3 /Users/xujian/Athena工作平台/main.py"
alias athena-dev="python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8080"

echo ""
echo "✅ 环境配置完成！"
echo ""
echo "可用命令："
echo "- athena         : 运行主程序"
echo "- athena-dev     : 开发模式启动（自动重载）"
echo ""
echo "本地模型列表："
echo "- BGE-Large-ZH-v1.5   : /Users/xujian/Athena工作平台/models/bge-large-zh-v1.5"
echo "- BGE-Base-ZH-v1.5    : /Users/xujian/Athena工作平台/models/bge-base-zh-v1.5"
echo "- Chinese-Legal-ELECTRA: /Users/xujian/Athena工作平台/models/chinese_legal_electra"
echo ""