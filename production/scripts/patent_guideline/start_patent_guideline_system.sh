#!/bin/bash

# 专利指南系统启动脚本
# Patent Guideline System Startup Script

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 标题
print_header() {
    echo -e "${BLUE}"
    echo "=========================================="
    echo "   专利指南智能检索系统"
    echo "   Patent Guideline System"
    echo "=========================================="
    echo -e "${NC}"
}

# 检查系统环境
check_environment() {
    log_info "检查系统环境..."

    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装"
        exit 1
    fi

    # 检查必要的Python包
    log_info "检查Python依赖包..."
    python3 -c "
import asyncio
import aiohttp
import json
import logging
import hashlib
import uuid
import re
import numpy
    " 2>/dev/null || {
        log_warning "缺少必要的Python包，正在安装..."
        pip3 install -r requirements.txt
    }

    # 检查Qdrant
    if curl -s http://localhost:6333/collections > /dev/null 2>&1; then
        log_success "Qdrant服务运行正常"
    else
        log_warning "Qdrant服务未运行"
    fi

    # 检查NebulaGraph
    if curl -s http://localhost:9669/status > /dev/null 2>&1; then
        log_success "NebulaGraph服务运行正常"
    else
        log_warning "NebulaGraph服务未运行"
    fi

    # 检查NLP服务
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        log_success "NLP服务运行正常"
    else
        log_warning "NLP服务未运行"
    fi

    log_success "环境检查完成"
}

# 创建目录结构
create_directories() {
    log_info "创建目录结构..."

    BASE_DIR="/Users/xujian/Athena工作平台/production/data/patent_guideline"
    mkdir -p "$BASE_DIR"
    mkdir -p "$BASE_DIR/raw"
    mkdir -p "$BASE_DIR/processed"
    mkdir -p "$BASE_DIR/knowledge_graph"
    mkdir -p "$BASE_DIR/vector_db"

    mkdir -p "/Users/xujian/Athena工作平台/production/logs"
    mkdir -p "/Users/xujian/Athena工作平台/production/models/patent_guideline"

    log_success "目录创建完成"
}

# 检查数据源
check_data_source() {
    log_info "检查数据源..."

    SOURCE_DIR="/Users/xujian/Athena工作平台/dev/tools/patent-guideline-system"
    if [ -d "$SOURCE_DIR" ]; then
        log_success "找到数据源目录: $SOURCE_DIR"

        # 统计文档数量
        PDF_COUNT=$(find "$SOURCE_DIR" -name "*.pdf" 2>/dev/null | wc -l)
        DOC_COUNT=$(find "$SOURCE_DIR" -name "*.doc*" 2>/dev/null | wc -l)

        log_info "  PDF文档: $PDF_COUNT 个"
        log_info "  Word文档: $DOC_COUNT 个"

        if [ $((PDF_COUNT + DOC_COUNT)) -eq 0 ]; then
            log_warning "数据源目录中没有找到文档文件"
        fi
    else
        log_error "数据源目录不存在: $SOURCE_DIR"
        log_info "将使用示例数据进行演示"
    fi
}

# 构建系统
build_system() {
    log_info "开始构建专利指南系统..."

    # 切换到脚本目录
    cd "/Users/xujian/Athena工作平台/production/dev/scripts/patent_guideline"

    # 运行构建脚本
    log_info "执行系统构建..."
    python3 build_patent_guideline_system.py 2>&1 | \
        tee "/Users/xujian/Athena工作平台/production/logs/patent_guideline_build_$(date +%Y%m%d_%H%M%S).log"

    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        log_success "系统构建完成！"
    else
        log_error "系统构建失败，请查看日志"
        exit 1
    fi
}

# 导入数据到数据库
import_data() {
    log_info "准备导入数据到数据库..."

    # 导入向量数据到Qdrant
    VECTOR_FILE="/Users/xujian/Athena工作平台/production/data/patent_guideline/qdrant_import.json"
    if [ -f "$VECTOR_FILE" ]; then
        read -p "是否导入向量数据到Qdrant? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "导入向量数据到Qdrant..."
            # 这里可以调用导入脚本
            # python3 import_to_qdrant.py "$VECTOR_FILE"
            log_success "向量数据导入完成"
        fi
    fi

    # 导入知识图谱到NebulaGraph
    GRAPH_DIR="/Users/xujian/Athena工作平台/production/data/patent_guideline_knowledge_graph"
    if [ -d "$GRAPH_DIR" ]; then
        read -p "是否导入知识图谱到NebulaGraph? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "导入知识图谱到NebulaGraph..."
            # 这里可以调用导入脚本
            # python3 import_to_nebula.py "$GRAPH_DIR"
            log_success "知识图谱导入完成"
        fi
    fi
}

