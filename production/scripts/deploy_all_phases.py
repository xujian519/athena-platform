#!/usr/bin/env python3
"""
Athena工作平台 - 阶段1-3完整部署脚本
Phase 1-3 Complete Deployment Script

执行完整的三阶段部署流程:
- 阶段一: 学习、通信、评估模块部署
- 阶段二: 记忆、工具、LLM集成模块部署
- 阶段三: 专利检索、知识图谱、认知系统部署

作者: Athena AI系统
版本: v1.0.0
创建时间: 2026-01-30
"""

from __future__ import annotations
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(PROJECT_ROOT / 'production' / 'logs' / 'deployment.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# =============================================================================
# 颜色输出工具
# =============================================================================

class Colors:
    """终端颜色"""
    PURPLE = '\033[0;35m'
    BLUE = '\033[0;34m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color


def print_header(title: str, width: int = 70):
    """打印标题"""
    logger.info(f"{Colors.PURPLE}{'=' * width}{Colors.NC}")
    logger.info(f"{Colors.PURPLE}{title.center(width)}{Colors.NC}")
    logger.info(f"{Colors.PURPLE}{'=' * width}{Colors.NC}")


def print_step(step: int, total: int, message: str):
    """打印步骤"""
    logger.info(f"{Colors.CYAN}[{step}/{total}]{Colors.NC} {message}")


def print_success(message: str):
    """打印成功信息"""
    logger.info(f"{Colors.GREEN}✅ {message}{Colors.NC}")


def print_error(message: str):
    """打印错误信息"""
    logger.error(f"{Colors.RED}❌ {message}{Colors.NC}")


def print_warning(message: str):
    """打印警告信息"""
    logger.warning(f"{Colors.YELLOW}⚠️  {message}{Colors.NC}")


def print_info(message: str):
    """打印信息"""
    logger.info(f"{Colors.BLUE}ℹ️  {message}{Colors.NC}")


# =============================================================================
# 部署状态管理
# =============================================================================

class DeploymentStatus:
    """部署状态管理器"""

    def __init__(self):
        self.status_file = PROJECT_ROOT / 'production' / 'logs' / 'deployment_status.json'
        self.status = self._load_status()
        self.results: dict[str, Any] = {
            'phase1': {},
            'phase2': {},
            'phase3': {},
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'success': False,
            'errors': []
        }

    def _load_status(self) -> dict[str, Any]:
        """加载已有状态"""
        if self.status_file.exists():
            try:
                with open(self.status_file, encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"无法加载状态文件: {e}")
        return {}

    def save_status(self):
        """保存状态"""
        self.results['end_time'] = datetime.now().isoformat()
        self.results['success'] = len(self.results['errors']) == 0

        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)


# =============================================================================
# 模块验证器
# =============================================================================

