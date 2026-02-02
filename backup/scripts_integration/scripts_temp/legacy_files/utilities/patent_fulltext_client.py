#!/usr/bin/env python3
"""
专利全文检索客户端
使用示例：python patent_fulltext_client.py --search '电动汽车' --full-text
"""

import argparse
import csv
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

# API端点配置
BASE_URL = 'http://localhost:8031'

class PatentFullTextClient:
    """专利全文检索客户端"""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()

    def search_patents(self,
                      keyword: str | None = None,
                      applicant: str | None = None,
                      ipc_class: str | None = None,
                      year: int | None = None,
                      year_start: int | None = None,
                      year_end: int | None = None,
                      patent_type: str | None = None,
                      limit: int = 20,
                      offset: int = 0) -> Dict:
        """搜索专利"""
        params = {
            'limit': limit,
            'offset': offset
        }

        if keyword:
            params['q'] = keyword
        if applicant:
            params['applicant'] = applicant
        if ipc_class:
            params['ipc_class'] = ipc_class
        if year:
            params['year'] = year
        if year_start:
            params['year_start'] = year_start
        if year_end:
            params['year_end'] = year_end
        if patent_type:
            params['patent_type'] = patent_type

        try:
            response = self.session.get(f"{self.base_url}/api/v2/search", params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.info(f"搜索失败: {e}")
            return {}

    def get_patent_full_text(self, application_number: str) -> Dict:
        """获取专利全文"""
        try:
            response = self.session.get(f"{self.base_url}/api/v2/patent/{application_number}/full")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.info(f"获取全文失败: {e}")
            return {}

    def batch_get_full_text(self, application_numbers: List[str]) -> Dict:
        """批量获取专利全文"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/v2/batch/full-text",
                json=application_numbers
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.info(f"批量获取失败: {e}")
            return {}

    def get_similar_patents(self, application_number: str, limit: int = 10) -> Dict:
        """获取相似专利"""
        params = {'limit': limit}
        try:
            response = self.session.get(
                f"{self.base_url}/api/v2/stats/similar",
                params={**params, 'application_number': application_number}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.info(f"获取相似专利失败: {e}")
            return {}

    def export_preview(self,
                      keyword: str | None = None,
                      applicant: str | None = None,
                      year_start: int | None = None,
                      year_end: int | None = None,
                      include_full_text: bool = False) -> Dict:
        """导出预览"""
        params = {'include_full_text': include_full_text}

        if keyword:
            params['q'] = keyword
        if applicant:
            params['applicant'] = applicant
        if year_start:
            params['year_start'] = year_start
        if year_end:
            params['year_end'] = year_end

        try:
            response = self.session.get(f"{self.base_url}/api/v2/export/preview", params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.info(f"导出预览失败: {e}")
            return {}

    def display_patent_brief(self, patent: Dict):
        """显示专利简要信息"""
        logger.info(f"\n{'='*60}")
        logger.info(f"专利名称: {patent.get('patent_name', 'N/A')}")
        logger.info(f"申请号: {patent.get('application_number', 'N/A')}")
        logger.info(f"申请人: {patent.get('applicant', 'N/A')}")
        print(f"发明人: {patent.get('inventor', 'N/A')[:50]}..." if patent.get('inventor') else "发明人: N/A")
        logger.info(f"申请日: {patent.get('application_date', 'N/A')}")
        logger.info(f"专利类型: {patent.get('patent_type', 'N/A')}")
        logger.info(f"IPC分类: {patent.get('ipc_main_class', 'N/A')}")

        if patent.get('abstract'):
            logger.info(f"\n摘要: {patent['abstract'][:200]}...")

    def display_patent_full(self, patent_full: Dict):
        """显示专利完整信息"""
        patent = patent_full.get('brief', {})
        full_text = patent_full.get('full_text', {})

        self.display_patent_brief(patent)

        if full_text:
            logger.info(f"\n{'='*60}")
            logger.info('【完整信息】')
            logger.info(f"Google专利链接: {patent_full.get('google_patent_url', 'N/A')}")

            if full_text.get('description'):
                logger.info(f"\n说明书（前500字）:")
                logger.info(str(full_text['description'][:500] + '...'))

            if patent_full.get('family_members'):
                logger.info(f"\n专利族成员 ({len(patent_full['family_members'])}):")
                for i, member in enumerate(patent_full['family_members'][:5], 1):
                    logger.info(f"  {i}. {member.get('title', 'N/A')[:50]}...")

            if patent_full.get('citations'):
                logger.info(f"\n引用文献 ({len(patent_full['citations'])}):")
                for i, citation in enumerate(patent_full['citations'][:5], 1):
                    logger.info(f"  {i}. {citation.get('title', 'N/A')[:50]}...")

        logger.info(f"\n获取时间: {patent_full.get('fetch_time', 'N/A'):.2f}秒")
        if patent_full.get('from_cache'):
            logger.info('来源: 缓存')
        else:
            logger.info('来源: 实时获取')

    def export_to_csv(self, patents: List[Dict], filename: str, include_full_text: bool = False):
        """导出到CSV文件"""
        if not patents:
            logger.info('没有数据可导出')
            return

        # 准备CSV字段
        fieldnames = [
            'id', 'patent_name', 'applicant', 'inventor',
            'application_number', 'application_date', 'publication_number',
            'ipc_main_class', 'patent_type', 'abstract'
        ]

        if include_full_text:
            fieldnames.extend([
                'full_title', 'full_abstract', 'claims',
                'description', 'google_patent_url'
            ])

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for patent_info in patents:
                row = patent_info.get('brief', patent_info)

                # 基本字段
                csv_row = {field: row.get(field, '') for field in fieldnames[:10]}

                # 全文字段
                if include_full_text and patent_info.get('full_text'):
                    full_text = patent_info['full_text']
                    csv_row.update({
                        'full_title': full_text.get('title', ''),
                        'full_abstract': full_text.get('abstract', ''),
                        'claims': full_text.get('claims', ''),
                        'description': full_text.get('description', ''),
                        'google_patent_url': patent_info.get('google_patent_url', '')
                    })

                writer.writerow(csv_row)

        logger.info(f"导出完成: {filename}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='专利全文检索客户端')

    # 搜索参数
    parser.add_argument('--search', '-s', help='搜索关键词')
    parser.add_argument('--applicant', '-a', help='申请人')
    parser.add_argument('--ipc', help='IPC分类号')
    parser.add_argument('--year', type=int, help='申请年份')
    parser.add_argument('--year-start', type=int, help='起始年份')
    parser.add_argument('--year-end', type=int, help='结束年份')
    parser.add_argument('--type', help='专利类型')
    parser.add_argument('--limit', type=int, default=20, help='返回数量')

    # 专利详情
    parser.add_argument('--detail', '-d', help='获取指定申请号的专利详情')
    parser.add_argument('--full-text', action='store_true', help='获取全文信息')

    # 相似专利
    parser.add_argument('--similar', help='查找与指定申请号相似的专利')

    # 导出功能
    parser.add_argument('--export', '-e', help='导出文件名（CSV格式）')
    parser.add_argument('--export-full', action='store_true', help='导出时包含全文')

    # 批量处理
    parser.add_argument('--batch', help='批量处理文件（每行一个申请号）')

    args = parser.parse_args()

    client = PatentFullTextClient()

    # 获取专利详情
    if args.detail:
        logger.info(f"获取专利详情: {args.detail}")
        if args.full_text:
            result = client.get_patent_full_text(args.detail)
            if result:
                client.display_patent_full(result)
            else:
                logger.info('未找到专利信息')
        else:
            # 获取简要信息
            search_result = client.search_patents(limit=1)
            if search_result.get('patents'):
                client.display_patent_brief(search_result['patents'][0])
            else:
                logger.info('未找到专利信息')
        return

    # 查找相似专利
    if args.similar:
        logger.info(f"查找相似专利: {args.similar}")
        result = client.get_similar_patents(args.similar)
        if result:
            ref_patent = result.get('reference_patent', {})
            logger.info(f"\n参考专利: {ref_patent.get('application_number', 'N/A')}")
            logger.info(f"专利类型: {ref_patent.get('patent_type', 'N/A')}")
            logger.info(f"IPC分类: {ref_patent.get('ipc_main_class', 'N/A')}")

            similar_patents = result.get('similar_patents', [])
            logger.info(f"\n找到 {len(similar_patents)} 个相似专利:\n")

            for i, patent in enumerate(similar_patents, 1):
                logger.info(f"{i}. {patent.get('patent_name', 'N/A')}")
                logger.info(f"   申请号: {patent.get('application_number', 'N/A')}")
                logger.info(f"   申请人: {patent.get('applicant', 'N/A')}\n")
        return

    # 批量处理
    if args.batch:
        logger.info(f"批量处理文件: {args.batch}")
        try:
            with open(args.batch, 'r', encoding='utf-8') as f:
                application_numbers = [line.strip() for line in f if line.strip()]

            logger.info(f"共 {len(application_numbers)} 个专利申请号")

            if args.full_text:
                # 批量获取全文
                result = client.batch_get_full_text(application_numbers)
                logger.info(f"任务ID: {result.get('task_id', 'N/A')}")
                logger.info('批量任务已启动，请稍后查看 outputs/ 目录中的结果文件')
            else:
                # 获取简要信息
                all_patents = []
                for app_num in application_numbers:
                    search_result = client.search_patents(limit=1)
                    if search_result.get('patents'):
                        all_patents.append(search_result['patents'][0])
                    time.sleep(0.1)  # 避免过于频繁的请求

                if args.export:
                    client.export_to_csv(all_patents, args.export)
                else:
                    for patent in all_patents:
                        client.display_patent_brief(patent)

        except FileNotFoundError:
            logger.info(f"文件不存在: {args.batch}")
        except Exception as e:
            logger.info(f"批量处理失败: {e}")
        return

    # 搜索专利
    if args.search or args.applicant or args.ipc or args.year or args.year_start or args.year_end or args.type:
        logger.info('搜索专利...')
        result = client.search_patents(
            keyword=args.search,
            applicant=args.applicant,
            ipc_class=args.ipc,
            year=args.year,
            year_start=args.year_start,
            year_end=args.year_end,
            patent_type=args.type,
            limit=args.limit
        )

        if result:
            total = result.get('total', 0)
            patents = result.get('patents', [])
            query_time = result.get('query_time', 0)

            logger.info(f"\n找到 {total} 条专利，用时 {query_time:.2f} 秒")
            logger.info(f"显示前 {len(patents)} 条:\n")

            for i, patent in enumerate(patents, 1):
                logger.info(f"{i}. {patent.get('patent_name', 'N/A')}")
                logger.info(f"   申请号: {patent.get('application_number', 'N/A')}")
                logger.info(f"   申请人: {patent.get('applicant', 'N/A')}")
                logger.info(f"   摘要: {patent.get('abstract', 'N/A')[:100]}...\n")

            # 导出功能
            if args.export:
                if args.full_text:
                    # 获取所有专利的全文
                    logger.info("\n正在获取全文信息，这可能需要一些时间...")
                    app_numbers = [p['application_number'] for p in patents]

                    full_patents = []
                    for app_num in app_numbers:
                        full_result = client.get_patent_full_text(app_num)
                        if full_result:
                            full_patents.append(full_result)
                        time.sleep(1)  # 延时避免请求过频

                    client.export_to_csv(full_patents, args.export, include_full_text=True)
                else:
                    client.export_to_csv(patents, args.export)
        else:
            logger.info('搜索失败')
        return

    # 如果没有指定任何操作，显示帮助
    parser.print_help()

if __name__ == '__main__':
    main()