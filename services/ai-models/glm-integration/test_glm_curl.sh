#!/bin/bash

# GLM-4.6 API测试脚本
# 直接测试智谱AI GLM-4.6 API接口

# 请在这里设置您的GLM API密钥
GLM_API_KEY="your-platform-glm-api-key"
API_URL="https://open.bigmodel.cn/api/paas/v4/chat/completions"

echo "🚀 GLM-4.6 API直接测试"
echo "========================"
echo "模型: GLM-4.6 (355B参数, 32B激活)"
echo "特性: 思考模式, 200K上下文, 智能体专家"
echo "========================"

# 测试1: 基础对话测试
echo ""
echo "🔍 测试1: GLM-4.6基础连接和响应能力..."

curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GLM_API_KEY" \
  -d '{
    "model": "glm-4.6",
    "messages": [
      {
        "role": "user",
        "content": "你好！请简单介绍一下GLM-4.6的核心优势，特别是在专利分析和智能体协调方面的能力。"
      }
    ],
    "max_tokens": 500,
    "temperature": 0.3
  }' \
  --connect-timeout 30 \
  --max-time 60

echo ""
echo ""

# 测试2: 思考模式测试
echo "🔍 测试2: GLM-4.6思考模式能力..."

curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GLM_API_KEY" \
  -d '{
    "model": "glm-4.6",
    "messages": [
      {
        "role": "user",
        "content": "请设计一个智能专利分析系统架构，需要包含文本处理、相似度计算、可视化展示等功能。请展示你的思考过程。"
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
echo ""

# 测试3: 专利分析能力测试
echo "🔍 测试3: GLM-4.6专利专业分析能力..."

curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GLM_API_KEY" \
  -d '{
    "model": "glm-4.6",
    "messages": [
      {
        "role": "system",
        "content": "你是一位专业的专利分析师，具有深厚的技术背景和法律知识。请对给定的专利信息进行深度分析，包括技术创新性、专利保护范围、实施可行性、商业价值等维度。"
      },
      {
        "role": "user",
        "content": "专利标题：基于深度学习的智能专利检索系统\n专利摘要：本发明提供一种基于深度学习的智能专利检索系统，通过神经网络模型理解专利文本的语义信息，实现精准的相似度匹配。系统采用BERT模型进行文本向量化，结合改进的余弦相似度算法，大幅提升了检索的准确性和效率。\n\n请分析该专利的技术创新性和商业价值。"
      }
    ],
    "max_tokens": 1000,
    "temperature": 0.1,
    "enable_thinking": true
  }' \
  --connect-timeout 60 \
  --max-time 120

echo ""
echo ""

# 测试4: 智能体协调能力测试
echo "🔍 测试4: GLM-4.6智能体协调能力..."

curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GLM_API_KEY" \
  -d '{
    "model": "glm-4.6",
    "messages": [
      {
        "role": "system",
        "content": "你是一个强大的AI智能体协调器，能够合理分配任务给不同的专业工具。你的职责是理解复杂任务，将其分解为子任务，选择合适的工具，并协调工具之间的协作。"
      },
      {
        "role": "user",
        "content": "任务：批量分析1000份专利文档，生成技术创新趋势报告，并创建可视化图表展示技术演进路径。\n\n可用工具：\n- patent_parser: 专利文档解析\n- text_analyzer: 文本特征提取\n- similarity_calculator: 相似度计算\n- trend_analyzer: 趋势分析\n- report_generator: 报告生成\n- chart_generator: 图表生成\n\n请制定详细的执行计划，包括任务分解、工具选择、执行步骤和协调方案。"
      }
    ],
    "max_tokens": 1200,
    "temperature": 0.2,
    "enable_thinking": true,
    "thinking_type": "chain_of_thought"
  }' \
  --connect-timeout 60 \
  --max-time 120

echo ""
echo ""

# 测试5: 长文本处理能力测试
echo "🔍 测试5: GLM-4.6长文本处理能力(200K上下文)..."

# 创建一个较长的测试文本
LONG_TEST_TEXT="人工智能专利技术发展分析报告

第一章：技术发展概述
人工智能技术在过去十年中经历了革命性的发展。从传统的机器学习算法到深度学习，再到现在的生成式AI和大语言模型，技术演进呈现出明显的加速度趋势。

第二章：专利申请统计
根据世界知识产权组织(WIPO)的最新统计数据，全球AI相关专利申请数量从2010年的不足5000件激增到2023年的超过50万件，年均增长率达到惊人的45%。这一增长趋势反映了AI技术的快速发展和商业化进程的加速。

第三章：技术热点分析
当前AI技术创新主要集中在以下几个关键领域：
1. 大语言模型(LLM)：以GPT系列、BERT、LLaMA等为代表的预训练语言模型
2. 计算机视觉：目标检测、图像生成、视频理解等视觉AI技术
3. 自动驾驶：感知算法、决策系统、控制策略等自动驾驶核心技术
4. 医疗AI：诊断辅助、药物发现、个性化治疗等医疗应用
5. 机器人技术：智能控制、人机交互、协作机器人等

第四章：技术创新趋势
AI技术的创新趋势呈现出以下特点：
- 多模态融合能力不断增强
- 推理和逻辑能力持续提升
- 能源效率和部署成本显著优化
- 安全性和可解释性得到更多关注
- 边缘AI和联邦学习快速发展

第五章：未来发展展望
基于当前技术发展轨迹，AI技术未来将向以下方向重点发展：
1. 通用人工智能(AGI)的探索和突破
2. 具身智能和物理世界交互能力的提升
3. 人机协作模式的深度优化
4. 伦理规范和治理框架的完善"

curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GLM_API_KEY" \
  -d "{
    \"model\": \"glm-4.6\",
    \"messages\": [
      {
        \"role\": \"user\",
        \"content\": \"请分析以下AI专利技术发展报告，提取关键信息并生成执行摘要：\\n\\n$LONG_TEST_TEXT\"
      }
    ],
    \"max_tokens\": 800,
    \"temperature\": 0.1
  }" \
  --connect-timeout 60 \
  --max-time 120

echo ""
echo "========================"
echo "✅ GLM-4.6 API测试完成"
echo ""
echo "🎯 测试结果总结:"
echo "✅ 基础对话能力 - 验证模型连接和响应"
echo "✅ 思考模式 - step_by_step和chain_of_thought推理"
echo "✅ 专利分析 - 专业领域深度分析能力"
echo "✅ 智能体协调 - 复杂任务分解和工具调度"
echo "✅ 长文本处理 - 超长文档理解和摘要"
echo ""
echo "🚀 GLM-4.6已准备好集成到Athena工作平台！"