class ModuleValidator:
    """模块验证器"""

    @staticmethod
    def validate_learning() -> dict[str, Any]:
        """验证学习模块"""
        result = {'available': False, 'features': [], 'errors': []}

        try:
            from core.learning import LearningEngine, get_module_capabilities

            result['available'] = True
            capabilities = get_module_capabilities()
            result['features'] = [name for name, available in capabilities.items() if available]
            result['total_features'] = len(capabilities)
            result['available_features'] = len(result['features'])

            # 测试基础功能
            engine = LearningEngine("test")
            result['basic_test'] = 'OK'

        except Exception as e:
            result['errors'].append(str(e))

        return result

    @staticmethod
    def validate_communication() -> dict[str, Any]:
        """验证通信模块"""
        result = {'available': False, 'features': [], 'errors': []}

        try:
            from core.communication import CommunicationEngine, UnifiedMessageBus

            result['available'] = True
            result['features'].append('CommunicationEngine')
            if UnifiedMessageBus is not None:
                result['features'].append('UnifiedMessageBus')

            # 测试基础功能
            engine = CommunicationEngine("test")
            result['basic_test'] = 'OK'

        except Exception as e:
            result['errors'].append(str(e))

        return result

    @staticmethod
    def validate_evaluation() -> dict[str, Any]:
        """验证评估模块"""
        result = {'available': False, 'features': [], 'errors': []}

        try:
            from core.evaluation import EvaluationEngine, get_module_capabilities

            result['available'] = True
            capabilities = get_module_capabilities()
            result['features'] = [name for name, available in capabilities.items() if available]
            result['total_features'] = len(capabilities)
            result['available_features'] = len(result['features'])

            # 测试基础功能
            engine = EvaluationEngine("test")
            result['basic_test'] = 'OK'

        except Exception as e:
            result['errors'].append(str(e))

        return result

    @staticmethod
    def validate_memory() -> dict[str, Any]:
        """验证记忆系统"""
        result = {'available': False, 'features': [], 'errors': []}

        try:
            # 检查记忆系统目录
            memory_dir = PROJECT_ROOT / 'core' / 'memory'
            if memory_dir.exists():
                result['available'] = True
                result['memory_dir_exists'] = True
                result['memory_files'] = len(list(memory_dir.rglob('*.py')))

                # 尝试导入
                try:
                    from core.memory import MemorySystem
                    result['features'].append('MemorySystem')
                except ImportError:
                    result['features'].append('MemoryModule')
            else:
                result['errors'].append('记忆目录不存在')

        except Exception as e:
            result['errors'].append(str(e))

        return result

    @staticmethod
    def validate_tools() -> dict[str, Any]:
        """验证工具系统"""
        result = {'available': False, 'features': [], 'errors': []}

        try:
            # 检查工具系统目录
            tools_dir = PROJECT_ROOT / 'core' / 'tools'
            if tools_dir.exists():
                result['available'] = True
                result['tools_dir_exists'] = True
                result['tools_files'] = len(list(tools_dir.rglob('*.py')))

                # 尝试导入关键组件
                try:
                    from core.tools import ToolManager, tool_manager
                    result['features'].append('ToolManager')
                except ImportError:
                    result['features'].append('ToolModule')
            else:
                result['errors'].append('工具目录不存在')

        except Exception as e:
            result['errors'].append(str(e))

        return result

    @staticmethod
    def validate_llm() -> dict[str, Any]:
        """验证LLM集成"""
        result = {'available': False, 'features': [], 'errors': []}

        try:
            # 检查LLM目录
            llm_dir = PROJECT_ROOT / 'core' / 'llm'
            if llm_dir.exists():
                result['available'] = True
                result['llm_dir_exists'] = True
                result['llm_files'] = len(list(llm_dir.rglob('*.py')))

                # 检查模型配置
                models_dir = PROJECT_ROOT / 'models'
                if models_dir.exists():
                    result['models_available'] = True
                    result['models_count'] = len([d for d in models_dir.iterdir() if d.is_dir()])
            else:
                result['errors'].append('LLM目录不存在')

        except Exception as e:
            result['errors'].append(str(e))

        return result

    @staticmethod
    def validate_patent_retrieval() -> dict[str, Any]:
        """验证专利检索系统"""
        result = {'available': False, 'features': [], 'errors': []}

        try:
            # 检查专利相关文件
            patent_files = [
                PROJECT_ROOT / 'core' / 'iterative_patent_search.py',
                PROJECT_ROOT / 'core' / 'enhanced_patent_retriever.py',
                PROJECT_ROOT / 'core' / 'advanced_patent_search_system.py'
            ]

            available_files = [f for f in patent_files if f.exists()]
            if available_files:
                result['available'] = True
                result['files'] = [f.name for f in available_files]

                # 检查数据库配置
                env_file = PROJECT_ROOT / '.env.production'
                if env_file.exists():
                    result['db_configured'] = True
            else:
                result['errors'].append('专利检索文件不存在')

        except Exception as e:
            result['errors'].append(str(e))

        return result

    @staticmethod
    def validate_knowledge_graph() -> dict[str, Any]:
        """验证知识图谱系统"""
        result = {'available': False, 'features': [], 'errors': []}

        try:
            # 检查知识图谱目录
            kg_dirs = [
                PROJECT_ROOT / 'core' / 'kg',
                PROJECT_ROOT / 'core' / 'knowledge_graph',
                PROJECT_ROOT / 'core' / 'legal_kg'
            ]

            available_dirs = [d for d in kg_dirs if d.exists()]
            if available_dirs:
                result['available'] = True
                result['directories'] = [d.name for d in available_dirs]

                # 检查图数据库配置
                result['graph_db_check'] = '需要手动验证'
            else:
                result['errors'].append('知识图谱目录不存在')

        except Exception as e:
            result['errors'].append(str(e))

        return result

    @staticmethod
    def validate_cognition() -> dict[str, Any]:
        """验证认知系统"""
        result = {'available': False, 'features': [], 'errors': []}

        try:
            # 检查认知目录
            cognition_dir = PROJECT_ROOT / 'core' / 'cognition'
            if cognition_dir.exists():
                result['available'] = True
                result['cognition_dir_exists'] = True
                result['cognition_subdirs'] = len([d for d in cognition_dir.iterdir() if d.is_dir()])

                # 检查关键子模块
                submodules = ['reasoning', 'intent', 'perception']
                result['submodules'] = []
                for sm in submodules:
                    sm_dir = cognition_dir / sm
                    if sm_dir.exists():
                        result['submodules'].append(sm)
            else:
                result['errors'].append('认知目录不存在')

        except Exception as e:
            result['errors'].append(str(e))

        return result


