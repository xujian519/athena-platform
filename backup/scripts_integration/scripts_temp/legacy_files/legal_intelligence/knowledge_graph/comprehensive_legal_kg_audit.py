#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
法律知识图谱全面审计工具
Comprehensive Legal Knowledge Graph Audit Tool

全面检查项目中所有法律知识图谱的完整性、运行状态和质量
"""

import json
import logging
import os
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests

# 导入标准化数据库工具
from shared.database.db_utils import DatabaseManager, build_safe_query

logger = logging.getLogger(__name__)

class LegalKnowledgeGraphAuditor:
    """法律知识图谱审计器"""

    def __init__(self):
        self.project_root = Path('/Users/xujian/Athena工作平台')
        self.data_root = self.project_root / 'data'
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'graph_databases': {},
            'api_services': {},
            'file_system': {},
            'tu_graph_status': {},
            'vector_databases': {},
            'overall_score': 0,
            'recommendations': []
        }

    def check_file_system_kgs(self):
        """检查文件系统中的知识图谱"""
        logger.info('📁 检查文件系统中的法律知识图谱...')

        kg_paths = [
            'fixed_legal_knowledge_graph/fixed_legal_knowledge_graph.json',
            'production_legal_knowledge_graph/production_legal_knowledge_graph.json',
            'legal_knowledge_graph_demo/legal_knowledge_graph_demo.json',
            'legal_knowledge_graph_enhanced/enhanced_legal_kg.json',
            'law_knowledge_graph_new/legal_knowledge_graph.json'
        ]

        file_kgs = {}
        for kg_path in kg_paths:
            full_path = self.data_root / kg_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        kg_data = json.load(f)

                    entities = kg_data.get('entities', [])
                    relations = kg_data.get('relations', [])

                    file_kgs[kg_path] = {
                        'status': '✅ 可用',
                        'entities_count': len(entities),
                        'relations_count': len(relations),
                        'file_size_mb': round(full_path.stat().st_size / 1024 / 1024, 2),
                        'last_modified': datetime.fromtimestamp(full_path.stat().st_mtime).isoformat(),
                        'quality_score': self._calculate_kg_quality_score(entities, relations),
                        'sample_entities': entities[:3] if entities else [],
                        'sample_relations': relations[:3] if relations else []
                    }
                    logger.info(f"  ✅ {kg_path}: {len(entities)} 实体, {len(relations)} 关系")

                except Exception as e:
                    file_kgs[kg_path] = {
                        'status': f'❌ 错误: {str(e)}',
                        'entities_count': 0,
                        'relations_count': 0
                    }
                    logger.info(f"  ❌ {kg_path}: {str(e)}")
            else:
                file_kgs[kg_path] = {
                    'status': '📂 文件不存在',
                    'entities_count': 0,
                    'relations_count': 0
                }
                logger.info(f"  📂 {kg_path}: 文件不存在")

        self.results['file_system'] = file_kgs
        return file_kgs

    def check_sqlite_databases(self):
        """检查SQLite数据库"""
        logger.info('🗄️ 检查SQLite法律数据库...')

        db_files = [
            'athena_knowledge_graph.db',
            'legal_laws_database.db',
            'patent_legal_database.db',
            'memory_active.db',
            'patent_cache.db'
        ]

        sqlite_status = {}
        for db_file in db_files:
            db_path = self.data_root / db_file
            if db_path.exists():
                try:
                    conn = sqlite3.connect(str(db_path))
                    cursor = conn.cursor()

                    # 获取表列表
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = [row[0] for row in cursor.fetchall()]

                    # 获取数据库统计信息
                    stats = {}
                    for table in tables:
        # TODO: 检查SQL注入风险 - cursor.execute(f"SELECT COUNT(*) FROM {table};")
                                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                        stats[table] = cursor.fetchone()[0]

                    # 检查法律相关表
                    legal_tables = [t for t in tables if any(keyword in t.lower()
                                    for keyword in ['legal', 'law', 'patent', 'knowledge', 'graph'])]

                    sqlite_status[db_file] = {
                        'status': '✅ 可用',
                        'tables_count': len(tables),
                        'legal_tables_count': len(legal_tables),
                        'tables': tables,
                        'legal_tables': legal_tables,
                        'table_stats': stats,
                        'file_size_mb': round(db_path.stat().st_size / 1024 / 1024, 2)
                    }
                    logger.info(f"  ✅ {db_file}: {len(tables)} 个表, {len(legal_tables)} 个法律相关表")

                    conn.close()

                except Exception as e:
                    sqlite_status[db_file] = {
                        'status': f'❌ 错误: {str(e)}',
                        'tables_count': 0,
                        'legal_tables_count': 0
                    }
                    logger.info(f"  ❌ {db_file}: {str(e)}")
            else:
                sqlite_status[db_file] = {
                    'status': '📂 文件不存在',
                    'tables_count': 0,
                    'legal_tables_count': 0
                }
                logger.info(f"  📂 {db_file}: 文件不存在")

        self.results['graph_databases']['sqlite'] = sqlite_status
        return sqlite_status

    def check_tu_graph_status(self):
        """检查TuGraph图数据库状态"""
        logger.info('🔗 检查TuGraph图数据库状态...')

        tugraph_status = {}

        # 检查Docker容器状态
        try:
            result = subprocess.run(
                ['docker', 'ps', '-f', 'name=athena-tugraph', '--format', '{{.Status}}'],
                capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0 and result.stdout.strip():
                tugraph_status['docker_container'] = {
                    'status': '✅ 运行中',
                    'details': result.stdout.strip()
                }
                logger.info(f"  ✅ TuGraph Docker容器: {result.stdout.strip()}")
            else:
                tugraph_status['docker_container'] = {
                    'status': '❌ 未运行',
                    'details': '容器未启动'
                }
                logger.info('  ❌ TuGraph Docker容器: 未运行')

        except Exception as e:
            tugraph_status['docker_container'] = {
                'status': f'❌ 错误: {str(e)}',
                'details': '无法检查容器状态'
            }
            logger.info(f"  ❌ TuGraph Docker容器检查失败: {str(e)}")

        # 检查图数据库
        try:
            graphs_to_check = [
                'fixed_legal_knowledge_graph',
                'clean_legal_knowledge_graph',
                'production_legal_knowledge_graph',
                'legal_knowledge_graph_demo'
            ]

            available_graphs = []
            for graph_name in graphs_to_check:
                cmd = [
                    'docker', 'exec', 'athena-tugraph', 'lgraph_cli',
                    '--user', 'admin', '--password', '73@TuGraph',
                    '--graph', graph_name, '--format', 'table',
                    'MATCH (n) RETURN COUNT(n) as vertex_count LIMIT 1'
                ]

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

                if result.returncode == 0 and result.stdout.strip():
                    lines = result.stdout.strip().split('\n')
                    if len(lines) >= 3:
                        try:
                            vertex_count = int(lines[-1].strip())
                            available_graphs.append({
                                'name': graph_name,
                                'vertex_count': vertex_count,
                                'status': '✅ 可用'
                            })
                            logger.info(f"  ✅ 图数据库 {graph_name}: {vertex_count} 个顶点")
                        except:
                            pass

            tugraph_status['graphs'] = {
                'status': f'✅ 发现 {len(available_graphs)} 个可用图',
                'available_graphs': available_graphs,
                'total_graphs': len(graphs_to_check)
            }

        except Exception as e:
            tugraph_status['graphs'] = {
                'status': f'❌ 错误: {str(e)}',
                'available_graphs': [],
                'total_graphs': 0
            }
            logger.info(f"  ❌ 图数据库检查失败: {str(e)}")

        self.results['tu_graph_status'] = tugraph_status
        return tugraph_status

    def check_api_services(self):
        """检查API服务状态"""
        logger.info('🌐 检查法律知识图谱API服务...')

        api_endpoints = [
            ('知识图谱API', 'http://localhost:8002/api/v1/graph/stats'),
            ('统一知识管理器', 'http://localhost:8005/api/v1/health'),
            ('智能搜索API', 'http://localhost:8003/api/v1/health'),
            ('法律向量API', 'http://localhost:8001/api/v1/health')
        ]

        api_status = {}
        for api_name, endpoint in api_endpoints:
            try:
                response = requests.get(endpoint, timeout=5)
                if response.status_code == 200:
                    api_status[api_name] = {
                        'status': '✅ 运行中',
                        'response_code': response.status_code,
                        'endpoint': endpoint
                    }
                    logger.info(f"  ✅ {api_name}: 运行正常")
                else:
                    api_status[api_name] = {
                        'status': f'⚠️ HTTP {response.status_code}',
                        'response_code': response.status_code,
                        'endpoint': endpoint
                    }
                    logger.info(f"  ⚠️ {api_name}: HTTP {response.status_code}")

            except requests.exceptions.ConnectionError:
                api_status[api_name] = {
                    'status': '❌ 连接失败',
                    'endpoint': endpoint
                }
                logger.info(f"  ❌ {api_name}: 连接失败")
            except Exception as e:
                api_status[api_name] = {
                    'status': f'❌ 错误: {str(e)}',
                    'endpoint': endpoint
                }
                logger.info(f"  ❌ {api_name}: {str(e)}")

        self.results['api_services'] = api_status
        return api_status

    def check_vector_databases(self):
        """检查向量数据库状态"""
        logger.info('🔍 检查向量数据库状态...')

        vector_dbs = [
            'qdrant',
            'ultra_fast_legal_vector_db',
            'legal_clause_vector_db_poc',
            'technical_terms_knowledge_graph'
        ]

        vector_status = {}
        for db_name in vector_dbs:
            db_path = self.data_root / db_name
            if db_path.exists() and db_path.is_dir():
                try:
                    # 统计文件数量
                    files = list(db_path.rglob('*'))
                    file_count = len([f for f in files if f.is_file()])
                    total_size = sum(f.stat().st_size for f in files if f.is_file())

                    vector_status[db_name] = {
                        'status': '✅ 可用',
                        'file_count': file_count,
                        'size_mb': round(total_size / 1024 / 1024, 2),
                        'path': str(db_path.relative_to(self.project_root))
                    }
                    logger.info(f"  ✅ {db_name}: {file_count} 个文件, {vector_status[db_name]['size_mb']} MB")

                except Exception as e:
                    vector_status[db_name] = {
                        'status': f'❌ 错误: {str(e)}',
                        'file_count': 0,
                        'size_mb': 0
                    }
                    logger.info(f"  ❌ {db_name}: {str(e)}")
            else:
                vector_status[db_name] = {
                    'status': '📂 目录不存在',
                    'file_count': 0,
                    'size_mb': 0
                }
                logger.info(f"  📂 {db_name}: 目录不存在")

        self.results['vector_databases'] = vector_status
        return vector_status

    def _calculate_kg_quality_score(self, entities: List[Dict], relations: List[Dict]) -> float:
        """计算知识图谱质量分数"""
        if not entities:
            return 0.0

        score = 0.0

        # 实体数量评分 (0-30分)
        entity_count = len(entities)
        if entity_count >= 1000:
            score += 30
        elif entity_count >= 500:
            score += 20
        elif entity_count >= 100:
            score += 10
        else:
            score += 5

        # 关系数量评分 (0-30分)
        relation_count = len(relations)
        if relation_count >= 1000:
            score += 30
        elif relation_count >= 500:
            score += 20
        elif relation_count >= 100:
            score += 10
        elif relation_count >= 50:
            score += 5

        # 实体完整性评分 (0-25分)
        complete_entities = sum(1 for e in entities if all(k in e for k in ['name', 'type']))
        if complete_entities > 0:
            score += (complete_entities / len(entities)) * 25

        # 关系完整性评分 (0-15分)
        complete_relations = sum(1 for r in relations if all(k in r for k in ['source', 'target', 'type']))
        if complete_relations > 0:
            score += (complete_relations / len(relations)) * 15

        return min(100.0, score)

    def calculate_overall_score(self):
        """计算整体质量分数"""
        logger.info('📊 计算整体质量分数...')

        scores = []

        # 文件系统知识图谱分数
        if self.results['file_system']:
            file_scores = []
            for kg_info in self.results['file_system'].values():
                if 'quality_score' in kg_info:
                    file_scores.append(kg_info['quality_score'])
            if file_scores:
                scores.append(('文件系统知识图谱', sum(file_scores) / len(file_scores)))

        # SQLite数据库分数
        if self.results['graph_databases'].get('sqlite'):
            sqlite_score = 0
            for db_info in self.results['graph_databases']['sqlite'].values():
                if db_info['legal_tables_count'] > 0:
                    sqlite_score += 50
                if db_info['tables_count'] > 0:
                    sqlite_score += 50
                    break
            scores.append(('SQLite数据库', min(100, sqlite_score)))

        # TuGraph分数
        if self.results['tu_graph_status'].get('graphs'):
            graphs = self.results['tu_graph_status']['graphs']['available_graphs']
            if graphs:
                total_vertices = sum(g['vertex_count'] for g in graphs)
                tugraph_score = min(100, total_vertices / 100)  # 每100个顶点1分
                scores.append(('TuGraph图数据库', tugraph_score))

        # API服务分数
        if self.results['api_services']:
            running_apis = sum(1 for api in self.results['api_services'].values()
                             if '✅' in api['status'])
            api_score = (running_apis / len(self.results['api_services'])) * 100
            scores.append(('API服务', api_score))

        # 向量数据库分数
        if self.results['vector_databases']:
            available_vectors = sum(1 for db in self.results['vector_databases'].values()
                                  if '✅' in db['status'])
            vector_score = (available_vectors / len(self.results['vector_databases'])) * 100
            scores.append(('向量数据库', vector_score))

        # 计算加权平均分数
        if scores:
            weights = {
                '文件系统知识图谱': 0.2,
                'SQLite数据库': 0.15,
                'TuGraph图数据库': 0.3,
                'API服务': 0.25,
                '向量数据库': 0.1
            }

            total_score = 0.0
            total_weight = 0.0
            for component, score in scores:
                weight = weights.get(component, 0.2)
                total_score += score * weight
                total_weight += weight

            overall_score = total_score / total_weight if total_weight > 0 else 0
            self.results['overall_score'] = round(overall_score, 1)

            logger.info(f"📈 整体质量分数: {overall_score:.1f}/100")
            for component, score in scores:
                weight = weights.get(component, 0.2)
                logger.info(f"  - {component}: {score:.1f} (权重: {weight*100}%)")

        return self.results['overall_score']

    def generate_recommendations(self):
        """生成改进建议"""
        logger.info('💡 生成改进建议...')

        recommendations = []

        # 基于整体分数的建议
        overall_score = self.results['overall_score']
        if overall_score < 60:
            recommendations.append('🔴 整体质量偏低，建议进行全面重构和优化')
        elif overall_score < 80:
            recommendations.append('🟡 质量中等，建议重点优化关键组件')
        else:
            recommendations.append('🟢 质量良好，建议持续维护和监控')

        # 基于各组件状态的建议
        if self.results['file_system']:
            missing_kgs = [kg for kg, info in self.results['file_system'].items()
                          if '不存在' in info['status']]
            if missing_kgs:
                recommendations.append(f"📁 缺失 {len(missing_kgs)} 个知识图谱文件，建议检查构建流程")

        if self.results['tu_graph_status'].get('graphs'):
            available_graphs = self.results['tu_graph_status']['graphs']['available_graphs']
            if len(available_graphs) == 0:
                recommendations.append('🔗 TuGraph中无可用图数据库，建议执行数据导入')
            elif len(available_graphs) < 2:
                recommendations.append('🔗 TuGraph图数据库较少，建议增加更多法律知识图谱')

        if self.results['api_services']:
            failed_apis = [api for api, info in self.results['api_services'].items()
                          if '❌' in info['status']]
            if failed_apis:
                recommendations.append(f"🌐 {len(failed_apis)} 个API服务异常，建议检查服务状态")

        # 添加通用建议
        recommendations.extend([
            '📊 建议建立定期质量检查和监控机制',
            '🔄 建议建立数据更新和同步流程',
            '📚 建议完善文档和使用指南',
            '🧪 建议增加自动化测试覆盖'
        ])

        self.results['recommendations'] = recommendations
        return recommendations

    def generate_audit_report(self):
        """生成审计报告"""
        logger.info('📄 生成审计报告...')

        report_content = f"""# 法律知识图谱全面审计报告

