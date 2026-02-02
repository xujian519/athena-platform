# Colab 代码链接：https://colab.research.google.com/drive/1qFpzmHYomA4vbtuuV1DJrW_cpAZAbY_m

# 依赖安装：
# pip install google-adk nest-asyncio

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai import types
import nest_asyncio
import asyncio

# Define variables required for Session setup and Agent execution
# 定义会话和智能体执行所需的变量
APP_NAME="Google Search_agent"
USER_ID="user1234"
SESSION_ID="1234"

# Define Agent with access to search tool
# 定义一个可以使用搜索功能的智能体
root_agent = Agent(
   name="basic_search_agent",
   model="gemini-2.0-flash-exp",
   description="Agent to answer questions using Google Search.",
   instruction="I can answer your questions by searching the internet. Just ask me anything!",
   tools=[google_search] # Google Search is a pre-built tool to perform Google searches. Google Search 是一个内置的工具，用来执行 Google 搜索。
)

# Agent Interaction
# 智能体调用函数
async def call_agent(query):
   """
   Helper function to call the agent with a query.
   辅助函数，传入查询参数调用智能体。
   """

   # Session and Runner
   # 会话和执行器
   session_service = InMemorySessionService()
   session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
   runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)

   content = types.Content(role='user', parts=[types.Part(text=query)])
   events = runner.run(user_id=USER_ID, session_id=SESSION_ID, new_message=content)


   for event in events:
       if event.is_final_response():
           final_response = event.content.parts[0].text
           print("Agent Response: ", final_response)

nest_asyncio.apply()
asyncio.run(call_agent("what's the latest ai news?"))


"""
输出示例（译者添加） | Example Output (Translator added):

Agent Response:  Here's some of the latest AI news:

**AI Infrastructure & Investment**

*   **NSF Expands National AI Infrastructure:** The U.S. National Science Foundation is launching the Integrated Data Systems and Services (IDSS) program to build a national-scale AI infrastructure. (August 28, 2025)
*   **TCS Launches AI-Enhanced Operations Center:** Tata Consultancy Services (TCS) has opened an AI-driven operations center in Mexico City to support AI, cloud, cybersecurity, IoT, and application development. (August 19, 2025)
*   **Alibaba's AI-Driven Cloud Growth:** Alibaba's stock surged due to strong growth in its AI-powered cloud business. (September 1, 2025)
*   **NVIDIA GPUs to Power Oracle's AI Services:** NVIDIA GPUs will power Oracle's next-generation enterprise AI services. (October 14, 2025)
*   **OpenAI and Broadcom Collaboration:** OpenAI and Broadcom are collaborating to deploy 10 gigawatts of OpenAI-designed AI accelerators. (October 13, 2025)
*   **AMD and OpenAI Partnership:** AMD and OpenAI announced a partnership to deploy 6 gigawatts of AMD GPUs. (October 6, 2025)

**AI Models and Applications**

*   **Generative AI Predicts Chemical Reactions:** MIT researchers have developed a generative AI system named FlowER that predicts chemical reactions. (September 3, 2025)
*   **Google's Veo 3 AI Video Creation Tools Widely Available:** Google's Veo 3 AI video creation tools are now widely available. (July 29, 2025)
*   **Gemini Enterprise: Google AI Agent:** Google aims to put an AI agent on every desk with Gemini Enterprise. (October 9, 2025)
*   **Skills for Claude:** Anthropic introduced Skills for Claude, a library of custom instruction manuals that let users tailor Claude's behavior to specific tasks
*   **IBM AI agents built with Watsonx Orchestrate:** IBM announced new AI agents built with Watsonx Orchestrate, now available on Oracle's Fusion Applications AI Agent Marketplace for workflow automation

**AI in Industry**

*   **AI in the Insurance Industry:** AI is rewriting the rules of the insurance industry. (July 11, 2025)
*   **AI for Patient Care:** MHRA is fast-tracking the next wave of AI tools for patient care. (October 16, 2025)

**Other News**

*   **SoftBank chief on ASI:** SoftBank chief believes ASI (Artificial Superintelligence) will be here within 10 years, going beyond AGI (Artificial General Intelligence).
*   **AI and Bias:**  Biased online images train AI bots to see women as younger, less experienced, revealing stereotypes shaping digital systems and hiring algorithms.
*   **AI Ethics:** New York became the first U.S. state to prohibit landlords from using AI algorithms to set rental prices.
*   **OpenAI Expert Council:** OpenAI has formed an Expert Council on Well-Being and AI. (October 14, 2025)
*   **US Army general admits using AI:** US Army general admits using AI for military decisions and is “really close” with ChatGPT
"""