#!/bin/bash

# Athena工作平台优化启动脚本
# 用于一键启动优化项目

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Logo
print_logo() {
    echo -e "${BLUE}"
    cat << 'EOF'
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                            ║
    ║        🚀 Athena工作平台优化项目启动器                      ║
    ║                                                            ║
    ║    让我们一起将Athena打造成更优秀的项目！                ║
    ║                                                            ║
    ╚══════════════════════════════════════════════════════════════╝
    ${NC}"
}

# 检查前置条件
check_prerequisites() {
    echo -e "${YELLOW}检查前置条件...${NC}"

    # 检查Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${YELLOW}⚠️ Python 3 未安装，请先安装Python 3.11+${NC}"
        exit 1
    fi

    # 检查Node.js
    if ! command -v node &> /dev/null; then
        echo -e "${YELLOW}⚠️ Node.js 未安装，请先安装Node.js 16+${NC}"
        exit 1
    fi

    # 检查Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${YELLOW}⚠️ Docker 未安装，某些功能可能受限${NC}"
    fi

    echo -e "${GREEN}✅ 前置条件检查通过${NC}"
}

# 显示优化计划
show_plan() {
    echo -e "\n${BLUE}📋 优化计划总览${NC}"
    echo
    echo -e "📅 第一周：安全加固与基础设施 (P0优先级)"
    echo "   - 消除安全风险"
    echo "   - 配置标准化"
    echo "   - 代码规范化"
    echo
    echo -e "📅 第二周：代码重构与质量提升"
    echo "   - Python代码优化"
    echo "   - JavaScript/TypeScript改进"
    echo "   - 数据库操作标准化"
    echo
    echo -e "📅 第三周：文档更新与知识管理"
    echo "   - 文档结构重组"
    echo "   - API文档自动化"
    echo "   - 知识库建设"
    echo
    echo -e "📅 第四周：自动化与监控"
    echo "   - CI/CD Pipeline"
    echo "   - 监控告警系统"
    echo "   - 持续改进机制"
    echo
}

# 选择执行模式
select_mode() {
    echo -e "\n${BLUE}请选择执行模式：${NC}"
    echo
    echo "1️⃣  执行完整优化计划（4周）"
    echo "2️⃣  执行特定阶段"
    echo "3️⃣  执行特定天的任务"
    echo "4️⃣  执行特定任务"
    echo "5️⃣  仅生成报告"
    echo "6️⃣  查看任务清单"
    echo
    read -p "请输入选择 (1-6): " choice

    case $choice in
        1)
            execute_full_plan
            ;;
        2)
            select_phase
            ;;
        3)
            select_day
            ;;
        4)
            select_task
            ;;
        5)
            generate_report only
            ;;
        6)
            view_checklist
            ;;
        *)
            echo -e "${YELLOW}无效选择，退出${NC}"
            exit 1
            ;;
    esac
}

# 执行完整计划
execute_full_plan() {
    echo -e "\n${GREEN}🚀 启动完整优化计划${NC}"
    echo
    echo -e "⚠️  注意：完整计划需要4周时间，建议分阶段执行"
    echo
    read -p "确定要继续吗？(y/N): " confirm

    if [[ $confirm == "y" || $confirm == "Y" ]]; then
        echo -e "${BLUE}建议先执行第一周的任务${NC}"
        execute_phase_1
    else
        echo "已取消"
    fi
}

# 选择阶段
select_phase() {
    echo -e "\n${BLUE}选择优化阶段：${NC}"
    echo
    echo "1️⃣  第一周：安全加固与基础设施"
    echo "2️⃣  第二周：代码重构与质量提升"
    echo "3️⃣  第三周：文档更新与知识管理"
    echo "4️⃣  第四周：自动化与监控"
    echo
    read -p "请输入选择 (1-4): " choice

    case $choice in
        1) execute_phase_1 ;;
        2) echo "第二周计划尚未准备完成" ;;
        3) echo "第三周计划尚未准备完成" ;;
        4) echo "第四周计划尚未准备完成" ;;
        *) echo "无效选择" ;;
    esac
}

# 选择天数
select_day() {
    echo -e "\n${BLUE}选择执行天数 (1-7)：${NC}"
    read -p "请输入天数: " day

    if [[ $day -ge 1 && $day -le 7 ]]; then
        echo -e "${GREEN}将执行第${day}天的任务${NC}"
        ./scripts/optimization/execute_optimization.sh day:$day
    else
        echo "无效的天数"
    fi
}

# 选择任务
select_task() {
    echo -e "\n${BLUE}输入任务ID (如 SEC-001)：${NC}"
    read -p "任务ID: " task_id

    if [[ -n $task_id ]]; then
        echo -e "${GREEN}执行任务: ${task_id}${NC}"
        ./scripts/optimization/execute_optimization.sh task:$task_id
    else
        echo "无效的任务ID"
    fi
}

# 生成报告
generate_report() {
    echo -e "\n${GREEN}📊 生成优化报告${NC}"

    # 执行状态检查
    ./scripts/optimization/execute_optimization.sh

    # 打开报告
    if command -v code &> /dev/null; then
        code documentation/analysis/
    elif command -v open &> /dev/null; then
        open documentation/analysis/
    fi
}

# 查看任务清单
view_checklist() {
    echo -e "\n${GREEN}📋 打开任务清单${NC}"

    if command -v code &> /dev/null; then
        code scripts/optimization/optimization_checklist.md
    elif command -v open &> /dev/null; then
        open scripts/optimization/optimization_checklist.md
    else
        echo "请手动打开: scripts/optimization/optimization_checklist.md"
    fi
}

# 执行第一阶段
execute_phase_1() {
    echo -e "\n${GREEN}🔒 启动第一阶段：安全加固与基础设施${NC}"
    echo

    # 创建工作目录
    mkdir -p optimization_work/{backup,logs}

    # 执行安全任务
    echo "正在执行安全任务..."
    ./scripts/optimization/execute_optimization.sh phase:1

    echo -e "\n${GREEN}✅ 第一阶段任务已启动${NC}"
    echo -e "${BLUE}请查看 optimization_work/logs/ 目录了解详细信息${NC}"
}

# 主函数
main() {
    print_logo
    check_prerequisites
    show_plan
    select_mode
}

# 运行主函数
main