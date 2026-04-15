#!/usr/bin/env python3
"""
专利知识图谱系统检查脚本
Patent Knowledge Graph System Check Script

检查系统环境和依赖
Check system environment and dependencies

作者: Athena AI系统
创建时间: 2025年12月6日
版本: 1.0.0
"""

import logging
import socket
import subprocess
import sys
from pathlib import Path

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

def check_python_version():
    """检查Python版本"""
    logger.info("\n🐍 Python环境检查:")
    print_status(f"Python版本: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} (满足要求)', 'SUCCESS")
    return True

def check_dependencies():
    """检查依赖包"""
    logger.info("\n📦 依赖包检查:")

    required_packages = [
        ('neo4j', 'Neo4j Python驱动'),
        ('flask', 'Flask Web框架'),
        ('pandas', '数据处理'),
        ('matplotlib', '图表绘制'),
        ('jieba', '中文分词'),
        ('spacy', 'NLP处理'),
        ('python_docx', 'Word文档处理')
    ]

    all_installed = True

    for package, description in required_packages:
        try:
            if package == 'python_docx':
                import docx
                print_status(f"{description} (python-docx)', 'SUCCESS")
            else:
                __import__(package)
                print_status(f"{description} ({package})', 'SUCCESS")
        except ImportError:
            print_status(f"{description} ({package}) - 未安装', 'ERROR")
            all_installed = False

    return all_installed

def check_spacy_model():
    """检查spaCy中文模型"""
    logger.info("\n🧠 spaCy中文模型检查:")
    try:
        import spacy
        spacy.load('zh_core_web_sm')
        print_status('spaCy中文模型 (zh_core_web_sm)', 'SUCCESS')
        return True
    except OSError:
        print_status('spaCy中文模型 (zh_core_web_sm) - 未安装', 'WARNING')
        logger.info('💡 运行: python3 -m spacy download zh_core_web_sm')
        return False

def check_data_directory():
    """检查数据目录"""
    logger.info("\n📂 数据目录检查:")

    data_dir = Path('/Users/xujian/学习资料/专利')
    if not data_dir.exists():
        print_status(f"数据目录不存在: {data_dir}', 'ERROR")
        return False

    # 统计文件
    doc_files = list(data_dir.rglob('*.doc*'))
    pdf_files = list(data_dir.rglob('*.pdf'))
    md_files = list(data_dir.rglob('*.md'))

    total_files = len(doc_files) + len(pdf_files) + len(md_files)

    print_status(f"数据目录: {data_dir}', 'SUCCESS")
    logger.info(f"📄 Word文档: {len(doc_files):,}个")
    logger.info(f"📋 PDF文档: {len(pdf_files):,}个")
    logger.info(f"📝 Markdown文档: {len(md_files):,}个")
    logger.info(f"📊 总计: {total_files:,}个文档")

    return total_files > 0

def check_neo4j_connection():
    """检查Neo4j连接"""
    logger.info("\n🗄️ Neo4j数据库检查:")

    # 检查端口
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 7687))
        sock.close()

        if result == 0:
            print_status('Neo4j Bolt端口 (7687) - 可访问', 'SUCCESS')
        else:
            print_status('Neo4j Bolt端口 (7687) - 不可访问', 'ERROR')
            return False
    except Exception as e:
        print_status(f"Neo4j Bolt端口检查失败: {e}', 'ERROR")
        return False

    # 检查Web界面
    try:
        import requests
        response = requests.get('http://localhost:7474', timeout=5)
        if response.status_code == 200:
            data = response.json()
            version = data.get('neo4j_version', 'Unknown')
            print_status(f"Neo4j Web界面 (7474) - 版本 {version}', 'SUCCESS")
            return True
    except Exception:
        print_status('Neo4j Web界面 (7474) - 不可访问', 'WARNING')

    return True

def check_project_structure():
    """检查项目结构"""
    logger.info("\n🏗️ 项目结构检查:")

    project_dir = Path('/Users/xujian/Athena工作平台/patent_workspace')

    required_files = [
        'src/knowledge_graph/patent_knowledge_graph_schema.py',
        'src/knowledge_graph/patent_knowledge_extractor.py',
        'src/knowledge_graph/neo4j_manager.py',
        'src/knowledge_graph/patent_kg_application.py',
        'build_patent_kg.py',
        'README.md'
    ]

    all_exist = True

    for file_path in required_files:
        full_path = project_dir / file_path
        if full_path.exists():
            print_status(f"项目文件: {file_path}', 'SUCCESS")
        else:
            print_status(f"项目文件: {file_path} - 不存在', 'ERROR")
            all_exist = False

    return all_exist

def check_docker_neo4j():
    """检查Docker中的Neo4j"""
    logger.info("\n🐳 Docker Neo4j容器检查:")

    try:
        result = subprocess.run(
            ['docker', 'ps', '--filter', 'ancestor=neo4j', '--format', 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:  # Skip header
                logger.info('正在运行的Neo4j容器:')
                for line in lines[1:]:
                    logger.info(f"  🔸 {line}")
                return True
            else:
                print_status('没有找到运行中的Neo4j容器', 'WARNING')
                return False
        else:
            print_status('Docker命令执行失败', 'ERROR')
            return False

    except subprocess.TimeoutExpired:
        print_status('Docker命令超时', 'ERROR')
        return False
    except FileNotFoundError:
        print_status('Docker未安装或不在PATH中', 'ERROR')
        return False
    except Exception as e:
        print_status(f"Docker检查异常: {e}', 'ERROR")
        return False

def generate_system_report():
    """生成系统报告"""
    logger.info("\n📋 系统检查报告:")
    logger.info(str('='*60))

    # 执行所有检查
    checks = [
        ('Python版本', check_python_version),
        ('依赖包', check_dependencies),
        ('spaCy中文模型', check_spacy_model),
        ('数据目录', check_data_directory),
        ('Neo4j连接', check_neo4j_connection),
        ('项目结构', check_project_structure),
        ('Docker容器', check_docker_neo4j)
    ]

    results = {}

    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print_status(f"{check_name}检查异常: {e}', 'ERROR")
            results[check_name] = False

    # 总结
    passed = sum(results.values())
    total = len(results)

    logger.info("\n📊 检查结果总结:")
    logger.info(f"✅ 通过: {passed}/{total}")
    logger.info(f"❌ 失败: {total-passed}/{total}")

    if passed == total:
        print_status('所有检查通过，系统准备就绪！', 'SUCCESS')
        return True
    else:
        print_status('部分检查未通过，请解决问题后重试', 'WARNING')

        # 显示需要修复的问题
        logger.info("\n🔧 需要修复的问题:")
        for check_name, passed in results.items():
            if not passed:
                logger.info(f"   ❌ {check_name}")

        return False

def main():
    """主函数"""
    logger.info('🏛️ 专利知识图谱系统检查')
    logger.info(str('='*60))
    logger.info('📊 检查目标: 验证系统环境和依赖是否满足运行要求')
    logger.info(str('='*60))

    success = generate_system_report()

    if success:
        logger.info("\n🎉 系统检查完成！可以开始使用专利知识图谱系统。")
        logger.info("\n💡 下一步建议:")
        logger.info("   1. 运行小批量测试: python3 test_small_batch.py")
        logger.info("   2. 启动Web界面: python3 build_patent_kg.py web")
        logger.info("   3. 开始构建知识图谱")
    else:
        logger.info("\n⚠️ 系统检查发现问题，请按照上述建议修复后重新检查。")

    return 0 if success else 1

if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n👋 检查被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.info(f"❌ 检查过程中发生异常: {e}")
        sys.exit(1)
