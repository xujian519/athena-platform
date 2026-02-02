from google.adk.agents import LlmAgent
from google.adk.tools import agent_tool
from google.genai import types

# 1. A simple function tool for the core capability.
# This follows the best practice of separating actions from reasoning.
# 1. 一个简单的函数工具
# 遵循分离操作与推理的最佳实践
def generate_image(prompt: str) -> dict:
   """
   Generates an image based on a textual prompt.
   基于文本提示生成图像

   Args:
       prompt: A detailed description of the image to generate.
       要生成的图像的详细描述
   Returns:
       A dictionary with the status and the generated image bytes.
       包含状态和生成的图像字节的字典
   """

   print(f"TOOL: Generating image for prompt: '{prompt}'")
   # In a real implementation, this would call an image generation API.
   # For this example, we return mock image data.
   # 在实际实现中，这里将调用真实的图像生成 API
   # 但是为了简便起见，在这个示例中，我们仅返回模拟的图像数据
   mock_image_bytes = b"mock_image_data_for_a_cat_wearing_a_hat"
   return {
       "status": "success",
       # The tool returns the raw bytes, the agent will handle the Part creation.
       # 工具返回原始字节，智能体将处理 Part 创建
       "image_bytes": mock_image_bytes,
       "mime_type": "image/png"
   }

# 2. Refactor the ImageGeneratorAgent into an LlmAgent.
# It now correctly uses the input passed to it.
# 2. 将 ImageGeneratorAgent 重构为 LlmAgent
# 它现在能接收并使用传给它的参数了
image_generator_agent = LlmAgent(
   name="ImageGen",
   model="gemini-2.0-flash",
   description="Generates an image based on a detailed text prompt.",
   instruction=(
       "You are an image generation specialist. Your task is to take the user's request "
       "and use the `generate_image` tool to create the image. "
       "The user's entire request should be used as the 'prompt' argument for the tool. "
       "After the tool returns the image bytes, you MUST output the image."
   ),
   tools=[generate_image]
)

# 3. Wrap the corrected agent in an AgentTool.
# The description here is what the parent agent sees.
# 3. 将智能体封装在 AgentTool 中
# 这里的描述对父智能体是可见的
image_tool = agent_tool.AgentTool(
   agent=image_generator_agent,
   description="Use this tool to generate an image. The input should be a descriptive prompt of the desired image."
)

# 4. The parent agent remains unchanged. Its logic was correct.
# 4. 父智能体保持不变。
artist_agent = LlmAgent(
   name="Artist",
   model="gemini-2.0-flash",
   instruction=(
       "You are a creative artist. First, invent a creative and descriptive prompt for an image. "
       "Then, use the `ImageGen` tool to generate the image using your prompt."
   ),
   tools=[image_tool]
)