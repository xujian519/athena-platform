# 智能体设计模式测试套件

本测试套件为智能体设计模式组件提供全面的测试覆盖，包括单元测试、集成测试和性能测试。

## 📁 目录结构

```
tests/
├── __init__.py                 # 测试框架初始化
├── test_framework.py          # 测试基础设施和工具
├── test_config.json          # 测试配置文件
├── run_all_tests.py          # 综合测试运行器
├── unit/                      # 单元测试
│   ├── test_agentic_task_planner.py
│   ├── test_prompt_chain_processor.py
│   └── test_goal_management_system.py
├── integration/               # 集成测试
│   └── test_agent_integrations.py
├── performance/               # 性能测试
│   └── test_performance_benchmarks.py
├── data/                     # 测试数据
│   └── performance_baseline.json
├── reports/                  # 测试报告
│   └── (生成的报告文件)
└── logs/                     # 测试日志
    └── test_run.log
```

## 🚀 快速开始

### 运行所有测试

```bash
python3 tests/run_all_tests.py
```

### 运行特定类型的测试

#### 单元测试
```bash
python3 -m unittest tests.unit.test_agentic_task_planner
python3 -m unittest tests.unit.test_prompt_chain_processor
python3 -m unittest tests.unit.test_goal_management_system
```

#### 集成测试
```bash
python3 -m unittest tests.integration.test_agent_integrations
```

#### 性能测试
```bash
python3 tests/performance/test_performance_benchmarks.py
```

### 运行单个测试文件

```bash
python3 -m unittest tests.unit.test_agentic_task_planner.TaskAgenticTaskPlanner.test_planner_initialization
```

## 📊 测试覆盖范围

### 单元测试

#### 智能任务规划器 (AgenticTaskPlanner)
- ✅ 初始化测试
- ✅ 创建执行计划测试
- ✅ 任务步骤创建测试
- ✅ 智能体能力测试
- ✅ 任务类型识别测试
- ✅ 依赖关系处理测试
- ✅ 资源分配测试
- ✅ 优先级分配测试
- ✅ 性能跟踪测试
- ✅ 错误处理测试
- ✅ 计划序列化测试
- ✅ 并发计划创建测试
- ✅ 边界情况测试
- ✅ 内存使用测试

#### 提示链处理器 (PromptChainProcessor)
- ✅ 处理器初始化测试
- ✅ 创建简单链测试
- ✅ 链步骤创建测试
- ✅ 验证规则测试
- ✅ 链执行模拟测试
- ✅ 精炼标准测试
- ✅ 错误处理测试
- ✅ 链状态管理测试
- ✅ 输入映射测试
- ✅ 链模板测试
- ✅ 并行步骤执行测试
- ✅ 链执行统计测试
- ✅ 链验证测试
- ✅ 链优化测试

#### 目标管理系统 (GoalManagementSystem)
- ✅ 管理器初始化测试
- ✅ 创建简单目标测试
- ✅ 创建复杂目标测试
- ✅ 子目标创建测试
- ✅ 进度指标测试
- ✅ 目标状态更新测试
- ✅ 子目标完成测试
- ✅ 进度计算测试
- ✅ 目标搜索测试
- ✅ 目标截止时间跟踪测试
- ✅ 目标分类管理测试
- ✅ 进度报告生成测试
- ✅ 详细进度分析测试
- ✅ 进度趋势测试

### 集成测试

#### 智能体集成
- ✅ 小诺规划集成测试
- ✅ 小娜提示链集成测试
- ✅ 云熙目标管理集成测试
- ✅ 小宸协作集成测试
- ✅ 跨智能体集成测试
- ✅ 集成性能测试
- ✅ 集成可靠性测试
- ✅ 完整集成场景测试

### 性能测试

#### 基准测试
- ✅ 任务规划器性能测试
- ✅ 提示链处理器性能测试
- ✅ 目标管理器性能测试
- ✅ 智能体集成性能测试
- ✅ 内存使用测试
- ✅ 并发负载测试
- ✅ 内存泄漏检测测试

## 📈 性能基准

