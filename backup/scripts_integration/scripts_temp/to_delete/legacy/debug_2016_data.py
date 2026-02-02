#!/usr/bin/env python3
"""
调试2016年专利数据
"""

import csv
import logging
import sys

import psycopg2

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',
    'database': 'patent_db'
}

def map_patent_type(raw_type):
    """映射专利类型到标准格式"""
    if not raw_type:
        return None

    # 发明专利类型映射
    if raw_type in ['发明授权', '发明专利授权', '发明']:
        return '发明'
    elif raw_type in ['发明申请', '发明专利申请']:
        return '发明'
    elif raw_type.startswith('发明'):
        return '发明'

    # 实用新型专利类型映射
    elif raw_type in ['实用新型授权', '实用新型专利授权', '实用新型']:
        return '实用新型'
    elif raw_type in ['实用新型申请', '实用新型专利申请']:
        return '实用新型'
    elif raw_type.startswith('实用新型'):
        return '实用新型'

    # 外观设计专利类型映射
    elif raw_type in ['外观设计授权', '外观设计专利授权', '外观设计']:
        return '外观设计'
    elif raw_type in ['外观设计申请', '外观设计专利申请']:
        return '外观设计'
    elif raw_type.startswith('外观设计'):
        return '外观设计'

    # 如果无法识别，返回None以避免约束错误
    return None

def debug_data(year=2016):
    """调试数据"""
    file_path = f"/Volumes/xujian/patent_data/china_patents/中国专利数据库{year}年.csv"

    try:
        with open(file_path, 'r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)

            logger.info(f"\n=== 字段信息 ===")
            logger.info(f"CSV字段数: {len(reader.fieldnames)}")
            logger.info(f"字段列表: {reader.fieldnames}")

            # 读取前5行
            for i, row in enumerate(reader):
                if i >= 5:
                    break

                logger.info(f"\n=== 第 {i+1} 行数据 ===")

                # 提取数据
                patent_name = row.get('专利名称', '').strip()
                patent_type_raw = row.get('专利类型', '').strip()
                patent_type = map_patent_type(patent_type_raw)
                applicant = row.get('申请人', '').strip()
                application_number = row.get('申请号', '').strip()

                logger.info(f"专利名称: {patent_name[:50]}...")
                logger.info(f"专利类型(原始): {patent_type_raw}")
                logger.info(f"专利类型(映射): {patent_type}")
                logger.info(f"申请人: {applicant}")
                logger.info(f"申请号: {application_number}")

                # 构建数据元组
                try:
                    data_tuple = (
                        patent_name[:1000] if patent_name else None,
                        patent_type,
                        application_number[:100] if application_number else None,
                        row.get('申请日', '').strip()[:20] if row.get('申请日') else None,
                        row.get('公开公告号', '').strip()[:50] if row.get('公开公告号') else None,
                        row.get('公开公告日', '').strip()[:20] if row.get('公开公告日') else None,
                        row.get('授权公告号', '').strip()[:50] if row.get('授权公告号') else None,
                        row.get('授权公告日', '').strip()[:20] if row.get('授权公告日') else None,
                        applicant[:500] if applicant else None,
                        row.get('申请人类型', '').strip()[:50] if row.get('申请人类型') else None,
                        row.get('申请人地址', '').strip()[:500] if row.get('申请人地址') else None,
                        row.get('申请人地区', '').strip()[:100] if row.get('申请人地区') else None,
                        row.get('申请人城市', '').strip()[:100] if row.get('申请人城市') else None,
                        row.get('申请人区县', '').strip()[:100] if row.get('申请人区县') else None,
                        row.get('当前权利人', '').strip()[:500] if row.get('当前权利人') else None,
                        row.get('当前专利权人地址', '').strip()[:500] if row.get('当前专利权人地址') else None,
                        row.get('专利权人类型', '').strip()[:50] if row.get('专利权人类型') else None,
                        row.get('统一社会信用代码', '').strip()[:50] if row.get('统一社会信用代码') else None,
                        row.get('发明人', '').strip()[:1000] if row.get('发明人') else None,
                        row.get('IPC分类号', '').strip()[:100] if row.get('IPC分类号') else None,
                        row.get('IPC主分类号', '').strip()[:20] if row.get('IPC主分类号') else None,
                        row.get('IPC分类号', '').strip()[:100] if row.get('IPC分类号') else None,
                        row.get('摘要文本', '').strip()[:5000] if row.get('摘要文本') else None,
                        row.get('主权项内容', '').strip()[:10000] if row.get('主权项内容') else None,
                        None,
                        int(float(row.get('引证次数', 0) or 0)),
                        int(float(row.get('被引证次数', 0) or 0)),
                        int(float(row.get('自引次数', 0) or 0)),
                        int(float(row.get('他引次数', 0) or 0)),
                        int(float(row.get('被自引次数', 0) or 0)),
                        int(float(row.get('被他引次数', 0) or 0)),
                        int(float(row.get('家族引证次数', 0) or 0)),
                        int(float(row.get('家族被引证次数', 0) or 0)),
                        year,
                        f'中国专利数据库{year}年.csv',
                        None
                    )

                    logger.info(f"数据元组长度: {len(data_tuple)}")

                    # 检查每个字段
                    for idx, value in enumerate(data_tuple):
                        if value is None:
                            logger.info(f"  字段 {idx+1}: None")
                        else:
                            logger.info(f"  字段 {idx+1}: {str(value)[:50]}...")

                except Exception as e:
                    logger.info(f"构建数据元组时出错: {e}")
                    import traceback
                    traceback.print_exc()

    except Exception as e:
        logger.error(f"读取文件失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_data(2016)