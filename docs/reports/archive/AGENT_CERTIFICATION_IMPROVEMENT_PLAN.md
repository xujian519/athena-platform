# Agent认证机制改进规划

> **版本**: v1.0.0
> **创建时间**: 2026-04-21
> **状态**: Phase 3前期规划
> **预计完成**: 2周

---

## 目录

1. [现状分析](#现状分析)
2. [问题识别](#问题识别)
3. [改进方案](#改进方案)
4. [实施计划](#实施计划)
5. [风险评估](#风险评估)

---

## 现状分析

### 现有认证系统概览

**认证工具**: `tools/agent_certifier.py`

**认证标准** (总分100分):

| 维度 | 分数 | 权重 | 必需 |
|------|------|------|------|
| 接口合规性 | 30分 | 30% | ✅ |
| 测试覆盖率 | 25分 | 25% | ✅ |
| 代码质量 | 20分 | 20% | ✅ |
| 文档完整性 | 15分 | 15% | ❌ |
| 最佳实践 | 10分 | 10% | ❌ |

**认证等级**:

| 等级 | 状态 | 条件 |
|------|------|------|
| ✅ PASSED | 通过认证 | ≥80分且所有必需项通过 |
| ⚠️ WARNING | 警告 | ≥60分但存在非必需问题 |
| ❌ FAILED | 未通过 | <60分或必需项失败 |

### 已认证Agent

截至2026-04-21，已迁移Agent认证状态预估：

| Agent | 接口 | 测试 | 质量 | 文档 | 最佳实践 | 总分 | 状态 |
|-------|------|------|------|------|---------|------|------|
| RetrieverAgent | ✅ | ✅ | ✅ | ⚠️ | ✅ | ~92 | ✅ PASSED |
| AnalyzerAgent | ✅ | ✅ | ✅ | ⚠️ | ✅ | ~90 | ✅ PASSED |
| WriterAgent | ✅ | ✅ | ✅ | ⚠️ | ✅ | ~88 | ✅ PASSED |
| XiaonuoAgentV2 | ✅ | ✅ | ✅ | ⚠️ | ✅ | ~85 | ✅ PASSED |
| PatentSearchAgentV2 | ✅ | ⚠️ | ✅ | ⚠️ | ✅ | ~78 | ⚠️ WARNING |
| YunxiIPAgentV3 | ✅ | ⚠️ | ✅ | ⚠️ | ✅ | ~75 | ⚠️ WARNING |

### CI/CD集成现状

**现有工作流**: `.github/workflows/agent-certification.yml`

```yaml
触发条件:
  - 推送到 main/develop
  - PR 到 main/develop
  - 每周定时执行
  - 手动触发

测试任务:
  - 接口合规性检查
  - 测试覆盖率检查
  - 代码质量检查
```

---

## 问题识别

### 1. 认证标准问题

#### 1.1 缺少性能认证

**现状**: 认证标准中未包含性能相关检查

**影响**:
- 无法保证Agent的性能表现
- 性能退化可能被忽视
- 用户体验不一致

**建议**: 新增性能认证维度

| 检查项 | 分数 | 目标 |
|--------|------|------|
| 初始化性能 | 5分 | <100ms P95 |
| 执行性能 | 5分 | <5s P95 |
| 内存使用 | 5分 | <500MB/Agent |
| 吞吐量 | 5分 | >10 QPS |

#### 1.2 安全检查缺失

**现状**: 没有安全相关的检查项

**影响**:
- 可能存在安全漏洞
- 敏感信息泄露风险
- 输入验证不充分

**建议**: 新增安全认证维度

| 检查项 | 分数 | 说明 |
|--------|------|------|
| 输入验证 | 3分 | validate_input实现质量 |
| 错误处理 | 3分 | 异常处理覆盖 |
| 敏感信息 | 2分 | 无硬编码密钥 |
| 依赖安全 | 2分 | 无已知漏洞依赖 |

#### 1.3 认证分级不足

**现状**: 只有单一认证标准（100分制）

**影响**:
- 所有Agent按相同标准评估
- 无法体现Agent的复杂度差异
- 简单Agent和复杂Agent难度不对等

**建议**: 引入认证分级

| 级别 | 名称 | 要求 | 适用场景 |
|------|------|------|---------|
| Bronze | 青铜认证 | ≥60分，基础接口 | 实验性Agent |
| Silver | 白银认证 | ≥75分，基础+测试 | 内部使用Agent |
| Gold | 黄金认证 | ≥85分，全部检查 | 生产环境Agent |
| Platinum | 白金认证 | ≥95分，+性能+安全 | 核心关键Agent |

### 2. 自动化问题

#### 2.1 本地验证不够便利

**现状**: 需要手动运行命令行工具

**影响**:
- 开发者可能忘记验证
- PR前才发现问题
- 修复成本高

**建议**: 提供更便捷的验证方式

```bash
# 一键验证
make certify

# Git hook自动验证
pre-commit: certify-agent

# IDE集成
# VSCode任务运行认证
```

#### 2.2 CI/CD反馈不及时

**现状**: CI/CD运行时间较长，反馈延迟

**影响**:
- 开发流程被打断
- 等待时间过长

**建议**: 优化CI/CD流程

```yaml
# 增量检查
只检查变更的Agent

# 缓存机制
缓存依赖和测试结果

# 并行执行
多个Agent并行认证
```

### 3. 徽章系统问题

#### 3.1 徽章生成未实现

**现状**: 文档中提到徽章但未实现自动生成

**影响**:
- 无法直观展示认证状态
- 用户难以识别可信Agent

**建议**: 实现自动徽章系统

```svg
<!-- 认证徽章示例 -->
docs/badges/
├── agent-certification.svg      # 整体认证状态
├── retriever-agent-cert.svg     # 单个Agent认证
├── analyzer-agent-cert.svg
└── ...
```

#### 3.2 徽章类型单一

**现状**: 只有通过/失败两种状态

**建议**: 扩展徽章系统

| 徽章类型 | 说明 | 展示内容 |
|---------|------|---------|
| 整体认证 | 仓库整体状态 | 通过率、认证数 |
| 单个Agent | 每个Agent状态 | 等级、分数 |
| 性能认证 | 性能达标情况 | P95、吞吐量 |
| 安全认证 | 安全检查结果 | 无漏洞 |

---

## 改进方案

### 方案1: 扩展认证维度

#### 新增性能认证维度 (20分)

```python
# tools/agent_certifier.py 扩展

def _check_performance(self, agent_class: Type, result: CertificationResult):
    """检查性能指标"""
    score = 0
    max_score = 20

    # 1. 初始化性能 (5分)
    init_times = []
    for i in range(50):
        start = time.perf_counter()
        agent = agent_class(agent_id=f"perf_test_{i}")
        init_times.append((time.perf_counter() - start) * 1000)

    p95_init = sorted(init_times)[int(len(init_times) * 0.95)]
    if p95_init < 100:
        score += 5

    # 2. 内存使用 (5分)
    import psutil
    process = psutil.Process()
    baseline = process.memory_info().rss / 1024 / 1024
    agents = [agent_class(agent_id=f"mem_test_{i}") for i in range(10)]
    peak = process.memory_info().rss / 1024 / 1024
    avg_memory = (peak - baseline) / 10

    if avg_memory < 500:
        score += 5

    # 3. 能力发现性能 (5分)
    agent = agent_class(agent_id="cap_test")
    cap_times = []
    for _ in range(100):
        start = time.perf_counter()
        _ = agent.get_capabilities()
        cap_times.append((time.perf_counter() - start) * 1000)

    p95_cap = sorted(cap_times)[int(len(cap_times) * 0.95)]
    if p95_cap < 5:
        score += 5

    # 4. 吞吐量 (5分)
    start = time.perf_counter()
    for _ in range(100):
        _ = agent.get_capabilities()
    elapsed = time.perf_counter() - start
    throughput = 100 / elapsed

    if throughput >= 100:
        score += 5

    result.add_check("performance", score >= max_score * 0.6, score, max_score,
                     f"性能检查: {score}/{max_score}")
```

#### 新增安全认证维度 (10分)

```python
def _check_security(self, agent_class: Type, result: CertificationResult):
    """检查安全性"""
    score = 0
    max_score = 10
    issues = []

    # 1. 输入验证 (3分)
    source = inspect.getsource(agent_class)
    if "validate_input" in source and hasattr(agent_class, "validate_input"):
        # 检查验证逻辑
        validate_method = getattr(agent_class, "validate_input")
        if validate_method.__doc__:
            score += 3
    else:
        issues.append("缺少输入验证")

    # 2. 错误处理 (3分)
    try_count = source.count("try:")
    except_count = source.count("except")
    if try_count > 0 and except_count > 0:
        score += 3
    else:
        issues.append("缺少错误处理")

    # 3. 敏感信息 (2分)
    sensitive_patterns = [
        r"password\s*=\s*['\"][^'\"]+['\"]",
        r"api_key\s*=\s*['\"][^'\"]+['\"]",
        r"secret\s*=\s*['\"][^'\"]+['\"]",
        r"token\s*=\s*['\"][^'\"]+['\"]",
    ]
    import re
    for pattern in sensitive_patterns:
        if re.search(pattern, source, re.IGNORECASE):
            issues.append(f"可能包含硬编码敏感信息: {pattern}")
            break
    else:
        score += 2

    # 4. 依赖安全 (2分)
    # 检查requirements.txt/pyproject.toml中的已知漏洞
    # 这里可以集成safety或bandit工具
    score += 2  # 假设已通过依赖扫描

    result.add_check("security", score >= max_score * 0.6, score, max_score,
                     f"安全检查: {score}/{max_score}" + (f" - {', '.join(issues)}" if issues else ""))
```

### 方案2: 认证分级系统

#### 认证级别定义

```python
class CertificationLevel(Enum):
    """认证级别"""
    BRONZE = "bronze"       # 青铜认证 (60-74分)
    SILVER = "silver"       # 白银认证 (75-84分)
    GOLD = "gold"           # 黄金认证 (85-94分)
    PLATINUM = "platinum"   # 白金认证 (95-100分)

class CertificationTier:
    """认证层级标准"""
    LEVELS = {
        CertificationLevel.BRONZE: {
            "name": "青铜认证",
            "min_score": 60,
            "required_checks": ["interface_compliance"],
            "description": "基础接口合规，适合实验性Agent",
            "badge_color": "#CD7F32",  # 青铜色
        },
        CertificationLevel.SILVER: {
            "name": "白银认证",
            "min_score": 75,
            "required_checks": ["interface_compliance", "test_coverage"],
            "description": "基础+测试覆盖，适合内部使用Agent",
            "badge_color": "#C0C0C0",  # 银色
        },
        CertificationLevel.GOLD: {
            "name": "黄金认证",
            "min_score": 85,
            "required_checks": ["interface_compliance", "test_coverage", "code_quality"],
            "description": "全部检查通过，适合生产环境Agent",
            "badge_color": "#FFD700",  # 金色
        },
        CertificationLevel.PLATINUM: {
            "name": "白金认证",
            "min_score": 95,
            "required_checks": ["interface_compliance", "test_coverage", "code_quality", "performance", "security"],
            "description": "最高标准，核心关键Agent专用",
            "badge_color": "#E5E4E2",  # 铂色
        },
    }

    @classmethod
    def get_level(cls, score: float, passed_checks: List[str]) -> CertificationLevel:
        """根据分数和通过的检查项确定认证级别"""
        for level in reversed(list(cls.LEVELS.keys())):
            tier = cls.LEVELS[level]
            if score >= tier["min_score"]:
                required = set(tier["required_checks"])
                if required.issubset(set(passed_checks)):
                    return level
        return CertificationLevel.BRONZE
```

#### 级别徽章生成

```python
def generate_certification_badge(agent_name: str, level: CertificationLevel, score: float) -> str:
    """生成认证徽章SVG"""
    tier = CertificationTier.LEVELS[level]
    color = tier["badge_color"]

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="200" height="24">
      <linearGradient id="b" x2="0" y2="100%">
        <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
        <stop offset="1" stop-opacity=".1"/>
      </linearGradient>
      <mask id="a">
        <rect width="200" height="24" rx="3" fill="#fff"/>
      </mask>
      <g mask="url(#a)">
        <path fill="#555" d="M0 0h110v24H0z"/>
        <path fill="{color}" d="M110 0h90v24H110z"/>
        <path fill="url(#b)" d="M0 0h200v24H0z"/>
      </g>
      <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
        <text x="55" y="17" fill="#010101" fill-opacity=".3">{agent_name}</text>
        <text x="55" y="16">{agent_name}</text>
        <text x="155" y="17" fill="#010101" fill-opacity=".3">{tier["name"]} {score:.0f}分</text>
        <text x="155" y="16">{tier["name"]} {score:.0f}分</text>
      </g>
    </svg>'''
    return svg
```

### 方案3: 自动化增强

#### Git Hook集成

```python
# .git/hooks/pre-commit
#!/usr/bin/env python3
"""Pre-commit hook for Agent certification"""

import sys
import subprocess
from pathlib import Path

def get_changed_agents():
    """获取变更的Agent文件"""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True, text=True
    )
    changed_files = result.stdout.strip().split('\n')

    agents = []
    for f in changed_files:
        if f.startswith("core/agents/") and f.endswith(".py"):
            # 解析Agent类名
            file_path = Path(f)
            module_path = str(file_path.with_suffix('')).replace('/', '.')
            agents.append(module_path)

    return agents

def certify_agents(agents):
    """认证变更的Agent"""
    if not agents:
        print("✅ 没有Agent文件变更，跳过认证")
        return 0

    print(f"🔍 认证 {len(agents)} 个Agent...")

    failed = []
    for agent in agents:
        print(f"   检查 {agent}...")
        result = subprocess.run(
            ["python", "tools/agent_certifier.py", "--agent", agent],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            failed.append(agent)
            print(f"   ❌ {agent} 认证失败")
        else:
            print(f"   ✅ {agent} 认证通过")

    if failed:
        print("\n❌ 以下Agent认证失败:")
        for agent in failed:
            print(f"   - {agent}")
        print("\n请修复问题后再提交，或使用 --no-verify 跳过检查")
        return 1

    return 0

if __name__ == "__main__":
    agents = get_changed_agents()
    sys.exit(certify_agents(agents))
```

#### Makefile集成

```makefile
# Makefile

.PHONY: certify certify-all certify-report

# 认证单个Agent
certify:
	@echo "🔍 认证变更的Agent..."
	@git diff --cached --name-only | grep "core/agents/.*\.py" | \
		while read file; do \
			module=$$(echo $$file | sed 's|core/agents/||' | sed 's|\.py$$||' | sed 's|/|.|g'); \
			python tools/agent_certifier.py --agent "core.agents.$$module"; \
		done

# 认证所有Agent
certify-all:
	@echo "🔍 认证所有Agent..."
	python tools/agent_certifier.py --all --report certification_report.json

# 生成认证报告
certify-report:
	@echo "📊 生成认证报告..."
	python tools/agent_certifier.py --all --report reports/certification_$(shell date +%Y%m%d).json

# 快速验证（跳过性能测试）
certify-quick:
	@echo "⚡ 快速认证..."
	python tools/agent_certifier.py --all --skip-performance
```

### 方案4: CI/CD优化

#### 增量认证工作流

```yaml
# .github/workflows/agent-certification.yml (优化版)

name: Agent Certification

on:
  push:
    branches: [ main, develop ]
    paths:
      - 'core/agents/**'
      - 'tests/agents/**'
      - '.github/workflows/agent-certification.yml'
  pull_request:
    branches: [ main, develop ]
    paths:
      - 'core/agents/**'
      - 'tests/agents/**'
  workflow_dispatch:

jobs:
  # 检测变更的Agent
  detect-changes:
    name: 🔍 Detect Changes
    runs-on: ubuntu-latest
    outputs:
      changed_agents: ${{ steps.changes.outputs.agents }}
      has_changes: ${{ steps.changes.outputs.has_changes }}
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Detect changed agents
        id: changes
        run: |
          # 获取变更的Agent文件
          CHANGED=$(git diff --name-only ${{ github.event.before }} ${{ github.sha }} | \
                    grep "core/agents/.*agent.*\.py" || true)

          if [ -n "$CHANGED" ]; then
            echo "has_changes=true" >> $GITHUB_OUTPUT
            echo "agents=$CHANGED" >> $GITHUB_OUTPUT
            echo "🔍 检测到变更的Agent:"
            echo "$CHANGED" | while read file; do echo "  - $file"; done
          else
            echo "has_changes=false" >> $GITHUB_OUTPUT
            echo "✅ 没有Agent变更"
          fi

  # 并行认证
  certify:
    name: 🏆 Certify ${{ matrix.agent }}
    needs: detect-changes
    if: needs.detect-changes.outputs.has_changes == 'true'
    runs-on: ubuntu-latest
    strategy:
      matrix:
        agent: ${{ fromJson(needs.detect-changes.outputs.changed_agents) }}
      fail-fast: false
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -e .

      - name: Certify Agent
        run: |
          agent_path="${{ matrix.agent }}"
          # 转换文件路径到模块路径
          module=$(echo "$agent_path" | sed 's|core/agents/||' | sed 's|\.py$$||' | sed 's|/|.|g')
          python tools/agent_certifier.py --agent "core.agents.$module"

      - name: Upload result
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: certification-${{ matrix.agent }}
          path: certification_*.json

  # 生成汇总报告
  summary:
    name: 📊 Summary Report
    needs: [detect-changes, certify]
    if: always() && needs.detect-changes.outputs.has_changes == 'true'
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Download all results
        uses: actions/download-artifact@v4
        with:
          path: results/

      - name: Generate summary
        run: |
          python << 'EOF'
          import json
          from pathlib import Path

          results = []
          for file in Path("results").rglob("*.json"):
              with open(file) as f:
                  results.append(json.load(f))

          print("## 🏆 Agent认证报告")
          print("")
          print("| Agent | 状态 | 得分 |")
          print("|-------|------|------|")

          for r in results:
              status_emoji = "✅" if r["status"] == "passed" else "❌"
              print(f"| {r['agent_name']} | {status_emoji} | {r['percentage']}% |")
          EOF

      - name: Generate badges
        run: |
          python tools/generate_certification_badges.py

      - name: Commit badges
        run: |
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
          git add docs/badges/*.svg || true
          git commit -m "chore: 更新认证徽章 [skip ci]" || true
          git push || true
```

---

## 实施计划

### Phase 3.1: 认证标准扩展 (3天)

**目标**: 扩展认证维度，添加性能和安全检查

| 任务 | 负责人 | 时间 | 交付物 |
|------|--------|------|--------|
| 设计性能认证标准 | 架构师 | 0.5天 | 性能认证规范 |
| 实现`_check_performance`方法 | 开发者 | 1天 | 性能检查代码 |
| 设计安全认证标准 | 安全专家 | 0.5天 | 安全认证规范 |
| 实现`_check_security`方法 | 开发者 | 1天 | 安全检查代码 |

**验收标准**:
- [ ] 性能认证维度正常工作
- [ ] 安全认证维度正常工作
- [ ] 单元测试覆盖新增检查
- [ ] 文档更新

### Phase 3.2: 认证分级系统 (2天)

**目标**: 实现认证分级和徽章生成

| 任务 | 负责人 | 时间 | 交付物 |
|------|--------|------|--------|
| 实现认证级别类 | 开发者 | 0.5天 | CertificationTier |
| 实现徽章生成器 | 开发者 | 0.5天 | 徽章生成代码 |
| 创建徽章目录结构 | 开发者 | 0.5天 | docs/badges/ |
| 集成到认证工具 | 开发者 | 0.5天 | 更新agent_certifier.py |

**验收标准**:
- [ ] 四级认证系统正常工作
- [ ] 徽章自动生成
- [ ] 每个Agent有对应徽章

### Phase 3.3: 自动化增强 (2天)

**目标**: 增强本地验证和CI/CD集成

| 任务 | 负责人 | 时间 | 交付物 |
|------|--------|------|--------|
| 实现Git Hook | 开发者 | 0.5天 | pre-commit hook |
| 添加Makefile目标 | 开发者 | 0.5天 | Makefile更新 |
| 优化CI/CD工作流 | DevOps | 1天 | 优化后的workflow |

**验收标准**:
- [ ] Pre-commit hook正常工作
- [ ] `make certify`命令可用
- [ ] CI/CD增量认证

### Phase 3.4: 文档和培训 (1天)

**目标**: 更新文档并提供培训

| 任务 | 负责人 | 时间 | 交付物 |
|------|--------|------|--------|
| 更新认证指南 | 技术文档 | 0.5天 | 更新的指南 |
| 创建迁移指南 | 技术文档 | 0.5天 | 升级指南 |
| 团队培训 | 培训师 | 0.5天 | 培训材料 |
| 录制演示视频 | 培训师 | 0.5天 | 视频教程 |

**验收标准**:
- [ ] 文档完整更新
- [ ] 团队培训完成
- [ ] 演示视频可用

---

## 风险评估

### 技术风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| 性能测试不稳定 | 中 | 中 | 增加重试机制，设置合理阈值 |
| 安全检查误报 | 中 | 低 | 优化规则，提供豁免机制 |
| CI/CD执行时间过长 | 低 | 中 | 增量检查，并行执行 |

### 流程风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| 团队采用缓慢 | 中 | 中 | 提供培训，逐步推广 |
| 兼容性问题 | 低 | 高 | 向后兼容，逐步迁移 |

### 业务风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| 影响交付速度 | 中 | 中 | 分阶段实施，允许临时豁免 |
| 阻塞紧急修复 | 低 | 高 | 提供快速通道，允许手动跳过 |

---

## 附录

### A. 新认证标准矩阵

| 维度 | 分数 | 必需 | Bronze | Silver | Gold | Platinum |
|------|------|------|--------|--------|------|----------|
| 接口合规性 | 25分 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 测试覆盖率 | 20分 | ✅ | ⚠️ | ✅ | ✅ | ✅ |
| 代码质量 | 15分 | ✅ | ⚠️ | ⚠️ | ✅ | ✅ |
| 文档完整性 | 10分 | ❌ | ❌ | ⚠️ | ✅ | ✅ |
| 最佳实践 | 10分 | ❌ | ❌ | ⚠️ | ✅ | ✅ |
| 性能认证 | 20分 | ❌ | ❌ | ❌ | ⚠️ | ✅ |
| 安全认证 | 10分 | ❌ | ❌ | ❌ | ⚠️ | ✅ |
| **总分** | **110分** | - | **≥60** | **≥75** | **≥90** | **≥100** |

### B. 认证检查清单 (增强版)

- [ ] 继承BaseXiaonaComponent
- [ ] 实现所有必需方法
- [ ] 注册Agent能力
- [ ] 添加文档字符串
- [ ] 使用类型注解
- [ ] 编写测试用例 (≥10个)
- [ ] 添加错误处理
- [ ] 使用logger记录日志
- [ ] 编写Agent文档
- [ ] 初始化性能 <100ms
- [ ] 内存使用 <500MB
- [ ] 输入验证完整
- [ ] 无硬编码密钥
- [ ] 无已知漏洞依赖

### C. 相关文件清单

| 文件 | 状态 | 说明 |
|------|------|------|
| `tools/agent_certifier.py` | 现有 | 认证工具主程序 |
| `docs/guides/AGENT_CERTIFICATION_GUIDE.md` | 现有 | 认证指南 |
| `.github/workflows/agent-certification.yml` | 现有 | CI/CD工作流 |
| `docs/badges/agent-certification.svg` | 待创建 | 整体认证徽章 |
| `tools/generate_certification_badges.py` | 待创建 | 徽章生成工具 |
| `.git/hooks/pre-commit` | 待创建 | Pre-commit hook |
| `Makefile` | 待更新 | 添加certify目标 |

---

**维护者**: Infrastructure-Agent
**审核者**: Team-Lead
**版本历史**:
- v1.0.0 (2026-04-21): 初始版本
