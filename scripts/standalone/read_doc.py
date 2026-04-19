#!/usr/bin/env python3
import subprocess

# 使用 subprocess 查找文件
result = subprocess.run(['find', '/Users/xujian', '-name', '*自修复*骨髓腔*', '-type', 'f'],
                       capture_output=True, text=True)
files = result.stdout.strip().split('\n')
print(f"Found {len(files)} files:")
for f in files:
    if f:
        print(f"  {f}")
        # 检查文件类型
        file_result = subprocess.run(['file', f], capture_output=True)
        print(f"    Type: {file_result.stdout.decode('utf-8', errors='ignore').strip()}")

        # 尝试读取文件
        try:
            with open(f, 'rb') as fp:
                header = fp.read(8)
                print(f"    Header: {header.hex()}")
                # 复制到 /tmp
                fp.seek(0)
                with open('/tmp/test.doc', 'wb') as out:
                    out.write(fp.read())
                print("    Copied to /tmp/test.doc")
        except Exception as e:
            print(f"    Error reading: {e}")