### 响应时间基准
- **优秀**: < 0.5 秒
- **良好**: < 1.0 秒
- **可接受**: < 2.0 秒
- **差**: > 5.0 秒

### 成功率基准
- **优秀**: > 99%
- **良好**: > 95%
- **可接受**: > 90%
- **差**: < 80%

### 内存使用基准
- **优秀**: < 50 MB
- **良好**: < 100 MB
- **可接受**: < 200 MB
- **差**: > 500 MB

## 🔧 配置说明

### 测试配置文件 (test_config.json)

```json
{
  "test_environment": {
    "mock_external_services": true,    // 是否模拟外部服务
    "enable_performance_monitoring": true,  // 是否启用性能监控
    "log_level": "INFO",               // 日志级别
    "timeout": 30                      // 超时时间（秒）
  },
  "unit_tests": {
    "enabled": true,                   // 是否启用单元测试
    "verbosity": 2,                    // 详细程度
    "buffer": true                     // 是否缓冲输出
  },
  "performance_tests": {
    "baseline_comparison": true,       // 是否与基准比较
    "memory_monitoring": true,         // 是否监控内存
    "generate_report": true            // 是否生成报告
  }
}
```

## 📊 测试报告

测试完成后，会在 `tests/reports/` 目录下生成以下报告：

1. **JSON报告**: 包含详细的测试数据和指标
2. **Markdown报告**: 人类可读的测试总结
3. **HTML报告**: 可视化的测试结果展示
4. **性能报告**: 详细的性能分析和建议

## 🛠️ 测试框架特性

### 测试环境管理
- 自动设置和清理测试环境
- 模拟外部服务依赖
- 隔离测试数据

### 性能监控
- 实时CPU和内存监控
- 响应时间统计
- 性能基准对比

### 错误处理
- 详细的错误信息收集
- 失败测试截图（如果适用）
- 自动重试机制

### 报告生成
- 多格式报告支持
- 历史数据对比
- 改进建议生成

## 🚨 持续集成

### GitHub Actions 集成

```yaml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    - name: Run tests
      run: python3 tests/run_all_tests.py
    - name: Upload test reports
      uses: actions/upload-artifact@v2
      with:
        name: test-reports
        path: tests/reports/
```

### 质量门禁

测试通过的质量标准：
- ✅ 所有测试必须通过
- ✅ 平均响应时间 < 2.0 秒
- ✅ 成功率 > 90%
- ✅ 内存使用 < 300 MB
- ✅ 无内存泄漏

## 🐛 故障排除

### 常见问题

#### 1. 测试超时
```
问题: 测试执行超时
解决: 增加 test_config.json 中的 timeout 值
```

#### 2. 导入错误
```
问题: ModuleNotFoundError
解决: 确保 PYTHONPATH 包含项目根目录
```

#### 3. 权限错误
```
问题: Permission denied
解决: 确保对 tests/ 目录有写权限
```

#### 4. 内存不足
```
问题: 内存使用过高
解决: 减少并发测试数量或增加系统内存
```

### 调试模式

启用详细日志输出：

```bash
export PYTHONPATH=/Users/xujian/Athena工作平台
python3 -m unittest -v tests.unit.test_agentic_task_planner
```

## 📝 贡献指南

### 添加新测试

1. 在相应的测试文件中添加测试方法
2. 遵循命名约定 `test_*`
3. 添加详细的文档字符串
4. 包含正面和负面测试用例

### 性能测试

1. 使用 `@unittest.skipIf` 跳过慢速测试
2. 设置合理的超时时间
3. 清理测试产生的资源

### 代码覆盖率

生成代码覆盖率报告：

```bash
pip install coverage
coverage run -m unittest discover tests/
coverage report -m
coverage html
```

## 📚 参考资料

- [Python unittest 文档](https://docs.python.org/3/library/unittest.html)
- [异步测试指南](https://docs.python.org/3/library/unittest.async-test-case-examples.html)
- [性能测试最佳实践](https://docs.python.org/3/library/profile.html)

## 🤝 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 GitHub Issue
- 发送邮件至开发团队
- 在团队频道中讨论

---

**最后更新**: 2025-12-17
**版本**: 1.0.0
**维护者**: Athena Platform Team