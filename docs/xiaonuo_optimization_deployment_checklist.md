# 小诺优化系统 - 生产部署检查清单

## 使用说明

- [ ] 未完成
- [x] 已完成
- [~] 进行中
- [-] 不适用

在部署过程中，请逐项检查并打勾。任何未完成项目都应在部署前解决。

---

## 📋 部署前检查 (Pre-Deployment)

### 环境检查

- [ ] Python版本 >= 3.9
  ```bash
  python3 --version
  ```

- [ ] 所需依赖包已安装
  ```bash
  pip list | grep -E "(numpy|scikit-learn|pyyaml)"
  ```

- [ ] 磁盘空间充足 (>500MB)
  ```bash
  df -h /var/log
  ```

- [ ] 内存充足 (>2GB可用)
  ```bash
  free -h
  ```

- [ ] CPU资源充足 (>2核)
  ```bash
  nproc
  ```

### 配置准备

- [ ] 生产配置文件已创建
  ```bash
  ls -la config/optimization/xiaonuo_production.yaml
  ```

- [ ] 配置文件已审核
  ```bash
  cat config/optimization/xiaonuo_production.yaml
  ```

- [ ] 备份当前配置
  ```bash
  cp -r config/ config_backup_$(date +%Y%m%d)/
  ```

- [ ] 监控配置已设置
  ```bash
  grep -A 10 "monitoring:" config/optimization/xiaonuo_production.yaml
  ```

- [ ] 告警阈值已配置
  ```bash
  grep -A 10 "alerts:" config/optimization/xiaonuo_production.yaml
  ```

### 日志和监控

- [ ] 日志目录已创建
  ```bash
  ls -la /var/log/xiaonuo
  ```

- [ ] 日志目录权限正确
  ```bash
  ls -ld /var/log/xiaonuo
  # 应该显示: drwxr-xr-x
  ```

- [ ] 监控系统可访问
  ```bash
  python3 -c "from core.monitoring.optimization_monitor import get_optimization_monitor; print('OK')"
  ```

- [ ] 告警渠道已配置（邮件/短信/钉钉）
  - [ ] 邮件通知
  - [ ] 短信通知
  - [ ] 即时通讯工具（钉钉/企业微信/Slack）

### 代码和测试

- [ ] 代码已合并到主分支
  ```bash
  git branch --show-current
  ```

- [ ] 单元测试全部通过
  ```bash
  python3 -m pytest tests/unit/ -v
  ```

- [ ] 集成测试全部通过
  ```bash
  python3 tests/integration/optimization/test_lightweight_modules.py
  ```

- [ ] 代码已审查
  - [ ] 至少1人审查
  - [ ] 审查意见已解决

### 备份和回滚

- [ ] 数据库已备份（如适用）
  ```bash
  # pg_dump xiaonuo_db > backup_$(date +%Y%m%d).sql
  ```

- [ ] 回滚方案已准备
  - [ ] 回滚步骤文档化
  - [ ] 回滚命令已验证

- [ ] 部署基线已记录
  ```bash
  git rev-parse HEAD > deployment_baseline.txt
  cat deployment_baseline.txt
  ```

### 团队沟通

- [ ] 团队成员已通知
  - [ ] 开发团队
  - [ ] 测试团队
  - [ ] 运维团队
  - [ ] 产品团队

- [ ] 部署时间窗口已确认
  - 日期: ___________
  - 时间: ___________
  - 时长: ___________

- [ ] 相关方已知晓
  - [ ] 业务方
  - [ ] 客户
  - [ ] 利益相关者

---

## 🚀 部署过程检查 (Deployment Process)

### 阶段1: 准备部署

- [ ] 停止应用服务（如需要）
  ```bash
  systemctl stop xiaonuo
  ```

- [ ] 部署新代码
  ```bash
  git pull origin feature/xiaonuo-integration
  ```

- [ ] 更新配置文件
  ```bash
  cp config/optimization/xiaonuo_production.yaml config/optimization/xiaonuo.yaml
  ```

- [ ] 验证配置加载
  ```bash
  python3 -c "
  from core.optimization.xiaonuo_optimization_manager import OptimizationConfig
  config = OptimizationConfig.from_yaml('config/optimization/xiaonuo.yaml')
  print('配置加载成功')
  print(f'工具发现: {config.enable_tool_discovery}')
  print(f'参数验证: {config.enable_parameter_validation}')
  print(f'错误预测: {config.enable_error_prediction}')
  "
  ```

