#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利知识图谱构建启动脚本
Patent Knowledge Graph Construction Startup Script

一键构建专利知识图谱的完整流程
One-click construction of patent knowledge graph with complete workflow

作者: Athena AI系统
创建时间: 2025年12月6日
版本: 1.0.0
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

# 导入本地模块
from knowledge_graph.patent_kg_application import PatentKnowledgeGraphApplication

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('patent_kg_build.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PatentKGBuilder:
    """专利知识图谱构建器"""

    def __init__(self):
        self.config = self._load_config()
        self.app = None
        self.start_time = datetime.now()

    def _load_config(self) -> dict:
        """加载配置"""
        config = {
            'extraction': {
                'batch_size': 1000,
                'confidence_threshold': 0.6,
                'max_file_size': 100 * 1024 * 1024,  # 100MB
                'timeout': 30,
                'max_files': 5000  # 限制文件数量以避免过长时间
            },
            'neo4j': {
                'uri': 'bolt://localhost:7687',
                'username': 'neo4j',
                'password': os.getenv('NEO4J_PASSWORD', 'password'),
                'database': 'patent_kg',
                'max_connection_pool_size': 50,
                'connection_timeout': 30
            },
            'web': {
                'host': '0.0.0.0',
                'port': 5000,
                'debug': False,
                'cors_origins': ['*'],
                'static_folder': 'static',
                'template_folder': 'templates'
            }
        }

        # 尝试加载外部配置文件
        config_file = project_root / 'config.json'
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    external_config = json.load(f)
                    # 深度合并配置
                    self._deep_merge(config, external_config)
                    logger.info(f"已加载外部配置文件: {config_file}")
            except Exception as e:
                logger.warning(f"加载配置文件失败: {e}")

        return config

    def _deep_merge(self, dict1: dict, dict2: dict):
        """深度合并字典"""
        for key, value in dict2.items():
            if key in dict1 and isinstance(dict1[key], dict) and isinstance(value, dict):
                self._deep_merge(dict1[key], value)
            else:
                dict1[key] = value

    def check_requirements(self) -> bool:
        """检查系统要求"""
        logger.info('检查系统要求...')

        requirements_met = True

        # 检查Python版本
        if sys.version_info < (3, 8):
            logger.error('Python版本过低，需要Python 3.8+')
            requirements_met = False

        # 检查必要的库
        required_packages = [
            ('neo4j', 'neo4j'),
            ('flask', 'flask'),
            ('pandas', 'pandas'),
            ('matplotlib', 'matplotlib'),
            ('seaborn', 'seaborn')
        ]

        for package_name, import_name in required_packages:
            try:
                __import__(import_name)
                logger.debug(f"✓ {package_name}")
            except ImportError:
                logger.error(f"✗ {package_name} 未安装，请使用: pip install {package_name}")
                requirements_met = False

        # 检查数据目录
        data_dir = Path('/Users/xujian/学习资料/专利')
        if not data_dir.exists():
            logger.error(f"数据目录不存在: {data_dir}")
            requirements_met = False
        else:
            file_count = len(list(data_dir.rglob('*.doc*')))
            logger.info(f"✓ 找到 {file_count} 个文档文件")

        return requirements_met

    def install_requirements(self):
        """安装必要的依赖"""
        logger.info('正在安装依赖包...')

        packages = [
            'neo4j',
            'flask',
            'flask-cors',
            'pandas',
            'matplotlib',
            'seaborn',
            'plotly',
            'python-docx',
            'PyPDF2',
            'jieba',
            'spacy',
            'wordcloud',
            'jinja2',
            'openpyxl'
        ]

        for package in packages:
            try:
                import importlib
                importlib.import_module(package)
                logger.info(f"✓ {package} 已安装")
            except ImportError:
                logger.info(f"安装 {package}...")
                os.system(f"pip install {package}")

        # 安装spaCy中文模型
        try:
            import spacy
            spacy.load('zh_core_web_sm')
            logger.info('✓ spaCy中文模型已安装')
        except (ImportError, OSError):
            logger.info('安装spaCy中文模型...')
            os.system('python -m spacy download zh_core_web_sm')

    def build_knowledge_graph(self, source_dir: str = None, output_dir: str = None) -> bool:
        """构建知识图谱"""
        logger.info('开始构建专利知识图谱...')

        # 使用默认路径
        if not source_dir:
            source_dir = '/Users/xujian/学习资料/专利'

        if not output_dir:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = f"/tmp/patent_kg_output_{timestamp}"

        # 创建输出目录
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        try:
            # 初始化应用
            logger.info('初始化应用组件...')
            self.app = PatentKnowledgeGraphApplication(self.config)

            # 初始化组件
            self.app.initialize_components()

            # 执行完整流程
            logger.info('执行完整构建流程...')
            self.app.create_complete_pipeline(source_dir, output_dir)

            # 生成构建报告
            self._generate_build_report(source_dir, output_dir)

            return True

        except Exception as e:
            logger.error(f"构建失败: {str(e)}")
            return False

    def _generate_build_report(self, source_dir: str, output_dir: str):
        """生成构建报告"""
        try:
            report = {
                'build_info': {
                    'timestamp': datetime.now().isoformat(),
                    'start_time': self.start_time.isoformat(),
                    'end_time': datetime.now().isoformat(),
                    'duration_seconds': (datetime.now() - self.start_time).total_seconds()
                },
                'config': self.config,
                'source_directory': source_dir,
                'output_directory': output_dir,
                'system_info': {
                    'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                    'platform': sys.platform,
                    'working_directory': os.getcwd()
                }
            }

            report_file = Path(output_dir) / 'build_report.json'
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)

            logger.info(f"构建报告已生成: {report_file}")

        except Exception as e:
            logger.warning(f"生成构建报告失败: {e}")

    def run_web_server(self):
        """运行Web服务器"""
        logger.info('启动Web服务器...')

        if not self.app:
            self.app = PatentKnowledgeGraphApplication(self.config)
            self.app.initialize_components()

        # 创建模板文件
        templates_dir = project_root / 'templates'
        self.app.create_templates_and_static_dir(str(templates_dir))

        try:
            self.app.run_web_server(
                host=self.config['web']['host'],
                port=self.config['web']['port'],
                debug=self.config['web']['debug']
            )
        except KeyboardInterrupt:
            logger.info('Web服务器已停止')

    def interactive_mode(self):
        """交互模式"""
        while True:
            logger.info(str("\n" + '='*50))
            logger.info('🏛️ 专利知识图谱构建系统')
            logger.info(str('='*50))
            logger.info('1. 检查系统要求')
            logger.info('2. 安装依赖包')
            logger.info('3. 构建知识图谱')
            logger.info('4. 启动Web服务器')
            logger.info('5. 查看构建统计')
            logger.info('0. 退出')
            logger.info(str('='*50))

            choice = input('请选择操作 (0-5): ').strip()

            if choice == '0':
                break
            elif choice == '1':
                if self.check_requirements():
                    logger.info('✅ 所有要求都满足')
                else:
                    logger.info('❌ 存在不满足的要求')
            elif choice == '2':
                self.install_requirements()
            elif choice == '3':
                source_dir = input('请输入源文档目录 (默认: /Users/xujian/学习资料/专利): ').strip()
                output_dir = input('请输入输出目录 (默认: 自动生成): ').strip()

                if not source_dir:
                    source_dir = '/Users/xujian/学习资料/专利'

                success = self.build_knowledge_graph(source_dir, output_dir)
                if success:
                    logger.info('✅ 知识图谱构建成功')
                else:
                    logger.info('❌ 知识图谱构建失败')
            elif choice == '4':
                self.run_web_server()
            elif choice == '5':
                self.show_build_stats()
            else:
                logger.info('无效选择')

    def show_build_stats(self):
        """显示构建统计"""
        # 查找最新的输出目录
        output_dirs = list(Path('/tmp').glob('patent_kg_output_*'))
        if not output_dirs:
            logger.info('没有找到构建输出目录')
            return

        latest_dir = max(output_dirs, key=lambda x: x.stat().st_mtime)
        report_file = latest_dir / 'build_report.json'

        if report_file.exists():
            try:
                with open(report_file, 'r', encoding='utf-8') as f:
                    report = json.load(f)

                logger.info("\n📊 构建统计信息:")
                logger.info(str('='*30))
                logger.info(f"构建时间: {report['build_info']['timestamp']}")
                logger.info(f"耗时: {report['build_info']['duration_seconds']:.2f}秒")
                logger.info(f"源目录: {report['source_directory']}")
                logger.info(f"输出目录: {report['output_directory']}")

            except Exception as e:
                logger.info(f"读取统计信息失败: {e}")
        else:
            logger.info('没有找到统计报告文件')

