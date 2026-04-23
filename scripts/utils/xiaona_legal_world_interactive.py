#!/usr/bin/env python3
"""
小娜·天秤女神 - 法律世界模型交互式系统
Xiaona Libra Goddess - Legal World Model Interactive System

提供交互式界面，让小娜基于法律世界模型处理专利业务

使用方式:
    python3 scripts/xiaona_legal_world_interactive.py

Author: Athena Team
Version: 1.0.0
Date: 2026-03-06
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.framework.agents.xiaona_with_legal_world import (
    LegalWorldIntegrationMode,
    XiaonaWithLegalWorld,
)


class XiaonaInteractiveSession:
    """小娜交互式会话"""

    def __init__(self):
        """初始化交互式会话"""
        self.agent: XiaonaWithLegalWorld | None = None
        self.session_active = False

    async def start(self):
        """启动交互式会话"""
        print("=" * 70)
        print("⚖️ 小娜·天秤女神 - 法律世界模型交互式系统")
        print("=" * 70)
        print()
        print("🔐 集成模式选择:")
        print("  1. 严格模式 (STRICT) - 必须使用法律世界模型")
        print("  2. 混合模式 (HYBRID) - 优先使用法律世界模型")
        print("  3. 回退模式 (FALLBACK) - 法律世界模型失败时回退")
        print()

        # 选择集成模式
        mode_choice = await self._get_user_choice(
            "请选择集成模式 (1-3)", ["1", "2", "3"], "2"
        )

        mode_map = {
            "1": LegalWorldIntegrationMode.STRICT,
            "2": LegalWorldIntegrationMode.HYBRID,
            "3": LegalWorldIntegrationMode.FALLBACK,
        }
        mode = mode_map[mode_choice]

        print()
        print("🔧 正在初始化小娜智能体...")

        try:
            # 创建智能体
            self.agent = XiaonaWithLegalWorld(integration_mode=mode)
            await self.agent.initialize()

            print("✅ 小娜智能体初始化完成")
            print()

            # 启动主循环
            self.session_active = True
            await self._main_loop()

        except Exception as e:
            print(f"❌ 初始化失败: {e}")
            import traceback

            traceback.print_exc()

    async def _main_loop(self):
        """主循环"""
        while self.session_active:
            print()
            print("-" * 70)
            print("📋 可用业务:")
            print("  1. 专利撰写 (基于法律世界模型)")
            print("  2. 审查意见答复 (基于法律世界模型)")
            print("  3. 无效宣告请求 (基于法律世界模型)")
            print("  4. 新颖性分析 (基于法律世界模型)")
            print("  5. 创造性分析 (基于法律世界模型)")
            print("  6. 查看统计信息")
            print("  0. 退出")
            print()

            choice = await self._get_user_choice("请选择业务类型 (0-6)", ["0", "1", "2", "3", "4", "5", "6"])

            if choice == "0":
                await self._exit()
            elif choice == "1":
                await self._handle_patent_drafting()
            elif choice == "2":
                await self._handle_office_action_response()
            elif choice == "3":
                await self._handle_invalidation_request()
            elif choice == "4":
                await self._handle_novelty_analysis()
            elif choice == "5":
                await self._handle_creativity_analysis()
            elif choice == "6":
                await self._show_statistics()

    async def _handle_patent_drafting(self):
        """处理专利撰写"""
        print()
        print("=" * 70)
        print("📝 专利撰写 (基于法律世界模型)")
        print("=" * 70)
        print()

        # 获取技术交底书路径
        disclosure_path = input("请输入技术交底书文件路径: ").strip()

        if not disclosure_path:
            # 使用默认路径
            disclosure_path = "/Users/xujian/Athena工作平台/data/reports/农业种植用起垄器_技术交底书.md"
            print(f"使用默认路径: {disclosure_path}")

        # 读取技术交底书
        try:
            with open(disclosure_path, encoding='utf-8') as f:
                tech_disclosure = f.read()
            print(f"✅ 已读取技术交底书 ({len(tech_disclosure)} 字)")
        except Exception as e:
            print(f"❌ 读取文件失败: {e}")
            return

        # 获取发明人信息（可选）
        print()
        inventor_info = {}
        add_inventor = await self._get_user_choice("是否添加发明人信息? (y/n)", ["y", "n", "Y", "N"], "n")

        if add_inventor.lower() == "y":
            name = input("发明人姓名: ").strip()
            if name:
                inventor_info["name"] = name
            id_card = input("身份证号: ").strip()
            if id_card:
                inventor_info["id_card"] = id_card
            address = input("地址: ").strip()
            if address:
                inventor_info["address"] = address

        print()
        print("🔄 正在基于法律世界模型撰写专利...")
        print("-" * 70)

        try:
            # 调用智能体
            result = await self.agent.process_patent_drafting_with_legal_world(
                tech_disclosure=tech_disclosure,
                inventor_info=inventor_info if inventor_info else None,
            )

            # 显示结果
            await self._display_result(result)

            # 保存结果
            if result.get("success"):
                await self._save_patent_specification(result)

        except Exception as e:
            print(f"❌ 处理失败: {e}")
            import traceback

            traceback.print_exc()

    async def _handle_office_action_response(self):
        """处理审查意见答复"""
        print()
        print("=" * 70)
        print("📋 审查意见答复 (基于法律世界模型)")
        print("=" * 70)
        print()

        # 获取审查意见
        oa_text = input("请输入审查意见文本 (或文件路径): ").strip()

        if oa_text.endswith('.txt') or oa_text.endswith('.md'):
            try:
                with open(oa_text, encoding='utf-8') as f:
                    oa_text = f.read()
                print(f"✅ 已读取审查意见 ({len(oa_text)} 字)")
            except Exception as e:
                print(f"❌ 读取文件失败: {e}")
                return

        # 获取申请号
        application_no = input("专利申请号: ").strip()

        # 获取权利要求书
        claims = input("权利要求书内容 (或文件路径): ").strip()

        if claims.endswith('.txt') or claims.endswith('.md'):
            try:
                with open(claims, encoding='utf-8') as f:
                    claims = f.read()
                print(f"✅ 已读取权利要求书 ({len(claims)} 字)")
            except Exception as e:
                print(f"❌ 读取文件失败: {e}")
                return

        print()
        print("🔄 正在基于法律世界模型答复审查意见...")
        print("-" * 70)

        try:
            result = await self.agent.process_office_action_response_with_legal_world(
                oa_text=oa_text,
                application_no=application_no,
                claims=claims,
            )

            await self._display_result(result)

        except Exception as e:
            print(f"❌ 处理失败: {e}")
            import traceback

            traceback.print_exc()

    async def _handle_invalidation_request(self):
        """处理无效宣告请求"""
        print()
        print("=" * 70)
        print("⚔️ 无效宣告请求 (基于法律世界模型)")
        print("=" * 70)
        print()

        # 获取专利号
        patent_no = input("目标专利号: ").strip()

        # 获取无效理由
        print("请输入无效理由 (每行一个，空行结束):")
        invalidity_grounds = []
        while True:
            ground = input(f"理由 {len(invalidity_grounds) + 1}: ").strip()
            if not ground:
                break
            invalidity_grounds.append(ground)

        if not invalidity_grounds:
            print("⚠️ 未提供无效理由")
            return

        print()
        print("🔄 正在基于法律世界模型生成无效宣告请求...")
        print("-" * 70)

        try:
            result = await self.agent.process_invalidation_with_legal_world(
                patent_no=patent_no,
                invalidity_grounds=invalidity_grounds,
            )

            await self._display_result(result)

        except Exception as e:
            print(f"❌ 处理失败: {e}")
            import traceback

            traceback.print_exc()

    async def _handle_novelty_analysis(self):
        """处理新颖性分析"""
        print()
        print("=" * 70)
        print("🔍 新颖性分析 (基于法律世界模型)")
        print("=" * 70)
        print()
        print("功能开发中...")
        # TODO: 实现新颖性分析

    async def _handle_creativity_analysis(self):
        """处理创造性分析"""
        print()
        print("=" * 70)
        print("💡 创造性分析 (基于法律世界模型)")
        print("=" * 70)
        print()
        print("功能开发中...")
        # TODO: 实现创造性分析

    async def _show_statistics(self):
        """显示统计信息"""
        print()
        print("=" * 70)
        print("📊 统计信息")
        print("=" * 70)
        print()

        stats = self.agent.get_statistics()

        print(f"总请求数: {stats.get('total_requests', 0)}")
        print(f"使用法律世界模型: {stats.get('legal_world_used', 0)}")
        print(f"回退到通用模式: {stats.get('fallback_to_generic', 0)}")
        print(f"验证失败: {stats.get('validation_failures', 0)}")
        print(f"法律世界模型使用率: {stats.get('legal_world_usage_rate', 0):.2%}")

    async def _display_result(self, result: dict):
        """显示处理结果"""
        print()
        print("=" * 70)
        print("✅ 处理完成")
        print("=" * 70)
        print()

        # 显示内容
        content = result.get("content", "")
        print(content)
        print()

        # 显示法律世界模型上下文
        if "legal_world_context" in result:
            print("-" * 70)
            print("📚 法律世界模型上下文")
            print("-" * 70)
            print()

            context = result["legal_world_context"]

            if "scenario" in context:
                scenario = context["scenario"]
                print(f"场景: {scenario.get('domain', '')}/{scenario.get('task_type', '')}/{scenario.get('phase', '')}")
                print(f"置信度: {scenario.get('confidence', 0):.2f}")
                print()

            if "legal_basis" in context and context["legal_basis"]:
                print("法律依据:")
                for basis in context["legal_basis"]:
                    print(f"  - {basis}")
                print()

            if "reference_cases" in context and context["reference_cases"]:
                print("参考案例:")
                for case in context["reference_cases"]:
                    print(f"  - {case.get('name', '未知')}: {case.get('relevance', '')}")
                print()

        # 显示可解释性说明
        if "explanation" in result:
            print("-" * 70)
            print("📖 可解释性说明")
            print("-" * 70)
            print()
            print(result["explanation"])

    async def _save_patent_specification(self, result: dict):
        """保存专利说明书"""
        save = await self._get_user_choice("是否保存专利说明书? (y/n)", ["y", "n", "Y", "N"], "y")

        if save.lower() != "y":
            return

        # 默认保存路径
        output_dir = Path("/Users/xujian/Athena工作平台/data/reports")
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = __import__("datetime").datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"专利说明书_法律世界模型版_{timestamp}.md"
        output_dir / default_filename

        # 获取用户输入的文件名
        filename = input(f"保存文件名 (默认: {default_filename}): ").strip()
        if not filename:
            filename = default_filename

        save_path = output_dir / filename

        # 保存文件
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(result.get("content", ""))

            print(f"✅ 文件已保存: {save_path}")
        except Exception as e:
            print(f"❌ 保存失败: {e}")

    async def _get_user_choice(
        self, prompt: str, valid_choices: list[str], default: str = ""
    ) -> str:
        """获取用户选择"""
        while True:
            try:
                if default:
                    full_prompt = f"{prompt} [默认: {default}]: "
                else:
                    full_prompt = f"{prompt}: "

                choice = input(full_prompt).strip()

                if not choice and default:
                    return default

                if choice in valid_choices:
                    return choice

                print(f"⚠️ 无效选择，请选择: {', '.join(valid_choices)}")

            except (EOFError, KeyboardInterrupt):
                print("\n⚠️ 用户中断")
                return default if default else valid_choices[0]

    async def _exit(self):
        """退出会话"""
        print()
        print("=" * 70)
        print("👋 感谢使用小娜·天秤女神法律世界模型系统")
        print("=" * 70)
        print()

        if self.agent:
            stats = self.agent.get_statistics()
            print("📊 会话统计:")
            print(f"  总请求数: {stats.get('total_requests', 0)}")
            print(f"  法律世界模型使用: {stats.get('legal_world_used', 0)}")
            print(f"  使用率: {stats.get('legal_world_usage_rate', 0):.2%}")

        self.session_active = False


async def main():
    """主函数"""
    session = XiaonaInteractiveSession()
    await session.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 用户中断，再见！")
        sys.exit(0)
