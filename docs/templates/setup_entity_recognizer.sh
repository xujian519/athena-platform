#!/bin/bash

# 专利实体识别器快速安装脚本
# Patent Entity Recognizer Quick Setup Script

echo "=========================================="
echo "专利实体识别器快速安装"
echo "Quick Setup for Patent Entity Recognizer"
echo "=========================================="

# 检查Python版本
echo "1. 检查Python版本..."
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
required_version="3.7"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python版本过低，需要3.7或更高版本"
    echo "当前版本: Python $python_version"
    exit 1
else
    echo "✅ Python版本检查通过: Python $python_version"
fi

# 创建虚拟环境（可选）
echo ""
echo "2. 创建虚拟环境（可选）..."
read -p "是否创建虚拟环境？(y/n): " create_venv

if [ "$create_venv" = "y" ] || [ "$create_venv" = "Y" ]; then
    python3 -m venv patent_entity_env
    source patent_entity_env/bin/activate
    echo "✅ 虚拟环境创建并激活"
fi

# 升级pip
echo ""
echo "3. 升级pip..."
pip install --upgrade pip

# 安装基础依赖
echo ""
echo "4. 安装基础依赖..."
pip install numpy

# 安装transformers（两种选择）
echo ""
echo "5. 安装transformers库..."
echo "选择安装方式："
echo "1) CPU版本（推荐用于快速开始）"
echo "2) GPU版本（如果有NVIDIA GPU）"
echo "3) 跳过（仅使用规则识别）"

read -p "请选择 (1/2/3): " install_choice

case $install_choice in
    1)
        echo "安装CPU版本的transformers..."
        pip install transformers torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
        echo "✅ CPU版本transformers安装完成"
        ;;
    2)
        echo "安装GPU版本的transformers..."
        # 检查是否有CUDA
        if command -v nvidia-smi &> /dev/null; then
            echo "检测到NVIDIA GPU"
            pip install transformers torch torchvision torchaudio
            echo "✅ GPU版本transformers安装完成"
        else
            echo "⚠️  未检测到CUDA，切换到CPU版本"
            pip install transformers torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
            echo "✅ CPU版本transformers安装完成"
        fi
        ;;
    3)
        echo "跳过transformers安装，将仅使用规则识别"
        ;;
    *)
        echo "无效选择，默认安装CPU版本"
        pip install transformers torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
        echo "✅ CPU版本transformers安装完成"
        ;;
esac

# 创建必要的目录
echo ""
echo "6. 创建工作目录..."
mkdir -p entity_recognizer_output
mkdir -p entity_recognizer_models
echo "✅ 工作目录创建完成"

# 下载BERT模型（可选）
echo ""
echo "7. 下载BERT模型（可选）..."
read -p "是否下载中文BERT模型？(y/n): " download_model

if [ "$download_model" = "y" ] || [ "$download_model" = "Y" ]; then
    echo "正在下载中文BERT模型..."
    python3 -c "
from transformers import AutoTokenizer, AutoModelForTokenClassification
model_name = 'ckiplab/bert-base-chinese-ner'
print(f'下载模型: {model_name}')
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForTokenClassification.from_pretrained(model_name)
print('✅ 模型下载完成')
"
fi

# 创建测试脚本
echo ""
echo "8. 创建测试脚本..."
cat > test_entity_recognizer.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利实体识别器测试脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from quick_start_entity_recognizer import QuickStartEntityRecognizer

def test():
    print("开始测试专利实体识别器...")
    print("-" * 50)

    # 创建识别器
    recognizer = QuickStartEntityRecognizer()

    # 测试文本
    test_text = """1、一种铜铝复合阳极母线，包括母线本体（1），其特征在于：所述母线本体（1）与导杆（6）的接触区域设置有凹槽（2），所述凹槽（2）内固定设置有接触铜板（4），所述接触铜板（4）与母线本体（1）表面平齐，所述接触铜板（4）宽度方向大于导杆（6）宽度。"""

    # 识别实体
    entities = recognizer.recognize_entities(test_text)

    print(f"\n识别到 {len(entities)} 个实体:")
    print("=" * 50)

    for i, entity in enumerate(entities, 1):
        print(f"{i}. 文本: {entity.text}")
        print(f"   类型: {entity.label}")
        print(f"   位置: {entity.start}-{entity.end}")
        print(f"   置信度: {entity.confidence:.2f}")
        print(f"   来源: {entity.source}")
        if entity.attributes:
            print(f"   属性: {entity.attributes}")
        print()

    # 保存结果
    import json
    from datetime import datetime

    result = {
        "test_time": datetime.now().isoformat(),
        "text": test_text,
        "entities": [
            {
                "text": e.text,
                "label": e.label,
                "start": e.start,
                "end": e.end,
                "confidence": e.confidence,
                "source": e.source,
                "attributes": e.attributes
            }
            for e in entities
        ]
    }

    output_file = "entity_recognizer_output/test_result.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"✅ 测试完成！结果已保存到: {output_file}")

if __name__ == "__main__":
    test()
EOF

    echo "✅ 测试脚本创建完成"

# 创建使用说明
echo ""
echo "9. 创建使用说明..."
cat > README_EntityRecognizer.md << 'EOF'
# 专利实体识别器使用说明

## 快速开始

### 1. 基本使用
```python
from quick_start_entity_recognizer import QuickStartEntityRecognizer

# 创建识别器
recognizer = QuickStartEntityRecognizer()

# 识别实体
text = "1、一种铜铝复合阳极母线，包括母线本体（1）..."
entities = recognizer.recognize_entities(text)

# 查看结果
for entity in entities:
    print(f"{entity.text} [{entity.label}]")
```

### 2. 批量处理
```python
texts = ["专利文本1", "专利文本2", "专利文本3"]
batch_results = recognizer.batch_recognize(texts)
```

### 3. 导出结果
```python
# JSON格式
json_output = recognizer.export_entities(entities, "json")

# CSV格式
csv_output = recognizer.export_entities(entities, "csv")
```

## 功能特点

- ✅ 规则识别：准确率高，无需训练
- ✅ BERT识别：智能识别，处理复杂语境
- ✅ 多实体类型：部件、材料、位置、结构、参数等
- ✅ 属性提取：自动提取附图标记、数值、单位等
- ✅ 结果融合：智能合并多识别器结果

## 安装要求

- Python 3.7+
- transformers库（BERT模型）
- numpy

## 使用技巧

1. **附图标记**：自动识别（1）、（2）等标记
2. **数值参数**：自动识别10mm、25℃等数值
3. **材料识别**：识别铜、铝、钢等材料
4. **批量处理**：适合处理大量专利文本

## 输出格式

JSON格式包含：
- 实体文本、类型、位置
- 置信度和来源
- 实体属性
- 统计信息
EOF

    echo "✅ 使用说明创建完成"

# 完成安装
echo ""
echo "=========================================="
echo "安装完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 运行测试: python3 test_entity_recognizer.py"
echo "2. 查看使用说明: cat README_EntityRecognizer.md"
echo "3. 开始使用: from quick_start_entity_recognizer import QuickStartEntityRecognizer"
echo ""
echo "输出目录: entity_recognizer_output/"

# 运行测试
echo ""
echo "是否立即运行测试？(y/n):"
read -p "选择: " run_test

if [ "$run_test" = "y" ] || [ "$run_test" = "Y" ]; then
    echo ""
    echo "运行测试..."
    python3 test_entity_recognizer.py
fi

echo ""
echo "🎉 安装脚本执行完成！"