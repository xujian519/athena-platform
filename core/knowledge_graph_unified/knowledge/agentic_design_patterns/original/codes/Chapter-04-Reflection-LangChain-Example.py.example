import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

# Colab 代码链接：https://colab.research.google.com/drive/1xnL6Rky6nsm4iAhomLnUK3kgwSyyYZfb

# 安装依赖
# pip install langchain langchain-community langchain-openai

# --- Configuration ---
# Load environment variables from .env file (for OPENAI_API_KEY)
# 从 .env 文件加载环境变量（如 OPENAI_API_KEY）
load_dotenv()

# Check if the API key is set
# 检查 API 密钥是否设置
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY not found in .env file. Please add it.")

# Initialize the Chat LLM. We use a powerful model like gpt-4o for better reasoning.
# A lower temperature is used for more deterministic and focused outputs.
# 使用 gpt-4o 或其他模型，并设置较低的温度值以获得更稳定的输出
llm = ChatOpenAI(model="gpt-4o", temperature=0.1)


def run_reflection_loop():
    """
    Demonstrates a multi-step AI reflection loop to progressively improve a Python function.
    展示了通过多步骤反思循环，逐步改进 Python 函数的方法。
    """

    # --- The Core Task ---
    # --- 核心任务的提示词 ---
    task_prompt = """
    Your task is to create a Python function named `calculate_factorial`.
    This function should do the following:
    1.  Accept a single integer `n` as input.
    2.  Calculate its factorial (n!).
    3.  Include a clear docstring explaining what the function does.
    4.  Handle edge cases: The factorial of 0 is 1.
    5.  Handle invalid input: Raise a ValueError if the input is a negative number.
    """

    # --- The Reflection Loop ---
    # --- 反思循环 ---
    max_iterations = 3
    current_code = ""
    # We will build a conversation history to provide context in each step.
    # 构建对话历史，为每一步提供必要的上下文信息。
    message_history = [HumanMessage(content=task_prompt)]

    for i in range(max_iterations):
        print("\n" + "="*25 + f" REFLECTION LOOP: ITERATION {i + 1} " + "="*25)

        # --- 1. GENERATE / REFINE STAGE ---
        # In the first iteration, it generates. In subsequent iterations, it refines.
        # 在第一次迭代时，生成初始代码；在后续迭代时，基于上一步的反馈优化代码。
        if i == 0:
            print("\n>>> STAGE 1: GENERATING initial code...")
            # The first message is just the task prompt.
            # 第一次迭代时，只需要任务提示词。
            response = llm.invoke(message_history)
            current_code = response.content
        else:
            print("\n>>> STAGE 1: REFINING code based on previous critique...")
            # The message history now contains the task, the last code, and the last critique.
            # We instruct the model to apply the critiques.
            # 后续迭代时，除了任务提示词，还包含上一步的代码和反馈。
            # 然后要求模型根据反馈意见优化代码。
            message_history.append(HumanMessage(content="Please refine the code using the critiques provided."))
            response = llm.invoke(message_history)
            current_code = response.content

        print("\n--- Generated Code (v" + str(i + 1) + ") ---\n" + current_code)
        message_history.append(response) # Add the generated code to history

        # --- 2. REFLECT STAGE ---
        # --- 反思阶段 ---
        print("\n>>> STAGE 2: REFLECTING on the generated code...")

        # Create a specific prompt for the reflector agent.
        # This asks the model to act as a senior code reviewer.
        # 创建一个特定的提示词，要求模型扮演高级软件工程师的角色，对代码进行仔细的审查。
        reflector_prompt = [
            SystemMessage(content="""
                You are a senior software engineer and an expert in Python.
                Your role is to perform a meticulous code review.
                Critically evaluate the provided Python code based on the original task requirements.
                Look for bugs, style issues, missing edge cases, and areas for improvement.
                If the code is perfect and meets all requirements, respond with the single phrase 'CODE_IS_PERFECT'.
                Otherwise, provide a bulleted list of your critiques.
            """),
            HumanMessage(content=f"Original Task:\n{task_prompt}\n\nCode to Review:\n{current_code}")
        ]

        critique_response = llm.invoke(reflector_prompt)
        critique = critique_response.content

        # --- 3. STOPPING CONDITION ---
        # 如果代码完美符合要求，则结束反思循环。
        if "CODE_IS_PERFECT" in critique:
            print("\n--- Critique ---\nNo further critiques found. The code is satisfactory.")
            break

        print("\n--- Critique ---\n" + critique)
        # Add the critique to the history for the next refinement loop.
        message_history.append(HumanMessage(content=f"Critique of the previous code:\n{critique}"))

    print("\n" + "="*30 + " FINAL RESULT " + "="*30)
    print("\nFinal refined code after the reflection process:\n")
    print(current_code)


if __name__ == "__main__":
    run_reflection_loop()


