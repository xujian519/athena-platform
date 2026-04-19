#!/bin/bash
# 小诺法律智能支持系统启动脚本
# 作者: 小诺·双鱼座

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    echo -e "${2}${1}${NC}"
}

# 打印标题
print_title() {
    echo ""
    print_message "👑 小诺法律智能支持系统启动器 👑" $PURPLE
    print_message "=" 50 $BLUE
}

# 检查依赖
check_dependencies() {
    print_message "🔍 检查系统依赖..." $BLUE

    # 检查Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -V 2>&1 | cut -d' ' -f2)
        print_message "✓ Python: $PYTHON_VERSION" $GREEN
    else
        print_message "✗ Python3 未安装" $RED
        exit 1
    fi

    # 检查Docker
    if command -v docker &> /dev/null; then
        print_message "✓ Docker: $(docker --version)" $GREEN
    else
        print_message "✗ Docker 未安装" $RED
        exit 1
    fi

    # 检查pip依赖
    print_message "🔍 检查Python依赖..." $BLUE

    # 创建requirements文件（如果不存在）
    if [ ! -f "requirements.txt" ]; then
        cat > requirements.txt << EOF
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
requests==2.31.0
sentence-transformers==2.2.2
numpy==1.24.3
jieba==0.42.1
networkx==3.2.1
aiofiles==23.2.1
python-multipart==0.0.6
EOF
    fi

    # 安装依赖
    print_message "📦 安装Python依赖..." $BLUE
    pip3 install -r requirements.txt

    print_message "✅ 依赖检查完成" $GREEN
}

# 启动NebulaGraph
start_nebula() {
    print_message "🕸️ 启动NebulaGraph图数据库..." $BLUE

    cd ../nebula-graph-deploy

    # 检查NebulaGraph是否已经运行
    if docker ps | grep nebula-graphd &> /dev/null; then
        print_message "✓ NebulaGraph 已经在运行" $GREEN
    else
        # 启动NebulaGraph
        ./nebula-manager.sh start

        # 等待服务启动
        print_message "⏳ 等待NebulaGraph启动..." $YELLOW
        sleep 10

        # 检查启动状态
        if docker ps | grep nebula-graphd &> /dev/null; then
            print_message "✅ NebulaGraph 启动成功" $GREEN
        else
            print_message "✗ NebulaGraph 启动失败" $RED
            exit 1
        fi
    fi

    cd -
}

# 验证数据
verify_data() {
    print_message "📊 验证知识图谱数据..." $BLUE

    cd ../nebula-graph-deploy

    # 检查法律知识图谱空间
    result=$(docker run --rm --network nebula-net \
        vesoft/nebula-console:v3.6.0 \
        -addr nebula-graphd \
        -port 9669 \
        -u root \
        -p nebula \
        -e "SHOW SPACES;" 2>/dev/null | grep "法律知识图谱")

    if [ -n "$result" ]; then
        print_message "✓ 法律知识图谱空间已创建" $GREEN
    else
        print_message "! 创建法律知识图谱空间..." $YELLOW
        docker run --rm --network nebula-net \
            vesoft/nebula-console:v3.6.0 \
            -addr nebula-graphd \
            -port 9669 \
            -u root \
            -p nebula \
            -e "CREATE SPACE IF NOT EXISTS 法律知识图谱(partition_num=10, replica_factor=1, vid_type=fixed_string(128));"
    fi

    cd -
}

# 启动API服务
start_api() {
    print_message "🚀 启动小诺法律API服务..." $BLUE

    # 创建日志目录
    mkdir -p logs

    # 后台启动API服务
    nohup python3 legal_qa_api.py > logs/xiaona_legal_api.log 2>&1 &
    API_PID=$!
    echo $API_PID > .api.pid

    # 等待服务启动
    print_message "⏳ 等待API服务启动..." $YELLOW
    sleep 5

    # 检查API服务
    if curl -s http://localhost:8000/health > /dev/null; then
        print_message "✅ API服务启动成功" $GREEN
        print_message "📍 API地址: http://localhost:8000" $BLUE
        print_message "📖 文档地址: http://localhost:8000/docs" $BLUE
    else
        print_message "✗ API服务启动失败" $RED
        print_message "📝 查看日志: tail -f logs/xiaona_legal_api.log" $YELLOW
        exit 1
    fi
}

# 运行集成测试
run_tests() {
    if [ "$1" = "--with-tests" ]; then
        print_message "🧪 运行集成测试..." $BLUE
        python3 integration_test.py
    fi
}

# 显示状态
show_status() {
    print_message "" $NC
    print_message "🎉 小诺法律智能支持系统已启动！" $GREEN
    print_message "" $NC
    print_message "📋 服务状态:" $BLUE
    print_message "  • NebulaGraph: 运行中" $GREEN
    print_message "  • API服务: http://localhost:8000" $GREEN
    print_message "" $NC
    print_message "🔗 快速访问:" $BLUE
    print_message "  • API文档: http://localhost:8000/docs" $YELLOW
    print_message "  • 健康检查: http://localhost:8000/health" $YELLOW
    print_message "" $NC
    print_message "📚 使用示例:" $BLUE
    print_message "  # 测试法律搜索" $NC
    print_message 'curl -X POST "http://localhost:8000/api/v1/search" \' $NC
    print_message '  -H "Content-Type: application/json" \' $NC
    print_message '  -d "{\"query\":\"离婚财产分割\",\"search_type\":\"hybrid\"}"' $NC
    print_message "" $NC
    print_message "  # 测试法律问答" $NC
    print_message 'curl -X POST "http://localhost:8000/api/v1/qa" \' $NC
    print_message '  -H "Content-Type: application/json" \' $NC
    print_message '  -d "{\"query\":\"劳动合同解除需要什么条件？\"}"' $NC
    print_message "" $NC
}

# 主函数
main() {
    print_title

    # 解析参数
    RUN_TESTS=false
    for arg in "$@"; do
        case $arg in
            --with-tests)
                RUN_TESTS=true
                shift
                ;;
            --help)
                echo "用法: $0 [选项]"
                echo "选项:"
                echo "  --with-tests  启动后运行集成测试"
                echo "  --help        显示此帮助信息"
                exit 0
                ;;
        esac
    done

    # 检查依赖
    check_dependencies

    # 启动NebulaGraph
    start_nebula

    # 验证数据
    verify_data

    # 启动API服务
    start_api

    # 运行测试（如果指定）
    if [ "$RUN_TESTS" = true ]; then
        run_tests --with-tests
    fi

    # 显示状态
    show_status
}

# 信号处理
cleanup() {
    print_message "" $NC
    print_message "🛑 正在停止服务..." $YELLOW

    # 停止API服务
    if [ -f .api.pid ]; then
        API_PID=$(cat .api.pid)
        kill $API_PID 2>/dev/null
        rm -f .api.pid
        print_message "✓ API服务已停止" $GREEN
    fi

    print_message "✅ 服务已停止" $GREEN
    exit 0
}

# 注册信号处理
trap cleanup SIGINT SIGTERM

# 运行主函数
main "$@"