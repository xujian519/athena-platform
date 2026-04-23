#!/bin/bash
################################################################################
# Athena平台 - Docs目录第二轮整理脚本
# Phase 2 Cleanup Script for docs/ Directory
#
# 功能：
#   1. 归档中文文档
#   2. 归档历史设计文档
#   3. 归档剩余临时报告
#   4. 整理身份配置文档
#
# 使用方法：
#   ./scripts/docs_cleanup_phase2.sh [--dry-run] [--force]
#
# 作者: 徐健 (xujian519@gmail.com)
# 创建: 2026-04-22
################################################################################

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 项目路径
PROJECT_ROOT="/Users/xujian/Athena工作平台"
DOCS_DIR="$PROJECT_ROOT/docs"

# 模式
DRY_RUN=false
FORCE=false

# 统计变量
MOVED_COUNT=0
SKIPPED_COUNT=0
ERROR_COUNT=0

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

log_action() {
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${CYAN}[DRY-RUN]${NC} $1"
    else
        echo -e "${GREEN}[MOVE]${NC} $1"
    fi
}

# 创建目录
ensure_dir() {
    local dir=$1
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "  mkdir -p $dir"
    else
        mkdir -p "$dir" 2>/dev/null || true
    fi
}

# 移动文件
move_file() {
    local src=$1
    local dst=$2

    if [[ ! -f "$src" ]]; then
        return
    fi

    local filename=$(basename "$src")
    local target_dir=$(dirname "$dst")

    # 检查目标文件是否已存在
    if [[ -f "$dst" ]]; then
        log_warning "目标已存在，跳过: $filename"
        SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
        return
    fi

    # 执行移动
    ensure_dir "$target_dir"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_action "$src → $dst"
    else
        mv "$src" "$dst" 2>/dev/null && {
            log_action "$filename → $dst"
            MOVED_COUNT=$((MOVED_COUNT + 1))
        } || {
            log_error "移动失败: $filename"
            ERROR_COUNT=$((ERROR_COUNT + 1))
        }
    fi
}

# 归档中文文档
archive_chinese_docs() {
    log_info "🇨🇳 归档中文文档..."

    # 多模态相关
    for file in "$DOCS_DIR"/多模态*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/projects/multimodal/$(basename "$file")"
    done

    # 技术图纸相关
    for file in "$DOCS_DIR"/技术*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/projects/patents/zh-cn/$(basename "$file")"
    done

    # 小娜专利检索
    for file in "$DOCS_DIR"/小娜*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/projects/patents/zh-cn/$(basename "$file")"
    done

    # 星河系列设计
    for file in "$DOCS_DIR"/xinghe*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/archive/design-legacy/$(basename "$file")"
    done

    # Athena优化系统
    for file in "$DOCS_DIR"/Athena优化系统*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/archive/legacy-2025/$(basename "$file")"
    done

    # 小诺端口迁移
    for file in "$DOCS_DIR"/XIAONUO_PORT_MIGRATION.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/archive/legacy-2025/$(basename "$file")"
    done
}

# 归档历史设计文档
archive_legacy_design() {
    log_info "📜 归档历史设计文档..."

    # 系统设计相关（2025年）
    for file in "$DOCS_DIR"/emotional-memory-system-design.md \
                "$DOCS_DIR"/webchat_system_design.md \
                "$DOCS_DIR"/DOCUMENT_STORAGE_TECH_STACK.md \
                "$DOCS_DIR"/ATHENA_STORAGE_ARCHITECTURE_DESIGN.md \
                "$DOCS_DIR"/STAGE2_HYBRID_ARCHITECTURE_DESIGN.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/archive/design-2025/$(basename "$file")"
    done

    # 集成方案
    for file in "$DOCS_DIR"/athena_optimized_v3_integration_guide.md \
                "$DOCS_DIR"/baochen_import_mapping_design.md \
                "$DOCS_DIR"/payment_records_mapping_design.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/archive/design-2025/$(basename "$file")"
    done

    # 自动演进相关
    for file in "$DOCS_DIR"/athena-auto-evolution-*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/archive/design-2025/$(basename "$file")"
    done

    # 架构优化建议
    for file in "$DOCS_DIR"/architecture_optimization_recommendations.md \
                "$DOCS_DIR"/architecture-diagrams.md \
                "$DOCS_DIR"/design_philosophy_quantum_legal.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/archive/design-2025/$(basename "$file")"
    done

    # NLP相关
    for file in "$DOCS_DIR"/nlp_*.md \
                "$DOCS_DIR"/bge_*.md \
                "$DOCS_DIR"/llm_*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/archive/nlp-legacy/$(basename "$file")"
    done
}