"""
输出示例（译者添加） | Example Output (Translator added):
========================= REFLECTION LOOP: ITERATION 1 =========================

>>> STAGE 1: GENERATING initial code...

--- Generated Code (v1) ---
Here's a Python function named `calculate_factorial` that meets all the specified requirements:

```python
def calculate_factorial(n):
    """
    Calculate the factorial of a non-negative integer n.

    The factorial of a non-negative integer n is the product of all positive integers less than or equal to n.
    The factorial of 0 is defined as 1.

    Parameters:
    n (int): A non-negative integer whose factorial is to be calculated.

    Returns:
    int: The factorial of the input integer n.

    Raises:
    ValueError: If the input is a negative integer.
    """
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers.")
    
    factorial = 1
    for i in range(2, n + 1):
        factorial *= i
    
    return factorial

# Example usage:
# print(calculate_factorial(5))  # Output: 120
# print(calculate_factorial(0))  # Output: 1
```

### Explanation:
1. **Docstring**: The function includes a docstring that explains its purpose, parameters, return value, and exceptions.
2. **Edge Case Handling**: The function correctly returns 1 for an input of 0, as the factorial of 0 is defined to be 1.
3. **Invalid Input Handling**: The function raises a `ValueError` if the input is a negative integer, as factorials are not defined for negative numbers.
4. **Factorial Calculation**: The function uses a loop to calculate the factorial of the input integer `n`. It multiplies all integers from 2 to `n` to compute the factorial.

>>> STAGE 2: REFLECTING on the generated code...

--- Critique ---
- The code correctly handles the calculation of factorials for non-negative integers, including the edge case where `n` is 0.
- The docstring is clear and provides necessary information about the function's purpose, parameters, return value, and exceptions.
- The function raises a `ValueError` for negative inputs, which is appropriate for handling invalid input.
- The loop starts from 2, which is efficient since multiplying by 1 is unnecessary.
- The code could be improved by adding a type check to ensure that the input is an integer. Currently, if a non-integer type is passed, it will raise a `TypeError` during the comparison `if n < 0:` or during the loop, which is not explicitly handled. Adding a type check with a clear error message would improve robustness.
- Consider adding type hints to the function signature for better readability and to provide additional information about expected input and output types. For example: `def calculate_factorial(n: int) -> int:`.
- The example usage comments are helpful, but adding a few more examples, including edge cases and invalid inputs, could further illustrate the function's behavior.

========================= REFLECTION LOOP: ITERATION 2 =========================

>>> STAGE 1: REFINING code based on previous critique...

--- Generated Code (v2) ---
Certainly! Here's the refined version of the `calculate_factorial` function, incorporating the critiques:

```python
def calculate_factorial(n: int) -> int:
    """
    Calculate the factorial of a non-negative integer n.

    The factorial of a non-negative integer n is the product of all positive integers less than or equal to n.
    The factorial of 0 is defined as 1.

    Parameters:
    n (int): A non-negative integer whose factorial is to be calculated.

    Returns:
    int: The factorial of the input integer n.

    Raises:
    ValueError: If the input is a negative integer.
    TypeError: If the input is not an integer.
    """
    if not isinstance(n, int):
        raise TypeError("Input must be an integer.")
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers.")
    
    factorial = 1
    for i in range(2, n + 1):
        factorial *= i
    
    return factorial

# Example usage:
# print(calculate_factorial(5))  # Output: 120
# print(calculate_factorial(0))  # Output: 1
# print(calculate_factorial(1))  # Output: 1
# print(calculate_factorial(10)) # Output: 3628800

# Example of handling invalid input:
# print(calculate_factorial(-3)) # Raises ValueError
# print(calculate_factorial(3.5)) # Raises TypeError
```

### Key Improvements:
1. **Type Checking**: Added a type check to ensure the input is an integer, raising a `TypeError` with a clear message if it is not.
2. **Type Hints**: Added type hints to the function signature to specify that the input should be an integer and the output will also be an integer.
3. **Additional Examples**: Included more example usages in the comments to illustrate the function's behavior, including edge cases and invalid inputs.

>>> STAGE 2: REFLECTING on the generated code...

--- Critique ---
No further critiques found. The code is satisfactory.

============================== FINAL RESULT ==============================

Final refined code after the reflection process:

Certainly! Here's the refined version of the `calculate_factorial` function, incorporating the critiques:

```python
def calculate_factorial(n: int) -> int:
    """
    Calculate the factorial of a non-negative integer n.

    The factorial of a non-negative integer n is the product of all positive integers less than or equal to n.
    The factorial of 0 is defined as 1.

    Parameters:
    n (int): A non-negative integer whose factorial is to be calculated.

    Returns:
    int: The factorial of the input integer n.

    Raises:
    ValueError: If the input is a negative integer.
    TypeError: If the input is not an integer.
    """
    if not isinstance(n, int):
        raise TypeError("Input must be an integer.")
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers.")
    
    factorial = 1
    for i in range(2, n + 1):
        factorial *= i
    
    return factorial

# Example usage:
# print(calculate_factorial(5))  # Output: 120
# print(calculate_factorial(0))  # Output: 1
# print(calculate_factorial(1))  # Output: 1
# print(calculate_factorial(10)) # Output: 3628800

# Example of handling invalid input:
# print(calculate_factorial(-3)) # Raises ValueError
# print(calculate_factorial(3.5)) # Raises TypeError
```

### Key Improvements:
1. **Type Checking**: Added a type check to ensure the input is an integer, raising a `TypeError` with a clear message if it is not.
2. **Type Hints**: Added type hints to the function signature to specify that the input should be an integer and the output will also be an integer.
3. **Additional Examples**: Included more example usages in the comments to illustrate the function's behavior, including edge cases and invalid inputs.
"""