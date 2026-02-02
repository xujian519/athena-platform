from google.adk.agents import SequentialAgent, Agent

# This agent's output will be saved to session.state["data"]
# 该智能体的输出将保存到 session.state["data"]
step1 = Agent(name="Step1_Fetch", output_key="data")

# This agent will use the data from the previous step.
# We instruct it on how to find and use this data.
# 该智能体会使用上一步的输出
# 通过指令告诉它如何查找和使用上一步的输出
step2 = Agent(
   name="Step2_Process",
   instruction="Analyze the information found in state['data'] and provide a summary."
)

pipeline = SequentialAgent(
   name="MyPipeline",
   sub_agents=[step1, step2]
)

# When the pipeline is run with an initial input, Step1 will execute,
# its response will be stored in session.state["data"], and then
# Step2 will execute, using the information from the state as instructed.
# 当使用原始输入运行 pipeline 时，Step1 先执行，
# 它的响应会保存到 session.state["data"] 中，然后
# Step2 再执行，按照指令使用状态中的信息