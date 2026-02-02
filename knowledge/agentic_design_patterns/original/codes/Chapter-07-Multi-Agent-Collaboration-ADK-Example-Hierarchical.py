from google.adk.agents import LlmAgent, BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from typing import AsyncGenerator

# Correctly implement a custom agent by extending BaseAgent
# 通过继承 BaseAgent 类实现自定义智能体
class TaskExecutor(BaseAgent):
   """
   A specialized agent with custom, non-LLM behavior.
   一个自定义的非基于大语言模型的智能体
   """
   name: str = "TaskExecutor"
   description: str = "Executes a predefined task."

   async def _run_async_impl(self, context: InvocationContext) -> AsyncGenerator[Event, None]:
       """
       Custom implementation logic for the task.
       自定义任务的实现逻辑
       """
       # This is where your custom logic would go.
       # For this example, we'll just yield a simple event.
       # 这里是自定义逻辑所在
       # 在这个示例中，我们只是返回一个简单的事件
       yield Event(author=self.name, content="Task finished successfully.")

# Define individual agents with proper initialization
# LlmAgent requires a model to be specified.
# 定义具有明确功能的智能体
# LlmAgent 需要指定使用的模型
greeter = LlmAgent(
   name="Greeter",
   model="gemini-2.0-flash-exp",
   instruction="You are a friendly greeter."
)

# Instantiate our concrete custom agent
# 实例化自定义智能体
task_doer = TaskExecutor() 

# Create a parent agent and assign its sub-agents
# The parent agent's description and instructions should guide its delegation logic.
# 创建一个父智能体并声明其子智能体列表
# 父智能体的描述和指令应该能够指导其委派子智能体的逻辑
coordinator = LlmAgent(
   name="Coordinator",
   model="gemini-2.0-flash-exp",
   description="A coordinator that can greet users and execute tasks.",
   instruction="When asked to greet, delegate to the Greeter. When asked to perform a task, delegate to the TaskExecutor.",
   sub_agents=[
       greeter,
       task_doer
   ]
)

# The ADK framework automatically establishes the parent-child relationships.
# These assertions will pass if checked after initialization.
# ADK 框架会自动建立上述层级关系
# 如果在初始化后检查，这些断言将成立
assert greeter.parent_agent == coordinator
assert task_doer.parent_agent == coordinator

print("Agent hierarchy created successfully.")