# 端到端测试套件

## 概述

本测试套件用于测试Athena平台中Agent的协作工作流，特别是：

1. **检索→分析→撰写**的完整专利处理流程
2. 各Agent的独立功能和集成能力
3. 系统性能和错误处理
4. CI/CD管道集成

## 测试架构

### 测试组件

```
tests/e2e/
├── conftest.py              # 测试配置和fixture
├── test_agent_workflow.py   # 主要工作流测试
├── run_e2e_tests.py        # 测试运行器
├── README.md               # 本文档
└── ...                     # 测试结果目录
```

### 测试场景

1. **专利分析场景**
   - 输入：专利申请请求
   - 流程：检索 → 分析 → 撰写
   - 验证：结果质量和完整性

2. **无效宣告场景**
   - 输入：无效宣告请求
   - 流程：检索 → 分析
   - 验证：法律分析准确性

3. **侵权分析场景**
   - 输入：侵权分析请求
   - 流程：检索 → 分析
   - 验证：风险评估合理性

4. **答复审查意见场景**
   - 输入：答复审查意见请求
   - 流程：检索 → 分析 → 撰写
   - 验证：答复文档质量

## 运行测试

### 本地运行

```bash
# 运行所有E2E测试
python tests/e2e/run_e2e_tests.py

# 指定输出目录
python tests/e2e/run_e2e_tests.py --output ./my_test_results

# 详细输出
python tests/e2e/run_e2e_tests.py --verbose
```

### 使用pytest

```bash
# 运行工作流测试
pytest tests/e2e/test_agent_workflow.py -v

# 运行性能测试
pytest tests/e2e/test_agent_workflow.py::TestAgentPerformance -v -m performance

# 运行集成测试
pytest tests/e2e/test_agent_workflow.py::TestAgentIntegration -v
```

### Docker环境

```bash
# 启动测试环境
docker-compose -f docker-compose.unified.yml --profile test up -d

# 运行测试
docker-compose -f docker-compose.unified.yml --profile test exec athena python tests/e2e/run_e2e_tests.py

# 查看测试结果
docker-compose -f docker-compose.unified.yml --profile test exec athena ls /app/tests/e2e/test_results
```

## 测试覆盖

### 工作流测试

| 测试项 | 描述 | 验证点 |
|--------|------|--------|
| `test_retriever_agent_workflow` | 检索者工作流 | 检索结果数量、相关性、性能 |
| `test_analyzer_agent_workflow` | 分析者工作流 | 技术特征提取、创造性分析 |
| `test_writer_agent_workflow` | 撰写者工作流 | 文档生成、质量评估 |
| `test_complete_workflow` | 完整工作流 | 端到端流程、结果聚合 |
| `test_error_handling` | 错误处理 | 异常情况恢复 |

### 性能测试

| 指标 | 阈值 | 监控点 |
|------|------|--------|
| Agent初始化 | <100ms | 冷启动时间 |
| 单个任务执行 | <5s | P95响应时间 |
| 完整工作流 | <15s | 端到端耗时 |
| QPS | >10 | 吞吐量 |
| 内存使用 | <500MB | 内存占用 |

### 集成测试

| 测试项 | 描述 |
|--------|------|
| `test_agent_registry_integration` | Agent注册表集成 |
| `test_scenario_detection` | 场景检测准确性 |
| `test_workflow_execution` | 工作流执行监控 |

## 测试结果

### 报告格式

测试运行后会生成两种格式的报告：

1. **JSON报告** (`e2e_test_report_YYYYMMDD_HHMMSS.json`)
   - 详细的技术数据
   - 性能指标
   - 错误详情

2. **Markdown报告** (`e2e_test_report_YYYYMMDD_HHMMSS.md`)
   - 可读性强的摘要
   - 测试结果概览
   - 失败详情

### 示例报告结构

