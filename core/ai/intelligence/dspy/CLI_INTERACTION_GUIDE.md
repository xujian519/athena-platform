# CLI人机交互实现指南
# CLI Human-in-the-Loop Implementation Guide

作者: Athena平台团队
创建时间: 2025-12-30
版本: 1.0.0

---

## 一、可行性分析

### ✅ CLI环境完全可以实现人机交互

```
Claude Code/CLI环境的人机交互能力:

┌─────────────────────────────────────────────────────────────┐
│  交互方式              │  适用场景              │  难度  │
├─────────────────────────────────────────────────────────────┤
│  1. input()确认         │ 简单是/否选择         │ ⭐    │
│  2. 菜单选择           │ 多选项决策             │ ⭐⭐  │
│  3. 多行输入           │ 复杂文本输入           │ ⭐⭐  │
│  4. 编辑器集成         │ 复杂内容编辑           │ ⭐⭐⭐│
│  5. 进度显示           │ 任务进度展示           │ ⭐    │
│  6. 延迟决策           │ 保存任务稍后处理       │ ⭐⭐  │
│  7. 分步确认           │ 逐步推进分析           │ ⭐⭐  │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、实现方式详解

### 方式1: 基础input()交互 (最简单)

```python
# 1. 确认交互
def confirm(message: str, default: bool = False) -> bool:
    while True:
        response = input(f"{message} [Y/n]: ").strip().lower()
        if response in ['y', 'yes', '是']:
            return True
        elif response in ['n', 'no', '否']:
            return False
        print("请输入 y 或 n")

# 使用
if confirm("接受AI分析结果?"):
    print("已接受")
else:
    print("已拒绝")
```

**优点**: 简单直接
**缺点**: 选项单一
**适用**: 简单确认场景

---

### 方式2: 菜单选择交互

```python
# 2. 菜单选择
def select_option(message: str, options: List[str]) -> int:
    print(f"\n{message}")
    for i, option in enumerate(options):
        print(f"  {i+1}. {option}")

    while True:
        try:
            response = input(f"\n请选择 [1-{len(options)}]: ")
            index = int(response) - 1
            if 0 <= index < len(options):
                return index
        except ValueError:
            print("请输入有效数字")

# 使用
decision = select_option("请做出决策:", [
    "专利权全部无效",
    "专利权部分无效",
    "维持专利权有效"
])
print(f"您的选择: {decision+1}")
```

**优点**: 清晰明了
**缺点**: 需要记住数字
**适用**: 多选项决策

---

### 方式3: 分步交互工作流

```python
# 3. 分步工作流
def step_by_step_analysis(case_info: dict):
    """分步执行分析"""

    print("=== 专利案例分析 ===\n")

    # 步骤1: 确认案例信息
    print("【步骤1/4】案例信息确认")
    print(f"案例ID: {case_info['case_id']}")
    print(f"技术领域: {case_info['technical_field']}")
    if not confirm("信息正确?", default=True):
        return

    # 步骤2: AI提取权利要求
    print("\n【步骤2/4】提取权利要求")
    ai_claims = ai_extract_claims(case_info)
    print(f"AI提取到 {len(ai_claims)} 项权利要求")

    if not confirm("接受提取结果?", default=True):
        # 允许修改
        ai_claims = manual_edit_claims(ai_claims)

    # 步骤3: 证据对比
    print("\n【步骤3/4】证据对比分析")
    comparison = ai_compare_claims(ai_claims)
    print_comparison_table(comparison)

    if not confirm("对比结果正确?", default=True):
        # 允许重新分析
        comparison = retry_comparison(case_info)

    # 步骤4: 最终结论
    print("\n【步骤4/4】生成最终结论")
    conclusion = select_option("请选择结论:", [
        "专利权全部无效",
        "专利权部分无效",
        "维持专利权有效"
    ])

    reasoning = input_multiline("请输入理由:\n")

    return {
        "conclusion": conclusion,
        "reasoning": reasoning
    }
```

**优点**: 流程清晰，可控
**缺点**: 步骤较多
**适用**: 复杂决策流程

---

### 方式4: 编辑器集成交互 (推荐用于复杂场景)

```python
# 4. 编辑器集成
def edit_with_editor(content: dict, filename: str) -> dict:
    """使用外部编辑器编辑内容"""

    import subprocess
    import tempfile

    # 保存到临时文件
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix=filename,
        delete=False
    ) as f:
        json.dump(content, f, indent=2)
        temp_path = f.name

    try:
        # 检测可用编辑器
        editor = os.environ.get('EDITOR', 'vim')

        print(f"正在打开编辑器: {editor}")
        subprocess.run([editor, temp_path])

        # 读取修改后的内容
        with open(temp_path, 'r') as f:
            return json.load(f)

    finally:
        # 清理临时文件
        os.unlink(temp_path)

