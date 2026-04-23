#!/usr/bin/env python3
"""
添加专利测试数据到PostgreSQL数据库

创建并插入一些真实的专利数据用于测试检索功能。

作者: Athena平台团队
创建时间: 2026-04-20
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, '.')

import logging

import psycopg2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 数据库配置（使用docker-compose中的athena数据库）
DB_CONFIG = {
    'host': 'localhost',
    'port': 15432,  # docker-compose映射的端口
    'database': 'athena',
    'user': 'athena',
    'password': 'athena_password_change_me'
}


# 测试专利数据
PATENT_DATA = [
    {
        'patent_id': 'CN123456789A',
        'title': '一种基于深度学习的图像识别方法',
        'abstract': '本发明公开了一种基于深度卷积神经网络的图像识别方法，包括特征提取层、卷积层、池化层和全连接层。该方法通过多尺度特征融合技术，提高了图像识别的准确率和鲁棒性。可应用于人脸识别、物体检测、场景分类等领域。',
        'claims': '1. 一种基于深度学习的图像识别方法，其特征在于，包括：输入层，用于接收待识别图像；卷积层，用于提取图像特征；池化层，用于降维和特征选择；全连接层，用于分类识别；输出层，输出识别结果。',
        'applicant': '北京大学',
        'inventor': '张三;李四;王五',
        'publication_date': '2023-05-15',
        'ipc_codes': 'G06K;G06N',
        'status': 'granted'
    },
    {
        'patent_id': 'CN987654321B',
        'title': '自动驾驶车辆路径规划系统及方法',
        'abstract': '本发明涉及一种自动驾驶车辆的路径规划系统，包括环境感知模块、路径决策模块和运动控制模块。环境感知模块通过激光雷达、摄像头和毫米波雷达获取车辆周围环境信息；路径决策模块采用改进的A*算法，结合实时交通信息和道路约束条件，生成最优路径；运动控制模块通过PID控制器实现车辆的精确跟踪。',
        'claims': '1. 一种自动驾驶车辆路径规划系统，包括：环境感知单元，用于采集车辆周围的环境数据；路径规划单元，用于根据环境数据生成行驶路径；运动控制单元，用于控制车辆沿路径行驶；其特征在于，所述路径规划单元采用改进的A*算法，引入启发式函数h(n) = g(n) + w*h(n)，其中w为动态权重系数。',
        'applicant': '百度在线网络技术（北京）有限公司',
        'inventor': '赵六;钱七;孙八',
        'publication_date': '2023-08-20',
        'ipc_codes': 'G05D;G01C',
        'status': 'pending'
    },
    {
        'patent_id': 'CN112233445C',
        'title': '人工智能专利检索方法及系统',
        'abstract': '本发明公开了一种基于语义理解和知识图谱的智能专利检索方法。该方法包括：构建专利知识图谱，其中节点表示专利实体，边表示实体间关系；对用户查询进行语义分析，提取查询意图和关键信息；利用图神经网络在专利知识图谱上进行推理，找到相关专利；对检索结果进行排序和过滤。本发明提高了专利检索的准确性和效率。',
        'claims': '1. 一种人工智能专利检索方法，包括以下步骤：构建多维专利知识图谱，所述知识图谱包含专利节点、技术节点、申请人节点和引用关系节点；接收用户查询，使用自然语言处理技术提取查询中的技术特征；在知识图谱上执行图遍历算法，找到与查询特征相关的专利子图；根据相关性得分对检索结果进行排序。',
        'applicant': '上海智星科技有限公司',
        'inventor': '周九;吴十;郑十一',
        'publication_date': '2023-11-10',
        'ipc_codes': 'G06F;G06N',
        'status': 'granted'
    },
    {
        'patent_id': 'CN445566778D',
        'title': '基于区块链的知识产权保护系统',
        'abstract': '本发明涉及一种基于区块链技术的知识产权保护系统和方法。系统包括：知识产权登记模块，用于记录知识产权信息到区块链；时间戳服务模块，为知识产权创建不可篡改的时间戳；智能合约模块，自动执行知识产权许可协议；监控模块，实时监控知识产权使用情况。本发明解决了传统知识产权保护中确权难、维权难的问题。',
        'claims': '1. 一种基于区块链的知识产权保护系统，其特征在于，包括：区块链网络，由多个节点组成；知识产权登记模块，将知识产权信息加密后存储到区块链上；智能合约引擎，预置多种知识产权许可场景；数字身份认证模块，用于验证用户身份。',
        'applicant': '深圳区块链技术有限公司',
        'inventor': '王十二;李十三',
        'publication_date': '2023-09-05',
        'ipc_codes': 'G06F;H04L',
        'status': 'pending'
    },
    {
        'patent_id': 'CN556677889E',
        'title': '机器学习模型的压缩与优化方法',
        'abstract': '本发明公开了一种深度神经网络模型的压缩和优化方法。该方法包括：模型剪枝步骤，移除网络中冗余的连接；知识蒸馏步骤，使用轻量级教师模型指导学生模型训练；量化压缩步骤，将模型权重从32位浮点数压缩到8位整数；硬件加速步骤，针对特定硬件平台进行指令级优化。通过上述方法，可将模型大小减少80%以上，同时保持精度损失小于1%。',
        'claims': '1. 一种机器学习模型的压缩方法，包括：结构剪枝步骤，使用L1正则化方法训练模型，剪枝权重小于阈值的连接；知识蒸馏步骤，使用预训练的教师模型对剪枝后的学生模型进行知识迁移；混合精度量化步骤，对模型的不同层使用不同位宽的量化；硬件感知优化步骤，针对目标硬件平台编译优化指令。',
        'applicant': '阿里巴巴集团控股有限公司',
        'inventor': '陈十四;林十五;黄十六',
        'publication_date': '2023-12-01',
        'ipc_codes': 'G06N;G06F',
        'status': 'granted'
    },
    {
        'patent_id': 'CN667788001F',
        'title': '自然语言处理中的情感分析方法',
        'abstract': '本发明涉及一种基于注意力机制和预训练语言模型的情感分析方法。该方法包括：文本预处理步骤，进行分词、去停用词和词性标注；特征提取步骤，使用双向LSTM和多头注意力机制捕获文本的上下文信息；情感分类步骤，通过全连接层输出情感极性和强度。本发明在电商评论分析、舆情监控、客户反馈等领域具有广泛应用价值。',
        'claims': '1. 一种自然语言处理情感分析方法，包括：获取待分析文本；对文本进行分词和词向量嵌入；使用双向长短期记忆网络（BiLSTM）提取文本序列特征；应用多头注意力机制，为不同词分配不同的权重；通过softmax分类器输出情感分类结果。',
        'applicant': '腾讯科技（深圳）有限公司',
        'inventor': '张十七;刘十八;杨十九',
        'publication_date': '2023-07-25',
        'ipc_codes': 'G10L;G06N',
        'status': 'granted'
    },
    {
        'patent_id': 'CN778899012G',
        'title': '量子计算加密通信系统',
        'abstract': '本发明公开了一种基于量子密钥分发的安全通信系统。系统包括：量子密钥生成模块，基于量子纠缠效应生成随机密钥；量子密钥分发模块，通过量子信道将密钥安全传输给通信双方；加密通信模块，使用量子密钥对通信内容进行加密；密钥管理模块，负责密钥的存储、更新和销毁。本发明利用量子力学原理保证了密钥分发的无条件安全性。',
        'claims': '1. 一种量子计算加密通信系统，包括：量子密钥源，用于产生纠缠光子对；量子信道，用于传输纠缠光子；经典信道，用于传输辅助信息；量子密钥提取模块，从纠缠光子中提取密钥；加密通信模块，使用提取的量子密钥进行对称加密通信。',
        'applicant': '中国科学技术大学',
        'inventor': '周二十;吴二十一;郑二十二',
        'publication_date': '2023-10-30',
        'ipc_codes': 'H04L;G09C',
        'status': 'pending'
    },
    {
        'patent_id': 'CN889900123H',
        'title': '计算机视觉中的目标跟踪算法',
        'abstract': '本发明涉及一种基于深度学习和卡尔曼滤波的多目标跟踪算法。该算法包括：目标检测模块，使用YOLOv5算法实时检测视频帧中的目标；特征提取模块，提取目标的视觉特征和运动特征；数据关联模块，使用匈牙利算法解决目标匹配问题；轨迹预测模块，使用扩展卡尔曼滤波器预测目标运动轨迹。本发明解决了复杂场景下的目标遮挡、快速运动和尺度变化等问题。',
        'claims': '1. 一种计算机视觉目标跟踪算法，其特征在于，包括以下步骤：使用YOLOv5检测器对视频帧进行目标检测，生成边界框；提取检测到的目标的Re-ID特征；使用卡尔曼滤波器预测目标的下一帧位置；计算检测位置和预测位置之间的距离矩阵；使用匈牙利算法进行最优匹配，实现目标关联。',
        'applicant': '商汤科技有限公司',
        'inventor': '陈二十三;林二十四;黄二十五',
        'publication_date': '2023-06-15',
        'ipc_codes': 'G06T;G06N',
        'status': 'granted'
    },
    {
        'patent_id': 'CN990011234I',
        'title': '智能推荐系统的多任务学习优化方法',
        'abstract': '本发明公开了一种基于多任务学习的智能推荐系统优化方法。该方法将用户兴趣建模、物品特征提取和推荐列表排序作为联合任务进行优化，共享底层表示学习。通过引入元学习机制，系统能够快速适应新用户和新物品的冷启动问题。本发明显著提高了推荐准确度和用户满意度，适用于电商、视频、音乐等多种推荐场景。',
        'claims': '1. 一种智能推荐系统的多任务学习优化方法，包括：构建用户行为序列特征，记录用户的浏览、点击、购买行为；构建物品内容特征，提取物品的文本、图像、类别信息；设计多任务神经网络，同时优化点击率预测和停留时长预测；使用梯度平衡策略，动态调整不同任务的损失权重。',
        'applicant': '北京字节跳动科技有限公司',
        'inventor': '张二十六;李二十七;王二十八',
        'publication_date': '2023-04-20',
        'ipc_codes': 'G06N;G06Q',
        'status': 'granted'
    },
    {
        'patent_id': 'CN101122334J',
        'title': '语音识别中的端到端建模方法',
        'abstract': '本发明涉及一种基于Transformer架构的端到端自动语音识别方法。该方法将声学模型、语言模型和对齐模型统一到一个端到端神经网络中，无需单独训练各个组件。通过引入自监督学习预训练和大规模标注数据微调，该方法在低资源语言和口音识别方面表现出色。可应用于语音助手、实时转写、会议记录等场景。',
        'claims': '1. 一种端到端语音识别方法，包括：收集音频信号并进行预处理；使用卷积神经网络提取声学特征；使用Transformer编码器建模序列依赖关系；通过连接时序分类器（CTC）解码输出文本序列；使用转移学习技术，将预训练模型适配到目标领域。',
        'applicant': '科大讯飞股份有限公司',
        'inventor': '赵二十九;钱三十;孙三十一',
        'publication_date': '2023-08-10',
        'ipc_codes': 'G10L;G06N',
        'status': 'granted'
    }
]


def create_patents_table():
    """创建patents表（如果不存在）"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        # 创建patents表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patents (
                id SERIAL PRIMARY KEY,
                patent_id VARCHAR(50) UNIQUE NOT NULL,
                title TEXT NOT NULL,
                abstract TEXT,
                claims TEXT,
                applicant VARCHAR(200),
                inventor TEXT,
                publication_date DATE,
                ipc_codes VARCHAR(200),
                status VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 创建全文搜索索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_patents_title_gin
            ON patents USING GIN(to_tsvector('simple', title));
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_patents_abstract_gin
            ON patents USING GIN(to_tsvector('simple', abstract));
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_patents_patent_id_btree
            ON patents(patent_id);
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_patents_applicant_btree
            ON patents(applicant);
        """)

        conn.commit()
        logger.info("✅ patents表和索引创建成功")

    except Exception as e:
        logger.error(f"❌ 创建表失败: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


def insert_patent_data():
    """插入专利测试数据"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        # 检查现有数据
        cursor.execute("SELECT COUNT(*) FROM patents;")
        count = cursor.fetchone()[0]
        logger.info(f"📊 当前数据库中有 {count} 条专利记录")

        # 插入测试数据
        inserted = 0
        for patent in PATENT_DATA:
            try:
                cursor.execute("""
                    INSERT INTO patents
                    (patent_id, title, abstract, claims, applicant, inventor,
                     publication_date, ipc_codes, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (patent_id) DO NOTHING;
                """, (
                    patent['patent_id'],
                    patent['title'],
                    patent['abstract'],
                    patent['claims'],
                    patent['applicant'],
                    patent['inventor'],
                    patent['publication_date'],
                    patent['ipc_codes'],
                    patent['status']
                ))
                inserted += 1
                logger.info(f"✅ 插入专利: {patent['patent_id']} - {patent['title'][:30]}...")
            except Exception as e:
                logger.warning(f"⚠️  插入专利失败 {patent['patent_id']}: {e}")

        conn.commit()
        logger.info(f"✅ 成功插入 {inserted} 条专利数据")

        # 验证插入结果
        cursor.execute("SELECT COUNT(*) FROM patents;")
        new_count = cursor.fetchone()[0]
        logger.info(f"📊 数据库中现有 {new_count} 条专利记录")

        return new_count

    except Exception as e:
        logger.error(f"❌ 插入数据失败: {e}")
        conn.rollback()
        return 0
    finally:
        cursor.close()
        conn.close()


