#!/bin/bash
#
# Athena项目结构迁移脚本
# 生成时间: 2026-01-27 12:38:40.835507
#
# ⚠️  警告: 执行前请确保已备份项目！
#

set -e  # 遇到错误立即退出

# 颜色输出
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
NC="\033[0m" # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 确认提示
echo "⚠️  即将开始项目结构迁移"
echo "此操作将移动大量文件和目录"
read -p "是否继续? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "操作已取消"
    exit 0
fi


# ============ PHASE1_PREPARATION ============

# 创建项目完整备份
tar -czf ../athena_backup_$(date +%Y%m%d_%H%M%S).tar.gz .
# 创建标准化目录结构
mkdir -p src/agents/{base,orchestrator,planner,executor,shared}
mkdir -p src/workflows
mkdir -p src/tools
mkdir -p config/{environments,agents,secrets,infrastructure,security}
mkdir -p data/{raw,processed,outputs/{logs,artifacts},knowledge}
mkdir -p docs/{architecture,api,guides,diagrams,reports}
mkdir -p tests/{unit/{agents,tools},integration,e2e,fixtures}
mkdir -p deploy/{docker,kubernetes,scripts}
mkdir -p external_projects
mkdir -p archive/{old_configs,old_scripts}

# ============ PHASE2_CORE_BUSINESS ============

# 整合智能体相关代码
log_info "移动 agent_collaboration/ -> src/agents/shared/collaboration/"
mv agent_collaboration/ src/agents/shared/collaboration/ 2>/dev/null || log_warn "agent_collaboration/ 不存在或移动失败"
log_info "移动 cognition/ -> src/agents/shared/cognition/"
mv cognition/ src/agents/shared/cognition/ 2>/dev/null || log_warn "cognition/ 不存在或移动失败"
log_info "移动 autonomous_control/ -> src/agents/orchestrator/"
mv autonomous_control/ src/agents/orchestrator/ 2>/dev/null || log_warn "autonomous_control/ 不存在或移动失败"
# 迁移和整合工具
log_info "移动 tools/ -> src/tools/"
mv tools/ src/tools/ 2>/dev/null || log_warn "tools/ 不存在或移动失败"
log_info "移动 utils/ -> src/utils/"
mv utils/ src/utils/ 2>/dev/null || log_warn "utils/ 不存在或移动失败"
log_info "移动 tasks/ -> src/tasks/"
mv tasks/ src/tasks/ 2>/dev/null || log_warn "tasks/ 不存在或移动失败"

# ============ PHASE3_EXTERNAL_PROJECTS ============


# ============ PHASE4_DATA_CONFIG ============

# 整合数据相关目录
log_info "移动 models/ -> data/models/"
mv models/ data/models/ 2>/dev/null || log_warn "models/ 不存在或移动失败"
log_info "移动 knowledge/ -> data/knowledge/"
mv knowledge/ data/knowledge/ 2>/dev/null || log_warn "knowledge/ 不存在或移动失败"
log_info "移动 knowledge_graph/ -> data/knowledge_graph/"
mv knowledge_graph/ data/knowledge_graph/ 2>/dev/null || log_warn "knowledge_graph/ 不存在或移动失败"
log_info "移动 memory/ -> data/memory/"
mv memory/ data/memory/ 2>/dev/null || log_warn "memory/ 不存在或移动失败"
log_info "移动 personal_secure_storage/ -> data/secure_storage/"
mv personal_secure_storage/ data/secure_storage/ 2>/dev/null || log_warn "personal_secure_storage/ 不存在或移动失败"
# 整合配置目录
log_info "移动 infrastructure/ -> config/infrastructure/"
mv infrastructure/ config/infrastructure/ 2>/dev/null || log_warn "infrastructure/ 不存在或移动失败"
log_info "移动 security/ -> config/security/"
mv security/ config/security/ 2>/dev/null || log_warn "security/ 不存在或移动失败"
# 整合部署相关
log_info "移动 deploy/ -> deploy/"
mv deploy/ deploy/ 2>/dev/null || log_warn "deploy/ 不存在或移动失败"
log_info "移动 docker/ -> deploy/docker/"
mv docker/ deploy/docker/ 2>/dev/null || log_warn "docker/ 不存在或移动失败"
log_info "移动 production/ -> deploy/production/"
mv production/ deploy/production/ 2>/dev/null || log_warn "production/ 不存在或移动失败"
log_info "移动 backup/ -> deploy/backups/"
mv backup/ deploy/backups/ 2>/dev/null || log_warn "backup/ 不存在或移动失败"
log_info "移动 backups/ -> deploy/backups/"
mv backups/ deploy/backups/ 2>/dev/null || log_warn "backups/ 不存在或移动失败"

# ============ PHASE5_CLEANUP ============

# 归档旧的配置文件
log_info "移动 .benchmarks -> archive/benchmarks"
mv .benchmarks archive/benchmarks 2>/dev/null || log_warn ".benchmarks 不存在或移动失败"
log_info "移动 .specify -> archive/specify"
mv .specify archive/specify 2>/dev/null || log_warn ".specify 不存在或移动失败"
log_info "移动 .system -> archive/system"
mv .system archive/system 2>/dev/null || log_warn ".system 不存在或移动失败"
# 清理空目录
find . -type d -empty -delete
# 运行测试验证迁移
pytest tests/ -v --tb=short

log_info "✅ 迁移完成！"
log_info "请运行测试验证: pytest tests/ -v"