### 阶段2: 验证部署

- [ ] 启动应用服务
  ```bash
  systemctl start xiaonuo
  ```

- [ ] 检查服务状态
  ```bash
  systemctl status xiaonuo
  ```

- [ ] 检查启动日志
  ```bash
  journalctl -u xiaonuo -n 50 --no-pager
  ```

- [ ] 检查优化模块加载
  ```bash
  grep "优化管理器初始化完成" /var/log/xiaonuo/optimization.log
  ```

- [ ] 运行冒烟测试
  ```bash
  python3 tests/smoke/test_basic.py
  ```

- [ ] 验证API端点
  ```bash
  curl http://localhost:8000/health
  # 预期: {"status": "healthy"}
  ```

### 阶段3: 灰度发布

**第1天: 10% 流量**

- [ ] 配置灰度规则
  ```python
  # 在代码中或网关配置
  GRAY_SCALE_PERCENTAGE = 0.1
  ```

- [ ] 监控错误率 < 5%
  ```bash
  python3 -c "
  from core.optimization.xiaonuo_optimization_manager import get_optimization_manager
  manager = get_optimization_manager()
  summary = manager.get_monitoring_summary()
  print(f'失败率: {summary[\"failure_rate\"]:.1%}')
  "
  ```

- [ ] 监控响应时间 < 500ms
  ```bash
  python3 -c "
  from core.monitoring.optimization_monitor import get_optimization_monitor
  monitor = get_optimization_monitor()
  summary = monitor.get_metrics_summary()
  print(f'平均响应时间: {summary[\"metrics\"][\"request.processing_time_ms\"][\"avg_5min\"]:.1f}ms')
  "
  ```

- [ ] 检查告警数量 = 0
  ```bash
  python3 -c "
  from core.optimization.xiaonuo_optimization_manager import get_optimization_manager
  manager = get_optimization_manager()
  alerts = manager.check_alerts()
  print(f'告警数量: {len(alerts)}')
  "
  ```

**第3天: 30% 流量** (如10%无问题)

- [ ] 调整灰度比例到30%
- [ ] 监控指标正常
- [ ] 用户反馈正常

**第5天: 50% 流量** (如30%无问题)

- [ ] 调整灰度比例到50%
- [ ] 监控指标正常
- [ ] 性能稳定

**第7天: 100% 流量** (如50%无问题)

- [ ] 移除灰度限制
- [ ] 全量上线
- [ ] 持续监控

---

## ✅ 部署后验证 (Post-Deployment)

### 功能验证

- [ ] 核心功能正常
  - [ ] 用户登录
  - [ ] 主要业务流程
  - [ ] API接口响应

- [ ] 优化功能正常
  ```bash
  python3 -c "
  from core.optimization.xiaonuo_optimization_manager import get_optimization_manager
  manager = get_optimization_manager()
  status = manager.get_module_status()
  print(status)
  # 应该显示各模块启用状态
  "
  ```

- [ ] 自动降级功能测试
  - [ ] 模拟优化失败
  - [ ] 验证降级到默认处理

### 性能验证

- [ ] 响应时间正常
  - [ ] P50 < 阈值
  - [ ] P95 < 阈值
  - [ ] P99 < 阈值

- [ ] 吞吐量正常
  ```bash
  # 使用压测工具
  ab -n 1000 -c 10 http://localhost:8000/api/endpoint
  ```

- [ ] 资源使用正常
  ```bash
  # CPU
  top -p $(pgrep -f xiaonuo)

  # 内存
  ps aux | grep xiaonuo

  # 磁盘I/O
  iostat -x 1 5
  ```

### 监控和告警验证

- [ ] 监控指标正常上报
  ```bash
  python3 -c "
  from core.optimization.xiaonuo_optimization_manager import get_optimization_manager
  manager = get_optimization_manager()
  summary = manager.get_monitoring_summary()
  print(summary)
  "
  ```

- [ ] 告警规则正常触发
  - [ ] 测试高失败率告警
  - [ ] 测试响应时间告警
  - [ ] 测试缓存命中率告警

- [ ] 日志正常输出
  ```bash
  tail -f /var/log/xiaonuo/optimization.log
  ```