def verify_fulltext_search():
    """验证全文搜索功能"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        # 测试中文全文搜索
        test_queries = [
            "人工智能",
            "深度学习",
            "自动驾驶",
            "区块链",
            "机器学习"
        ]

        print("\n" + "=" * 80)
        print("🔍 验证全文搜索功能")
        print("=" * 80)

        for query in test_queries:
            cursor.execute("""
                SELECT patent_id, title,
                       ts_rank(to_tsvector('simple', title), to_tsquery('simple', %s)) AS rank
                FROM patents
                WHERE title % %s
                ORDER BY rank DESC
                LIMIT 3;
            """, (query, query))

            results = cursor.fetchall()
            print(f"\n查询: '{query}'")
            if results:
                for rank, (patent_id, title, _relevance) in enumerate(results[:3], 1):
                    print(f"  {rank}. [{patent_id}] {title}")
            else:
                print("  未找到结果")

        conn.commit()

    except Exception as e:
        logger.error(f"❌ 全文搜索验证失败: {e}")
    finally:
        cursor.close()
        conn.close()


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("📝 添加专利测试数据")
    print("=" * 80)

    print("\n数据库配置:")
    print(f"  主机: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"  数据库: {DB_CONFIG['database']}")
    print(f"  用户: {DB_CONFIG['user']}")
    print()

    # 步骤1: 创建表
    print("步骤1: 创建patents表和索引...")
    create_patents_table()

    # 步骤2: 插入数据
    print("\n步骤2: 插入专利测试数据...")
    total_count = insert_patent_data()

    # 步骤3: 验证全文搜索
    if total_count > 0:
        print("\n步骤3: 验证全文搜索功能...")
        verify_fulltext_search()

    print("\n" + "=" * 80)
    print("✅ 数据添加完成！")
    print("=" * 80)

    print("\n📊 数据库统计:")
    print(f"  总专利数: {total_count}")
    print("  涵盖技术: AI, 深度学习, 自动驾驶, 区块链, 量子计算等")
    print("  申请人: 北京大学, 百度, 阿里巴巴, 腾讯, 科大讯飞等")
    print()

    print("🚀 下一步: 运行检索测试")
    print("   python3 tests/agents/test_xiaona_patent_search.py")


if __name__ == "__main__":
    main()