def main():
    """主程序"""
    logger.info('🏛️ 专利知识图谱构建系统启动器')
    logger.info(str('='*50))

    builder = PatentKGBuilder()

    # 检查命令行参数
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'check':
            # 检查系统要求
            if builder.check_requirements():
                logger.info('✅ 系统要求检查通过')
                return 0
            else:
                logger.info('❌ 系统要求检查失败')
                return 1

        elif command == 'install':
            # 安装依赖
            builder.install_requirements()
            return 0

        elif command == 'build':
            # 构建知识图谱
            source_dir = sys.argv[2] if len(sys.argv) > 2 else None
            output_dir = sys.argv[3] if len(sys.argv) > 3 else None

            success = builder.build_knowledge_graph(source_dir, output_dir)
            return 0 if success else 1

        elif command == 'web':
            # 启动Web服务器
            builder.run_web_server()
            return 0

        elif command == 'stats':
            # 显示统计
            builder.show_build_stats()
            return 0

        else:
            logger.info(f"未知命令: {command}")
            print_usage()
            return 1
    else:
        # 交互模式
        builder.interactive_mode()

    return 0

def print_usage():
    """打印使用说明"""
    logger.info(str("""
使用方法:
  python build_patent_kg.py [command] [options]

命令:
  check       检查系统要求
  install     安装依赖包
  build       构建知识图谱
  web         启动Web服务器
  stats       查看构建统计
  (无参数))     交互模式

示例:
  python build_patent_kg.py check
  python build_patent_kg.py build /path/to/patents /path/to/output
  python build_patent_kg.py web
""")

if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"程序异常退出: {str(e)}")
        sys.exit(1)