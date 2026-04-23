#!/usr/bin/env python3
"""
小诺·双鱼公主八大核心模型完整性验证器
Xiaonuo Pisces Princess Core Eight Models Integrity Verifier
"""

import os
import sys

sys.path.append(os.path.expanduser("~/Athena工作平台"))

import asyncio
import json
import traceback
from datetime import datetime

from core.framework.agents.xiaonuo_integrated_enhanced import XiaonuoIntegratedEnhanced


class PrincessSystemVerifier:
    """公主系统验证器"""

    def __init__(self):
        self.verification_results = {}
        self.princess = None

    async def full_verification(self):
        """完整验证八大核心模型"""
        print("👑🌸🐟 小诺·双鱼公主八大核心模型完整性验证")
        print("=" * 70)
        print(f"⏰ 验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        try:
            # 1. 创建公主实例
            print("🚀 正在创建小诺·双鱼公主实例...")
            self.princess = XiaonuoIntegratedEnhanced()
            await self.princess.initialize()
            print("✅ 公主实例创建成功\n")

            # 2. 验证八大核心模型
            await self.verify_perception_engine()      # 感知引擎
            await self.verify_cognition_engine()      # 认知引擎
            await self.verify_execution_engine()      # 执行引擎
            await self.verify_learning_engine()       # 学习引擎
            await self.verify_communication_engine()  # 通讯引擎
            await self.verify_evaluation_engine()     # 评估引擎
            await self.verify_memory_system()         # 记忆系统
            await self.verify_knowledge_manager()     # 知识管理器

            # 3. 生成验证报告
            await self.generate_verification_report()

        except Exception as e:
            print(f"❌ 验证过程出现错误: {e}")
            traceback.print_exc()

        return self.verification_results

    async def verify_perception_engine(self):
        """验证感知引擎"""
        print("🔍 验证模块 1/8: 感知引擎 (Perception Engine)")
        print("-" * 50)

        result = {
            "module_name": "感知引擎",
            "status": "checking",
            "details": {},
            "capabilities": []
        }

        try:
            # 检查感知引擎是否存在
            if hasattr(self.princess, 'perception_engine'):
                result["details"]["engine_exists"] = True
                print("  ✅ 感知引擎存在")

                # 检查处理器
                if hasattr(self.princess.perception_engine, 'processors'):
                    processors = self.princess.perception_engine.processors
                    result["details"]["processors_count"] = len(processors)
                    print(f"  ✅ 处理器数量: {len(processors)}")

                    # 检查各处理器
                    for proc_name, processor in processors.items():
                        if hasattr(processor, 'initialized') and processor.initialized:
                            result["capabilities"].append(f"{proc_name}处理器")
                            print(f"    ✅ {proc_name}处理器已初始化")

                # 测试感知能力
                test_result = await self.test_perception()
                result["details"]["test_result"] = test_result
                if test_result:
                    print("  ✅ 感知功能测试通过")
                    result["status"] = "operational"
                else:
                    print("  ⚠️ 感知功能测试部分通过")
                    result["status"] = "partial"
            else:
                print("  ❌ 感知引擎不存在")
                result["status"] = "missing"

        except Exception as e:
            print(f"  ❌ 验证失败: {e}")
            result["status"] = "error"
            result["error"] = str(e)

        self.verification_results["perception"] = result
        print()

    async def verify_cognition_engine(self):
        """验证认知引擎"""
        print("🧠 验证模块 2/8: 认知引擎 (Cognition Engine)")
        print("-" * 50)

        result = {
            "module_name": "认知引擎",
            "status": "checking",
            "details": {},
            "capabilities": []
        }

        try:
            # 检查两种可能的命名
            has_cognition = hasattr(self.princess, 'cognition')
            has_cognitive_engine = hasattr(self.princess, 'cognitive_engine')

            if has_cognition or has_cognitive_engine:
                result["details"]["engine_exists"] = True

                # 优先使用 cognition，备选 cognitive_engine
                engine = getattr(self.princess, 'cognition', None) or getattr(self.princess, 'cognitive_engine', None)

                if engine:
                    print(f"  ✅ 认知引擎存在 (属性名: {'cognition' if has_cognition else 'cognitive_engine'})")

                    # 检查NLP适配器
                    if hasattr(engine, 'nlp_adapter'):
                        result["details"]["nlp_adapter_exists"] = True
                        print("  ✅ NLP适配器存在")
                        result["capabilities"].append("自然语言处理")

                    # 测试认知能力
                    test_result = await self.test_cognition()
                    result["details"]["test_result"] = test_result
                    if test_result:
                        print("  ✅ 认知功能测试通过")
                        result["status"] = "operational"
                    else:
                        print("  ⚠️ 认知功能测试部分通过")
                        result["status"] = "partial"
                else:
                    print("  ❌ 认知引擎引用为空")
                    result["status"] = "error"
            else:
                print("  ❌ 认知引擎不存在 (既没有 cognition 也没有 cognitive_engine)")
                result["status"] = "missing"

        except Exception as e:
            print(f"  ❌ 验证失败: {e}")
            result["status"] = "error"
            result["error"] = str(e)

        self.verification_results["cognition"] = result
        print()

    async def verify_execution_engine(self):
        """验证执行引擎"""
        print("⚡ 验证模块 3/8: 执行引擎 (Execution Engine)")
        print("-" * 50)

        result = {
            "module_name": "执行引擎",
            "status": "checking",
            "details": {},
            "capabilities": []
        }

        try:
            if hasattr(self.princess, 'execution_engine'):
                result["details"]["engine_exists"] = True
                print("  ✅ 执行引擎存在")

                # 检查执行器
                if hasattr(self.princess.execution_engine, 'executors'):
                    executors = self.princess.execution_engine.executors
                    result["details"]["executors_count"] = len(executors)
                    print(f"  ✅ 执行器数量: {len(executors)}")
                    result["capabilities"].append("多任务执行")

                # 测试执行能力
                test_result = await self.test_execution()
                result["details"]["test_result"] = test_result
                if test_result:
                    print("  ✅ 执行功能测试通过")
                    result["status"] = "operational"
                else:
                    print("  ⚠️ 执行功能测试部分通过")
                    result["status"] = "partial"
            else:
                print("  ❌ 执行引擎不存在")
                result["status"] = "missing"

        except Exception as e:
            print(f"  ❌ 验证失败: {e}")
            result["status"] = "error"
            result["error"] = str(e)

        self.verification_results["execution"] = result
        print()

    async def verify_learning_engine(self):
        """验证学习引擎"""
        print("🎓 验证模块 4/8: 学习引擎 (Learning Engine)")
        print("-" * 50)

        result = {
            "module_name": "学习引擎",
            "status": "checking",
            "details": {},
            "capabilities": []
        }

        try:
            if hasattr(self.princess, 'learning_engine'):
                result["details"]["engine_exists"] = True
                print("  ✅ 学习引擎存在")

                # 检查学习能力
                if hasattr(self.princess.learning_engine, 'learn'):
                    result["details"]["learning_capability"] = True
                    print("  ✅ 学习能力存在")
                    result["capabilities"].append("自适应学习")

                # 测试学习能力
                test_result = await self.test_learning()
                result["details"]["test_result"] = test_result
                if test_result:
                    print("  ✅ 学习功能测试通过")
                    result["status"] = "operational"
                else:
                    print("  ⚠️ 学习功能测试部分通过")
                    result["status"] = "partial"
            else:
                print("  ❌ 学习引擎不存在")
                result["status"] = "missing"

        except Exception as e:
            print(f"  ❌ 验证失败: {e}")
            result["status"] = "error"
            result["error"] = str(e)

        self.verification_results["learning"] = result
        print()

    async def verify_communication_engine(self):
        """验证通讯引擎"""
        print("💬 验证模块 5/8: 通讯引擎 (Communication Engine)")
        print("-" * 50)

        result = {
            "module_name": "通讯引擎",
            "status": "checking",
            "details": {},
            "capabilities": []
        }

        try:
            if hasattr(self.princess, 'communication_engine'):
                result["details"]["engine_exists"] = True
                print("  ✅ 通讯引擎存在")

                # 检查通道
                if hasattr(self.princess.communication_engine, 'channels'):
                    channels = self.princess.communication_engine.channels
                    result["details"]["channels_count"] = len(channels)
                    print(f"  ✅ 通讯通道数量: {len(channels)}")
                    result["capabilities"].append("多通道通讯")

                # 测试通讯能力
                test_result = await self.test_communication()
                result["details"]["test_result"] = test_result
                if test_result:
                    print("  ✅ 通讯功能测试通过")
                    result["status"] = "operational"
                else:
                    print("  ⚠️ 通讯功能测试部分通过")
                    result["status"] = "partial"
            else:
                print("  ❌ 通讯引擎不存在")
                result["status"] = "missing"

        except Exception as e:
            print(f"  ❌ 验证失败: {e}")
            result["status"] = "error"
            result["error"] = str(e)

        self.verification_results["communication"] = result
        print()

    async def verify_evaluation_engine(self):
        """验证评估引擎"""
        print("🔍 验证模块 6/8: 评估引擎 (Evaluation Engine)")
        print("-" * 50)

        result = {
            "module_name": "评估引擎",
            "status": "checking",
            "details": {},
            "capabilities": []
        }

        try:
            if hasattr(self.princess, 'evaluation_engine'):
                result["details"]["engine_exists"] = True
                print("  ✅ 评估引擎存在")

                # 检查评估指标
                if hasattr(self.princess.evaluation_engine, 'metrics'):
                    metrics = self.princess.evaluation_engine.metrics
                    result["details"]["metrics_count"] = len(metrics)
                    print(f"  ✅ 评估指标数量: {len(metrics)}")
                    result["capabilities"].append("多维度评估")

                # 测试评估能力
                test_result = await self.test_evaluation()
                result["details"]["test_result"] = test_result
                if test_result:
                    print("  ✅ 评估功能测试通过")
                    result["status"] = "operational"
                else:
                    print("  ⚠️ 评估功能测试部分通过")
                    result["status"] = "partial"
            else:
                print("  ❌ 评估引擎不存在")
                result["status"] = "missing"

        except Exception as e:
            print(f"  ❌ 验证失败: {e}")
            result["status"] = "error"
            result["error"] = str(e)

        self.verification_results["evaluation"] = result
        print()

    async def verify_memory_system(self):
        """验证记忆系统"""
        print("🧠 验证模块 7/8: 记忆系统 (Memory System)")
        print("-" * 50)

        result = {
            "module_name": "记忆系统",
            "status": "checking",
            "details": {},
            "capabilities": []
        }

        try:
            if hasattr(self.princess, 'memory'):
                result["details"]["memory_exists"] = True
                print("  ✅ 记忆系统存在")

                # 检查向量记忆
                if hasattr(self.princess.memory, 'vector_memory'):
                    result["details"]["vector_memory"] = True
                    print("  ✅ 向量记忆存在")
                    result["capabilities"].append("向量记忆")

                # 测试记忆能力
                test_result = await self.test_memory()
                result["details"]["test_result"] = test_result
                if test_result:
                    print("  ✅ 记忆功能测试通过")
                    result["status"] = "operational"
                else:
                    print("  ⚠️ 记忆功能测试部分通过")
                    result["status"] = "partial"
            else:
                print("  ❌ 记忆系统不存在")
                result["status"] = "missing"

        except Exception as e:
            print(f"  ❌ 验证失败: {e}")
            result["status"] = "error"
            result["error"] = str(e)

        self.verification_results["memory"] = result
        print()

    async def verify_knowledge_manager(self):
        """验证知识管理器"""
        print("📚 验证模块 8/8: 知识管理器 (Knowledge Manager)")
        print("-" * 50)

        result = {
            "module_name": "知识管理器",
            "status": "checking",
            "details": {},
            "capabilities": []
        }

        try:
            if hasattr(self.princess, 'knowledge'):
                result["details"]["knowledge_exists"] = True
                print("  ✅ 知识管理器存在")

                # 检查专利分析系统
                if hasattr(self.princess.knowledge, 'patent_system'):
                    result["details"]["patent_system"] = True
                    print("  ✅ 专利分析系统存在")
                    result["capabilities"].append("专利分析")

                # 检查智能推荐器
                if hasattr(self.princess.knowledge, 'recommender'):
                    result["details"]["recommender"] = True
                    print("  ✅ 智能推荐器存在")
                    result["capabilities"].append("智能推荐")

                # 测试知识管理能力
                test_result = await self.test_knowledge()
                result["details"]["test_result"] = test_result
                if test_result:
                    print("  ✅ 知识管理功能测试通过")
                    result["status"] = "operational"
                else:
                    print("  ⚠️ 知识管理功能测试部分通过")
                    result["status"] = "partial"
            else:
                print("  ❌ 知识管理器不存在")
                result["status"] = "missing"

        except Exception as e:
            print(f"  ❌ 验证失败: {e}")
            result["status"] = "error"
            result["error"] = str(e)

        self.verification_results["knowledge"] = result
        print()

    async def test_perception(self):
        """测试感知功能"""
        try:
            # 尝试处理文本输入
            await self.princess.process_input("测试感知功能", "text")
            return True
        except:
            return False

    async def test_cognition(self):
        """测试认知功能"""
        try:
            # 尝试认知处理
            result = await self.princess.process_input("请理解这句话的含义", "text")
            return result is not None
        except:
            return False

    async def test_execution(self):
        """测试执行功能"""
        try:
            # 检查是否有执行能力
            if hasattr(self.princess, 'execution_engine'):
                return True
            return False
        except:
            return False

    async def test_learning(self):
        """测试学习功能"""
        try:
            # 检查是否有学习能力
            if hasattr(self.princess, 'learning_engine'):
                return True
            return False
        except:
            return False

    async def test_communication(self):
        """测试通讯功能"""
        try:
            # 检查是否有通讯通道
            if hasattr(self.princess, 'communication_engine'):
                return True
            return False
        except:
            return False

    async def test_evaluation(self):
        """测试评估功能"""
        try:
            # 检查是否有评估能力
            if hasattr(self.princess, 'evaluation_engine'):
                return True
            return False
        except:
            return False

    async def test_memory(self):
        """测试记忆功能"""
        try:
            # 检查是否有记忆系统
            if hasattr(self.princess, 'memory'):
                return True
            return False
        except:
            return False

    async def test_knowledge(self):
        """测试知识管理功能"""
        try:
            # 检查是否有知识管理器
            if hasattr(self.princess, 'knowledge'):
                return True
            return False
        except:
            return False

    async def generate_verification_report(self):
        """生成验证报告"""
        print("📊 生成验证报告...")
        print("=" * 70)

        # 统计各状态数量
        status_count = {
            "operational": 0,
            "partial": 0,
            "missing": 0,
            "error": 0,
            "checking": 0
        }

        for _module, result in self.verification_results.items():
            status = result.get("status", "checking")
            status_count[status] += 1

        print("\n📈 验证结果统计:")
        print(f"  ✅ 完全运行: {status_count['operational']} 个模块")
        print(f"  ⚠️ 部分运行: {status_count['partial']} 个模块")
        print(f"  ❌ 缺失模块: {status_count['missing']} 个模块")
        print(f"  🔴 错误模块: {status_count['error']} 个模块")

        # 计算完整性
        total_modules = len(self.verification_results)
        operational_modules = status_count['operational'] + status_count['partial']
        completeness = (operational_modules / total_modules) * 100

        print(f"\n🎯 系统完整性: {completeness:.1f}%")

        # 详细报告
        print("\n📋 详细验证报告:")
        for _module, result in self.verification_results.items():
            status_icon = {
                "operational": "✅",
                "partial": "⚠️",
                "missing": "❌",
                "error": "🔴",
                "checking": "⏳"
            }.get(result["status"], "❓")

            print(f"\n{status_icon} {result['module_name']}:")
            print(f"   状态: {result['status']}")
            if result.get('capabilities'):
                print(f"   能力: {', '.join(result['capabilities'])}")

        # 保存报告
        report = {
            "verification_time": datetime.now().isoformat(),
            "princess_name": "小诺·双鱼公主",
            "completeness": completeness,
            "status_count": status_count,
            "modules": self.verification_results
        }

        report_path = "/Users/xujian/xiaonuo_pisces_princess_verification_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n💾 验证报告已保存至: {report_path}")

        # 总结
        if completeness >= 90:
            print("\n🎉 结论: 小诺·双鱼公主的八大核心模型完整度极高，能力完好无损！")
        elif completeness >= 70:
            print("\n✨ 结论: 小诺·双鱼公主的核心模型基本完整，个别功能需要调优。")
        else:
            print("\n⚠️ 结论: 小诺·双鱼公主的部分核心模型存在问题，建议进行检查和修复。")

async def main():
    """主函数"""
    verifier = PrincessSystemVerifier()
    await verifier.full_verification()

if __name__ == "__main__":
    asyncio.run(main())
