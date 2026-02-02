# 按需启动AI系统配置
# 根据您的使用模式调整这些参数

# 内存配置 (MB)
MEMORY_CONFIG = {
    "xiaonuo": 40,   # 小诺 - 最小内存
    "xiaona": 100,   # 小娜 - 专利分析
    "yunxi": 80,     # 云熙 - IP管理
    "xiaochen": 60   # 小宸 - 内容创作
}

# 空闲超时配置 (秒)
IDLE_TIMEOUTS = {
    "xiaonuo": 0,     # 永不停止
    "xiaona": 300,    # 5分钟
    "yunxi": 180,     # 3分钟
    "xiaochen": 120   # 2分钟
}

# 性能配置
PERFORMANCE_CONFIG = {
    "max_concurrent_tasks": 50,
    "task_queue_size": 100,
    "health_check_interval": 30
}

# 根据使用模式选择预设
USE_CASE = "minimal"  # "development", "production", "minimal" - 最大化资源节省

if USE_CASE == "development":
    # 开发环境 - 较长超时，方便调试
    IDLE_TIMEOUTS = {k: v * 2 for k, v in IDLE_TIMEOUTS.items() if k != "xiaonuo"}

elif USE_CASE == "production":
    # 生产环境 - 平衡性能和资源
    MEMORY_CONFIG = {k: v * 1.2 for k, v in MEMORY_CONFIG.items()}

elif USE_CASE == "minimal":
    # 最小化配置 - 最大化资源节省
    MEMORY_CONFIG = {k: int(v * 0.7) for k, v in MEMORY_CONFIG.items()}
    IDLE_TIMEOUTS = {k: max(v // 2, 60) for k, v in IDLE_TIMEOUTS.items() if k != "xiaonuo"}

print(f"📊 当前配置:")
print(f"   使用模式: {USE_CASE}")
print(f"   内存配置: {MEMORY_CONFIG}")
print(f"   空闲超时: {IDLE_TIMEOUTS}")
