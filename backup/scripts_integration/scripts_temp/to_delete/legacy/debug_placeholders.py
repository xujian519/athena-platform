#!/usr/bin/env python3
"""
调试占位符问题
"""

import logging
import re

logger = logging.getLogger(__name__)

def debug_placeholders():
    """调试占位符问题"""
    sql = """
                INSERT INTO patents (
                    patent_name, patent_type, application_number, application_date,
                    publication_number, publication_date, authorization_number,
                    authorization_date, applicant, applicant_type, applicant_address,
                    applicant_region, applicant_city, applicant_district,
                    current_assignee, current_assignee_address, assignee_type,
                    credit_code, inventor, ipc_code, ipc_main_class,
                    ipc_classification, abstract, claims_content, claims,
                    citation_count, cited_count, self_citation_count,
                    other_citation_count, cited_by_self_count, cited_by_others_count,
                    family_citation_count, family_cited_count,
                    source_year, source_file, file_hash
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """

    # 提取VALUES部分
    values_start = sql.find('VALUES (') + 8
    values_end = sql.find(')', values_start)
    values_part = sql[values_start:values_end]

    logger.info('VALUES部分分析:')
    logger.info(str(values_part))
    logger.info("\n每个占位符:")

    # 分割并编号
    parts = values_part.split(',')
    placeholder_count = 0
    for i, part in enumerate(parts):
        part = part.strip()
        if '%s' in part:
            placeholder_count += 1
            logger.info(f"  第{placeholder_count}个: {part}")
        else:
            logger.info(f"  (非占位符): {part}")

    logger.info(f"\n总占位符数: {placeholder_count}")

    # 创建正确的VALUES部分
    correct_values = ', '.join(['%s'] * 36)
    logger.info(f"\n正确的VALUES部分应该是:")
    logger.info(f"  ({correct_values})")

if __name__ == '__main__':
    debug_placeholders()