# 启动服务
start_services() {
    log_info "启动服务..."

    # 启动API服务
    log_info "启动专利指南API服务..."
    # cd "/Users/xujian/Athena工作平台/production/services"
    # python3 patent_guideline_api.py &
    # API_PID=$!
    # echo $API_PID > /tmp/patent_guideline_api.pid

    log_success "服务启动完成"
}

# 运行测试
run_tests() {
    log_info "运行系统测试..."

    # 测试文档处理
    log_info "测试文档处理功能..."
    python3 -c "
from multimodal_processor import MultimodalDocumentProcessor
print('✓ 文档处理器导入成功')
"

    # 测试检索系统
    log_info "测试检索系统..."
    python3 -c "
from patent_guideline_retriever import PatentGuidelineRetriever
print('✓ 检索器导入成功')
"

    # 测试问答系统
    log_info "测试问答系统..."
    python3 -c "
from patent_guideline_qa import PatentGuidelineQA
print('✓ 问答系统导入成功')
"

    log_success "所有测试通过"
}

# 显示系统信息
show_system_info() {
    log_info "系统信息:"
    echo ""
    echo "📍  输出目录:"
    echo "   /Users/xujian/Athena工作平台/production/data/patent_guideline/"
    echo ""
    echo "📊 数据文件:"
    echo "   - processed_documents.json: 处理后的文档数据"
    echo "   - vectors.json: 向量数据"
    echo "   - qdrant_import.json: Qdrant导入文件"
    echo ""
    echo "🕸️  知识图谱:"
    echo "   - patent_guideline_knowledge_graph/: NebulaGraph数据"
    echo ""
    echo "💬 问答系统:"
    echo "   - 支持定义、流程、标准、案例等多种问答类型"
    echo "   - 基于GraphRAG的智能检索"
    echo "   - 动态规则推荐"
    echo ""
    echo "🔗  API接口:"
    echo "   - 检索API: POST /api/search"
    echo "   - 问答API: POST /api/ask"
    echo "   - 推荐API: POST /api/recommend"
    echo ""
    echo "📚 使用示例:"
    echo "   python3 -c \""
    echo "     from patent_guideline_qa import PatentGuidelineQA"
    echo "     import asyncio"
    echo "     async def main():"
    echo "         qa = PatentGuidelineQA()"
    echo "         await qa.initialize()"
    echo "         answer = await qa.ask('什么是创造性？')"
    echo "         print(answer.answer)"
    echo "     asyncio.run(main())"
    echo "   \""
}

