#!/usr/bin/env python3
"""
使用统一LLM管理器和小娜的专业提示词系统重新撰写专利申请文件
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

async def rewrite_patent_with_llm():
    """使用统一LLM管理器重新撰写专利申请"""

    print("="*70)
    print("🌟 小娜·天秤女神 - 专利申请撰写助手")
    print("="*70)
    print()

    try:
        # 导入统一LLM管理器
        from core.llm.unified_llm_manager import UnifiedLLMManager

        print("🔧 正在初始化LLM管理器...")
        llm_manager = UnifiedLLMManager()
        await llm_manager.initialize()
        print("✅ LLM管理器已初始化\n")

        # 构建专业提示词
        patent_prompt = """你是一位资深的专利代理人，拥有20年的专利申请撰写经验。请为发明人李艳撰写"滴灌带防堵塞自清洁装置"的实用新型专利申请文件。

# 发明人信息
- 发明人：李艳
- 身份证号：372325197904023645
- 联系地址：山东省沾化县黄升乡中心路4号6排16号
- 申请日期：2026年3月5日

# 最接近的现有技术（对比文件）

## CN223026867U - 滴灌过滤器
- 申请人：河北碧源水务工程设备有限公司
- 公开日：2024年
- 技术特征：采用石英砂滤料+可更换滤筒+人工拆卸清洗
- 主要缺陷：
  1. 过滤精度不足（约0.1mm），无法有效过滤<0.03mm的细颗粒
  2. 无自清洁功能，需人工拆卸更换滤芯，劳动强度大
  3. 维护时需停机，影响灌溉作业连续性

## CN201760177U - 具有反冲洗功能的滴灌过滤器
- 技术特征：采用并联滤网+电控反冲系统
- 主要缺陷：
  1. 需要电动阀门、控制器、传感器等电子元件
  2. 需要外部电源供电，增加了系统复杂性
  3. 滤网精度有限（0.125-0.18mm），仍无法过滤细颗粒

# 本发明技术方案

## 发明名称
滴灌带防堵塞自清洁装置

## 核心创新点（三重组合创新）
本发明采用了以下三重创新组合（现有技术中未发现此组合）：

1. **PE烧结滤芯**（0.02mm精度）
   - 材质：超高分子量聚乙烯（UHMWPE）烧结成型
   - 过滤精度：0.02mm
   - 孔隙率：40-50%
   - 可截留>95%的<0.03mm细颗粒悬浮物

2. **纯机械压差触发机构**
   - 弹性膜片：丁腈橡胶，厚度1.5mm
   - 设定弹簧：不锈钢压缩弹簧
   - 触发阈值：0.1MPa（可调范围0.08-0.15MPa）
   - 联动杆：连接膜片和反冲阀
   - 完全机械式，无需电子元件或外部电源

3. **自动反冲执行机构**
   - 反冲阀：液动/水力驱动阀
   - 反冲水源：利用出水口压力反向冲刷
   - 反冲时间：10-15秒
   - 杂质沉积腔：锥形结构，便于杂质集中

## 技术效果
- 过滤精度：0.02mm（比现有技术提升5-9倍）
- 维护频次：每年1-2次（比现有技术降低50倍）
- 能耗需求：零能耗（无需外部电源）
- 滤芯寿命：3-5年（比现有技术提升3倍）

# 撰写要求

请按照以下结构撰写完整的专利申请文件（使用Markdown格式）：

## 一、发明名称

## 二、技术领域

## 三、背景技术
（请包含现有技术对比表格，详细分析CN223026867U和CN201760177U的技术特征和缺陷）

## 四、发明内容
### 4.1 要解决的技术问题
### 4.2 技术方案
（请详细描述以下部件的结构和连接关系）
- 主体壳体
- 进水口、出水口、排污口
- 粗过滤单元（100目不锈钢滤网）
- PE烧结滤芯（0.02mm精度）
- 纯机械压差触发机构（弹性膜片、弹簧、联动杆）
- 自动反冲机构（反冲阀、反冲水管）
- 杂质沉积腔（锥形结构）

### 4.3 有益效果
（请与现有技术进行详细对比，用表格形式展示）

## 五、附图说明
（请描述8张附图：图1-整体结构、图2-多级过滤、图3-滤芯微观结构、图4-压差触发机构、图5-正常过滤状态、图6-自动反冲状态、图7-压差特性曲线、图8-杂质沉积腔）

## 六、具体实施方式
（请提供3个实施例：基本型、增强型、并联扩展型）

## 七、权利要求书
（请撰写1项独立权利要求和若干从属权利要求）

## 八、与对比文件的区别特征
（请详细说明本发明与CN223026867U和CN201760177U的区别）

# 注意事项
1. 语言风格：专业、严谨、准确，符合专利申请要求
2. 技术描述：详细、具体，便于本领域技术人员实施
3. 创造性分析：明确指出"三重组合创新"在现有技术中未发现
4. 保护范围：合理设置权利要求边界，既保护核心创新，又避免保护范围过窄
5. 突出优势：强调"零能耗、高精度、免维护"的三大核心优势

请开始撰写完整的专利申请文件。"""

        print("📝 正在通过LLM生成专利申请文件...")
        print("-"*70)

        # 调用LLM生成专利申请
        messages = [
            {"role": "user", "content": patent_prompt}
        ]

        response = await llm_manager.generate(
            messages=messages,
            model="claude-3-5-sonnet-20241022",
            temperature=0.3,
            max_tokens=8000
        )

        print()
        print("="*70)
        print("✅ 专利申请撰写完成")
        print("="*70)
        print()

        # 保存结果
        output_dir = Path("/Users/xujian/工作/01_客户管理/01_正式客户/李艳/滴灌带防堵塞自清洁装置")
        output_dir.mkdir(parents=True, exist_ok=True)

        # 保存专利说明书
        spec_file = output_dir / "滴灌带防堵塞自清洁装置_专利说明书_小娜版.md"
        with open(spec_file, 'w', encoding='utf-8') as f:
            f.write(response)
        print(f"📄 专利说明书已保存: {spec_file}")

        print()
        print("📊 撰写统计:")
        print(f"  - 总字数: {len(response)} 字")
        paragraph_delimiter = '\n\n'
        print(f"  - 段落数: {len([p for p in response.split(paragraph_delimiter) if p.strip()])} 段")

        # 关闭LLM管理器
        await llm_manager.shutdown()
        print()
        print("✅ 专利申请撰写任务完成")

    except Exception as e:
        print(f"❌ 任务执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = asyncio.run(rewrite_patent_with_llm())
    sys.exit(0 if success else 1)