**审计时间**: {self.results['timestamp']}
**审计工具**: Athena法律知识图谱审计器
**整体质量分数**: {self.results['overall_score']}/100

---

## 📊 整体评估

**状态**: {'🟢 优秀' if self.results['overall_score'] >= 80 else '🟡 中等' if self.results['overall_score'] >= 60 else '🔴 需改进'}

---

## 📁 文件系统知识图谱状态

"""

        # 文件系统知识图谱
        for kg_path, kg_info in self.results['file_system'].items():
            report_content += f"### {kg_path}\n"
            report_content += f"- **状态**: {kg_info['status']}\n"
            if kg_info['entities_count'] > 0:
                report_content += f"- **实体数量**: {kg_info['entities_count']}\n"
                report_content += f"- **关系数量**: {kg_info['relations_count']}\n"
                report_content += f"- **文件大小**: {kg_info.get('file_size_mb', 0)} MB\n"
                report_content += f"- **质量分数**: {kg_info.get('quality_score', 0)}/100\n"
            report_content += "\n"

        # SQLite数据库
        report_content += "---\n\n## 🗄️ SQLite数据库状态\n\n"
        sqlite_dbs = self.results['graph_databases'].get('sqlite', {})
        for db_name, db_info in sqlite_dbs.items():
            report_content += f"### {db_name}\n"
            report_content += f"- **状态**: {db_info['status']}\n"
            if db_info['tables_count'] > 0:
                report_content += f"- **表数量**: {db_info['tables_count']}\n"
                report_content += f"- **法律相关表**: {db_info['legal_tables_count']}\n"
                report_content += f"- **文件大小**: {db_info.get('file_size_mb', 0)} MB\n"
            report_content += "\n"

        # TuGraph状态
        report_content += "---\n\n## 🔗 TuGraph图数据库状态\n\n"
        tugraph = self.results['tu_graph_status']
        report_content += f"### Docker容器\n"
        report_content += f"- **状态**: {tugraph['docker_container']['status']}\n"
        report_content += f"- **详情**: {tugraph['docker_container']['details']}\n\n"

        if tugraph.get('graphs'):
            report_content += f"### 图数据库\n"
            report_content += f"- **状态**: {tugraph['graphs']['status']}\n"
            report_content += f"- **可用图数量**: {len(tugraph['graphs']['available_graphs'])}/{tugraph['graphs']['total_graphs']}\n\n"

            for graph in tugraph['graphs']['available_graphs']:
                report_content += f"#### {graph['name']}\n"
                report_content += f"- **状态**: {graph['status']}\n"
                report_content += f"- **顶点数量**: {graph['vertex_count']}\n\n"

        # API服务状态
        report_content += "---\n\n## 🌐 API服务状态\n\n"
        for api_name, api_info in self.results['api_services'].items():
            report_content += f"### {api_name}\n"
            report_content += f"- **状态**: {api_info['status']}\n"
            if 'endpoint' in api_info:
                report_content += f"- **端点**: {api_info['endpoint']}\n"
            report_content += "\n"

        # 向量数据库状态
        report_content += "---\n\n## 🔍 向量数据库状态\n\n"
        for db_name, db_info in self.results['vector_databases'].items():
            report_content += f"### {db_name}\n"
            report_content += f"- **状态**: {db_info['status']}\n"
            if db_info['file_count'] > 0:
                report_content += f"- **文件数量**: {db_info['file_count']}\n"
                report_content += f"- **大小**: {db_info['size_mb']} MB\n"
            report_content += "\n"

        # 改进建议
        report_content += "---\n\n## 💡 改进建议\n\n"
        for i, recommendation in enumerate(self.results['recommendations'], 1):
            report_content += f"{i}. {recommendation}\n"

        report_content += f"""