# 使用
ai_result = {"analysis": "AI的分析结果..."}
print("原始AI结果:")
print(json.dumps(ai_result, indent=2))

modified = edit_with_editor(ai_result, "analysis.json")
print("\n修改后的结果:")
print(json.dumps(modified, indent=2))
```

**优点**: 编辑功能强大，可修改复杂内容
**缺点**: 需要离开CLI界面
**适用**: 复杂内容编辑

---

### 方式5: 延迟决策机制

```python
# 5. 延迟决策
class DeferredDecisionSystem:
    """延迟决策系统"""

    def __init__(self, save_dir: Path = Path("./pending_tasks")):
        self.save_dir = save_dir
        self.save_dir.mkdir(exist_ok=True)

    def save_for_later(self, task_id: str, data: dict):
        """保存任务到待处理队列"""
        timestamp = datetime.now().isoformat()
        filename = f"{task_id}_{timestamp}.json"
        filepath = self.save_dir / filename

        pending_task = {
            "task_id": task_id,
            "saved_at": timestamp,
            "data": data
        }

        with open(filepath, 'w') as f:
            json.dump(pending_task, f, indent=2)

        print(f"✓ 任务已保存: {filepath}")
        print(f"  稍后可使用: --resume {filename}")

    def list_pending(self):
        """列出所有待处理任务"""
        files = list(self.save_dir.glob("*.json"))

        if not files:
            print("没有待处理任务")
            return

        print("\n待处理任务:")
        for i, f in enumerate(files):
            with open(f) as fp:
                task = json.load(fp)
            print(f"  {i+1}. {task['task_id']} - {task['saved_at']}")

# 使用
if not confirm("现在做出决策?", default=True):
    deferred.save_for_later("task_123", task_data)
    print("任务已保存，可以稍后处理")
```

**优点**: 灵活安排时间
**缺点**: 需要额外管理机制
**适用**: 需要时间思考的复杂决策

---

### 方式6: 进度条和状态显示

```python
# 6. 进度显示
from tqdm import tqdm  # 需要安装: pip install tqdm

# 方法1: 使用tqdm库
for i in tqdm(range(100), desc="处理进度"):
    # 处理逻辑
    time.sleep(0.01)

# 方法2: 简单ASCII进度条
def print_progress(current: int, total: int):
    percent = current / total
    bar_length = 40
    filled = int(bar_length * percent)

    bar = '█' * filled + '░' * (bar_length - filled)
    print(f"\r进度: [{bar}] {current}/{total} ({percent:.1%})", end='')

    if current == total:
        print()

# 使用
for i in range(100):
    print_progress(i+1, 100)
    time.sleep(0.05)
```

**优点**: 直观显示进度
**缺点**: 需要额外库或代码
**适用**: 长时间处理任务

---

## 三、实际应用示例

### 示例1: 简单确认流程

```bash
# 运行CLI程序
$ python patent_analysis.py

=== 专利案例分析 ===

案例ID: CN202310000000.0
技术领域: 人工智能

[步骤1/4] AI提取权利要求...
✓ 提取到 5 项权利要求

接受AI结果? [Y/n]: y

[步骤2/4] 提取证据...
✓ 提取到 3 份证据

接受AI结果? [Y/n]: y

[步骤3/4] 证据对比分析...
AI置信度: 65%

1. 接受AI结果
2. 修改后接受
3. 拒绝并重新分析
4. 跳过

请选择 [1-4]: 2
⏳ 请输入修改内容...

[步骤4/4] 最终结论...

请做出决策:
  1. 专利权全部无效
  2. 专利权部分无效
  3. 维持专利权有效

请选择 [1-3]: 1
请输入理由 (输入END结束):
基于权利要求1与证据1完全相同，不具备新颖性...
END

✓ 分析完成!
```

---

### 示例2: 编辑器集成流程

```bash
# 运行编辑器集成模式
$ python patent_analysis.py --editor

AI分析结果已生成，正在打开编辑器...
vim /tmp/patent_analysis_123.json

# [在vim中编辑内容]
#
# {
#   "conclusion": "专利权全部无效",
#   "reasoning": "..."
# }

# [保存退出vim]

✓ 编辑完成
修改已保存: /results/analysis_123.json
```

---

### 示例3: 延迟决策流程

```bash
# 初始运行
$ python patent_analysis.py

[步骤3/4] 需要决策: 证据对比分析
AI置信度: 55%

1. 现在决策
2. 稍后处理

请选择 [1-2]: 2

✓ 任务已保存到: ./pending_tasks/task_3_20231230.json
  稍后可使用: python patent_analysis.py --resume task_3_20231230.json

# [稍后恢复处理]
$ python patent_analysis.py --resume task_3_20231230.json

恢复任务: task_3
延迟原因: 用户选择延迟处理

请做出决策:
  1. 专利权全部无效
  2. 专利权部分无效

请选择 [1-2]: 1

