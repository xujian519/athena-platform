#!/usr/bin/env python3
"""
CLI人机交互专利分析系统
CLI-based Human-in-the-Loop Patent Analysis System

作者: Athena平台团队
创建时间: 2025-12-30
版本: 1.0.0

本系统演示在CLI环境中实现多种人机交互方式:
1. 简单输入确认 (input/confirm)
2. 菜单选择 (menu/picker)
3. 渐进式交互 (step-by-step)
4. 编辑器集成 (vim/vscode)
5. 延迟决策 (save for later)
"""

import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional



# ANSI颜色代码
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    END = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_header(text: str) -> Any:
    """打印标题"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text:^70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")


def print_success(text: str) -> Any:
    """打印成功消息"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_warning(text: str) -> Any:
    """打印警告消息"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")


def print_error(text: str) -> Any:
    """打印错误消息"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_info(text: str) -> Any:
    """打印信息"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")


def print_waiting(text: str) -> Any:
    """打印等待消息"""
    print(f"{Colors.CYAN}⏳ {text}{Colors.END}")


# ===============================
# 1. 基础交互方式
# ===============================


class BasicInteractive:
    """基础交互类 - 最简单的CLI交互"""

    @staticmethod
    def confirm(message: str, default: bool = False) -> bool:
        """
        简单确认交互

        Args:
            message: 提示消息
            default: 默认值

        Returns:
            用户选择 (True/False)
        """
        default_str = "Y/n" if default else "y/N"
        while True:
            response = input(f"{message} [{default_str}]: ").strip().lower()
            if not response:
                return default
            if response in ["y", "yes", "是", "ok", "好的"]:
                return True
            if response in ["n", "no", "否", "不", "cancel"]:
                return False
            print_warning("请输入 y 或 n")

    @staticmethod
    def select_option(message: str, options: list[str], default: int = 0) -> int:
        """
        菜单选择交互

        Args:
            message: 提示消息
            options: 选项列表
            default: 默认选中索引

        Returns:
            选中的索引
        """
        print(f"\n{message}")
        for i, option in enumerate(options):
            prefix = f"{Colors.GREEN}*{Colors.END}" if i == default else " "
            print(f"  {prefix} {i+1}. {option}")

        while True:
            try:
                response = input(f"\n请选择 [1-{len(options)},默认{default+1}]: ").strip()
                if not response:
                    return default
                index = int(response) - 1
                if 0 <= index < len(options):
                    return index
                print_error(f"请输入 1-{len(options)} 之间的数字")
            except ValueError:
                print_error("请输入有效的数字")

    @staticmethod
    def input_text(message: str, default: str = "", required: bool = False) -> str:
        """
        文本输入交互

        Args:
            message: 提示消息
            default: 默认值
            required: 是否必填

        Returns:
            用户输入的文本
        """
        prompt = f"{message} [默认: {default}]: " if default else f"{message}: "

        while True:
            response = input(prompt).strip()
            if response:
                return response
            if default:
                return default
            if not required:
                return ""
            print_warning("此项为必填,请输入")

    @staticmethod
    def input_multiline(message: str, end_marker: str = "END") -> str:
        """
        多行文本输入

        Args:
            message: 提示消息
            end_marker: 结束标记

        Returns:
            多行文本
        """
        print(f"\n{message}")
        print(f"输入内容,输入 '{end_marker}' 结束:\n")

        lines = []
        while True:
            line = input()
            if line.strip() == end_marker:
                break
            lines.append(line)

        return "\n".join(lines)


# ===============================
# 2. 复杂任务交互
# ===============================


class TaskInteractive:
    """复杂任务交互类"""

    def __init__(self):
        self.basic = BasicInteractive()

    def review_ai_result(self, task_id: str, ai_result: dict, confidence: float) -> dict[str, Any]:
        """
        审核AI结果

        Returns:
            人类决策
        """
        print_header(f"任务审核: {task_id}")

        # 显示AI结果
        print(f"\n{Colors.YELLOW}AI分析结果:{Colors.END}")
        print(json.dumps(ai_result, ensure_ascii=False, indent=2))

        # 显示置信度
        conf_color = (
            Colors.GREEN if confidence > 0.8 else Colors.YELLOW if confidence > 0.6 else Colors.RED
        )
        print(f"\n{conf_color}置信度: {confidence:.1%}{Colors.END}")

        if confidence < 0.7:
            print_warning("AI置信度较低,建议仔细审核")

        # 选择操作
        action = self.basic.select_option(
            "请选择操作:", ["接受AI结果", "修改后接受", "拒绝并重新分析", "跳过此任务"]
        )

        if action == 0:  # 接受
            return {
                "action": "accept",
                "result": ai_result,
                "confidence": 1.0,
                "comments": "接受AI分析结果",
            }

        elif action == 1:  # 修改
            modified_result = self._modify_result_interactive(ai_result)
            return {
                "action": "modify",
                "result": modified_result,
                "confidence": 0.9,
                "comments": "人类修改后的结果",
            }

        elif action == 2:  # 拒绝
            new_result = self._input_new_result(task_id)
            return {
                "action": "reject",
                "result": new_result,
                "confidence": 1.0,
                "comments": "重新分析的结果",
            }

        else:  # 跳过
            return {"action": "skip", "result": None, "confidence": 0.0, "comments": "跳过此任务"}

    def _modify_result_interactive(self, original_result: dict) -> dict:
        """交互式修改结果"""
        print_header("修改AI结果")

        print(f"\n{Colors.CYAN}原始结果:{Colors.END}")
        print(json.dumps(original_result, ensure_ascii=False, indent=2))

        print(f"\n{Colors.YELLOW}修改选项:{Colors.END}")
        print("1. 修改JSON格式")
        print("2. 添加备注")
        print("3. 返回")

        choice = self.basic.select_option("", ["修改JSON", "添加备注", "返回"], default=2)

        if choice == 0:  # 修改JSON
            print_waiting("\n请输入修改后的JSON (输入空行保存):")
            json_str = self.basic.input_multiline("JSON内容:", "END")
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                print_error(f"JSON格式错误: {e}")
                print_info("使用原始结果")
                return original_result

        elif choice == 1:  # 添加备注
            comment = self.basic.input_text("请输入备注")
            original_result["human_comment"] = comment
            return original_result

        else:  # 返回
            return original_result

    def _input_new_result(self, task_id: str) -> dict:
        """输入新的分析结果"""
        print_header("重新分析")

        print(f"\n{Colors.CYAN}任务: {task_id}{Colors.END}")
        print(f"{Colors.YELLOW}请提供您的分析结果{Colors.END}\n")

        result = {
            "analysis": self.basic.input_text("分析结论"),
            "reasoning": self.basic.input_text("推理过程"),
            "confidence": 1.0,
            "expert_signature": self.basic.input_text("专家签名/ID", required=False),
        }

        return result

    def make_decision(self, task_id: str, context: dict) -> dict[str, Any]:
        """
        人类决策

        Returns:
            决策结果
        """
        print_header(f"决策任务: {task_id}")

        # 显示上下文信息
        if context:
            print(f"\n{Colors.CYAN}上下文信息:{Colors.END}")
            for key, value in context.items():
                if isinstance(value, dict):
                    print(f"\n{key}:")
                    print(json.dumps(value, ensure_ascii=False, indent=2))
                else:
                    print(f"  {key}: {value}")

        # 选择决策选项
        decision = self.basic.select_option(
            "请做出决策:", ["专利权全部无效", "专利权部分无效", "维持专利权有效", "其他 (自定义)"]
        )

        decisions = ["专利权全部无效", "专利权部分无效", "维持专利权有效"]

        result = decisions[decision] if decision < 3 else self.basic.input_text("请输入自定义决策")

        # 输入理由
        reasoning = self.basic.input_multiline("请输入决策理由:", "END")

        return {
            "decision": result,
            "reasoning": reasoning,
            "confidence": 1.0,
            "expert_signature": self.basic.input_text("专家签名/ID"),
        }


# ===============================
# 3. 编辑器集成交互
# ===============================


class EditorInteractive:
    """编辑器集成交互类"""

    def __init__(self, editor: str | None = None):
        """
        Args:
            editor: 编辑器路径 (None则自动检测)
        """
        self.editor = editor or self._detect_editor()
        self.temp_dir = Path("/tmp/patent_analysis")
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def _detect_editor(self) -> str:
        """检测可用编辑器"""
        # 优先级: code > vim > nano > vi
        editors = ["code", "vim", "nano", "vi"]
        for editor in editors:
            try:
                subprocess.run(["which", editor], check=True, capture_output=True)
                return editor
            except subprocess.CalledProcessError:
                continue

        # 默认使用vi
        return "vi"

    def edit_result(self, task_id: str, ai_result: dict) -> dict:
        """
        使用编辑器修改AI结果

        Args:
            task_id: 任务ID
            ai_result: AI分析结果

        Returns:
            修改后的结果
        """
        print_header(f"编辑任务结果: {task_id}")

        # 保存到临时文件
        temp_file = self.temp_dir / f"{task_id}_{int(time.time())}.json"

        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(ai_result, f, ensure_ascii=False, indent=2)

        print(f"\n{Colors.CYAN}正在打开编辑器: {self.editor}{Colors.END}")
        print(f"{Colors.YELLOW}提示: 修改完成后保存并关闭编辑器{Colors.END}\n")

        # 打开编辑器
        try:
            subprocess.run([self.editor, str(temp_file)])
        except Exception as e:
            print_error(f"编辑器启动失败: {e}")
            return ai_result

        # 读取修改后的内容
        try:
            with open(temp_file, encoding="utf-8") as f:
                modified_result = json.load(f)

            print_success("修改已保存")
            return modified_result

        except json.JSONDecodeError as e:
            print_error(f"JSON格式错误: {e}")
            print_info("使用原始结果")
            return ai_result

    def edit_multiline_text(self, prompt: str, initial_text: str = "") -> str:
        """
        使用编辑器输入多行文本

        Args:
            prompt: 提示信息
            initial_text: 初始文本

        Returns:
            编辑后的文本
        """
        print(f"\n{Colors.CYAN}{prompt}{Colors.END}")

        # 保存到临时文件
        temp_file = self.temp_dir / f"edit_{int(time.time())}.md"

        with open(temp_file, "w", encoding="utf-8") as f:
            if initial_text:
                f.write(initial_text)
            else:
                f.write("# 请输入内容\n")
                f.write("# 输入完成后保存并退出\n\n")

        # 打开编辑器
        subprocess.run([self.editor, str(temp_file)])

        # 读取内容
        with open(temp_file, encoding="utf-8") as f:
            content = f.read()

        return content


# ===============================
# 4. 延迟决策交互
# ===============================


class DeferredDecision:
    """延迟决策类 - 保存任务稍后处理"""

    def __init__(self, save_dir: Path | None = None):
        self.save_dir = save_dir or Path("./pending_tasks")
        self.save_dir.mkdir(parents=True, exist_ok=True)

    def save_for_later(self, task_id: str, task_data: dict, reason: str = "") -> str:
        """
        保存任务到待处理队列

        Returns:
            保存的文件路径
        """
        pending_task = {
            "task_id": task_id,
            "saved_at": datetime.now().isoformat(),
            "reason": reason,
            "task_data": task_data,
        }

        filename = f"{task_id}_{int(time.time())}.json"
        filepath = self.save_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(pending_task, f, ensure_ascii=False, indent=2)

        print_success(f"任务已保存: {filepath}")
        print_info(f"稍后可使用: python cli_human_loop.py --resume {filename}")

        return str(filepath)

    def list_pending(self) -> list[dict]:
        """列出所有待处理任务"""
        pending_files = list(self.save_dir.glob("*.json"))

        if not pending_files:
            print_info("没有待处理任务")
            return []

        print(f"\n{Colors.BOLD}待处理任务列表:{Colors.END}\n")

        tasks = []
        for i, filepath in enumerate(pending_files):
            with open(filepath, encoding="utf-8") as f:
                task = json.load(f)

            print(f"{Colors.CYAN}{i+1}. {task['task_id']}{Colors.END}")
            print(f"   保存时间: {task['saved_at']}")
            if task.get("reason"):
                print(f"   延迟原因: {task['reason']}")
            print(f"   文件: {filepath.name}\n")

            tasks.append({"index": i, "task": task, "filepath": filepath})

        return tasks

    def resume_task(self, filepath: Path) -> dict:
        """恢复待处理任务"""
        with open(filepath, encoding="utf-8") as f:
            pending_task = json.load(f)

        print_header(f"恢复任务: {pending_task['task_id']}")

        if pending_task.get("reason"):
            print_info(f"延迟原因: {pending_task['reason']}")

        return pending_task["task_data"]

    def complete_task(self, filepath: Path, result: dict) -> Any:
        """完成任务并删除待处理记录"""
        # 保存结果
        result_dir = self.save_dir / "completed"
        result_dir.mkdir(exist_ok=True)

        result_file = result_dir / filepath.name
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(
                {"completed_at": datetime.now().isoformat(), "result": result},
                f,
                ensure_ascii=False,
                indent=2,
            )

        # 删除待处理记录
        filepath.unlink()

        print_success(f"任务完成,结果已保存: {result_file}")


# ===============================
# 5. 进度条与状态显示
# ===============================


class ProgressDisplay:
    """进度显示类"""

    @staticmethod
    def print_progress(current: int, total: int, prefix: str = "进度"):
        """打印进度条"""
        percent = current / total
        bar_length = 40
        filled = int(bar_length * percent)

        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"\r{prefix}: [{bar}] {current}/{total} ({percent:.1%})", end="", flush=True)

        if current == total:
            print()  # 完成后换行

    @staticmethod
    def print_spinner(message: str, duration: float = 2) -> Any:
        """显示旋转加载动画"""
        import itertools

        spinner = itertools.cycle(["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠇", "⠏"])

        start = time.time()
        while time.time() - start < duration:
            print(f"\r{message} {next(spinner)}", end="", flush=True)
            time.sleep(0.1)

        print(f"\r{message} ✓")


# ===============================
# 6. 完整的CLI人机交互系统
# ===============================


class CLIHumanInTheLoopSystem:
    """完整的CLI人机交互系统"""

    def __init__(self):
        self.basic = BasicInteractive()
        self.task_interactive = TaskInteractive()
        self.editor_interactive = EditorInteractive()
        self.deferred = DeferredDecision()
        self.progress = ProgressDisplay()

    def run_case_analysis(self, case_info: dict, case_type: str) -> Any:
        """运行完整的案例分析流程"""
        print_header("人机协作专利分析系统 (CLI版)")

        # 显示案例信息
        print(f"{Colors.BOLD}案例信息:{Colors.END}")
        print(f"  案例ID: {case_info.get('case_id', 'unknown')}")
        print(f"  案例类型: {case_type}")
        print(f"  技术领域: {case_info.get('technical_field', 'unknown')}")
        print()

        # 确认开始
        if not self.basic.confirm("开始分析?", default=True):
            print_info("已取消")
            return

        # 模拟任务执行流程
        self._simulate_workflow(case_info, case_type)

    def _simulate_workflow(self, case_info: dict, case_type: str) -> Any:
        """模拟工作流程"""
        # 定义任务序列
        tasks = self._get_tasks_for_case_type(case_type)

        total = len(tasks)
        results = []

        for i, task in enumerate(tasks):
            print(f"\n{Colors.BOLD}>>> 任务 {i+1}/{total}: {task['description']}{Colors.END}")

            # 显示进度
            self.progress.print_progress(i, total, "总体进度")

            # 根据任务类型选择交互方式
            result = self._execute_task_with_interaction(task, case_info)
            results.append(result)

        # 完成进度
        self.progress.print_progress(total, total, "总体进度")

        # 显示总结
        self._print_summary(results)

    def _execute_task_with_interaction(self, task: dict, context: dict) -> dict:
        """根据任务类型执行交互"""
        task_type = task["type"]

        if task_type == "AI_AUTOMATIC":
            # AI自动执行,简单确认
            print_waiting("AI自动执行中...")
            ai_result = self._simulate_ai_execution(task)
            print_success(f"完成 (置信度: {ai_result['confidence']:.1%})")

            if self.basic.confirm("接受AI结果?", default=True):
                return ai_result
            else:
                return self.task_interactive.review_ai_result(
                    task["task_id"], ai_result, ai_result["confidence"]
                )

        elif task_type == "AI_WITH_VALIDATION":
            # AI执行,根据置信度决定是否需要人类审核
            print_waiting("AI执行中...")
            ai_result = self._simulate_ai_execution(task)

            if ai_result["confidence"] >= 0.7:
                print_success(f"完成 (置信度: {ai_result['confidence']:.1%})")
                return ai_result
            else:
                print_warning(f"置信度较低 ({ai_result['confidence']:.1%}),需要审核")
                return self.task_interactive.review_ai_result(
                    task["task_id"], ai_result, ai_result["confidence"]
                )

        elif task_type == "HUMAN_DECISION":
            # 人类决策
            return self.task_interactive.make_decision(task["task_id"], context)

        else:
            # 默认: 提供多种选择
            return self._offer_interaction_options(task, context)

    def _offer_interaction_options(self, task: dict, context: dict) -> dict:
        """提供多种交互选项"""
        print(f"\n{Colors.YELLOW}任务类型: {task['type']}{Colors.END}")

        choice = self.basic.select_option(
            "选择交互方式:",
            ["使用编辑器详细分析", "快速输入结论", "延迟处理 (稍后决策)", "跳过此任务"],
        )

        if choice == 0:  # 编辑器
            ai_result = self._simulate_ai_execution(task)
            return self.editor_interactive.edit_result(task["task_id"], ai_result)

        elif choice == 1:  # 快速输入
            return self.task_interactive.make_decision(task["task_id"], context)

        elif choice == 2:  # 延迟处理
            self.deferred.save_for_later(
                task["task_id"], {"task": task, "context": context}, "用户选择延迟处理"
            )
            return {"action": "deferred", "result": None}

        else:  # 跳过
            return {"action": "skipped", "result": None}

    def _simulate_ai_execution(self, task: dict) -> dict:
        """模拟AI执行 (实际应用中调用DSPy模型)"""
        time.sleep(0.5)  # 模拟处理时间

        return {
            "result": f"AI对 {task['task_id']} 的分析结果",
            "confidence": 0.75 + random.random() * 0.2,  # 0.75-0.95
            "reasoning": "基于证据对比和法条分析...",
        }

    def _get_tasks_for_case_type(self, case_type: str) -> list[dict]:
        """获取案例类型的任务列表"""
        tasks = {
            "novelty": [
                {
                    "task_id": "extract_claims",
                    "type": "AI_AUTOMATIC",
                    "description": "提取涉案专利权利要求",
                },
                {
                    "task_id": "extract_evidence",
                    "type": "AI_AUTOMATIC",
                    "description": "提取对比文件证据",
                },
                {
                    "task_id": "claim_comparison",
                    "type": "AI_WITH_VALIDATION",
                    "description": "权利要求与证据逐条对比",
                },
                {
                    "task_id": "novelty_conclusion",
                    "type": "HUMAN_DECISION",
                    "description": "新颖性结论判断",
                },
            ],
            "creative": [
                {
                    "task_id": "extract_problem",
                    "type": "AI_WITH_VALIDATION",
                    "description": "提取发明要解决的技术问题",
                },
                {
                    "task_id": "identify_differences",
                    "type": "AI_WITH_VALIDATION",
                    "description": "识别与现有技术的区别特征",
                },
                {
                    "task_id": "obviousness_analysis",
                    "type": "HUMAN_DECISION",
                    "description": "显而易见性分析",
                },
                {
                    "task_id": "creative_conclusion",
                    "type": "HUMAN_DECISION",
                    "description": "创造性结论判断",
                },
            ],
        }

        return tasks.get(case_type, [])

    def _print_summary(self, results: list[dict]) -> Any:
        """打印总结"""
        print_header("分析完成")

        print(f"{Colors.BOLD}执行统计:{Colors.END}")
        print(f"  总任务数: {len(results)}")
        print(f"  AI执行: {sum(1 for r in results if not r.get('human_intervention'))}")
        print(f"  人类介入: {sum(1 for r in results if r.get('human_intervention'))}")

        print(f"\n{Colors.BOLD}任务结果:{Colors.END}")
        for i, result in enumerate(results, 1):
            status = (
                Colors.GREEN + "✓" + Colors.END
                if result.get("result")
                else Colors.RED + "✗" + Colors.END
            )
            print(f"  {status} 任务 {i}: {result.get('action', 'completed')}")

        # 保存结果
        self._save_results(results)

    def _save_results(self, results: list[dict]) -> Any:
        """保存分析结果"""
        output_dir = Path("./cli_analysis_results")
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = output_dir / f"analysis_{timestamp}.json"

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({"timestamp": timestamp, "results": results}, f, ensure_ascii=False, indent=2)

        print(f"\n{Colors.CYAN}结果已保存: {filepath}{Colors.END}")


# ===============================
# 7. 主程序
# ===============================


def main() -> None:
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="CLI人机协作专利分析系统")
    parser.add_argument(
        "--case-type",
        choices=["novelty", "creative", "disclosure", "clarity"],
        default="novelty",
        help="案例类型",
    )
    parser.add_argument(
        "--interactive", choices=["basic", "editor", "deferred"], default="basic", help="交互模式"
    )
    parser.add_argument("--resume", help="恢复待处理任务")

    args = parser.parse_args()

    # 恢复待处理任务
    if args.resume:
        deferred = DeferredDecision()
        filepath = Path(args.resume)
        if not filepath.exists():
            filepath = Path("./pending_tasks") / args.resume

        if filepath.exists():
            task_data = deferred.resume_task(filepath)
            print_info(f"已恢复任务: {task_data.get('task_id')}")
            return

    # 创建系统
    system = CLIHumanInTheLoopSystem()

    # 示例案例
    case_info = {
        "case_id": "CN202310000000.0",
        "background": "案由: 本专利涉及一种数据处理方法...",
        "technical_field": "人工智能",
        "patent_number": "CN202310000000.0",
    }

    # 运行分析
    system.run_case_analysis(case_info, args.case_type)


if __name__ == "__main__":

    main()