# 归档临时报告和修复报告
archive_temp_reports_phase2() {
    log_info "📋 归档剩余临时报告..."

    # 系统验证报告
    for file in "$DOCS_DIR"/SYSTEM_VERIFICATION_REPORT*.md \
                "$DOCS_DIR"/SYNTAX_FIX_*.md \
                "$DOCS_DIR"/TEST_COLLECTION_*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/archive/temp-reports/2026-02/$(basename "$file")"
    done

    # 项目清理和优化报告
    for file in "$DOCS_DIR"/platform_cleanup_summary.md \
                "$DOCS_DIR"/optimization_checklist.md \
                "$DOCS_DIR"/continuous-improvement-process.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/archive/temp-reports/$(basename "$file")"
    done

    # 其他报告
    for file in "$DOCS_DIR"/qdrant_analysis_and_solution.md \
                "$DOCS_DIR"/UNIFIED_REPORT_DEPLOYMENT.md \
                "$DOCS_DIR"/TRIPLE_DATABASE_PERSISTENCE_SOLUTION.md \
                "$DOCS_DIR"/VECTOR_STORAGE_ANALYSIS_AND_RECOMMENDATIONS.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/archive/temp-reports/$(basename "$file")"
    done
}

# 整理迁移相关文档
organize_migration() {
    log_info "🔄 整理迁移文档..."

    for file in "$DOCS_DIR"/Migration*.md \
                "$DOCS_DIR"/K8S_MESH_INTEGRATION_PLAN.md \
                "$DOCS_DIR"/service-mesh_integration_plan.md \
                "$DOCS_DIR"/service-mesh_integration_plan.md \
                "$DOCS_DIR"/gateway_migration_plan.md \
                "$DOCS_DIR"/ServiceMesh*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/deployment/migration/$(basename "$file")"
    done
}

# 整理身份和配置文档
organize_identity_config() {
    log_info "👤 整理身份配置文档..."

    # 身份相关
    for file in "$DOCS_DIR"/father_identity_profile.md \
                "$DOCS_DIR"/xiaonuo_identity_profile.md \
                "$DOCS_DIR"/IDENTITY_INFORMATION.md \
                "$DOCS_DIR"/CurrentArchitecture*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/reference/identity/$(basename "$file")"
    done

    # 外部依赖
    for file in "$DOCS_DIR"/ExternalDependencies_*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/reference/dependencies/$(basename "$file")"
    done

    # 部署扩展
    for file in "$DOCS_DIR"/deploy_gateway_extended.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/deployment/$(basename "$file")"
    done
}

# 整理性能和基准文档
organize_performance() {
    log_info "⚡ 整理性能文档..."

    for file in "$DOCS_DIR"/Performance*.md \
                "$DOCS_DIR"/Benchmark*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/reports/performance/$(basename "$file")"
    done
}

# 整理安全文档
organize_security_phase2() {
    log_info "🔒 整理安全文档..."

    for file in "$DOCS_DIR"/Security*.md \
                "$DOCS_DIR"/TLS_*.md \
                "$DOCS_DIR"/SPIFFE_*.md \
                "$DOCS_DIR"/CredentialManagement_*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/security/$(basename "$file")"
    done

    # SQL注入相关
    for file in "$DOCS_DIR"/SQL_INJECTION_*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/security/$(basename "$file")"
    done
}

# 整理项目结构文档
organize_project_structure() {
    log_info "📁 整理项目结构文档..."

    for file in "$DOCS_DIR"/PROJECT_STRUCTURE*.md \
                "$DOCS_DIR"/project-structure.md \
                "$DOCS_DIR"/PROJECT_STRUCTURE_OPTIMIZATION_PLAN.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/reference/project-structure/$(basename "$file")"
    done
}

# 整理计划和任务文档
organize_plans() {
    log_info "📝 整理计划和任务文档..."

    for file in "$DOCS_DIR"/NEXT_PHASE_TASKS.md \
                "$DOCS_DIR"/TODO_TRACKING.md \
                "$DOCS_DIR"/implementation-plan-summary.md \
                "$DOCS_DIR"/phase1_implementation_plan.md \
                "$DOCS_DIR"/MULTIMODAL_PATENT_ANALYSIS_ROADMAP.md \
                "$DOCS_DIR"/intent_recognition_99percent_progress.md \
                "$DOCS_DIR"/nlp_intent_99percent_roadmap.md \
                "$DOCS_DIR"/OPENCLAW_INTEGRATION_PROGRESS.md \
                "$DOCS_DIR"/OIMPLEMENTATION_SUMMARY_*.md \
                "$DOCS_DIR"/LEGAL_WORLD_MODEL_STABILITY_PLAN.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/plans/$(basename "$file")"
    done
}