- [ ] 健康检查接口正常
  ```bash
  curl http://localhost:8000/health
  # 预期: {"status": "healthy", ...}
  ```

---

## 🔍 持续监控检查 (Ongoing Monitoring)

### 每日检查

- [ ] 检查系统健康状态
  ```bash
  ./scripts/health_check.sh
  ```

- [ ] 检查错误日志
  ```bash
  grep -i error /var/log/xiaonuo/optimization.log | tail -20
  ```

- [ ] 检查关键指标
  - [ ] 优化成功率 > 95%
  - [ ] 响应时间 < 阈值
  - [ ] 缓存命中率 > 50%

- [ ] 检查告警
  ```bash
  python3 -c "
  from core.optimization.xiaonuo_optimization_manager import get_optimization_manager
  manager = get_optimization_manager()
  alerts = manager.check_alerts()
  for alert in alerts:
      print(alert)
  "
  ```

### 每周检查

- [ ] 生成监控报告
  ```bash
  python3 scripts/generate_monitoring_report.py
  ```

- [ ] 审查性能趋势
  - [ ] 响应时间趋势
  - [ ] 吞吐量趋势
  - [ ] 资源使用趋势

- [ ] 审查优化效果
  - [ ] 工具发现准确率
  - [ ] 错误预防率
  - [ ] 用户满意度

### 每月检查

- [ ] 全面性能审查
  - [ ] 运行压测
  - [ ] 分析瓶颈
  - [ ] 优化建议

- [ ] 配置审查
  - [ ] 调整缓存大小
  - [ ] 调整告警阈值
  - [ ] 优化参数

- [ ] 容量规划
  - [ ] 预测增长需求
  - [ ] 规划扩容
  - [ ] 预算申请

---

## 🚨 应急响应检查 (Emergency Response)

### 回滚准备

- [ ] 回滚步骤已文档化
- [ ] 回滚命令已验证
- [ ] 回滚时间 < 5分钟
  ```bash
  # 快速回滚
  cp config/optimization/xiaonuo_backup.yaml config/optimization/xiaonuo.yaml
  systemctl restart xiaonuo
  ```

### 应急联系人

- [ ] 技术负责人: _________________
- [ ] 运维负责人: _________________
- [ ] 业务负责人: _________________
- [ ] 值班电话: _________________

### 应急场景

- [ ] 系统不可用
  - [ ] 识别问题 < 5分钟
  - [ ] 决策回滚 < 10分钟
  - [ ] 执行回滚 < 15分钟

- [ ] 性能严重下降
  - [ ] 定位瓶颈
  - [ ] 临时优化
  - [ ] 根本解决

- [ ] 数据异常
  - [ ] 停止写入
  - [ ] 数据验证
  - [ ] 恢复备份

---

## 📊 部署报告 (Deployment Report)

### 基本信息

- **部署日期**: ___________
- **部署时间**: ___________
- **部署人员**: ___________
- **审核人员**: ___________
- **版本号**: ___________

### 部署统计

- **总检查项**: ___________
- **已完成**: ___________
- **未完成**: ___________
- **不适用**: ___________
- **完成率**: ___________%

### 问题记录

| 问题 | 严重程度 | 状态 | 解决方案 |
|------|---------|------|---------|
|      |         |      |         |
|      |         |      |         |

### 经验教训

1. **做得好的地方**:
   -
   -

2. **需要改进的地方**:
   -
   -

3. **下次部署建议**:
   -
   -

### 签字确认

- [ ] 部署人员签字: ___________ 日期: ___________
- [ ] 审核人员签字: ___________ 日期: ___________
- [ ] 运维确认签字: ___________ 日期: ___________

---

## 附录：快速命令参考

```bash
# 健康检查
curl http://localhost:8000/health

# 查看日志
tail -f /var/log/xiaonuo/optimization.log

# 重启服务
systemctl restart xiaonuo

# 查看状态
systemctl status xiaonuo

# 检查监控
python3 -c "
from core.optimization.xiaonuo_optimization_manager import get_optimization_manager
manager = get_optimization_manager()
print(manager.get_health_status())
"

# 快速回滚
cp config/optimization/xiaonuo_backup.yaml config/optimization/xiaonuo.yaml
systemctl restart xiaonuo
```

---

**文档版本**: v1.0.0
**最后更新**: 2025-12-27
**维护团队**: Athena平台团队
