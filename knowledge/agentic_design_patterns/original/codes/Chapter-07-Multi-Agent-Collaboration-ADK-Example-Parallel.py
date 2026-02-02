from google.adk.agents import Agent, ParallelAgent

# It's better to define the fetching logic as tools for the agents
# For simplicity in this example, we'll embed the logic in the agent's instruction.
# In a real-world scenario, you would use tools.
# 在实际场景中最好将查询数据的逻辑定义为智能体的工具
# 为了简单起见，在这个示例中，我们将查询数据的逻辑放在了智能体的指令中

# Define the individual agents that will run in parallel
# 定义两个并行运行的子智能体：weather_fetcher 和 news_fetcher
weather_fetcher = Agent(
   name="weather_fetcher",
   model="gemini-2.0-flash-exp",
   instruction="Fetch the weather for the given location and return only the weather report.",
   output_key="weather_data"  # The result will be stored in session.state["weather_data"]
)

news_fetcher = Agent(
   name="news_fetcher",
   model="gemini-2.0-flash-exp",
   instruction="Fetch the top news story for the given topic and return only that story.",
   output_key="news_data"      # The result will be stored in session.state["news_data"]
)

# Create the ParallelAgent to orchestrate the sub-agents
# 使用 ParallelAgent 编排子智能体并行执行
data_gatherer = ParallelAgent(
   name="data_gatherer",
   sub_agents=[
       weather_fetcher,
       news_fetcher
   ]
)