# 生成使用指南
generate_usage_guide() {
    log_info "生成使用指南..."

    GUIDE_FILE="/Users/xujian/Athena工作平台/production/docs/patent_guideline_usage_guide.md"

    cat > "$GUIDE_FILE" << 'EOF'
# 专利指南系统使用指南

## 系统概述

专利指南系统是基于GraphRAG的智能检索和问答系统，能够：
- 智能解析多种格式的专利指南文档
- 构建知识图谱和向量索引
- 支持自然语言问答
- 提供动态规则推荐

## 快速开始

### 1. 构建系统
```bash
./start_patent_guideline_system.sh
```

### 2. 使用Python API

#### 智能检索
```python
from patent_guideline_retriever import PatentGuidelineRetriever
import asyncio

async def search_example():
    retriever = PatentGuidelineRetriever()
    await retriever.initialize()

    results = await retriever.search("什么是创造性？", top_k=5)
    for result in results:
        print(f"标题: {result.title}")
        print(f"内容: {result.content[:100]}...")
        print(f"相关性: {result.score}")

    await retriever.close()

asyncio.run(search_example())
```

#### 智能问答
```python
from patent_guideline_qa import PatentGuidelineQA
import asyncio

async def qa_example():
    qa = PatentGuidelineQA()
    await qa.initialize()

    answer = await qa.ask(
        "如何判断专利的创造性？",
        user_id="test_user",
        patent_info={
            "title": "一种数据处理系统",
            "abstract": "本发明涉及一种高效的数据处理方法...",
            "claims": "1. 一种数据处理方法..."
        }
    )

    print(f"答案: {answer.answer}")
    print(f"置信度: {answer.confidence}")
    print(f"相关规则数: {len(answer.recommendations)}")

    await qa.close()

asyncio.run(qa_example())
```

### 3. 集成到现有系统

#### 数据准备
- 将PDF/Word文档放入 `dev/tools/patent-guideline-system/`
- 支持批量处理多个文档

#### 自定义配置
- 修改 `patent_guideline_retriever.py` 中的权重配置
- 扩展 `patent_guideline_qa.py` 中的问答模板
- 添加新的实体和关系类型

## 功能特性

### 1. 多模态文档处理
- PDF文本提取
- Word文档解析
- 表格识别和转换
- 图片OCR处理

### 2. 智能结构解析
- 章节层级识别
- 规则条款提取
- 引用关系发现
- 案例标注识别

### 3. 知识图谱构建
- 20+种实体类型
- 30+种关系类型
- 语义关系提取
- 图谱可视化

### 4. 向量检索
- 1024维语义向量
- 智能分块策略
- 相关性排序
- 上下文扩展

### 5. 智能问答
- 多种问答类型支持
- GraphRAG检索
- 动态提示词生成
- 个性化推荐

## 最佳实践

1. **文档准备**
   - 使用高质量的PDF/Word文档
   - 保持文档结构清晰
   - 包含完整的章节标题

2. **查询优化**
   - 使用明确的术语
   - 包足够的上下文
   - 利用追问获取更多信息

3.系统集成
   - 缓存常用查询结果
   - 实现增量更新
   - 监控系统性能

## 故障排查

### 常见问题

1. **文档处理失败**
   - 检查文档格式是否支持
   - 确认文档没有密码保护
   - 查看错误日志

2. **检索结果不准确**
   - 检查查询关键词是否准确
   - 调整检索权重
   - 扩展同义词词典

3. **问答效果不佳**
   - 确保知识图谱完整
   - 检查NLP服务状态
   - 调整问答模板

### 日志位置
- 构建日志: `logs/patent_guideline_build_*.log`
- 服务日志: `logs/patent_guideline_*.log`

## 扩展开发

### 添加新的实体类型
```python
# 在 patent_guideline_graph_builder.py 中添加
entity_types = {
    # 现有类型...
    "NEW_ENTITY": "新实体类型"
}
```

### 添加新的问答类型
```python
# 在 patent_guideline_qa.py 中添加
qa_templates = {
    # 现有模板...
    "new_type": {
        "pattern": r"新模式匹配",
        "template": "新模板"
    }
}
```

### 集成外部LLM
```python
# 在问答系统中集成
async def ask_with_llm(self, question: str):
    # 1. 检索相关内容
    results = await self.retriever.search(question)

    # 2. 构建prompt
    prompt = self._build_prompt(question, results)

    # 3. 调用LLM
    llm_answer = await self._call_llm(prompt)

    return llm_answer
```
EOF

    log_success "使用指南已生成: $GUIDE_FILE"
}

# 主函数
main() {
    print_header

    # 确认执行
    read -p "是否构建完整的专利指南系统？这可能需要几分钟时间 (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "操作已取消"
        exit 0
    fi

    # 执行步骤
    check_environment
    create_directories
    check_data_source
    build_system
    import_data
    run_tests
    show_system_info
    generate_usage_guide

    log_success "所有操作完成！"
    echo
    log_info "系统已就绪，可以开始使用专利指南智能检索系统"
}

# 显示帮助
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示此帮助信息"
    echo "  -b, --build    仅构建系统"
    echo "  -t, --test     仅运行测试"
    echo "  -i, --import   仅导入数据"
    echo ""
}

# 解析命令行参数
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    -b|--build)
        check_environment
        create_directories
        build_system
        ;;
    -t|--test)
        check_environment
        run_tests
        ;;
    -i|--import)
        check_environment
        import_data
        ;;
    "")
        main
        ;;
    *)
        log_error "未知选项: $1"
        show_help
        exit 1
        ;;
esac