```json
{
  "total_tests": 5,
  "passed_tests": 4,
  "failed_tests": 1,
  "pass_rate": 0.8,
  "total_duration": 25.3,
  "avg_duration": 5.06,
  "test_groups": {
    "workflow": {
      "count": 3,
      "passed": 3,
      "failed": 0
    },
    "performance": {
      "count": 1,
      "passed": 1,
      "failed": 0
    },
    "integration": {
      "count": 1,
      "passed": 0,
      "failed": 1
    }
  }
}
```

## CI/CD集成

### GitHub Actions

测试已集成到GitHub Actions，触发条件：

- 推送到main/develop分支
- Pull Request到main/develop
- 每天凌晨2点自动运行
- 手动触发

### 环境变量

```bash
# 测试模式
export TEST_MODE=e2e
export MOCK_DATA=true

# 数据库配置
export POSTGRES_USER=athena
export POSTGRES_PASSWORD=athena123
export POSTGRES_DB=athena_test

# Redis配置
export REDIS_PASSWORD=redis123
```

### 质量门禁

- 通过率必须 ≥ 80%
- 平均响应时间 ≤ 5秒
- 无严重性能回归
- 所有关键测试必须通过

## Mock数据

测试使用模拟数据来减少外部依赖：

### 专利数据
```python
{
    "id": "CN123456789A",
    "title": "一种结合拟人驾驶行为的自动驾驶掉头路段脱困规划方法",
    "abstract": "本发明涉及自动驾驶技术领域...",
    "inventor": ["张三", "李四"],
    "assignee": "某科技有限公司"
}
```

### 检索结果
- 3个相关专利
- 相关性评分：0.82-0.95
- 多数据库覆盖（CNIPA、WIPO）

### 分析结果
- 2个主要技术特征
- 创造性评分：0.75-0.85
- 侵权风险评估：中等

## 故障排除

### 常见问题

1. **测试超时**
   ```
   pytest: test timed out after 30 seconds
   ```
   解决：增加超时时间或优化测试逻辑

2. **数据库连接失败**
   ```
   psycopg2.OperationalError: connection to server failed
   ```
   解决：确保PostgreSQL服务正在运行

3. **Redis连接失败**
   ```
   redis.exceptions.ConnectionError: Error connecting to Redis
   ```
   解决：检查Redis服务状态

4. **导入错误**
   ```
   ModuleNotFoundError: No module named 'core.agents'
   ```
   解决：设置PYTHONPATH或使用poetry运行

### 调试模式

```bash
# 启用详细日志
export LOG_LEVEL=DEBUG
python tests/e2e/run_e2e_tests.py --verbose

# 单步调试
pytest tests/e2e/test_agent_workflow.py::TestE2EWorkflow::test_complete_workflow -v --no-header --tb=long
```

## 扩展测试

### 添加新的测试场景

1. 在`conftest.py`中添加新的测试数据
2. 在`test_agent_workflow.py`中添加新的测试方法
3. 更新CI/CD配置（如需要）

### 性能基准

```python
# 在TestAgentPerformance中添加新的性能测试
async def test_custom_performance(self):
    # 自定义性能测试逻辑
    pass
```

### Mock数据扩展

```python
# 创建新的MockAgent类
class CustomMockAgent:
    async def execute(self, context):
        # 自定义Mock逻辑
        pass
```

## 最佳实践

1. **保持测试独立性**
   - 每个测试应该能够独立运行
   - 使用fixture来共享测试数据

2. **Mock优先**
   - 使用Mock数据减少外部依赖
   - 只在必要时使用真实服务

3. **性能监控**
   - 设置合理的性能阈值
   - 定期检查性能趋势

4. **错误处理**
   - 测试各种错误场景
   - 验证错误恢复机制

5. **文档更新**
   - 更新测试文档
   - 记录新的测试场景

## 联系方式

如有问题或建议，请联系：
- Athena Team
- GitHub Issues
- 邮件：athena-team@example.com