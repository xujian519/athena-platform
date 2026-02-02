# Colab 代码链接：https://colab.research.google.com/drive/1iF4I_mkV_as0fYoVBuKtf5gfTONEySfK

# 依赖安装：
# pip install google-adk nest-asyncio python-dotenv

import os, getpass
import asyncio
import nest_asyncio
from typing import List
from dotenv import load_dotenv
import logging
from google.adk.agents import Agent as ADKAgent, LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.adk.code_executors import BuiltInCodeExecutor
from google.genai import types

# Define variables required for Session setup and Agent execution
# 定义会话和智能体执行所需的变量
APP_NAME="calculator"
USER_ID="user1234"
SESSION_ID="session_code_exec_async"


# Agent Definition
# 定义一个可以执行代码的智能体
code_agent = LlmAgent(
   name="calculator_agent",
   model="gemini-2.0-flash",
   code_executor=BuiltInCodeExecutor(),
   instruction="""You are a calculator agent.
   When given a mathematical expression, write and execute Python code to calculate the result.
   Return only the final numerical result as plain text, without markdown or code blocks.
   """,
   description="Executes Python code to perform calculations.",
)

# Agent Interaction (Async)
# 异步执行智能体
async def call_agent_async(query):

   # Session and Runner
   # 创建会话和执行器
   session_service = InMemorySessionService()
   session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
   runner = Runner(agent=code_agent, app_name=APP_NAME, session_service=session_service)

   content = types.Content(role='user', parts=[types.Part(text=query)])
   print(f"\n--- Running Query: {query} ---")
   final_response_text = "No final text response captured."
   try:
       # Use run_async
       # 使用 run_async 方法异步执行智能体
       async for event in runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content):
           print(f"Event ID: {event.id}, Author: {event.author}")

           # --- Check for specific parts FIRST ---
           # has_specific_part = False
           # 首先检查是否有特定的部分
           if event.content and event.content.parts and event.is_final_response():
               for part in event.content.parts: # Iterate through all parts
                   if part.executable_code:
                       # Access the actual code string via .code
                       # 通过 .code 获取智能体生成的代码
                       print(f"  Debug: Agent generated code:\n```python\n{part.executable_code.code}\n```")
                       has_specific_part = True
                   elif part.code_execution_result:
                       # Access outcome and output correctly
                       # 获取代码执行结果并打印输出
                       print(f"  Debug: Code Execution Result: {part.code_execution_result.outcome} - Output:\n{part.code_execution_result.output}")
                       has_specific_part = True
                   # Also print any text parts found in any event for debugging
                   # 同时打印其他内容，便于调试
                   elif part.text and not part.text.isspace():
                       print(f"  Text: '{part.text.strip()}'")
                       # Do not set has_specific_part=True here, as we want the final response logic below
                       # 不要在这里设置 has_specific_part=True，因为我们还想要继续等待最终输出结果

               # --- Check for final response AFTER specific parts ---
               # 然后在特定部分检查之后处理最终结果
               text_parts = [part.text for part in event.content.parts if part.text]
               final_result = "".join(text_parts)
               print(f"==> Final Agent Response: {final_result}")

   except Exception as e:
       print(f"ERROR during agent run: {e}")
   print("-" * 30)

# Main async function to run the examples
# 运行示例
async def main():
   await call_agent_async("Calculate the value of (5 + 7) * 3")
   await call_agent_async("What is 10 factorial?")


# Execute the main async function
# 运行主异步函数以启动程序流程
try:
   nest_asyncio.apply()
   asyncio.run(main())
except RuntimeError as e:
   # Handle specific error when running asyncio.run in an already running loop (like Jupyter/Colab)
   # 处理在已经运行的循环（如 Jupyter/Colab）中运行 asyncio.run 时的特定错误
   if "cannot be called from a running event loop" in str(e):
       print("\nRunning in an existing event loop (like Colab/Jupyter).")
       print("Please run `await main()` in a notebook cell instead.")
       # If in an interactive environment like a notebook, you might need to run:
       # 在交互式环境中（如 Jupyter 笔记本），你可能需要运行：
       # await main()
   else:
       raise e # Re-raise other runtime errors



"""
输出示例（译者添加） | Example Output (Translator added):

--- Running Query: Calculate the value of (5 + 7) * 3 ---
Warning: there are non-text parts in the response: ['executable_code', 'code_execution_result'], returning concatenated text result from text parts. Check the full candidates.content.parts accessor to get the full model response.
Event ID: e2ff2538-fe83-4e3d-ac66-7240df32ee03, Author: calculator_agent
  Debug: Agent generated code:
```python
print((5 + 7) * 3)

```
  Debug: Code Execution Result: Outcome.OUTCOME_OK - Output:
36

  Text: '36'
==> Final Agent Response: 36

------------------------------

--- Running Query: What is 10 factorial? ---
Warning: there are non-text parts in the response: ['executable_code', 'code_execution_result'], returning concatenated text result from text parts. Check the full candidates.content.parts accessor to get the full model response.
Event ID: 208aeb7b-d8fd-4ddf-9fc2-f9218f50e084, Author: calculator_agent
  Debug: Agent generated code:
```python
import math
print(math.factorial(10))

```
  Debug: Code Execution Result: Outcome.OUTCOME_OK - Output:
3628800

  Text: '3628800'
==> Final Agent Response: 3628800

------------------------------
"""
