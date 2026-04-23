#!/bin/bash
# 创建迁移前基线快照
# 功能：在开始迁移前记录系统所有关键信息

set -euo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BASELINE_FILE="/migration/baseline_${TIMESTAMP}.txt"

echo "🏷️  创建迁移前基线快照..."
echo "========================================" | tee "$BASELINE_FILE"
echo "Athena迁移前基线快照" | tee -a "$BASELINE_FILE"
echo "时间: $(date)" | tee -a "$BASELINE_FILE"
echo "========================================" | tee -a "$BASELINE_FILE"
echo "" | tee -a "$BASELINE_FILE"

# 1. Git信息
echo "📍 Git状态:" | tee -a "$BASELINE_FILE"
echo "分支: $(git branch --show-current)" | tee -a "$BASELINE_FILE"
echo "最新提交: $(git log -1 --oneline)" | tee -a "$BASELINE_FILE"
echo "" | tee -a "$BASELINE_FILE"

# 2. 数据库状态
echo "💾 数据库状态:" | tee -a "$BASELINE_FILE"
psql -h localhost -U postgres -d athena_db -c "SELECT COUNT(*) as table_count FROM information_schema.tables;" -t | tee -a "$BASELINE_FILE"
echo "" | tee -a "$BASELINE_FILE"

# 3. Docker服务状态
echo "🐳 Docker服务状态:" | tee -a "$BASELINE_FILE"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | tee -a "$BASELINE_FILE"
echo "" | tee -a "$BASELINE_FILE"

# 4. 磁盘使用
echo "💿 磁盘使用:" | tee -a "$BASELINE_FILE"
df -h | tee -a "$BASELINE_FILE"
echo "" | tee -a "$BASELINE_FILE"

# 5. 资源使用
echo "📊 资源使用:" | tee -a "$BASELINE_FILE"
echo "CPU: $(top -l 1 | grep "CPU usage" | awk '{print $3}' | sed 's/%//')" | tee -a "$BASELINE_FILE"
echo "内存: $(vm_stat | grep "Pages free" | awk '{print $3}' | xargs -I {} echo "scale=2; {}*4096/1024/1024/1024" | bc) GB free" | tee -a "$BASELINE_FILE"
echo "" | tee -a "$BASELINE_FILE"

# 6. 核心文件统计
echo "📁 核心文件统计:" | tee -a "$BASELINE_FILE"
echo "法律世界模型: $(find /Users/xujian/Athena工作平台/core/legal_world_model -type f | wc -l | tr -d ' ') 文件" | tee -a "$BASELINE_FILE"
echo "Python文件: $(find /Users/xujian/Athena工作平台/core -name "*.py" | wc -l | tr -d ' ') 个" | tee -a "$BASELINE_FILE"
echo "" | tee -a "$BASELINE_FILE"

# 7. 创建Git标签
TAG_NAME="pre-migration-baseline-${TIMESTAMP}"
echo "🏷️  创建Git标签: ${TAG_NAME}"
git tag -a "$TAG_NAME" -m "迁移前基线快照

时间: $(date)
分支: $(git branch --show-current)
提交: $(git log -1 --oneline)

系统状态记录在: ${BASELINE_FILE}"
git push origin "$TAG_NAME"

echo "" | tee -a "$BASELINE_FILE"
echo "========================================" | tee -a "$BASELINE_FILE"
echo "✅ 基线快照创建完成！" | tee -a "$BASELINE_FILE"
echo "Git标签: ${TAG_NAME}" | tee -a "$BASELINE_FILE"
echo "基线文件: ${BASELINE_FILE}" | tee -a "$BASELINE_FILE"
echo "========================================" | tee -a "$BASELINE_FILE"

echo ""
echo "🎯 基线信息已保存，可以安全开始迁移了！"
echo "   如需回滚，使用: git checkout ${TAG_NAME}"
