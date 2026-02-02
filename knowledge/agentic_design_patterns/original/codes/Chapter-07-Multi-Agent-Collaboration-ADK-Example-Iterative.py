import asyncio
from typing import AsyncGenerator
from google.adk.agents import LoopAgent, LlmAgent, BaseAgent
from google.adk.events import Event, EventActions
from google.adk.agents.invocation_context import InvocationContext

# Best Practice: Define custom agents as complete, self-describing classes.
# 最佳实践：将自定义智能体定义为完整的、自描述的类
class ConditionChecker(BaseAgent):
   """
   A custom agent that checks for a 'completed' status in the session state.
   一个自定义的智能体，用于检查会话是否为「completed」状态
   """
   name: str = "ConditionChecker"
   description: str = "Checks if a process is complete and signals the loop to stop."

   async def _run_async_impl(
       self, context: InvocationContext
   ) -> AsyncGenerator[Event, None]:
       """
       Checks state and yields an event to either continue or stop the loop.
       检查状态并产生事件以继续或停止循环
       """
       status = context.session.state.get("status", "pending")
       is_done = (status == "completed")

       if is_done:
           # Escalate to terminate the loop when the condition is met.
           # 满足条件时终止循环
           yield Event(author=self.name, actions=EventActions(escalate=True))
       else:
           # Yield a simple event to continue the loop.
           # 否则，发出简单事件以继续循环
           yield Event(author=self.name, content="Condition not met, continuing loop.")

# Correction: The LlmAgent must have a model and clear instructions.
# 说明：LlmAgent 必须指定使用的模型和清晰的指令
process_step = LlmAgent(
   name="ProcessingStep",
   model="gemini-2.0-flash-exp",
   instruction="You are a step in a longer process. Perform your task. If you are the final step, update session state by setting 'status' to 'completed'."
)

# The LoopAgent orchestrates the workflow.
# 使用 LoopAgent 编排工作流
poller = LoopAgent(
   name="StatusPoller",
   max_iterations=10,
   sub_agents=[
       process_step,
       ConditionChecker() # Instantiating the well-defined custom agent.
   ]
)

# This poller will now execute 'process_step'
# and then 'ConditionChecker'
# repeatedly until the status is 'completed' or 10 iterations
# have passed.
# 此轮询器现在将执行 'process_step' 智能体
# 然后执行 'ConditionChecker' 智能体    
# 重复执行直到状态为 'completed' 或达到 10 次循环