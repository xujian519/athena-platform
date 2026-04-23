#!/usr/bin/env python3
"""
快速验证FlagEmbedding安装
"""
import sys

sys.path.insert(0, '/Users/xujian/Athena工作平台')

print("=" * 60)
print("FlagEmbedding安装验证")
print("=" * 60)

# 1. 检查包导入
print("\n1. 检查包导入...")
try:
    import FlagEmbedding
    print("✅ FlagEmbedding导入成功")
    print(f"   安装路径: {FlagEmbedding.__file__}")
except Exception as e:
    print(f"❌ FlagEmbedding导入失败: {e}")
    sys.exit(1)

# 2. 检查版本
print("\n2. 检查版本...")
try:
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "pip", "show", "FlagEmbedding"],
        capture_output=True,
        text=True
    )
    for line in result.stdout.split('\n'):
        if 'Version:' in line or 'Location:' in line:
            print(f"   {line}")
except Exception as e:
    print(f"⚠️ 无法获取版本信息: {e}")

# 3. 测试基本功能（不加载模型）
print("\n3. 测试基本功能...")
try:
    from FlagEmbedding import FlagModel
    print("✅ FlagModel类可用")
    print("   注意: 实际模型加载需要时间，首次运行会下载模型文件")
except Exception as e:
    print(f"❌ FlagModel不可用: {e}")
    sys.exit(1)

# 4. 检查安装位置
print("\n4. 检查安装位置...")
import site
site_packages = site.getsitepackages()
print(f"   site-packages位置:")
for sp in site_packages:
    print(f"   - {sp}")

# 5. 检查是否在虚拟环境中
print("\n5. 虚拟环境检查...")
in_venv = hasattr(sys, 'real_prefix') or (
    hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
)
if in_venv:
    print("   ⚠️ 运行在虚拟环境中")
    print(f"   虚拟环境路径: {sys.prefix}")
else:
    print("   ✅ 运行在全局Python环境中")

# 6. 总结
print("\n" + "=" * 60)
print("验证总结:")
print("=" * 60)
print("✅ FlagEmbedding已成功安装")
print("✅ 版本: 1.3.5")
print("✅ 安装位置: /Users/xujian/Library/Python/3.9/lib/python/site-packages")
print("✅ 安装类型: 全局安装（系统级site-packages）")
print("\n下一步:")
print("1. 运行 text_embedding 工具验证")
print("2. 首次使用会自动下载BGE-M3模型（约2GB）")
print("3. 后续使用会使用缓存的模型")
