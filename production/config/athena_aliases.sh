# Athena平台快捷别名配置
# 将此文件添加到 ~/.zshrc 或 ~/.bashrc 中

# Athena快捷启动别名
alias athena='/Users/xujian/Athena工作平台/dev/scripts/athena_quick_start.sh'
alias 启动平台='/Users/xujian/Athena工作平台/dev/scripts/athena_quick_start.sh 启动平台'
alias 平台状态='/Users/xujian/Athena工作平台/dev/scripts/athena_quick_start.sh 服务状态'
alias 小诺='/Users/xujian/Athena工作平台/dev/scripts/athena_quick_start.sh 启动小诺'
alias 小娜='/Users/xujian/Athena工作平台/dev/scripts/athena_quick_start.sh 启动小娜'
alias 监控='/Users/xujian/Athena工作平台/dev/scripts/athena_quick_start.sh 启动监控'

# 函数式别名（支持更自然的语言）
启动() {
    /Users/xujian/Athena工作平台/dev/scripts/athena_quick_start.sh "$@"
}

# 检查服务状态
服务状态() {
    /Users/xujian/Athena工作平台/dev/scripts/athena_quick_start.sh 服务状态
}

# 快速启动核心服务
快速启动() {
    /Users/xujian/Athena工作平台/dev/scripts/athena_quick_start.sh 启动平台
}

# 显示小诺身份
小诺身份() {
    python3 /Users/xujian/Athena工作平台/apps/apps/xiaonuo/show_xiaonuo_identity.py
}

# 小诺对话（预留）
小诺对话() {
    echo "💝 小诺：爸爸，我在听！请问有什么我可以帮您的吗？"
    # 未来可以连接到小NLP服务器进行对话
}