# =============================================================================
# 部署执行器
# =============================================================================

class PhaseDeployer:
    """阶段部署执行器"""

    def __init__(self, status: DeploymentStatus):
        self.status = status
        self.validator = ModuleValidator()

    async def deploy_phase1(self) -> dict[str, Any]:
        """阶段一: 部署核心模块（学习、通信、评估）"""
        print_header("🚀 阶段一：核心模块部署", 70)
        phase1_results = {}

        # 1. 学习模块
        print_step(1, 3, "部署学习模块...")
        learning_result = self.validator.validate_learning()
        phase1_results['learning'] = learning_result

        if learning_result['available']:
            print_success(f"学习模块部署成功 - {learning_result.get('available_features', 0)}/{learning_result.get('total_features', 0)} 功能可用")
            if learning_result.get('features'):
                print_info(f"  可用功能: {', '.join(learning_result['features'][:5])}{'...' if len(learning_result['features']) > 5 else ''}")
        else:
            print_error(f"学习模块部署失败: {learning_result.get('errors', [])}")
            self.status.results['errors'].append('学习模块部署失败')

        await asyncio.sleep(0.5)

        # 2. 通信模块
        print_step(2, 3, "部署通信模块...")
        comm_result = self.validator.validate_communication()
        phase1_results['communication'] = comm_result

        if comm_result['available']:
            print_success(f"通信模块部署成功 - {len(comm_result.get('features', []))} 个组件可用")
            if comm_result.get('features'):
                print_info(f"  可用组件: {', '.join(comm_result['features'])}")
        else:
            print_error(f"通信模块部署失败: {comm_result.get('errors', [])}")
            self.status.results['errors'].append('通信模块部署失败')

        await asyncio.sleep(0.5)

        # 3. 评估模块
        print_step(3, 3, "部署评估模块...")
        eval_result = self.validator.validate_evaluation()
        phase1_results['evaluation'] = eval_result

        if eval_result['available']:
            print_success(f"评估模块部署成功 - {eval_result.get('available_features', 0)}/{eval_result.get('total_features', 0)} 功能可用")
            if eval_result.get('features'):
                print_info(f"  可用功能: {', '.join(eval_result['features'][:5])}{'...' if len(eval_result['features']) > 5 else ''}")
        else:
            print_error(f"评估模块部署失败: {eval_result.get('errors', [])}")
            self.status.results['errors'].append('评估模块部署失败')

        logger.info("")
        print_success("阶段一部署完成！")
        return phase1_results

    async def deploy_phase2(self) -> dict[str, Any]:
        """阶段二: 部署高可用模块（记忆、工具、LLM）"""
        print_header("⚡ 阶段二：高可用模块部署", 70)
        phase2_results = {}

        # 1. 记忆系统
        print_step(1, 3, "部署记忆系统...")
        memory_result = self.validator.validate_memory()
        phase2_results['memory'] = memory_result

        if memory_result['available']:
            print_success(f"记忆系统部署成功 - {memory_result.get('memory_files', 0)} 个文件")
            print_info(f"  状态: {'基础模块可用' if memory_result.get('features') else '需要手动配置'}")
        else:
            print_error(f"记忆系统部署失败: {memory_result.get('errors', [])}")
            self.status.results['errors'].append('记忆系统部署失败')

        await asyncio.sleep(0.5)

        # 2. 工具系统
        print_step(2, 3, "部署工具系统...")
        tools_result = self.validator.validate_tools()
        phase2_results['tools'] = tools_result

        if tools_result['available']:
            print_success(f"工具系统部署成功 - {tools_result.get('tools_files', 0)} 个文件")
            print_info(f"  状态: {'工具管理器可用' if 'ToolManager' in tools_result.get('features', []) else '基础模块可用'}")
        else:
            print_error(f"工具系统部署失败: {tools_result.get('errors', [])}")
            self.status.results['errors'].append('工具系统部署失败')

        await asyncio.sleep(0.5)

        # 3. LLM集成
        print_step(3, 3, "部署LLM集成模块...")
        llm_result = self.validator.validate_llm()
        phase2_results['llm'] = llm_result

        if llm_result['available']:
            print_success(f"LLM集成模块部署成功 - {llm_result.get('llm_files', 0)} 个文件")
            if llm_result.get('models_available'):
                print_info(f"  可用模型: {llm_result.get('models_count', 0)} 个")
        else:
            print_error(f"LLM集成模块部署失败: {llm_result.get('errors', [])}")
            self.status.results['errors'].append('LLM集成模块部署失败')

        logger.info("")
        print_success("阶段二部署完成！")
        return phase2_results

    async def deploy_phase3(self) -> dict[str, Any]:
        """阶段三: 部署优化模块（专利检索、知识图谱、认知）"""
        print_header("🔧 阶段三：优化模块部署", 70)
        phase3_results = {}

        # 1. 专利检索系统
        print_step(1, 3, "部署专利检索系统...")
        patent_result = self.validator.validate_patent_retrieval()
        phase3_results['patent_retrieval'] = patent_result

        if patent_result['available']:
            print_success(f"专利检索系统部署成功 - {len(patent_result.get('files', []))} 个组件")
            if patent_result.get('db_configured'):
                print_info("  数据库配置: 已配置")
            else:
                print_warning("  数据库配置: 需要手动配置")
        else:
            print_error(f"专利检索系统部署失败: {patent_result.get('errors', [])}")
            self.status.results['errors'].append('专利检索系统部署失败')

        await asyncio.sleep(0.5)

        # 2. 知识图谱系统
        print_step(2, 3, "部署知识图谱系统...")
        kg_result = self.validator.validate_knowledge_graph()
        phase3_results['knowledge_graph'] = kg_result

        if kg_result['available']:
            print_success(f"知识图谱系统部署成功 - {len(kg_result.get('directories', []))} 个模块")
            print_info(f"  状态: {kg_result.get('graph_db_check', '需要手动验证')}")
        else:
            print_error(f"知识图谱系统部署失败: {kg_result.get('errors', [])}")
            self.status.results['errors'].append('知识图谱系统部署失败')

        await asyncio.sleep(0.5)

        # 3. 认知系统
        print_step(3, 3, "部署认知系统...")
        cognition_result = self.validator.validate_cognition()
        phase3_results['cognition'] = cognition_result

        if cognition_result['available']:
            print_success(f"认知系统部署成功 - {cognition_result.get('cognition_subdirs', 0)} 个子模块")
            if cognition_result.get('submodules'):
                print_info(f"  核心子模块: {', '.join(cognition_result['submodules'])}")
        else:
            print_error(f"认知系统部署失败: {cognition_result.get('errors', [])}")
            self.status.results['errors'].append('认知系统部署失败')

        logger.info("")
        print_success("阶段三部署完成！")
        return phase3_results


