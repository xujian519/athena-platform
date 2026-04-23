
# Colab 代码链接：https://colab.research.google.com/drive/1TBcatcgnntrm31kfIzENsSMNYwMNLUOh
# 依赖安装：
# pip install crewai langchain-openai
import logging
import os

from crewai import Agent, Crew, Task
from crewai.tools import tool

# --- Best Practice: Configure Logging ---
# A basic logging setup helps in debugging and tracking the crew's execution.
# --- 最佳实践：配置日志 ---
# 良好的日志设置有助于调试和追踪 crewAI 的执行过程。
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Set up your API Key ---
# For production, it's recommended to use a more secure method for key management
# like environment variables loaded at runtime or a secret manager.
# --- 设置你的 API 密钥 ---
# 在生产环境中，推荐使用更安全的密钥管理方法，
# 例如在运行时加载环境变量或使用密钥管理器。
#
# Set the environment variable for your chosen LLM provider (e.g., OPENAI_API_KEY)
# 根据你选择的模型提供商设置环境变量（如 OPENAI_API_KEY）
# os.environ["OPENAI_API_KEY"] = "YOUR_API_KEY"
# os.environ["OPENAI_MODEL_NAME"] = "gpt-4o"

# --- 1. Refactored Tool: Returns Clean Data ---
# The tool now returns raw data (a float) or raises a standard Python error.
# This makes it more reusable and forces the agent to handle outcomes properly.
# --- 1. 重构后的工具 ---
# 该工具现在返回模拟的股价（一个浮点数）或抛出标准的 Python 错误。
# 这样可以提高可重用性，并确保智能体在处理结果时采取适当的处理措施。
@tool("Stock Price Lookup Tool")
def get_stock_price(ticker: str) -> float:
    """
    Fetches the latest simulated stock price for a given stock ticker symbol.
    Returns the price as a float. Raises a ValueError if the ticker is not found.
    获取指定股票代码的最新模拟股价信息。
    返回该股票的价格（浮点数）。如果找不到该代码，会抛出 ValueError 异常。
    """
    logging.info(f"Tool Call: get_stock_price for ticker '{ticker}'")
    simulated_prices = {
        "AAPL": 178.15,
        "GOOGL": 1750.30,
        "MSFT": 425.50,
    }
    price = simulated_prices.get(ticker.upper())

    if price is not None:
        return price
    else:
        # Raising a specific error is better than returning a string.
        # The agent is equipped to handle exceptions and can decide on the next action.
        # 与其返回一个字符串，不如抛出一个明确的错误，这样更清晰也便于处理。
        # 该智能体具备异常处理能力，能够在发生问题时判断并选择合适的后续动作。
        raise ValueError(f"Simulated price for ticker '{ticker.upper()}' not found.")


# --- 2. Define the Agent ---
# The agent definition remains the same, but it will now leverage the improved tool.
# --- 2. 定义智能体 ---
# 智能体的定义仍然沿用原有内容，不过现在会使用增强后的工具。
financial_analyst_agent = Agent(
  role='Senior Financial Analyst',
  goal='Analyze stock data using provided tools and report key prices.',
  backstory="You are an experienced financial analyst adept at using data sources to find stock information. You provide clear, direct answers.",
  verbose=True,
  tools=[get_stock_price],
  # Allowing delegation can be useful, but is not necessary for this simple task.
  # 允许委托在某些情况下很有用，但对于这个简单的任务并非必需。
  allow_delegation=False,
)

# --- 3. Refined Task: Clearer Instructions and Error Handling ---
# The task description is more specific and guides the agent on how to react
# to both successful data retrieval and potential errors.
# --- 3. 优化后的任务：提供更清晰的指引与更完善的错误处理 ---
# 任务描述更加详尽，能够指导智能体在查询成功和抛出错误时都采取正确的处理。
analyze_aapl_task = Task(
  description=(
      "What is the current simulated stock price for Apple (ticker: AAPL)? "
      "Use the 'Stock Price Lookup Tool' to find it. "
      "If the ticker is not found, you must report that you were unable to retrieve the price."
  ),
  expected_output=(
      "A single, clear sentence stating the simulated stock price for AAPL. "
      "For example: 'The simulated stock price for AAPL is $178.15.' "
      "If the price cannot be found, state that clearly."
  ),
  agent=financial_analyst_agent,
)

# --- 4. Formulate the Crew ---
# The crew orchestrates how the agent and task work together.
# --- 4. 构建 Crew 实例 ---
# 由该实例来负责协调智能体和任务。
financial_crew = Crew(
  agents=[financial_analyst_agent],
  tasks=[analyze_aapl_task],
  verbose=True # Set to False for less detailed logs in production
)

# --- 5. Run the Crew within a Main Execution Block ---
# Using a __name__ == "__main__": block is a standard Python best practice.
# --- 5. 在主程序中运行 ---
# 使用 __name__ == "__main__": 块是 Python 的最佳实践。
def main():
    """Main function to run the crew."""
    # Check for API key before starting to avoid runtime errors.
    # 在启动 Crew 之前，检查 OPENAI_API_KEY 环境变量是否已设置。
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: The OPENAI_API_KEY environment variable is not set.")
        print("Please set it before running the script.")
        return

    print("\n## Starting the Financial Crew...")
    print("---------------------------------")

    # The kickoff method starts the execution.
    # 使用 kickoff 方法启动执行。
    result = financial_crew.kickoff()

    print("\n---------------------------------")
    print("## Crew execution finished.")
    print("\nFinal Result:\n", result)

