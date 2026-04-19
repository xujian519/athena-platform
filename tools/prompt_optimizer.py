#!/usr/bin/env python3
"""
Claude Code 提示词优化器
自动优化用户输入，提升模型回复质量

作者: 小诺·双鱼公主
版本: v1.0.0
"""

from pathlib import Path


class ClaudeCodePromptOptimizer:
    """Claude Code 提示词优化器"""

    def __init__(self):
        self.project_context = self._load_project_context()
        self.templates = self._load_templates()

    def _load_project_context(self) -> str:
        """加载项目上下文"""
        context_file = Path("/Users/xujian/Athena工作平台/.claude-project-context.md")
        if context_file.exists():
            return context_file.read_text()
        return self._get_default_project_context()

    def _get_default_project_context(self) -> str:
        """获取默认项目上下文"""
        return """
## 项目上下文

项目名称: Athena工作平台
项目类型: 专利法律AI平台
当前阶段: Gateway架构转型 (Phase 0 准备阶段)
技术栈: Python 3.11+, PostgreSQL, Neo4j, Qdrant, Docker
核心目标: 构建专业的专利法律AI智能体平台

## 核心模块
- 存储层: PostgreSQL + Qdrant + Neo4j (三级缓存)
- 智能体系统: 小娜(法律专家)、小诺(调度官)、云熙(IP管理)
- 备份系统: 实时+每日+异地三层备份
- 知识图谱: 法律知识图谱引擎

## 当前进度
- ✅ Phase 0: 准备阶段 (备份系统已部署)
- 🔄 Phase 1: Gateway并行运行 (即将开始)
- ⏳ Phase 2: 灰度切流 (计划中)
- ⏳ Phase 3: 稳定运行 (计划中)

## 技术债务
- core/ 目录 180+ 子模块需要精简
- 部分代码存在 Python 3.12 兼容性问题
- 测试覆盖率需要提升

## 团队偏好
- 代码风格: PEP 8 + 中文注释
- 架构原则: 简单优于复杂
- 安全优先: 本地优先，隐私保护
- 质量标准: 核心功能必须有测试
"""

    def _load_templates(self) -> dict[str, str]:
        """加载提示词模板"""
        return {
            "code_analysis": """
## 代码分析要求

请按照以下结构进行分析：

### 1. 代码概述
- 功能: [这段代码的功能]
- 关键逻辑: [核心逻辑说明]
- 依赖关系: [依赖的模块/库]

### 2. 代码质量评估
- 优点: [代码的优点]
- 问题: [潜在的问题]
- 改进建议: [具体的改进建议]

### 3. 技术细节
- 时间复杂度: [复杂度分析]
- 空间复杂度: [内存使用]
- 并发安全性: [是否线程安全]

### 4. 优化建议
- 性能优化: [性能提升方案]
- 可读性优化: [代码改进方案]
- 测试建议: [需要测试的场景]

请提供具体的、可执行的建议。
""",

            "architecture_design": """
## 架构设计分析

请以资深架构师的视角进行设计：

### 1. 需求理解
- 业务目标: [要解决的业务问题]
- 技术约束: [技术限制条件]
- 非功能性需求: [性能、安全、可扩展性等]

### 2. 方案对比
分析至少 2 种技术方案：

#### 方案 A
- 描述: [方案描述]
- 优势: [3-5个优势]
- 劣势: [3-5个劣势]
- 适用场景: [适用条件]

#### 方案 B
- 描述: [方案描述]
- 优势: [3-5个优势]
- 劣势: [3-5个劣势]
- 适用场景: [适用条件]

### 3. 推荐方案
基于以下维度给出推荐：
- 技术可行性: [评估]
- 实施成本: [评估]
- 风险评估: [评估]
- 长期价值: [评估]

### 4. 实施路线图
- Phase 1 (1-2周): [短期任务]
- Phase 2 (1个月): [中期任务]
- Phase 3 (3个月): [长期任务]

### 5. 风险与缓解
- 风险点: [识别的风险]
- 缓解措施: [具体缓解方案]
- 应急预案: [回滚计划]

请确保方案考虑了Athena工作平台的现有架构。
""",

            "bug_diagnosis": """
## Bug 诊断分析

### 问题定位
1. **现象描述**: [具体的bug表现]
2. **复现步骤**: [如何复现]
3. **影响范围**: [影响哪些功能/用户]

### 根因分析
让我们逐步思考：
1. 可能的直接原因是什么？
2. 深层的根本原因是什么？
3. 是否有类似的历史问题？

### 解决方案
提供至少 2 种解决方案：

#### 方案 1: 快速修复
- 实施难度: [低/中/高]
- 实施时间: [估算]
- 副作用: [潜在影响]

#### 方案 2: 根本解决
- 实施难度: [低/中/高]
- 实施时间: [估算]
- 长期收益: [说明]

### 测试验证
- 单元测试: [需要测试的场景]
- 集成测试: [需要测试的场景]
- 回归测试: [需要验证的功能]

### 预防措施
- 代码审查: [需要关注的检查点]
- 自动化检测: [可以添加的检测]
- 文档更新: [需要更新的文档]

请提供具体的、可执行的代码修复方案。
""",

            "refactoring": """
## 代码重构建议

### 当前代码分析
- 文件: {file_path}
- 功能: [功能描述]
- 代码行数: [行数]
- 复杂度: [当前复杂度]

### 识别的问题
- [问题1]: [具体描述]
- [问题2]: [具体描述]
- [问题3]: [具体描述]

### 重构目标
- 提高可读性: [具体目标]
- 提升可维护性: [具体目标]
- 优化性能: [具体目标]
- 增强测试性: [具体目标]

### 重构方案

#### 方案 1: 渐进式重构
- 步骤: [分步骤说明]
- 风险: [风险评估]
- 时间: [时间估算]

#### 方案 2: 完全重写
- 理由: [重写原因]
- 优势: [预期改进]
- 风险: [主要风险]

### 重构后的代码
请提供：
1. 完整的重构代码（带中文注释）
2. 改动说明（为什么这样改）
3. 迁移步骤（如何安全迁移）
4. 测试用例（需要测试什么）

### 代码审查检查点
- [ ] 代码可读性
- [ ] 命名规范性
- [ ] 注释完整性
- [ ] 错误处理
- [ ] 测试覆盖

请确保重构后的代码符合 PEP 8 规范，并包含详细的中文注释。
""",

            "security_review": """
## 安全性审查

### 审查范围
- 文件/模块: [审查对象]
- 审查类型: [代码审查/架构审查/部署审查]

### 安全检查清单

#### 1. 输入验证
- [ ] 参数验证
- [ ] 类型检查
- [ ] 边界条件
- [ ] 异常输入处理

#### 2. 输出编码
- [ ] SQL 注入防护
- [ ] XSS 防护
- [ ] 路径遍历防护
- [ ] 敏感信息过滤

#### 3. 认证授权
- [ ] 身份验证
- [ ] 权限检查
- [ ] 会话管理
- [ ] Token 验证

#### 4. 数据保护
- [ ] 加密存储
- [ ] 传输加密
- [ ] 日志脱敏
- [ ] 备份安全

#### 5. 依赖安全
- [ ] 第三方库版本
- [ ] 已知漏洞
- [ ] 许可证合规
- [ ] 供应链安全

### 风险评级
- 严重风险: [立即修复]
- 高风险: [尽快修复]
- 中风险: [计划修复]
- 低风险: [观察]

### 修复建议
对每个风险提供：
1. 风险描述
2. 影响分析
3. 修复方案
4. 预防措施

请以安全专家的视角进行严格审查，不回避任何潜在问题。
"""
        }

    def optimize(
        self,
        user_input: str,
        context_type: str | None = None
    ) -> str:
        """
        优化用户输入

        Args:
            user_input: 原始用户输入
            context: 额外上下文信息

        Returns:
            优化后的提示词
        """
        # 检测任务类型
        task_type = self._detect_task_type(user_input)

        # 选择模板
        template = self.templates.get(task_type, "")

        # 构建优化后的提示
        optimized = f"""{self.project_context}

{template}

## 当前任务
{user_input}

## 输出要求
请使用简体中文回答，代码使用英文编写并附带中文注释。
对于复杂问题，请使用思维链逐步分析。
"""

        return optimized

    def _detect_task_type(self, user_input: str) -> str:
        """检测任务类型"""
        user_input_lower = user_input.lower()

        # 关键词映射
        task_keywords = {
            "code_analysis": [
                "分析代码", "解释代码", "代码怎么工作",
                "这段代码", "函数是", "类是什么",
                "analyze code", "explain code", "how does"
            ],
            "architecture_design": [
                "架构设计", "系统设计", "技术选型",
                "设计方案", "架构优化", "技术方案",
                "architecture", "design", "technical"
            ],
            "bug_diagnosis": [
                "bug", "错误", "问题", "不工作",
                "修复", "解决", "调试",
                "error", "fix", "debug", "issue"
            ],
            "refactoring": [
                "重构", "优化代码", "改进",
                "代码质量", "代码改进",
                "refactor", "optimize", "improve"
            ],
            "security_review": [
                "安全", "漏洞", "注入",
                "权限", "认证", "防护",
                "security", "vulnerability", "auth"
            ]
        }

        # 匹配关键词
        for task_type, keywords in task_keywords.items():
            if any(keyword in user_input_lower for keyword in keywords):
                return task_type

        # 默认返回通用分析
        return "code_analysis"

    def get_quick_template(self, scenario: str) -> str:
        """获取快速模板"""
        quick_templates = {
            "review": "# 代码审查\n\n请审查以下代码，关注：\n1. 代码质量\n2. 潜在bug\n3. 性能问题\n4. 安全风险\n\n## 代码\n```\n{code}\n```",

            "explain": "# 代码解释\n\n请详细解释以下代码：\n\n## 代码\n```\n{code}\n```\n\n要求：\n- 逐行解释关键逻辑\n- 说明设计意图\n- 指出注意事项",

            "test": "# 测试用例设计\n\n为以下代码设计测试用例：\n\n## 代码\n```\n{code}\n```\n\n要求：\n- 正常场景测试\n- 边界条件测试\n- 异常情况测试\n- 提供pytest代码",

            "optimize": "# 性能优化\n\n分析并优化以下代码的性能：\n\n## 代码\n```\n{code}\n```\n\n要求：\n- 识别性能瓶颈\n- 提供优化方案\n- 给出优化前后对比"
        }

        return quick_templates.get(scenario, "")

    def format_context_info(self, file_path: str = None) -> str:
        """格式化上下文信息"""
        context_parts = ["## 当前工作环境"]

        if file_path:
            context_parts.append(f"""
### 当前文件
- 路径: {file_path}
- 请先阅读该文件，了解其功能和上下文
""")

        return "\n".join(context_parts)


# 快速使用示例
def quick_optimize(prompt: str, scenario: str = "") -> str:
    """快速优化提示词"""
    optimizer = ClaudeCodePromptOptimizer()

    if scenario:
        template = optimizer.get_quick_template(scenario)
        return f"{optimizer.project_context}\n\n{template}\n\n## 用户输入\n{prompt}"

    return optimizer.optimize(prompt)


# 命令行使用
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        user_input = " ".join(sys.argv[1:])
        optimizer = ClaudeCodePromptOptimizer()
        optimized = optimizer.optimize(user_input)
        print("=== 优化后的提示词 ===\n")
        print(optimized)
    else:
        print("用法: python prompt_optimizer.py '您的问题'")
        print("\n示例:")
        print("  python prompt_optimizer.py '分析这个存储层的设计'")
        print("  python prompt_optimizer.py '帮我修复这个bug'")