---

## 📈 详细统计

- **检查组件数**: 5个 (文件系统、SQLite、TuGraph、API、向量数据库)
- **整体质量分数**: {self.results['overall_score']}/100
- **建议数量**: {len(self.results['recommendations'])}

---

**审计完成时间**: {datetime.now().isoformat()}
"""

        # 保存报告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = self.project_root / 'reports' / f"legal_kg_audit_report_{timestamp}.md"
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        # 保存详细JSON结果
        json_path = self.project_root / 'reports' / f"legal_kg_audit_data_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 审计报告已保存: {report_path}")
        logger.info(f"✅ 详细数据已保存: {json_path}")
        return report_path

    def run_comprehensive_audit(self):
        """运行全面审计"""
        logger.info('🔍 开始法律知识图谱全面审计')
        logger.info(str('='*60))

        try:
            # 1. 检查文件系统知识图谱
            self.check_file_system_kgs()

            # 2. 检查SQLite数据库
            self.check_sqlite_databases()

            # 3. 检查TuGraph状态
            self.check_tu_graph_status()

            # 4. 检查API服务
            self.check_api_services()

            # 5. 检查向量数据库
            self.check_vector_databases()

            # 6. 计算整体分数
            self.calculate_overall_score()

            # 7. 生成建议
            self.generate_recommendations()

            # 8. 生成报告
            report_path = self.generate_audit_report()

            logger.info(str('='*60))
            logger.info('🎉 法律知识图谱全面审计完成!')
            logger.info(f"📊 整体质量分数: {self.results['overall_score']}/100")
            logger.info(f"📄 详细报告: {report_path}")

            return True

        except Exception as e:
            logger.info(f"❌ 审计过程异常: {str(e)}")
            return False

def main():
    """主函数"""
    logger.info('⚖️ 法律知识图谱全面审计工具')
    logger.info('全面检查项目中所有法律知识图谱的完整性、运行状态和质量')
    logger.info(str('='*60))

    # 创建审计器
    auditor = LegalKnowledgeGraphAuditor()

    # 运行审计
    success = auditor.run_comprehensive_audit()

    if success:
        score = auditor.results['overall_score']
        if score >= 80:
            logger.info(f"\n🟢 审计完成！法律知识图谱质量优秀 ({score}/100)")
        elif score >= 60:
            logger.info(f"\n🟡 审计完成！法律知识图谱质量中等 ({score}/100)，建议优化")
        else:
            logger.info(f"\n🔴 审计完成！法律知识图谱需要改进 ({score}/100)")
    else:
        logger.info("\n❌ 审计失败，请检查错误信息")

if __name__ == '__main__':
    main()