if __name__ == "__main__":
    main()


"""
输出示例（译者添加） | Example Output (Translator added):

## Starting the Financial Crew...
---------------------------------
╭────────────────────────────────────────────────────────────────── Crew Execution Started ──────────────────────────────────────────────────────────────────╮
│                                                                                                                                                            │
│  Crew Execution Started                                                                                                                                    │
│  Name: crew                                                                                                                                                │
│  ID: 66cd65e8-b995-4d76-b5d1-0b89e98df7b9                                                                                                                  │
│  Tool Args:                                                                                                                                                │
│                                                                                                                                                            │
│                                                                                                                                                            │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

🚀 Crew: crew
└── 📋 Task: 1b11482d-6338-4f92-9fdd-b9304ad7c6cd
    Status: Executing Task...
╭───────────────────────────────────────────────────────────────────── 🤖 Agent Started ─────────────────────────────────────────────────────────────────────╮
│                                                                                                                                                            │
│  Agent: Senior Financial Analyst                                                                                                                           │
│                                                                                                                                                            │
│  Task: What is the current simulated stock price for Apple (ticker: AAPL)? Use the 'Stock Price Lookup Tool' to find it. If the ticker is not found, you   │
│  must report that you were unable to retrieve the price.                                                                                                   │
│                                                                                                                                                            │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

23:25:25 - LiteLLM:INFO: utils.py:3258 -
LiteLLM completion() model= gpt-4o-mini; provider = openai
2025-10-17 23:25:25,493 - INFO -
LiteLLM completion() model= gpt-4o-mini; provider = openai
🚀 Crew: crew
🚀 Crew: crew
└── 📋 Task: 1b11482d-6338-4f92-9fdd-b9304ad7c6cd
🚀 Crew: crew
🚀 Crew: crew
└── 📋 Task: 1b11482d-6338-4f92-9fdd-b9304ad7c6cd
    Status: Executing Task...
    └── 🔧 Used Stock Price Lookup Tool (1)
╭───────────────────────────────────────────────────────────────── 🔧 Agent Tool Execution ──────────────────────────────────────────────────────────────────╮
│                                                                                                                                                            │
│  Agent: Senior Financial Analyst                                                                                                                           │
│                                                                                                                                                            │
│  Thought: I should use the Stock Price Lookup Tool to find the current simulated stock price for Apple (AAPL).                                             │
│                                                                                                                                                            │
│  Using Tool: Stock Price Lookup Tool                                                                                                                       │
│                                                                                                                                                            │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭──────────────────────────────────────────────────────────────────────── Tool Input ────────────────────────────────────────────────────────────────────────╮
│                                                                                                                                                            │
│  {                                                                                                                                                         │
│    "ticker": "AAPL"                                                                                                                                        │
│  }                                                                                                                                                         │
│                                                                                                                                                            │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─────────────────────────────────────────────────────────────────────── Tool Output ────────────────────────────────────────────────────────────────────────╮
│                                                                                                                                                            │
│  178.15                                                                                                                                                    │
│                                                                                                                                                            │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

23:25:28 - LiteLLM:INFO: utils.py:3258 -
LiteLLM completion() model= gpt-4o-mini; provider = openai
2025-10-17 23:25:28,360 - INFO -
LiteLLM completion() model= gpt-4o-mini; provider = openai
🚀 Crew: crew
🚀 Crew: crew
└── 📋 Task: 1b11482d-6338-4f92-9fdd-b9304ad7c6cd
🚀 Crew: crew
└── 📋 Task: 1b11482d-6338-4f92-9fdd-b9304ad7c6cd
    Status: Executing Task...
    └── 🔧 Used Stock Price Lookup Tool (1)
╭────────────────────────────────────────────────────────────────── ✅ Agent Final Answer ───────────────────────────────────────────────────────────────────╮
│                                                                                                                                                            │
│  Agent: Senior Financial Analyst                                                                                                                           │
│                                                                                                                                                            │
│  Final Answer:                                                                                                                                             │
│  The simulated stock price for AAPL is $178.15.                                                                                                            │
│                                                                                                                                                            │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

🚀 Crew: crew
└── 📋 Task: 1b11482d-6338-4f92-9fdd-b9304ad7c6cd
    Assigned to: Senior Financial Analyst
    Status: ✅ Completed
    └── 🔧 Used Stock Price Lookup Tool (1)
╭───────────────────────────────────────────────────────────────────── Task Completion ──────────────────────────────────────────────────────────────────────╮
│                                                                                                                                                            │
│  Task Completed                                                                                                                                            │
│  Name: 1b11482d-6338-4f92-9fdd-b9304ad7c6cd                                                                                                                │
│  Agent: Senior Financial Analyst                                                                                                                           │
│  Tool Args:                                                                                                                                                │
│                                                                                                                                                            │
│                                                                                                                                                            │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

╭───────────────────────────────────────────────────────────────────── Crew Completion ──────────────────────────────────────────────────────────────────────╮
│                                                                                                                                                            │
│  Crew Execution Completed                                                                                                                                  │
│  Name: crew                                                                                                                                                │
│  ID: 66cd65e8-b995-4d76-b5d1-0b89e98df7b9                                                                                                                  │
│  Tool Args:                                                                                                                                                │
│  Final Output: The simulated stock price for AAPL is $178.15.                                                                                              │
│                                                                                                                                                            │
│                                                                                                                                                            │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

"""

