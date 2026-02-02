# 依赖安装：
# pip install crewai langchain-google-genai python-dotenv

import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI

def setup_environment():
   """
   Loads environment variables and checks for the required API key.
   加载环境变量并检查所需的 API 密钥
   """
   load_dotenv()
   if not os.getenv("GOOGLE_API_KEY"):
       raise ValueError("GOOGLE_API_KEY not found. Please set it in your .env file.")

def main():
   """
   Initializes and runs the AI crew for content creation using the latest Gemini model.
   使用 Gemini 2.0 Flash 模型初始化并运行用于内容创建的 AI 智能体「创作团队」
   """
   setup_environment()

   # Define the language model to use.
   # Updated to a model from the Gemini 2.0 series for better performance and features.
   # For cutting-edge (preview) capabilities, you could use "gemini-2.5-flash".
   # 定义要使用的语言模型
   # 更新为 Gemini 2.0 系列的模型以获得更好的性能和功能
   # 如需最新的特性，可以使用 "gemini-2.5-flash" 模型
   llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

   # Define Agents with specific roles and goals
   # 定义具体的角色和目标的智能体
   researcher = Agent(
       role='Senior Research Analyst',
       goal='Find and summarize the latest trends in AI.',
       backstory="You are an experienced research analyst with a knack for identifying key trends and synthesizing information.",
       verbose=True,
       allow_delegation=False,
   )

   writer = Agent(
       role='Technical Content Writer',
       goal='Write a clear and engaging blog post based on research findings.',
       backstory="You are a skilled writer who can translate complex technical topics into accessible content.",
       verbose=True,
       allow_delegation=False,
   )

   # Define Tasks for the agents
   # 为智能体定义任务
   research_task = Task(
       description="Research the top 3 emerging trends in Artificial Intelligence in 2024-2025. Focus on practical applications and potential impact.",
       expected_output="A detailed summary of the top 3 AI trends, including key points and sources.",
       agent=researcher,
   )

   writing_task = Task(
       description="Write a 500-word blog post based on the research findings. The post should be engaging and easy for a general audience to understand.",
       expected_output="A complete 500-word blog post about the latest AI trends.",
       agent=writer,
       context=[research_task],
   )

   # Create the Crew
   # 创建 Crew 实例
   blog_creation_crew = Crew(
       agents=[researcher, writer],
       tasks=[research_task, writing_task],
       process=Process.sequential,
       llm=llm,
       # verbose=2 # Set verbosity for detailed crew execution logs
       verbose=True  # 译者注：CrewAI 的 Crew 类在最新版本中，verbose 参数只接受布尔值（True 或 False），不再支持整数级别（0, 1, 2）
   )

   # Execute the Crew
   # 启动 Crew 实例
   print("## Running the blog creation crew with Gemini 2.0 Flash... ##")
   try:
       result = blog_creation_crew.kickoff()
       print("\n------------------\n")
       print("## Crew Final Output ##")
       print(result)
   except Exception as e:
       print(f"\nAn unexpected error occurred: {e}")


if __name__ == "__main__":
   main()