✓ 决策已记录
```

---

## 四、在Claude Code环境中的特殊实现

### 方法1: 使用Claude Code的文件编辑能力

```python
# 利用Claude Code的编辑能力
def claude_code_edit(content: str, filepath: str):
    """
    通过Claude Code编辑文件

    实现: 生成文件 → 用户用Claude Code编辑 → 读取修改
    """
    # 1. 生成初始文件
    Path(filepath).write_text(content)

    # 2. 提示用户编辑
    print(f"✓ 已生成文件: {filepath}")
    print(f"  请在Claude Code中编辑此文件")
    print(f"  编辑完成后，按回车继续...")

    input()  # 等待用户在Claude Code中编辑完成

    # 3. 读取修改后的内容
    modified = Path(filepath).read_text()

    return modified
```

---

### 方法2: 使用临时文件 + 系统编辑器

```python
def system_editor_edit(content: str) -> str:
    """使用系统编辑器编辑内容"""
    import tempfile
    import subprocess

    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.md',
        delete=False
    ) as f:
        f.write(content)
        temp_path = f.name

    # 检测可用编辑器 (优先VSCode)
    if shutil.which("code"):
        editor = "code --wait"
    elif shutil.which("vim"):
        editor = "vim"
    else:
        editor = os.environ.get("EDITOR", "vi")

    print(f"正在打开编辑器: {editor}")
    subprocess.run([editor, temp_path])

    # 读取修改结果
    modified = Path(temp_path).read_text()

    # 清理临时文件
    Path(temp_path).unlink()

    return modified
```

---

## 五、最佳实践建议

### ✅ 推荐做法

1. **简单场景**: 使用`input()` + 菜单选择
2. **复杂内容**: 使用编辑器集成
3. **需要时间思考**: 使用延迟决策机制
4. **长时间任务**: 显示进度条
5. **批量处理**: 提供保存/恢复功能

### ❌ 避免做法

1. 不要在一次交互中要求太多输入
2. 不要忘记提供默认值和示例
3. 不要在CLI中展示大量文本(建议用编辑器)
4. 不要忘记保存中间结果
5. 不要假设用户总是有空立即决策

---

## 六、实际代码示例

已创建的文件:
1. `/core/intelligence/dspy/cli_human_loop.py` - 完整的CLI交互系统
2. `/core/intelligence/dspy/human_in_the_loop_system.py` - 核心系统实现

关键类:
- `BasicInteractive`: 基础交互 (确认、选择、输入)
- `TaskInteractive`: 任务交互 (审核、决策)
- `EditorInteractive`: 编辑器集成
- `DeferredDecision`: 延迟决策
- `CLIHumanInTheLoopSystem`: 完整系统

---

## 七、使用方法

### 直接运行 (交互式)

```bash
cd /Users/xujian/Athena工作平台/core/intelligence/dspy

# 基础交互模式
python3 cli_human_loop.py --case-type novelty

# 编辑器集成模式
python3 cli_human_loop.py --case-type creative --interactive editor

# 恢复待处理任务
python3 cli_human_loop.py --resume task_file.json
```

### 集成到DSPy训练流程

```python
# 在DSPy评估阶段加入人机交互
from cli_human_loop import CLIHumanInTheLoopSystem

# 创建交互系统
hil_system = CLIHumanInTheLoopSystem()

# 评估时遇到低置信度样本
for example in testset:
    pred = model(example)
    score = metric(example, pred)

    if score < 0.7:
        # 低置信度，请求人类审核
        print(f"\n⚠️ 样本 {example.case_id} 置信度低: {score:.2%}")

        # 人类审核
        reviewed = hil_system.task_interactive.review_ai_result(
            task_id=example.case_id,
            ai_result=pred,
            confidence=score
        )

        # 使用审核后的结果
        pred = reviewed["result"]
```

---

## 八、总结

### ✅ CLI环境完全可以实现人机交互

| 交互方式 | 复杂度 | 适用场景 | Claude Code支持 |
|---------|-------|---------|----------------|
| input确认 | ⭐ | 简单是/否 | ✅ |
| 菜单选择 | ⭐⭐ | 多选项决策 | ✅ |
| 编辑器集成 | ⭐⭐⭐ | 复杂内容编辑 | ✅ (推荐) |
| 延迟决策 | ⭐⭐ | 需要时间思考 | ✅ |
| 进度显示 | ⭐ | 长时间任务 | ✅ |

### 推荐方案

**对于您的专利分析场景**:

1. **AI自动任务** (提取、分类): 直接执行，无需交互
2. **低置信度任务** (对比分析):
   - 简单场景: 菜单选择
   - 复杂场景: 编辑器集成
3. **最终决策** (结论判断):
   - 简单场景: 菜单选择
   - 复杂场景: 编辑器集成
4. **批量处理**: 保存待处理任务，稍后逐个处理

这样既保持了AI的效率优势，又发挥了人类在关键决策点的判断能力。