# 整理感知模块文档
organize_perception() {
    log_info "👁️ 整理感知模块文档..."

    for file in "$DOCS_DIR"/PERCEPTION_*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/guides/perception/$(basename "$file")"
    done
}

# 整理知识图谱文档
organize_knowledge_graph() {
    log_info "🕸️ 整理知识图谱文档..."

    for file in "$DOCS_DIR"/knowledge_graph_*.md \
                "$DOCS_DIR"/MULTI_KNOWLEDGE_GRAPH_*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/architecture/knowledge-graph/$(basename "$file")"
    done
}

# 整理代理文档
organize_agents() {
    log_info "🤖 整理代理文档..."

    for file in "$DOCS_DIR"/Enhanced_Xiaonuo*.md \
                "$DOCS_DIR"/AGENTS.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/agents/$(basename "$file")"
    done
}

# 整理记忆系统文档
organize_memory() {
    log_info "🧠 整理记忆系统文档..."

    for file in "$DOCS_DIR"/MEMORY_SYSTEM_*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/architecture/memory/$(basename "$file")"
    done
}

# 整理部署相关
organize_deployment_phase2() {
    log_info "🚀 整理部署文档..."

    for file in "$DOCS_DIR"/production_*.md \
                "$DOCS_DIR"/DEPLOYMENT_MEMORY.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/deployment/$(basename "$file")"
    done
}

# 整理模型和AI相关
organize_models() {
    log_info "🤖 整理模型相关文档..."

    for file in "$DOCS_DIR"/LOCAL_MODELS_SETUP.md \
                "$DOCS_DIR"/XIAOCHEN_TRANSFORMATION_DESIGN.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/guides/ai-models/$(basename "$file")"
    done
}

# 整理工具和服务相关
organize_tools() {
    log_info "🛠️ 整理工具和服务文档..."

    for file in "$DOCS_DIR"/gaode-mcp-*.md \
                "$DOCS_DIR"/google-patents-*.md \
                "$DOCS_DIR"/multimodal_file_system_*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/guides/tools/$(basename "$file")"
    done
}

