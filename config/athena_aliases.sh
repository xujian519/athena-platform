#!/bin/bash
# Athena工作平台 - 快捷别名配置
# 最后更新: 2026-02-03

# 项目路径快捷方式
export ATHENA_HOME="/Users/xujian/Athena工作平台"
export ATHENA_CONFIG="$ATHENA_HOME/config"
export ATHENA_CORE="$ATHENA_HOME/core"

# 快捷导航别名
alias athena="cd $ATHENA_HOME"
alias aconf="cd $ATHENA_CONFIG"
alias acore="cd $ATHENA_HOME/core"
alias alogs="cd $ATHENA_HOME/logs"

# Docker快捷命令
alias adown="cd $ATHENA_HOME && docker-compose down"
alias aup="cd $ATHENA_HOME && docker-compose up -d"
alias alogs="cd $ATHENA_HOME && docker-compose logs -f"
alias arestart="cd $ATHENA_HOME && docker-compose restart"

# 常用命令
alias astatus="cd $ATHENA_HOME && docker-compose ps"
alias aenv="cat $ATHENA_HOME/.env"

# 显示帮助信息
alias athena-help="cat << 'EOF'
🏛️  Athena工作平台 - 快捷命令

导航:
  athena    - 进入项目根目录
  aconf     - 进入config目录
  acore     - 进入core目录
  alogs     - 进入logs目录

Docker:
  aup       - 启动所有服务
  adown     - 停止所有服务
  arestart  - 重启所有服务
  astatus   - 查看服务状态
  alogs     - 查看实时日志

其他:
  aenv      - 查看环境变量配置
EOF"
