#!/usr/bin/env python3
"""
提取所有客户（申请人）名称
Extract All Patent Customers

遍历整个专利表，提取所有客户名称并标准化
"""

import json
import os
import re
from collections import defaultdict
from datetime import datetime

import psycopg2


class CustomerExtractor:
    """客户提取器"""

    def __init__(self):
        # PostgreSQL配置
        self.db_config = {
            "host": "localhost",
            "port": 5432,
            "database": "patent_archive",
            "user": "xujian",
            "password": ""
        }

        # 检查PostgreSQL路径
        postgres_path = "/opt/homebrew/opt/postgresql@17/bin"
        if postgres_path not in os.environ.get("PATH", ""):
            os.environ["PATH"] = postgres_path + ":" + os.environ.get("PATH", "")

    def get_connection(self):
        """获取数据库连接"""
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except Exception as e:
            print(f"❌ 数据库连接失败: {str(e)}")
            return None

    def extract_all_customer_names(self):
        """提取所有客户信息（名称、地址、联系人、电话）"""
        conn = self.get_connection()
        if not conn:
            return

        try:
            cursor = conn.cursor()

            # 查询所有专利，包含联系信息
            cursor.execute("""
                SELECT
                    patent_name as 客户名称,
                    contact_info as 联系信息,
                    archive_location as 档案存放,
                    agency as 代理机构,
                    COUNT(*) as 专利数量,
                    STRING_AGG(patent_number, ', ') as 申请号示例,
                    STRING_AGG(DISTINCT a.client_name, ', ') as 案源人
                FROM patents p
                LEFT JOIN patent_agents a ON p.agent_id = a.id
                WHERE p.patent_name IS NOT NULL
                AND p.patent_name != ''
                AND p.patent_name != 'nan'
                GROUP BY p.patent_name, p.contact_info, p.archive_location, p.agency
                ORDER BY 专利数量 DESC
            """)

            customers = cursor.fetchall()
            print(f"\n📊 总共找到 {len(customers)} 个不同的客户（申请人）\n")

            # 解析联系信息
            def parse_contact_info(contact_str):
                """解析联系信息，提取联系人、电话等"""
                if not contact_str or contact_str == 'nan':
                    return {"联系人": "", "电话": "", "其他": ""}

                # 常见的分隔符
                separators = ['，', '、', '/', '\\', '|', ';', '；']

                # 尝试分割
                parts = [contact_str]
                for sep in separators:
                    new_parts = []
                    for part in parts:
                        new_parts.extend(part.split(sep))
                    parts = new_parts

                # 提取电话号码（11位或包含特殊字符）
                phone_pattern = re.compile(r'1[3-9]\d{9}|\d{3,4}[-\s]?\d{7,8}')
                phones = []
                contacts = []
                others = []

                for part in parts:
                    part = part.strip()
                    if not part:
                        continue

                    if phone_pattern.search(part):
                        phones.append(part)
                    elif any(word in part for word in ['先生', '女士', '老师', '教授', '经理', '主任']):
                        contacts.append(part)
                    else:
                        others.append(part)

                return {
                    "联系人": '; '.join(contacts),
                    "电话": '; '.join(phones),
                    "其他": '; '.join(others)
                }

            # 分类统计并存储详细信息
            customer_details = []
            company_customers = []
            school_customers = []
            institution_customers = []
            other_customers = []

            for customer in customers:
                name = customer[0]
                contact_info = customer[1] or ""
                archive_location = customer[2] or ""
                agency = customer[3] or ""
                count = customer[4]
                patent_examples = customer[5] or ""
                agents = customer[6] or ""

                # 解析联系信息
                parsed_contact = parse_contact_info(contact_info)

                customer_detail = {
                    "客户名称": name,
                    "联系信息": contact_info,
                    "档案存放": archive_location,
                    "代理机构": agency,
                    "联系人": parsed_contact["联系人"],
                    "电话": parsed_contact["电话"],
                    "联系信息其他": parsed_contact["其他"],
                    "专利数量": count,
                    "申请号示例": patent_examples,
                    "案源人": agents
                }

                customer_details.append(customer_detail)

                # 分类
                if '公司' in name or '集团' in name or '企业' in name or '有限公司' in name or '股份' in name:
                    company_customers.append(customer_detail)
                elif '学院' in name or '大学' in name or '学校' in name:
                    school_customers.append(customer_detail)
                elif '研究所' in name or '研究院' in name or '中心' in name:
                    institution_customers.append(customer_detail)
                else:
                    other_customers.append(customer_detail)

            # 打印分类结果（包含详细信息）
            print(f"🏢 企业类客户 ({len(company_customers)}个)：")
            print("-" * 120)
            print(f"{'序号':<4} {'客户名称':<40} {'联系人':<15} {'电话':<20} {'专利数':<8}")
            print("-" * 120)
            for i, customer in enumerate(company_customers[:30], 1):
                print(f"{i:4d} {customer['客户名称'][:38]:<40} {customer['联系人'][:13]:<15} {customer['电话'][:18]:<20} {customer['专利数量']:>6}")
            if len(company_customers) > 30:
                print(f"... 还有 {len(company_customers) - 30} 个企业客户")

            print(f"\n🎓 学校类客户 ({len(school_customers)}个)：")
            print("-" * 120)
            print(f"{'序号':<4} {'客户名称':<40} {'联系人':<15} {'电话':<20} {'专利数':<8}")
            print("-" * 120)
            for i, customer in enumerate(school_customers, 1):
                print(f"{i:4d} {customer['客户名称'][:38]:<40} {customer['联系人'][:13]:<15} {customer['电话'][:18]:<20} {customer['专利数量']:>6}")

            print(f"\n🏛️  机构类客户 ({len(institution_customers)}个)：")
            print("-" * 120)
            print(f"{'序号':<4} {'客户名称':<40} {'联系人':<15} {'电话':<20} {'专利数':<8}")
            print("-" * 120)
            for i, customer in enumerate(institution_customers, 1):
                print(f"{i:4d} {customer['客户名称'][:38]:<40} {customer['联系人'][:13]:<15} {customer['电话'][:18]:<20} {customer['专利数量']:>6}")

            print(f"\n📝 其他类客户 ({len(other_customers)}个)：")
            print("-" * 120)
            print(f"{'序号':<4} {'客户名称':<40} {'联系人':<15} {'电话':<20} {'专利数':<8}")
            print("-" * 120)
            for i, customer in enumerate(other_customers[:20], 1):
                print(f"{i:4d} {customer['客户名称'][:38]:<40} {customer['联系人'][:13]:<15} {customer['电话'][:18]:<20} {customer['专利数量']:>6}")
            if len(other_customers) > 20:
                print(f"... 还有 {len(other_customers) - 20} 个其他客户")

            # 显示有联系信息的客户示例
            print("\n📞 有联系信息的客户示例：")
            print("-" * 120)
            contact_customers = [c for c in customer_details if c['联系人'] or c['电话']
            for i, customer in enumerate(contact_customers[:10], 1):
                print(f"{i:2d}. {customer['客户名称']}")
                print(f"   地址: {customer['地址']}")
                print(f"   联系人: {customer['联系人']}")
                print(f"   电话: {customer['电话']}")
                print(f"   案源人: {customer['案源人']}")
                print()

            # 保存完整列表
            all_customers = {
                "企业类客户": company_customers,
                "学校类客户": school_customers,
                "机构类客户": institution_customers,
                "其他类客户": other_customers,
                "统计信息": {
                    "总客户数": len(customers),
                    "企业类": len(company_customers),
                    "学校类": len(school_customers),
                    "机构类": len(institution_customers),
                    "其他类": len(other_customers)
                }
            }

            # 保存到JSON
            with open("all_customers.json", "w", encoding="utf-8") as f:
                json.dump(all_customers, f, ensure_ascii=False, indent=2)

            # 保存到CSV
            with open("all_customers.csv", "w", encoding="utf-8") as f:
                f.write("客户名称,专利数量,客户类型\n")
                for name, count in company_customers:
                    f.write(f'"{name}",{count},"企业"\n')
                for name, count in school_customers:
                    f.write(f'"{name}",{count},"学校"\n')
                for name, count in institution_customers:
                    f.write(f'"{name}",{count},"机构"\n')
                for name, count in other_customers:
                    f.write(f'"{name}",{count},"其他"\n')

            print("\n✅ 客户列表已保存到：")
            print("- all_customers.json (JSON格式)")
            print("- all_customers.csv (CSV格式)")

            # 分析名称变更
            print("\n🔄 分析名称变更记录...")
            self.analyze_name_changes()

            # 分析地域分布
            print("\n📍 分析地域分布...")
            self.analyze_regional_distribution()

            cursor.close()
            conn.close()

            return all_customers

        except Exception as e:
            print(f"❌ 提取失败: {str(e)}")
            return None

    def analyze_name_changes(self):
        """分析名称变更记录"""
        conn = self.get_connection()
        if not conn:
            return

        cursor = conn.cursor()

        # 查找包含变更信息的客户
        cursor.execute("""
            SELECT patent_name, COUNT(*) as count
            FROM patents
            WHERE patent_name LIKE '%（变更为：%'
               OR patent_name LIKE '%(变更为:%'
            GROUP BY patent_name
            ORDER BY count DESC
        """)

        changed_customers = cursor.fetchall()

        if changed_customers:
            print(f"\n发现 {len(changed_customers)} 个客户有名称变更记录：")
            print("-" * 100)
            for name, count in changed_customers:
                print(f"{name:<60} ({count}件)")

            # 提取变更关系
            name_changes = []
            for name, count in changed_customers:
                # 提取原始名称和变更后名称
                if '（变更为：' in name:
                    parts = name.split('（变更为：')
                elif '(变更为:' in name:
                    parts = name.split('(变更为:')
                else:
                    continue

                if len(parts) == 2:
                    original = parts[0]
                    changed = parts[1].rstrip('）').rstrip(')')
                    name_changes.append({
                        "原始名称": original,
                        "变更后名称": changed,
                        "专利数量": count,
                        "完整记录": name
                    })

            # 保存名称变更记录
            with open("customer_name_changes.json", "w", encoding="utf-8") as f:
                json.dump(name_changes, f, ensure_ascii=False, indent=2)

            print("\n名称变更关系已保存到：customer_name_changes.json")

        cursor.close()
        conn.close()

    def analyze_regional_distribution(self):
        """分析地域分布"""
        conn = self.get_connection()
        if not conn:
            return

        cursor = conn.cursor()

        # 查询所有客户
        cursor.execute("""
            SELECT patent_name, COUNT(*) as count
            FROM patents
            WHERE patent_name IS NOT NULL
            AND patent_name != ''
            GROUP BY patent_name
        """)

        customers = cursor.fetchall()
        region_stats = defaultdict(int)

        # 地域关键词映射
        region_keywords = {
            "山东省": ["山东"],
            "广东省": ["广东"],
            "北京市": ["北京"],
            "上海市": ["上海"],
            "江苏省": ["江苏", "南京"],
            "浙江省": ["浙江", "杭州"],
            "河北省": ["河北", "石家庄"],
            "河南省": ["河南", "郑州"],
            "湖北省": ["湖北", "武汉"],
            "湖南省": ["湖南", "长沙"],
            "四川省": ["四川", "成都"],
            "辽宁省": ["辽宁", "沈阳", "大连"],
            "黑龙江省": ["黑龙江", "哈尔滨"],
            "吉林省": ["吉林", "长春"],
            "安徽省": ["安徽", "合肥"],
            "福建省": ["福建", "福州", "厦门"],
            "江西省": ["江西", "南昌"],
            "广西": ["广西", "南宁"],
            "海南省": ["海南", "海口"],
            "重庆市": ["重庆"],
            "云南省": ["云南", "昆明"],
            "贵州省": ["贵州", "贵阳"],
            "陕西省": ["陕西", "西安"],
            "甘肃省": ["甘肃", "兰州"],
            "青海省": ["青海", "西宁"],
            "新疆": ["新疆", "乌鲁木齐"],
            "西藏": ["西藏", "拉萨"],
            "宁夏": ["宁夏", "银川"],
            "内蒙古": ["内蒙古", "呼和浩特"],
            "天津市": ["天津"]
        }

        # 统计地域分布
        other_count = 0
        for name, count in customers:
            matched = False
            for region, keywords in region_keywords.items():
                for keyword in keywords:
                    if keyword in name:
                        region_stats[region] += count
                        matched = True
                        break
                if matched:
                    break
            if not matched:
                other_count += count

        # 打印地域分布
        print("\n客户地域分布：")
        print("-" * 60)
        sorted_regions = sorted(region_stats.items(), key=lambda x: x[1], reverse=True)
        for region, count in sorted_regions:
            print(f"{region:<10} {count:>6} 件专利 ({count/sum(list(region_stats.values()))*100:.1f}%)")

        if other_count > 0:
            total = sum(region_stats.values())
            print(f"{'其他地区':<10} {other_count:>6} 件专利 ({other_count/(total+other_count)*100:.1f}%)")

        # 保存地域分布
        regional_data = {
            "地域分布": dict(sorted_regions),
            "其他地区": other_count,
            "统计时间": datetime.now().isoformat()
        }

        with open("customer_regional_distribution.json", "w", encoding="utf-8") as f:
            json.dump(regional_data, f, ensure_ascii=False, indent=2)

        print("\n地域分布已保存到：customer_regional_distribution.json")

        cursor.close()
        conn.close()

    def create_customer_table(self):
        """创建客户表并插入数据"""
        conn = self.get_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()

            # 创建客户表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS patent_customers (
                    id SERIAL PRIMARY KEY,
                    original_name VARCHAR(500) NOT NULL,  -- 原始名称
                    standard_name VARCHAR(200),           -- 标准化名称（待完善）
                    customer_type VARCHAR(50),            -- 客户类型
                    region VARCHAR(50),                  -- 地区
                    patent_count INTEGER DEFAULT 0,      -- 专利数量
                    has_name_change BOOLEAN DEFAULT FALSE, -- 是否有名称变更
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(original_name)
                );
            """)

            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_type ON patent_customers(customer_type);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_region ON patent_customers(region);")

            # 读取客户数据
            with open("all_customers.json", encoding="utf-8") as f:
                customers_data = json.load(f)

            # 插入数据
            for customer_type, customer_list in customers_data.items():
                if customer_type == "统计信息":
                    continue

                type_mapping = {
                    "企业类客户": "企业",
                    "学校类客户": "学校",
                    "机构类客户": "机构",
                    "其他类客户": "其他"
                }

                for name, count in customer_list:
                    # 提取地域
                    region = "其他"
                    for r, keywords in {
                        "山东": ["山东"], "广东": ["广东"], "北京": ["北京"],
                        "上海": ["上海"], "江苏": ["江苏"], "浙江": ["浙江"],
                        "河北": ["河北"], "河南": ["河南"], "湖北": ["湖北"],
                        "湖南": ["湖南"], "四川": ["四川"], "辽宁": ["辽宁"]
                    }.items():
                        if any(k in name for k in keywords):
                            region = r
                            break

                    # 检查是否有名称变更
                    has_change = '变更为：' in name or '(变更为:' in name

                    cursor.execute("""
                        INSERT INTO patent_customers
                        (original_name, customer_type, region, patent_count, has_name_change)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (original_name) DO NOTHING
                    """, (name, type_mapping.get(customer_type, "其他"), region, count, has_change))

            conn.commit()
            print("\n✅ 客户数据已导入到 patent_customers 表")

            # 显示统计
            cursor.execute("SELECT customer_type, COUNT(*), SUM(patent_count) FROM patent_customers GROUP BY customer_type")
            print("\n客户类型统计：")
            for row in cursor.fetchall():
                print(f"{row[0]}: {row[1]}个客户, {row[2]}件专利")

            cursor.close()
            conn.close()
            return True

        except Exception as e:
            print(f"❌ 创建客户表失败: {str(e)}")
            conn.rollback()
            return False
        finally:
            if conn:
                conn.close()


def main():
    """主函数"""
    extractor = CustomerExtractor()

    # 1. 提取所有客户
    customers = extractor.extract_all_customer_names()

    # 2. 创建客户表
    if customers:
        print("\n" + "="*60)
        extractor.create_customer_table()

    print("\n✅ 任务完成！")
    print("\n生成的文件：")
    print("- all_customers.json - 所有客户列表（JSON）")
    print("- all_customers.csv - 所有客户列表（CSV）")
    print("- customer_name_changes.json - 名称变更记录")
    print("- customer_regional_distribution.json - 地域分布统计")
    print("- 数据库表: patent_customers")


if __name__ == "__main__":
    main()
