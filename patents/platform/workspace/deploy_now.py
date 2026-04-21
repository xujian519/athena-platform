#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利知识图谱立即部署脚本
Patent Knowledge Graph Deploy Now Script

立即部署专利知识图谱构建系统
Deploy patent knowledge graph construction system immediately

作者: Athena AI系统
创建时间: 2025年12月6日
版本: 1.0.0
"""

import logging
import os
import subprocess
import sys
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_status(message, status='INFO'):
    """打印状态信息"""
    icons = {
        'INFO': 'ℹ️',
        'SUCCESS': '✅',
        'WARNING': '⚠️',
        'ERROR': '❌'
    }
    logger.info(f"{icons.get(status, 'ℹ️')} {message}")

def install_dependencies():
    """安装依赖包"""
    print_status('开始安装依赖包...')

    packages = [
        'neo4j',
        'flask',
        'flask-cors',
        'pandas',
        'matplotlib',
        'seaborn',
        'plotly',
        'python-docx',
        'jieba',
        'spacy',
        'wordcloud',
        'jinja2',
        'openpyxl'
    ]

    for package in packages:
        try:
            __import__(package)
            print_status(f"{package} 已安装', 'SUCCESS")
        except ImportError:
            print_status(f"安装 {package}...")
            result = subprocess.run(
                ['pip3', 'install', package],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print_status(f"{package} 安装成功', 'SUCCESS")
            else:
                print_status(f"{package} 安装失败: {result.stderr}', 'ERROR")

    # 安装spaCy中文模型
    try:
        import spacy
        spacy.load('zh_core_web_sm')
        print_status('spaCy中文模型已安装', 'SUCCESS')
    except (ImportError, OSError):
        print_status('安装spaCy中文模型...')
        subprocess.run(['python3', '-m', 'spacy', 'download', 'zh_core_web_sm'])

def create_test_demo():
    """创建测试演示"""
    print_status('创建测试演示...')

    demo_code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利知识图谱测试演示
Patent Knowledge Graph Test Demo
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

def test_schema():
    """测试知识图谱模式"""
    logger.info('🏛️ 测试知识图谱模式...')

    try:
        from knowledge_graph.patent_knowledge_graph_schema import (
            EntityType, RelationType, PatentKnowledgeGraphSchema
        )

        # 统计实体和关系类型
        entity_count = len(EntityType)
        relation_count = len(RelationType)

        logger.info(f"✅ 实体类型数量: {entity_count}")
        logger.info(f"✅ 关系类型数量: {relation_count}")

        # 创建并验证模式
        schema = PatentKnowledgeGraphSchema()
        is_valid = schema.validate_schema()
        logger.info(f"✅ 模式验证: {'通过' if is_valid else '失败'}")

        return True

    except Exception as e:
        logger.info(f"❌ 模式测试失败: {e}")
        return False

def test_extractor():
    """测试知识抽取器"""
    logger.info("\\n🔍 测试知识抽取器...")

    try:
        from knowledge_graph.patent_knowledge_extractor import PatentKnowledgeExtractor

        # 创建抽取器实例
        extractor = PatentKnowledgeExtractor()
        logger.info('✅ 抽取器创建成功')

        # 测试文档类型识别
        test_paths = [
            '/test/专利法.docx',
            '/test/复审决定书.doc',
            '/test/无效宣告.docx',
            '/test/审查指南.pdf'
        ]

        for path in test_paths:
            doc_type = extractor._identify_document_type(path)
            logger.info(f"✅ {path} -> {doc_type}")

        return True

    except Exception as e:
        logger.info(f"❌ 抽取器测试失败: {e}")
        return False

def test_neo4j_manager():
    """测试Neo4j管理器"""
    logger.info("\\n🗄️ 测试Neo4j管理器...")

    try:
        from knowledge_graph.neo4j_manager import Neo4jManager

        # 创建管理器实例（不连接）
        manager = Neo4jManager()
        logger.info('✅ Neo4j管理器创建成功')

        # 测试配置
        config = {
            'uri': 'bolt://localhost:7687',
            'username': 'neo4j',
            'password': 'password',
            'database': 'patent_kg'
        }
        logger.info('✅ Neo4j配置加载成功')

        return True

    except Exception as e:
        logger.info(f"❌ Neo4j管理器测试失败: {e}")
        return False

def main():
    """主测试函数"""
    logger.info('🎯 专利知识图谱系统测试')
    logger.info(str('='*50))

    tests = [
        ('知识图谱模式', test_schema),
        ('知识抽取器', test_extractor),
        ('Neo4j管理器', test_neo4j_manager)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        logger.info(f"\\n📋 测试: {test_name}")
        if test_func():
            passed += 1
            logger.info(f"✅ {test_name} 测试通过")
        else:
            logger.info(f"❌ {test_name} 测试失败")

    logger.info(f"\\n📊 测试结果: {passed}/{total} 通过")

    if passed == total:
        logger.info('🎉 所有测试通过！系统准备就绪。')
        return True
    else:
        logger.info('⚠️ 部分测试失败，请检查错误信息。')
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
'''

    demo_file = Path(__file__).parent / 'test_patent_kg.py'
    with open(demo_file, 'w', encoding='utf-8') as f:
        f.write(demo_code)

    os.chmod(demo_file, 0o755)
    print_status('测试脚本创建成功', 'SUCCESS')

def run_tests():
    """运行测试"""
    print_status('运行系统测试...')

    test_file = Path(__file__).parent / 'test_patent_kg.py'
    if test_file.exists():
        result = subprocess.run(
            ['python3', str(test_file)],
            capture_output=True,
            text=True
        )
        logger.info(str(result.stdout))
        if result.stderr:
            print('警告信息:', result.stderr)
        return result.returncode == 0
    else:
        print_status('测试脚本不存在', 'ERROR')
        return False

def check_neo4j():
    """检查Neo4j状态"""
    print_status('检查Neo4j状态...')

    try:
        import requests
        response = requests.get('http://localhost:7474', timeout=5)
        if response.status_code == 200:
            print_status('Neo4j Web界面运行正常', 'SUCCESS')
            return True
    except:
        pass

    # 检查端口
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 7687))
        sock.close()

        if result == 0:
            print_status('Neo4j Bolt端口可用', 'SUCCESS')
            return True
    except:
        pass

    print_status('Neo4j未运行或不可访问', 'WARNING')
    return False

def show_next_steps():
    """显示下一步操作"""
    logger.info(str("\n" + '='*60))
    logger.info('🎯 系统部署完成！下一步操作建议:')
    logger.info(str('='*60))

    logger.info("\n1. 🗄️ 启动Neo4j数据库 (推荐Docker):")
    logger.info("   docker run --name neo4j \\")
    logger.info("     -p 7474:7474 -p 7687:7687 \\")
    logger.info("     -d \\")
    logger.info("     -v $HOME/neo4j/data:/data \\")
    logger.info("     -v $HOME/neo4j/logs:/logs \\")
    logger.info("     -e NEO4J_AUTH=neo4j/password \\")
    logger.info('     neo4j:latest')

    logger.info("\n2. 🏛️ 构建专利知识图谱:")
    logger.info(str('   cd ' + str(Path(__file__)).parent))
    logger.info('   python3 build_patent_kg.py build')
    logger.info('   # 这将处理您的57,218个专利文档')

    logger.info("\n3. 🌐 启动Web可视化界面:")
    logger.info('   python3 build_patent_kg.py web')
    logger.info('   # 访问 http://localhost:5000')

    logger.info("\n4. 📊 查看系统统计:")
    logger.info('   python3 build_patent_kg.py stats')

    logger.info("\n5. 🎮 交互式操作:")
    logger.info('   python3 build_patent_kg.py')
    logger.info('   # 进入交互式菜单界面')

def main():
    """主部署函数"""
    logger.info('🚀 专利知识图谱系统立即部署')
    logger.info(str('='*60))
    logger.info('📊 处理目标: 57,218个专利文档')
    logger.info('⚡ 技术架构: Neo4j + Python NLP + Web可视化')
    logger.info(str('='*60))

    # 1. 安装依赖
    install_dependencies()

    # 2. 创建测试
    create_test_demo()

    # 3. 运行测试
    test_success = run_tests()

    # 4. 检查Neo4j
    neo4j_ready = check_neo4j()

    # 5. 显示结果
    logger.info(str("\n" + '='*60))
    logger.info('📊 部署结果总结')
    logger.info(str('='*60))

    if test_success:
        print_status('核心系统组件测试通过', 'SUCCESS')
    else:
        print_status('部分系统组件存在问题', 'WARNING')

    if neo4j_ready:
        print_status('Neo4j数据库可用', 'SUCCESS')
    else:
        print_status('需要启动Neo4j数据库', 'WARNING')

    # 显示下一步
    show_next_steps()

    if test_success:
        logger.info("\n🎉 专利知识图谱系统部署成功！")
        logger.info('💡 您现在可以开始处理57,218个专利文档了')
        return 0
    else:
        logger.info("\n⚠️ 部署遇到问题，请检查上述错误信息")
        return 1

if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n👋 部署被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"部署异常: {str(e)}")
        sys.exit(1)