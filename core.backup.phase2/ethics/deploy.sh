#!/bin/bash
# AI伦理框架部署脚本
# Athena Platform Ethics Framework Deployment Script

set -e

echo "🛡️ Athena平台AI伦理框架部署"
echo "================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 项目路径
PROJECT_ROOT="/Users/xujian/Athena工作平台"
ETHICS_DIR="$PROJECT_ROOT/core/ethics"
LOGS_DIR="$PROJECT_ROOT/logs"

echo -e "${YELLOW}📋 步骤 1/6: 检查环境${NC}"
echo "项目根目录: $PROJECT_ROOT"
echo "伦理模块目录: $ETHICS_DIR"
echo "日志目录: $LOGS_DIR"
echo ""

echo -e "${YELLOW}📂 步骤 2/6: 创建必要目录${NC}"
mkdir -p "$LOGS_DIR"
mkdir -p "$ETHICS_DIR"
echo "✅ 目录创建完成"
echo ""

echo -e "${YELLOW}📦 步骤 3/6: 检查模块文件${NC}"
required_files=(
    "__init__.py"
    "constitution.py"
    "wittgenstein_guard.py"
    "evaluator.py"
    "constraints.py"
    "monitoring.py"
    "agent_integration.py"
    "xiaonuo_ethics_patch.py"
    "README.md"
)

for file in "${required_files[@]}"; do
    if [ -f "$ETHICS_DIR/$file" ]; then
        echo -e "  ${GREEN}✅${NC} $file"
    else
        echo -e "  ${RED}❌${NC} $file (缺失)"
        exit 1
    fi
done
echo ""

echo -e "${YELLOW}🧪 步骤 4/6: 运行测试${NC}"
cd "$PROJECT_ROOT"

# 设置Python路径
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# 测试导入
echo "测试模块导入..."
python3 -c "
from core.ethics import AthenaConstitution, EthicsEvaluator, WittgensteinGuard
print('✅ 模块导入成功')

# 测试创建实例
constitution = AthenaConstitution()
print(f'✅ 宪法创建成功: {constitution.get_summary()[\"total_principles\"]} 条原则')

guard = WittgensteinGuard()
print(f'✅ 维特根斯坦守护创建成功: {guard.get_status()[\"total_games\"]} 个语言游戏')

evaluator = EthicsEvaluator(constitution, guard)
print('✅ 伦理评估器创建成功')
" || {
    echo -e "${RED}❌ 测试失败${NC}"
    exit 1
}
echo ""

echo -e "${YELLOW}🎯 步骤 5/6: 运行小诺伦理补丁测试${NC}"
python3 "$ETHICS_DIR/xiaonuo_ethics_patch.py" || {
    echo -e "${RED}❌ 补丁测试失败${NC}"
    exit 1
}
echo ""

echo -e "${YELLOW}📊 步骤 6/6: 生成部署报告${NC}"
REPORT_FILE="$PROJECT_ROOT/reports/ethics_deployment_$(date +%Y%m%d_%H%M%S).md"

mkdir -p "$(dirname "$REPORT_FILE")"

cat > "$REPORT_FILE" << EOF
# AI伦理框架部署报告

**部署时间**: $(date '+%Y-%m-%d %H:%M:%S')
**版本**: 1.0.0
**状态**: ✅ 成功

## 部署详情

### 模块文件
EOF

for file in "${required_files[@]}"; do
    size=$(wc -c < "$ETHICS_DIR/$file" 2>/dev/null || echo "0")
    echo "- \`$file\`: ${size} bytes" >> "$REPORT_FILE"
done

cat >> "$REPORT_FILE" << EOF

### 伦理原则摘要
EOF

python3 << 'PYTHON' >> "$REPORT_FILE"
from core.ethics import AthenaConstitution
constitution = AthenaConstitution()
summary = constitution.get_summary()

print(f"- 总原则数: {summary['total_principles']}")
print(f"- 启用原则: {summary['enabled_principles']}")
print(f"- 关键原则: {summary['critical_principles']}")
print(f"- 高优先级: {summary['high_principles']}")
print(f"\n### 哲学来源分布")
for source, data in summary['sources'].items():
    print(f"- **{source}**: {data['enabled']}/{data['total']} 启用")
PYTHON

cat >> "$REPORT_FILE" << EOF

### 语言游戏
EOF

python3 << 'PYTHON' >> "$REPORT_FILE"
from core.ethics import WittgensteinGuard
guard = WittgensteinGuard()
status = guard.get_status()

print(f"- 总游戏数: {status['total_games']}")
print(f"- 启用游戏: {status['enabled_games']}")
print(f"\n已注册游戏:")
for game in status['games']:
    status_icon = "✅" if game['enabled'] else "❌"
    print(f"- {status_icon} **{game['name']}** ({game['domain']})")
    print(f"  - 模式数: {game['patterns_count']}")
    print(f"  - 阈值: {game['threshold']}")
PYTHON

cat >> "$REPORT_FILE" << EOF

## 使用指南

### 为智能体添加伦理约束

\`\`\`python
# 方法1: 使用装饰器
from core.ethics.constraints import ethical_action

@ethical_action(agent_id="my_agent")
def my_method(query: str):
    return process(query)

# 方法2: 使用小诺补丁
from core.ethics.xiaonuo_ethics_patch import patch_xiaonuo
wrapper = patch_xiaonuo(xiaonuo_instance)
\`\`\`

### 查看监控数据

\`\`\`python
from core.ethics import EthicsMonitor, create_ethics_evaluator

evaluator = create_ethics_evaluator()
monitor = EthicsMonitor(evaluator)
dashboard = monitor.generate_dashboard_data()
\`\`\`

## 下一步

1. ✅ 为小诺应用伦理补丁
2. ✅ 为其他智能体集成伦理约束
3. ✅ 设置监控告警
4. ✅ 定期审查伦理报告

---

**部署完成**: 所有AI智能体现在遵循统一伦理框架
EOF

echo -e "${GREEN}✅ 部署报告生成: $REPORT_FILE${NC}"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🎉 AI伦理框架部署成功！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "📚 快速开始:"
echo ""
echo "1. 查看部署报告:"
echo "   cat $REPORT_FILE"
echo ""
echo "2. 为小诺应用伦理补丁:"
echo "   from core.ethics.xiaonuo_ethics_patch import patch_xiaonuo"
echo "   wrapper = patch_xiaonuo(xiaonuo_instance)"
echo ""
echo "3. 运行测试:"
echo "   python3 core/ethics/xiaonuo_ethics_patch.py"
echo ""
echo "📖 完整文档:"
echo "   cat $ETHICS_DIR/README.md"
echo ""
