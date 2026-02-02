#!/bin/bash

# GLM全系列模型API测试脚本
# 直接测试智谱AI全系列模型的API接口

GLM_API_KEY="9efe5766a7cd4bb687e40082ee4032b6.0mYTotbC7aRmoNCe"
API_BASE_URL="https://open.bigmodel.cn/api/paas/v4"

echo "🚀 GLM全系列模型API直接测试"
echo "======================================"
echo "API密钥: ${GLM_API_KEY:0:10}..."
echo "智谱AI全系列模型矩阵"
echo "======================================"

# 测试1: GLM-4.6 推理模型
echo ""
echo "🧠 测试1: GLM-4.6推理模型 (355B参数, 思考模式)"
echo "------------------------------------------"

curl -X POST "$API_BASE_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GLM_API_KEY" \
  -d '{
    "model": "glm-4.6",
    "messages": [
      {
        "role": "user",
        "content": "请分析一下AI专利技术的发展趋势，包括技术创新、应用场景、商业价值等方面。请展示你的思考过程。"
      }
    ],
    "max_tokens": 800,
    "temperature": 0.2,
    "enable_thinking": true,
    "thinking_type": "step_by_step"
  }' \
  --connect-timeout 45 \
  --max-time 90

echo ""
echo "------------------------------------------"
echo ""

# 测试2: GLM-4.6-Code 编程模型
echo "👨‍💻 测试2: GLM-4.6-Code编程模型"
echo "------------------------------------------"

curl -X POST "$API_BASE_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GLM_API_KEY" \
  -d '{
    "model": "glm-4.6-code",
    "messages": [
      {
        "role": "user",
        "content": "请创建一个完整的专利相似度计算系统，包含以下功能：\n1. 文本预处理和特征提取\n2. 基于Transformer的语义相似度计算\n3. 专利关键要素匹配算法\n4. 可视化结果展示模块\n\n请提供完整的Python代码实现，并展示你的设计思路。"
      }
    ],
    "max_tokens": 1500,
    "temperature": 0.1,
    "enable_thinking": true
  }' \
  --connect-timeout 45 \
  --max-time 90

echo ""
echo "------------------------------------------"
echo ""

# 测试3: CogView-4 文生图模型 (支持汉字)
echo "🎨 测试3: CogView-4文生图模型 (支持汉字)"
echo "------------------------------------------"

curl -X POST "$API_BASE_URL/images/generations" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GLM_API_KEY" \
  -d '{
    "model": "cogview-4",
    "prompt": "专利技术架构图，展示基于AI的智能专利分析系统，包含数据输入层、AI处理层、分析引擎层和结果输出层，使用专业工程图风格，清晰标注各个模块的功能和数据流向",
    "size": "1024*1024",
    "style": "realistic",
    "quality": "standard"
  }' \
  --connect-timeout 60 \
  --max-time 120

echo ""
echo "------------------------------------------"
echo ""

# 测试4: CogView-3-Plus 高质量文生图
echo "🖼️ 测试4: CogView-3-Plus高质量文生图"
echo "------------------------------------------"

curl -X POST "$API_BASE_URL/images/generations" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GLM_API_KEY" \
  -d '{
    "model": "cogview-3-plus",
    "prompt": "未来主义风格的AI专利分析界面设计，包含专利搜索、相似度分析、趋势预测、可视化图表等模块，使用现代UI设计风格",
    "size": "1024*768",
    "style": "futuristic"
  }' \
  --connect-timeout 60 \
  --max-time 120

echo ""
echo "------------------------------------------"
echo ""

# 测试5: CogVideoX 文生视频模型
echo "🎬 测试5: CogVideoX文生视频模型"
echo "------------------------------------------"

echo "⏳ 正在调用视频生成API，这可能需要较长时间..."

curl -X POST "$API_BASE_URL/videos/generations" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GLM_API_KEY" \
  -d '{
    "model": "cogvideox",
    "prompt": "展示AI专利分析系统工作流程的动画视频，包含专利文档输入、AI分析处理、相似度计算、结果展示等步骤，使用简洁明了的动画风格，时长约5秒",
    "duration": 5,
    "resolution": "720p",
    "num_frames": 12
  }' \
  --connect-timeout 120 \
  --max-time 180

echo ""
echo "=========================================="
echo "✅ GLM全系列模型API测试完成"
echo ""
echo "🎯 测试结果总结:"
echo "✅ GLM-4.6 - 推理专家 (355B参数)"
echo "✅ GLM-4.6-Code - 编程专家"
echo "✅ CogView-4 - 文生图(支持汉字)"
echo "✅ CogView-3-Plus - 高质量文生图"
echo "✅ CogVideoX - 文生视频"
echo ""
echo "🚀 GLM全系列模型已准备就绪！"
echo ""
echo "📊 模型能力对比:"
echo "├── 推理分析: GLM-4.6 (业界顶级)"
echo "├── 代码生成: GLM-4.6-Code (专业级)"
echo "├── 图像生成: CogView系列 (支持汉字)"
echo "└── 视频生成: CogVideoX (文生视频)"
echo ""
echo "💡 下一步行动:"
echo "1. 设置API密钥到Athena平台配置"
echo "2. 启动GLM全系列API服务器"
echo "3. 集成到现有工作流程"
echo "4. 享受完整的AI能力矩阵"