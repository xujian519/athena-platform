#!/usr/bin/env python3
import sys
print("Python version:", sys.version, flush=True)
print("开始测试...", flush=True)

try:
    import asyncio
    print("✅ asyncio导入成功", flush=True)

    import websockets
    print("✅ websockets导入成功", flush=True)

    async def quick_test():
        print("✅ 进入async函数", flush=True)
        uri = "ws://localhost:8005/ws"
        print(f"尝试连接: {uri}", flush=True)

        try:
            ws = await websockets.connect(uri, close_timeout=5)
            print("✅ 连接成功!", flush=True)
            await ws.close()
            print("✅ 连接已关闭", flush=True)
            return True
        except Exception as e:
            print(f"❌ 连接失败: {e}", flush=True)
            return False

    result = asyncio.run(quick_test())
    print(f"测试结果: {result}", flush=True)

except Exception as e:
    print(f"❌ 错误: {e}", flush=True)
    import traceback
    traceback.print_exc()
