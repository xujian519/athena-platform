# Colab 代码链接：https://colab.research.google.com/drive/1AhF4Jam8wuYMEYU27y22r1uTbixs9MSE

# 依赖安装：
# pip install google-adk nest-asyncio python-dotenv

import asyncio
from google.genai import types
from google.adk import agents
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
import os

# --- Configuration ---
# --- 环境变量配置 ---
# Ensure you have set your GOOGLE_API_KEY and DATASTORE_ID environment variables
# 请确认已在环境变量中配置 GOOGLE_API_KEY 和 DATASTORE_ID

# For example:
# os.environ["GOOGLE_API_KEY"] = "YOUR_API_KEY"
# os.environ["DATASTORE_ID"] = "YOUR_DATASTORE_ID"

DATASTORE_ID = os.environ.get("DATASTORE_ID")

# --- Application Constants ---
# --- 定义常量 ---
APP_NAME = "vsearch_app"
USER_ID = "user_123"  # Example User ID
SESSION_ID = "session_456" # Example Session ID

# --- Agent Definition (Updated with the newer model from the guide) ---
# --- 定义一个使用 Vertex AI Search 数据存储的智能体 ---
vsearch_agent = agents.VSearchAgent(
    name="q2_strategy_vsearch_agent",
    description="Answers questions about Q2 strategy documents using Vertex AI Search.",
    model="gemini-2.0-flash-exp", # Updated model based on the guide's examples
    datastore_id=DATASTORE_ID,
    model_parameters={"temperature": 0.0}
)

# --- Runner and Session Initialization ---
# --- 初始化执行器和会话 ---
runner = Runner(
    agent=vsearch_agent,
    app_name=APP_NAME,
    session_service=InMemorySessionService(),
)

# --- Agent Invocation Logic ---
# --- 智能体调用逻辑 ---
async def call_vsearch_agent_async(query: str):
    """
    Initializes a session and streams the agent's response.
    初始化会话并使用流式输出智能体的响应。
    """
    print(f"User: {query}")
    print("Agent: ", end="", flush=True)

    try:
        # Construct the message content correctly
        # 构造消息对象
        content = types.Content(role='user', parts=[types.Part(text=query)])

        # Process events as they arrive from the asynchronous runner
        # 执行并处理异步事件
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=content
        ):
            # For token-by-token streaming of the response text
            # 处理流式输出的文本
            if hasattr(event, 'content_part_delta') and event.content_part_delta:
                print(event.content_part_delta.text, end="", flush=True)

            # Process the final response and its associated metadata
            # 处理最终输出及其关联的元数据
            if event.is_final_response():
                print() # Newline after the streaming response
                if event.grounding_metadata:
                    print(f"  (Source Attributions: {len(event.grounding_metadata.grounding_attributions)} sources found)")
                else:
                    print("  (No grounding metadata found)")
                print("-" * 30)

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Please ensure your datastore ID is correct and that the service account has the necessary permissions.")
        print("-" * 30)

# --- Run Example ---
# --- 运行示例 ---
async def run_vsearch_example():
    # Replace with a question relevant to YOUR datastore content
    # 请将此处的示例问题替换为与您数据存储内容相关、具体的问题
    await call_vsearch_agent_async("Summarize the main points about the Q2 strategy document.")
    await call_vsearch_agent_async("What safety procedures are mentioned for lab X?")

# --- Execution ---
# --- 执行 ---
if __name__ == "__main__":
    if not DATASTORE_ID:
        print("Error: DATASTORE_ID environment variable is not set.")
    else:
        try:
            asyncio.run(run_vsearch_example())
        except RuntimeError as e:
            # This handles cases where asyncio.run is called in an environment
            # that already has a running event loop (like a Jupyter notebook).
            # 处理在已经运行的循环（如 Jupyter notebook）中运行 asyncio.run 时的特定错误
            if "cannot be called from a running event loop" in str(e):
                print("Skipping execution in a running event loop. Please run this script directly.")
            else:
                raise e