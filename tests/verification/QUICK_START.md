# Athena平台验证测试 - 快速开始

## 30秒快速测试

```bash
# 1. 启动服务
docker-compose up -d

# 2. 运行快速测试
./tests/verification/quick_test.sh
```

## 完整测试流程

```bash
# 1. 快速连通性测试 (30秒)
./tests/verification/quick_test.sh

# 2. Python测试套件 (5分钟)
pytest tests/verification/ -v

# 3. 性能测试 (1分钟)
locust -f tests/verification/locust_kb_performance.py --headless --users=100 --run-time=60s
```

## 测试报告

```bash
# 查看最新报告
cat tests/verification/reports/kb_verification_*.json | jq '.summary'
```

## 文档

详见 [README.md](./README.md)