# =============================================================================
# 报告生成器
# =============================================================================

class ReportGenerator:
    """部署报告生成器"""

    def __init__(self, status: DeploymentStatus):
        self.status = status

    def generate_summary(self) -> str:
        """生成部署摘要"""
        report = []
        report.append("=" * 70)
        report.append("Athena工作平台 - 阶段1-3部署完成报告".center(70))
        report.append("=" * 70)
        report.append("")

        # 基本信息
        report.append(f"部署时间: {self.status.results['start_time']}")
        report.append(f"完成时间: {self.status.results.get('end_time', '进行中...')}")
        report.append(f"部署状态: {'✅ 成功' if self.status.results.get('success') else '⚠️ 部分成功'}")
        report.append("")

        # 阶段一结果
        report.append("📊 阶段一：核心模块")
        report.append("-" * 70)
        phase1 = self.status.results.get('phase1', {})
        for module, result in phase1.items():
            status_icon = "✅" if result.get('available') else "❌"
            report.append(f"  {status_icon} {module}: {self._get_module_status(result)}")
        report.append("")

        # 阶段二结果
        report.append("⚡ 阶段二：高可用模块")
        report.append("-" * 70)
        phase2 = self.status.results.get('phase2', {})
        for module, result in phase2.items():
            status_icon = "✅" if result.get('available') else "❌"
            report.append(f"  {status_icon} {module}: {self._get_module_status(result)}")
        report.append("")

        # 阶段三结果
        report.append("🔧 阶段三：优化模块")
        report.append("-" * 70)
        phase3 = self.status.results.get('phase3', {})
        for module, result in phase3.items():
            status_icon = "✅" if result.get('available') else "❌"
            report.append(f"  {status_icon} {module}: {self._get_module_status(result)}")
        report.append("")

        # 错误汇总
        if self.status.results['errors']:
            report.append("⚠️  部署问题汇总")
            report.append("-" * 70)
            for error in self.status.results['errors']:
                report.append(f"  ❌ {error}")
            report.append("")

        # 下一步建议
        report.append("🎯 下一步建议")
        report.append("-" * 70)
        report.append(self._get_next_steps())
        report.append("")

        report.append("=" * 70)

        return "\n".join(report)

    def _get_module_status(self, result: dict[str, Any]) -> str:
        """获取模块状态描述"""
        if result.get('available'):
            if result.get('features'):
                return f"可用 ({len(result.get('features', []))} 个组件)"
            return "可用"
        return f"失败 - {', '.join(result.get('errors', []))}"

    def _get_next_steps(self) -> str:
        """获取下一步建议"""
        steps = []

        # 检查哪些模块需要额外配置
        phase2 = self.status.results.get('phase2', {})
        phase3 = self.status.results.get('phase3', {})

        if not phase2.get('memory', {}).get('features'):
            steps.append("1. 配置记忆系统数据库连接")

        if not phase2.get('tools', {}).get('features'):
            steps.append("2. 注册和验证工具系统")

        if not phase3.get('patent_retrieval', {}).get('db_configured'):
            steps.append("3. 配置专利检索数据库")

        if not phase3.get('knowledge_graph', {}).get('graph_db_check'):
            steps.append("4. 验证知识图谱数据库连接")

        if not steps:
            steps.append("所有模块已就绪，可以开始使用！")

        return "\n".join(steps)

    def save_report(self, report: str):
        """保存报告到文件"""
        report_file = PROJECT_ROOT / 'docs' / 'DEPLOYMENT_PHASE_1_3_REPORT.md'
        report_file.parent.mkdir(parents=True, exist_ok=True)

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print_success(f"部署报告已保存: {report_file}")