# 生成整理报告
generate_report() {
    local report_file="$DOCS_DIR/DOCS_CLEANUP_PHASE2_REPORT_$(date +%Y%m%d_%H%M%S).md"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "📋 预览模式 - 不会生成报告文件"
        echo ""
        echo "=========================================="
        echo "第二轮整理预览完成"
        echo "=========================================="
        echo "预计移动: $MOVED_COUNT 个文件"
        echo "预计跳过: $SKIPPED_COUNT 个文件"
        echo "预计错误: $ERROR_COUNT 个文件"
        echo ""
        echo "执行实际整理，运行："
        echo "  bash scripts/docs_cleanup_phase2.sh"
        return
    fi

    cat > "$report_file" << EOF
# Docs目录第二轮整理报告

> **生成时间**: $(date '+%Y-%m-%d %H:%M:%S')
> **执行脚本**: scripts/docs_cleanup_phase2.sh

---

## 📊 整理统计

| 项目 | 数量 |
|-----|------|
| 已移动文件 | $MOVED_COUNT |
| 跳过文件 | $SKIPPED_COUNT |
| 错误文件 | $ERROR_COUNT |
| 总计处理 | $((MOVED_COUNT + SKIPPED_COUNT + ERROR_COUNT)) |

---

## 🗂️ 整理详情

### 1. 中文文档归档
- 多模态文档 → \`projects/multimodal/\`
- 技术图纸文档 → \`projects/patents/zh-cn/\`
- 小娜专利检索 → \`projects/patents/zh-cn/\`
- 星河系列设计 → \`archive/design-legacy/\`

### 2. 历史设计文档归档
- 系统设计文档 → \`archive/design-2025/\`
- 集成方案 → \`archive/design-2025/\`
- 自动演进相关 → \`archive/design-2025/\`
- 架构优化建议 → \`archive/design-2025/\`
- NLP相关 → \`archive/nlp-legacy/\`

### 3. 临时报告归档
- 系统验证报告 → \`archive/temp-reports/2026-02/\`
- 语法修复报告 → \`archive/temp-reports/2026-02/\`
- 项目清理报告 → \`archive/temp-reports/\`

### 4. 迁移文档整理
- Migration相关 → \`deployment/migration/\`
- Service Mesh相关 → \`deployment/migration/\`

### 5. 身份配置文档
- 身份相关 → \`reference/identity/\`
- 外部依赖 → \`reference/dependencies/\`

### 6. 性能文档
- 性能相关 → \`reports/performance/\`

### 7. 安全文档
- 安全相关 → \`security/\`
- TLS相关 → \`security/\`
- SPIFFE相关 → \`security/\`

### 8. 项目结构文档
- 项目结构相关 → \`reference/project-structure/\`

### 9. 计划和任务
- 计划文档 → \`plans/\`
- 任务跟踪 → \`plans/\`

### 10. 感知模块
- 感知模块相关 → \`guides/perception/\`

### 11. 知识图谱
- 知识图谱相关 → \`architecture/knowledge-graph/\`

### 12. 代理文档
- 代理相关 → \`agents/\`

### 13. 记忆系统
- 记忆系统相关 → \`architecture/memory/\`

### 14. 部署文档
- 部署相关 → \`deployment/\`

### 15. 模型和AI
- AI模型相关 → \`guides/ai-models/\`

### 16. 工具和服务
- 工具相关 → \`guides/tools/\`

---

## ✅ 下一步

1. **检查整理结果**
   \`\`\`bash
   ls -lh docs/
   ls -lh docs/archive/
   \`\`\`

2. **更新文档索引**
   - 更新 \`docs/README.md\`
   - 更新 \`docs/INDEX.md\`

3. **建立维护规范**
   - 新文档按分类存放
   - 定期归档临时报告
   - 保持根目录整洁（<30个文件）

---

**脚本版本**: 2.0.0
**执行者**: $(whoami)
**主机**: $(hostname)
EOF

    log_success "📋 第二轮整理报告已生成: $report_file"
}

# 显示帮助
show_help() {
    cat << EOF
Athena平台 - Docs目录第二轮整理脚本

用法:
    $0 [选项]

选项:
    --dry-run   预览模式，不实际移动文件
    --force     强制执行，不询问确认
    --help      显示帮助信息

功能:
    1. 归档中文文档（多模态、技术图纸等）
    2. 归档历史设计文档（2025年设计）
    3. 归档剩余临时报告
    4. 整理迁移相关文档
    5. 整理身份配置文档
    6. 整理性能和安全文档
    7. 整理项目结构文档
    8. 整理计划和任务文档
    9. 整理感知、知识图谱、代理等专项文档

示例:
    $0 --dry-run          # 预览整理计划
    $0                    # 执行整理
    $0 --force            # 强制执行

EOF
}

# 主函数
main() {
    echo "=========================================="
    echo "  Athena平台 - Docs目录第二轮整理"
    echo "=========================================="
    echo ""

    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                DRY_RUN=true
                log_info "🔍 预览模式已启用"
                shift
                ;;
            --force)
                FORCE=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # 确认执行
    if [[ "$FORCE" != "true" && "$DRY_RUN" != "true" ]]; then
        echo "即将执行第二轮整理，进一步减少根目录文件"
        echo ""
        read -p "确认继续? (yes/no): " confirm
        if [[ "$confirm" != "yes" ]]; then
            log_info "已取消"
            exit 0
        fi
    fi

    # 执行整理
    echo ""
    log_info "🚀 开始第二轮整理..."
    echo ""

    archive_chinese_docs
    archive_legacy_design
    archive_temp_reports_phase2
    organize_migration
    organize_identity_config
    organize_performance
    organize_security_phase2
    organize_project_structure
    organize_plans
    organize_perception
    organize_knowledge_graph
    organize_agents
    organize_memory
    organize_deployment_phase2
    organize_models
    organize_tools

    echo ""
    log_success "✅ 第二轮整理完成！"
    echo ""

    # 生成报告
    generate_report

    # 显示最终状态
    echo ""
    echo "=========================================="
    echo "  第二轮整理后状态"
    echo "=========================================="
    echo ""
    echo "根目录剩余文件数: $(ls "$DOCS_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ')"
    echo ""
    echo "查看详细报告: $DOCS_DIR/DOCS_CLEANUP_PHASE2_REPORT_*.md"
}

# 执行主函数
main "$@"