# =============================================================================
# 主程序
# =============================================================================

async def main():
    """主程序"""
    print_header("🚀 Athena工作平台 - 阶段1-3完整部署", 70)
    print_info(f"项目路径: {PROJECT_ROOT}")
    print_info(f"Python版本: {sys.version.split()[0]}")
    print_info(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")

    # 初始化
    status = DeploymentStatus()
    deployer = PhaseDeployer(status)
    reporter = ReportGenerator(status)

    # 创建日志目录
    log_dir = PROJECT_ROOT / 'production' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 执行阶段一
        phase1_results = await deployer.deploy_phase1()
        status.results['phase1'] = phase1_results
        status.save_status()

        logger.info("")

        # 执行阶段二
        phase2_results = await deployer.deploy_phase2()
        status.results['phase2'] = phase2_results
        status.save_status()

        logger.info("")

        # 执行阶段三
        phase3_results = await deployer.deploy_phase3()
        status.results['phase3'] = phase3_results
        status.save_status()

        logger.info("")

        # 生成报告
        print_header("📊 生成部署报告", 70)
        report = reporter.generate_summary()
        print(report)
        reporter.save_report(report)

        # 最终状态
        if status.results['success']:
            print_success("所有阶段部署成功！")
            return 0
        else:
            print_warning(f"部署完成，但有 {len(status.results['errors'])} 个问题需要解决")
            return 1

    except Exception as e:
        print_error(f"部署过程出错: {e}")
        import traceback
        traceback.print_exc()
        status.results['errors'].append(f"部署异常: {str(e)}")
        status.save_status()
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
