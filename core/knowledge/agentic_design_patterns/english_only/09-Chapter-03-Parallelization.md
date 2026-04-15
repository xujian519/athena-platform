# Agentic Design Patterns (English Version)

> **Extract Time**: 2025-12-17 05:14:24
> **Content Type**: English Only Version
> **Total Pages**: 424
> **Original Source**: https://github.com/ginobefun/agentic-design-patterns-cn

---

# Chapter 3: Parallelization | <mark></mark>

## Parallelization Pattern Overview | <mark></mark>

In the previous chapters, we've explored Prompt Chaining for sequential workflows and Routing for dynamic decision-making and transitions between different paths. While these patterns are essential, many complex agentic tasks involve multiple sub-tasks that can be executed *simultaneously* rather than one after another. This is where the **Parallelization** pattern becomes crucial.

<mark>。<strong></strong>。<strong></strong>。</mark>

Parallelization involves executing multiple components, such as LLM calls, tool usages, or even entire sub-agents, concurrently (see Fig.1). Instead of waiting for one step to complete before starting the next, parallel execution allows independent tasks to run at the same time, significantly reducing the overall execution time for tasks that can be broken down into independent parts.

<mark>、 1。。</mark>

Consider an agent designed to research a topic and summarize its findings. A sequential approach might:

<mark>。</mark>

1. Search for Source A.

<mark> A。</mark>

2. Summarize Source A.

<mark> A。</mark>

3. Search for Source B.

<mark> B。</mark>

4. Summarize Source B.

<mark> B。</mark>

5. Synthesize a final answer from summaries A and B.

<mark> A B 。</mark>

A parallel approach could instead:

<mark></mark>

1. Search for Source A *and* Search for Source B simultaneously.

<mark><strong></strong> A B。</mark>

2. Once both searches are complete, Summarize Source A *and* Summarize Source B simultaneously.

<mark> A B 。</mark>

3. Synthesize a final answer from summaries A and B (this step is typically sequential, waiting for the parallel steps to finish).

<mark> A B 。。</mark>

The core idea is to identify parts of the workflow that do not depend on the output of other parts and execute them in parallel. This is particularly effective when dealing with external services (like APIs or databases) that have latency, as you can issue multiple requests concurrently.

<mark>。 API 。</mark>

Implementing parallelization often requires frameworks that support asynchronous execution or multi-threading/multi-processing. Modern agentic frameworks are designed with asynchronous operations in mind, allowing you to easily define steps that can run in parallel.

<mark>、。。</mark>

![Parallelization Example](/images/chapter03_fig1.png)

Fig.1. Example of parallelization with sub-agents

<mark> 1</mark>

Frameworks like LangChain, LangGraph, and Google ADK provide mechanisms for parallel execution. In LangChain Expression Language (LCEL), you can achieve parallel execution by combining runnable objects using operators like | (for sequential) and by structuring your chains or graphs to have branches that execute concurrently. LangGraph, with its graph structure, allows you to define multiple nodes that can be executed from a single state transition, effectively enabling parallel branches in the workflow. Google ADK provides robust, native mechanisms to facilitate and manage the parallel execution of agents, significantly enhancing the efficiency and scalability of complex, multi-agent systems. This inherent capability within the ADK framework allows developers to design and implement solutions where multiple agents can operate concurrently, rather than sequentially.

<mark>LangChain、LangGraph Google ADK 。</mark>

<mark> LangChain LCEL <code>|</code> 。 LangGraph 。</mark>

<mark>Google ADK 。ADK 。</mark>

The Parallelization pattern is vital for improving the efficiency and responsiveness of agentic systems, especially when dealing with tasks that involve multiple independent lookups, computations, or interactions with external services. It's a key technique for optimizing the performance of complex agent workflows.

<mark>、。。</mark>

---

## Practical Applications & Use Cases | <mark></mark>

Parallelization is a powerful pattern for optimizing agent performance across various applications:

<mark></mark>


Collecting information from multiple sources simultaneously is a classic use case.

<mark>。</mark>

- **Use Case:** An agent researching a company.

<mark><strong></strong>。</mark>

- **Parallel Tasks:** Search news articles, pull stock data, check social media mentions, and query a company database, all at the same time.

<mark><strong></strong>、、。</mark>

- **Benefit:** Gathers a comprehensive view much faster than sequential lookups.

<mark><strong></strong>。</mark>


Applying different analysis techniques or processing different data segments concurrently.

<mark>。</mark>

- **Use Case:** An agent analyzing customer feedback.

<mark><strong></strong>。</mark>

- **Parallel Tasks:** Run sentiment analysis, extract keywords, categorize feedback, and identify urgent issues simultaneously across a batch of feedback entries.

<mark><strong></strong>、、。</mark>

- **Benefit:** Provides a multi-faceted analysis quickly.

<mark><strong></strong>。</mark>


Calling multiple independent APIs or tools to gather different types of information or perform different actions.

<mark> API 。</mark>

- **Use Case:** A travel planning agent.

<mark><strong></strong>。</mark>

- **Parallel Tasks:** Check flight prices, search for hotel availability, look up local events, and find restaurant recommendations concurrently.

<mark><strong></strong>、、。</mark>

- **Benefit:** Presents a complete travel plan faster.

<mark><strong></strong>。</mark>


Generating different parts of a complex piece of content in parallel.

<mark>。</mark>

- **Use Case:** An agent creating a marketing email.

<mark><strong></strong>。</mark>

- **Parallel Tasks:** Generate a subject line, draft the email body, find a relevant image, and create a call-to-action button text simultaneously.

<mark><strong></strong>、、。</mark>

- **Benefit:** Assembles the final email more efficiently.

<mark><strong></strong>。</mark>


Performing multiple independent checks or validations concurrently.

<mark>。</mark>

- **Use Case:** An agent verifying user input.

<mark><strong></strong>。</mark>

- **Parallel Tasks:** Check email format, validate phone number, verify address against a database, and check for profanity simultaneously.

<mark><strong></strong>、、。</mark>

- **Benefit:** Provides faster feedback on input validity.

<mark><strong></strong>。</mark>


Processing different modalities (text, image, audio) of the same input concurrently.

<mark>、、。</mark>

- **Use Case:** An agent analyzing a social media post with text and an image.

<mark><strong></strong>。</mark>

- **Parallel Tasks:** Analyze the text for sentiment and keywords *and* analyze the image for objects and scene description simultaneously.

<mark><strong></strong>。</mark>

- **Benefit:** Integrates insights from different modalities more quickly.

<mark><strong></strong>。</mark>


Generating multiple variations of a response or output in parallel to select the best one.

<mark>。</mark>

- **Use Case:** An agent generating different creative text options.

<mark><strong></strong>。</mark>

- **Parallel Tasks:** Generate three different headlines for an article simultaneously using slightly different prompts or models.

<mark><strong></strong>。</mark>

- **Benefit:** Allows for quick comparison and selection of the best option.

<mark><strong></strong>。</mark>

Parallelization is a fundamental optimization technique in agentic design, allowing developers to build more performant and responsive applications by leveraging concurrent execution for independent tasks.

<mark>。、。</mark>

---

## Hands-On Code Example (LangChain) | <mark> LangChain</mark>

Parallel execution within the LangChain framework is facilitated by the LangChain Expression Language (LCEL). The primary method involves structuring multiple runnable components within a dictionary or list construct. When this collection is passed as input to a subsequent component in the chain, the LCEL runtime executes the contained runnables concurrently.

<mark> LangChain LangChain LCEL。。LCEL 。</mark>

In the context of LangGraph, this principle is applied to the graph's topology. Parallel workflows are defined by architecting the graph such that multiple nodes, lacking direct sequential dependencies, can be initiated from a single common node. These parallel pathways execute independently before their results can be aggregated at a subsequent convergence point in the graph.

<mark> LangGraph 。。。</mark>

The following implementation demonstrates a parallel processing workflow constructed with the LangChain framework. This workflow is designed to execute two independent operations concurrently in response to a single user query. These parallel processes are instantiated as distinct chains or functions, and their respective outputs are subsequently aggregated into a unified result.

<mark> LangChain 。</mark>

The prerequisites for this implementation include the installation of the requisite Python packages, such as langchain, langchain-community, and a model provider library like langchain-openai. Furthermore, a valid API key for the chosen language model must be configured in the local environment for authentication.

<mark> Python langchain、langchain-community langchain-openai 。 API 。</mark>

```python
import os
import asyncio
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable, RunnableParallel, RunnablePassthrough


#
# pip install langchain langchain-community langchain-openai langgraph

# For better security, load environment variables from a .env file
# .env
from dotenv import load_dotenv
load_dotenv()

# --- Configuration ---
# Ensure your API key environment variable is set (e.g., OPENAI_API_KEY)
# API ( OPENAI_API_KEY)
try:
llm: Optional[ChatOpenAI] = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
if llm:
print(f"Language model initialized: {llm.model_name}")
except Exception as e:
print(f"Error initializing language model: {e}")
llm = None


# --- Define Independent Chains ---
# These three chains represent distinct tasks that can be executed in parallel.
# --- ---
# 、。
summarize_chain: Runnable = (
ChatPromptTemplate.from_messages([
("system", "Summarize the following topic concisely:"),
("user", "{topic}")
])
| llm
| StrOutputParser()
)

questions_chain: Runnable = (
ChatPromptTemplate.from_messages([
("system", "Generate three interesting questions about the following topic:"),
("user", "{topic}")
])
| llm
| StrOutputParser()
)

terms_chain: Runnable = (
ChatPromptTemplate.from_messages([
("system", "Identify 5-10 key terms from the following topic, separated by commas:"),
("user", "{topic}")
])
| llm
| StrOutputParser()
)


# --- Build the Parallel + Synthesis Chain ---

# 1. Define the block of tasks to run in parallel. The results of these,
# along with the original topic, will be fed into the next step.
# --- 。。
map_chain = RunnableParallel(
{
"summary": summarize_chain,
"questions": questions_chain,
"key_terms": terms_chain,
"topic": RunnablePassthrough(),  # Pass the original topic through
}
)

# 2. Define the final synthesis prompt which will combine the parallel results.
# --- 。
synthesis_prompt = ChatPromptTemplate.from_messages([
("system", """Based on the following information:
Summary: {summary}
Related Questions: {questions}
Key Terms: {key_terms}
Synthesize a comprehensive answer."""),
("user", "Original topic: {topic}")
])

# 3. Construct the full chain by piping the parallel results directly
# into the synthesis prompt, followed by the LLM and output parser.
# --- 。
full_parallel_chain = map_chain | synthesis_prompt | llm | StrOutputParser()


# --- Run the Chain ---
# --- ---
async def run_parallel_example(topic: str) -> None:
"""
Asynchronously invokes the parallel processing chain with a specific topic
and prints the synthesized result.

Args:
topic: The input topic to be processed by the LangChain chains.
"""
if not llm:
print("LLM not initialized. Cannot run example.")
return

print(f"\n--- Running Parallel LangChain Example for Topic: '{topic}' ---")
try:
# The input to `ainvoke` is the single 'topic' string, which is
# then passed to each runnable in the `map_chain`.
# `ainvoke` 'topic' `map_chain` 。
response = await full_parallel_chain.ainvoke(topic)
print("\n--- Final Response ---")
print(response)
except Exception as e:
print(f"\nAn error occurred during chain execution: {e}")

if __name__ == "__main__":
test_topic = "The history of space exploration"
# In Python 3.7+, asyncio.run is the standard way to run an async function.
# Python 3.7 asyncio.run 。
asyncio.run(run_parallel_example(test_topic))
```

[Colab ](https://colab.research.google.com/drive/1uK1r9p-5sdX0ffMjAi_dbIkaMedb1sTj) [](/codes/Chapter-03-Parallelization-LangChain-Example.py)。


```text
Language model initialized: gpt-4o-mini

--- Running Parallel LangChain Example for Topic: 'The history of space exploration' ---

--- Final Response ---
The history of space exploration is a fascinating narrative marked by human curiosity, technological advancement, and international cooperation. It began in the mid-20th century, with the launch of the Soviet satellite Sputnik 1 in 1957, which signified the dawn of the Space Age. This event triggered a series of significant milestones that would shape our understanding of the cosmos.

In 1961, the Soviet space program successfully launched Yuri Gagarin, the first human to journey into space, further igniting the Space Race between the United States and the Soviet Union. This fierce competition led to rapid advancements in technology and culminated with the U.S. Apollo program, which achieved the historic Moon landing in 1969. The success of Apollo 11 not only demonstrated human capability but also inspired generations to look to the stars.

Throughout the 1970s and 1980s, space exploration expanded to include missions to Mars, the launch of revolutionary space telescopes like the Hubble Space Telescope, and the development of the Space Shuttle program. These initiatives allowed for more extended missions and the ability to deploy and service satellites, enhancing our understanding of the universe and our place within it.

The late 1990s saw the launch of the International Space Station (ISS), a landmark achievement in international cooperation in space research. The ISS has become a platform for collaboration among multiple space agencies, including NASA, Roscosmos, ESA, JAXA, and others, allowing scientists from around the world to work together in the unique environment of space.

In recent years, technological advancements, particularly in the realm of reusable rockets, have reshaped the goals and capabilities of space exploration. Companies such as SpaceX and Blue Origin have pioneered private spaceflight initiatives, driving costs down and making space more accessible than ever. This shift has reignited interest in missions targeting Mars, the Moon, and beyond, with plans for crewed missions to Mars on the horizon.

The Space Race has also had lasting effects on international cooperation in contemporary space exploration. The competitive spirit of the Cold War era has evolved into a collaborative approach, exemplified by the ISS and joint missions like the Mars rover endeavors, where multiple countries contribute resources and expertise to achieve common goals.

However, the entrance of private companies into the space exploration sector raises various ethical considerations and potential implications. These include questions about the commercialization of space, the prioritization of profit over scientific research, and concerns about space debris and environmental impacts. As private entities take on larger roles in exploration, the dynamics of scientific research and exploration beyond Earth's atmosphere may shift, necessitating new frameworks for governance and collaboration.

In summary, the history of space exploration is a rich tapestry woven from human ingenuity and cooperation. It reflects our quest to understand the universe, marked by milestones that highlight both our achievements and the challenges that lie ahead. As we move into a new era of exploration, the interplay between public and private initiatives will shape the future of our endeavors among the stars.
```

The provided Python code implements a LangChain application designed for processing a given topic efficiently by leveraging parallel execution. Note that asyncio provides concurrency, not parallelism. It achieves this on a single thread by using an event loop that intelligently switches between tasks when one is idle (e.g., waiting for a network request). This creates the effect of multiple tasks progressing at once, but the code itself is still being executed by only one thread, constrained by Python's Global Interpreter Lock (GIL).

<mark> Python LangChain 。asyncio ConcurrencyParallelism。。 Python GIL。</mark>

The code begins by importing essential modules from langchain_openai and langchain_core, including components for language models, prompts, output parsing, and runnable structures. The code attempts to initialize a ChatOpenAI instance, specifically using the "gpt-4o-mini" model, with a specified temperature for controlling creativity. A try-except block is used for robustness during the language model initialization. Three independent LangChain "chains" are then defined, each designed to perform a distinct task on the input topic. The first chain is for summarizing the topic concisely, using a system message and a user message containing the topic placeholder. The second chain is configured to generate three interesting questions related to the topic. The third chain is set up to identify between 5 and 10 key terms from the input topic, requesting them to be comma-separated. Each of these independent chains consists of a ChatPromptTemplate tailored to its specific task, followed by the initialized language model and a StrOutputParser to format the output as a string.

<mark> <code>langchain_openai</code> <code>langchain_core</code> 、、。 <code>ChatOpenAI</code> <code>gpt-4o-mini</code> <code>try-except</code> 。 LangChain 5 10 。 <code>ChatPromptTemplate</code>、 <code>StrOutputParser</code> 。</mark>

A RunnableParallel block is then constructed to bundle these three chains, allowing them to execute simultaneously. This parallel runnable also includes a RunnablePassthrough to ensure the original input topic is available for subsequent steps. A separate ChatPromptTemplate is defined for the final synthesis step, taking the summary, questions, key terms, and the original topic as input to generate a comprehensive answer. The full end-to-end processing chain, named full_parallel_chain, is created by sequencing the map_chain (the parallel block) into the synthesis prompt, followed by the language model and the output parser. An asynchronous function run_parallel_example is provided to demonstrate how to invoke this full_parallel_chain. This function takes the topic as input and uses invoke to run the asynchronous chain. Finally, the standard Python if __name__ == "__main__": block shows how to execute the run_parallel_example with a sample topic, in this case, "The history of space exploration", using asyncio.run to manage the asynchronous execution.

<mark> <code>RunnableParallel</code> 。 <code>RunnablePassthrough</code>。</mark>

<mark> <code>ChatPromptTemplate</code>、、。 <code>full_parallel_chain</code> <code>map_chain</code> 。</mark>

<mark> <code>run_parallel_example</code> <code>full_parallel_chain</code> <code>invoke</code> 。</mark>

<mark> Python <code>if __name__ == "__main__":</code> <code>asyncio.run</code> <code>run_parallel_example</code> 「」。</mark>

In essence, this code sets up a workflow where multiple LLM calls (for summarizing, questions, and terms) happen at the same time for a given topic, and their results are then combined by a final LLM call. This showcases the core idea of parallelization in an agentic workflow using LangChain.

<mark>、。 LangChain 。</mark>

---

## Hands-On Code Example (Google ADK) | <mark> Google ADK</mark>

Okay, let's now turn our attention to a concrete example illustrating these concepts within the Google ADK framework. We'll examine how the ADK primitives, such as ParallelAgent and SequentialAgent, can be applied to build an agent flow that leverages concurrent execution for improved efficiency.

<mark> Google ADK 。 ADK ParallelAgent SequentialAgent。</mark>

```python
# Part of agent.py --> Follow https: //google.github.io/adk-docs/get-started/quickstart/ to learn the setup
# --- 1. Define Researcher Sub-Agents (to run in parallel) ---
# --- ---

# Researcher 1: Renewable Energy
# 1
researcher_agent_1 = LlmAgent(
name="RenewableEnergyResearcher",
model=GEMINI_MODEL,
instruction="""You are an AI Research Assistant specializing in energy.
Research the latest advancements in 'renewable energy sources'.
Use the Google Search tool provided.
Summarize your key findings concisely (1-2 sentences).
Output *only* the summary.
""",
description="Researches renewable energy sources.",
tools=[google_search],
# Store result in state for the merger agent
output_key="renewable_energy_result"
)

# Researcher 2: Electric Vehicles
# 2
researcher_agent_2 = LlmAgent(
name="EVResearcher",
model=GEMINI_MODEL,
instruction="""You are an AI Research Assistant specializing in transportation.
Research the latest developments in 'electric vehicle technology'.
Use the Google Search tool provided.
Summarize your key findings concisely (1-2 sentences).
Output *only* the summary.
""",
description="Researches electric vehicle technology.",
tools=[google_search],
# Store result in state for the merger agent
output_key="ev_technology_result"
)

# Researcher 3: Carbon Capture
# 3
researcher_agent_3 = LlmAgent(
name="CarbonCaptureResearcher",
model=GEMINI_MODEL,
instruction="""You are an AI Research Assistant specializing in climate solutions.
Research the current state of 'carbon capture methods'.
Use the Google Search tool provided.
Summarize your key findings concisely (1-2 sentences).
Output *only* the summary.
""",
description="Researches carbon capture methods.",
tools=[google_search],
# Store result in state for the merger agent
output_key="carbon_capture_result"
)

# --- 2. Create the ParallelAgent (Runs researchers concurrently) ---
# This agent orchestrates the concurrent execution of the researchers.
# It finishes once all researchers have completed and stored their results in state.
# --- 2. ParallelAgent ---
# 。
# 。
parallel_research_agent = ParallelAgent(
name="ParallelWebResearchAgent",
sub_agents=[researcher_agent_1, researcher_agent_2, researcher_agent_3],
description="Runs multiple research agents in parallel to gather information."
)

# --- 3. Define the Merger Agent (Runs *after* the parallel agents) ---
# This agent takes the results stored in the session state by the parallel agents
# and synthesizes them into a single, structured response with attributions.
# --- 3. ---
#
# 。
merger_agent = LlmAgent(
name="SynthesisAgent",
model=GEMINI_MODEL,  # Or potentially a more powerful model if needed for synthesis
instruction="""You are an AI Assistant responsible for combining research findings into a structured report.

Your primary task is to synthesize the following research summaries, clearly attributing findings to their source areas. Structure your response using headings for each topic. Ensure the report is coherent and integrates the key points smoothly.

**Crucially: Your entire response MUST be grounded *exclusively* on the information provided in the 'Input Summaries' below. Do NOT add any external knowledge, facts, or details not present in these specific summaries.**

**Input Summaries:**

*   **Renewable Energy:**
{renewable_energy_result}

*   **Electric Vehicles:**
{ev_technology_result}

*   **Carbon Capture:**
{carbon_capture_result}

**Output Format:**

## Summary of Recent Sustainable Technology Advancements

### Renewable Energy Findings
(Based on RenewableEnergyResearcher's findings)
[Synthesize and elaborate *only* on the renewable energy input summary provided above.]

### Electric Vehicle Findings
(Based on EVResearcher's findings)
[Synthesize and elaborate *only* on the EV input summary provided above.]

### Carbon Capture Findings
(Based on CarbonCaptureResearcher's findings)
[Synthesize and elaborate *only* on the carbon capture input summary provided above.]

### Overall Conclusion
[Provide a brief (1-2 sentence) concluding statement that connects *only* the findings presented above.]

Output *only* the structured report following this format. Do not include introductory or concluding phrases outside this structure, and strictly adhere to using only the provided input summary content.
""",
description="Combines research findings from parallel agents into a structured, cited report, strictly grounded on provided inputs.",
# No tools needed for merging
# No output_key needed here, as its direct response is the final output of the sequence
)


# --- 4. Create the SequentialAgent (Orchestrates the overall flow) ---
# This is the main agent that will be run. It first executes the ParallelAgent
# to populate the state, and then executes the MergerAgent to produce the final output.
# --- 4. SequentialAgent ---
# 。 ParallelAgent
# MergerAgent 。
sequential_pipeline_agent = SequentialAgent(
name="ResearchAndSynthesisPipeline",
# Run parallel research first, then merge
sub_agents=[parallel_research_agent, merger_agent],
description="Coordinates parallel research and synthesizes the results."
)

root_agent = sequential_pipeline_agent
```

[Colab ](https://colab.research.google.com/drive/1gcztL9ebeqGeWl-_0E9FeMcHMOsknB0I) [](/codes/Chapter-03-Parallelization-ADK-Example.py)。

This code defines a multi-agent system used to research and synthesize information on sustainable technology advancements. It sets up three LlmAgent instances to act as specialized researchers. ResearcherAgent_1 focuses on renewable energy sources, ResearcherAgent_2 researches electric vehicle technology, and ResearcherAgent_3 investigates carbon capture methods. Each researcher agent is configured to use a GEMINI_MODEL and the google_search tool. They are instructed to summarize their findings concisely (1-2 sentences) and store these summaries in the session state using output_key.

<mark>。<code>ResearcherAgent_1</code> <code>ResearcherAgent_2</code> <code>ResearcherAgent_3</code> 。 <code>GEMINI_MODEL</code> <code>google_search</code> <code>output_key</code> 。</mark>

A ParallelAgent named ParallelWebResearchAgent is then created to run these three researcher agents concurrently. This allows the research to be conducted in parallel, potentially saving time. The ParallelAgent completes its execution once all its sub-agents (the researchers) have finished and populated the state.

<mark> <code>ParallelWebResearchAgent</code> 。。。</mark>

Next, a MergerAgent (also an LlmAgent) is defined to synthesize the research results. This agent takes the summaries stored in the session state by the parallel researchers as input. Its instruction emphasizes that the output must be strictly based only on the provided input summaries, prohibiting the addition of external knowledge. The MergerAgent is designed to structure the combined findings into a report with headings for each topic and a brief overall conclusion.

<mark> <code>MergerAgent</code> <code>LlmAgent</code>。。。<code>MergerAgent</code> 。</mark>

Finally, a SequentialAgent named ResearchAndSynthesisPipeline is created to orchestrate the entire workflow. As the primary controller, this main agent first executes the ParallelAgent to perform the research. Once the ParallelAgent is complete, the SequentialAgent then executes the MergerAgent to synthesize the collected information. The sequential_pipeline_agent is set as the root_agent, representing the entry point for running this multi-agent system. The overall process is designed to efficiently gather information from multiple sources in parallel and then combine it into a single, structured report.

<mark> <code>ResearchAndSynthesisPipeline</code> 。 <code>ParallelAgent</code> 。<code>ParallelAgent</code> <code>SequentialAgent</code> <code>MergerAgent</code> 。<code>sequential_pipeline_agent</code> <code>root_agent</code>。。</mark>

---

## At a Glance | <mark></mark>

**What:** Many agentic workflows involve multiple sub-tasks that must be completed to achieve a final goal. A purely sequential execution, where each task waits for the previous one to finish, is often inefficient and slow. This latency becomes a significant bottleneck when tasks depend on external I/O operations, such as calling different APIs or querying multiple databases. Without a mechanism for concurrent execution, the total processing time is the sum of all individual task durations, hindering the system's overall performance and responsiveness.

<mark><strong></strong>。。 I/O API 。。</mark>

**Why:** The Parallelization pattern provides a standardized solution by enabling the simultaneous execution of independent tasks. It works by identifying components of a workflow, like tool usages or LLM calls, that do not rely on each other's immediate outputs. Agentic frameworks like LangChain and the Google ADK provide built-in constructs to define and manage these concurrent operations. For instance, a main process can invoke several sub-tasks that run in parallel and wait for all of them to complete before proceeding to the next step. By running these independent tasks at the same time rather than one after another, this pattern drastically reduces the total execution time.

<mark><strong></strong>。。 LangChain Google ADK 。。。</mark>

**Rule of thumb:** Use this pattern when a workflow contains multiple independent operations that can run simultaneously, such as fetching data from several APIs, processing different chunks of data, or generating multiple pieces of content for later synthesis.

<mark><strong></strong> API 、。</mark>


![Parallelization Pattern](/images/chapter03_fig2.jpg)

Fig.2: Parallelization design pattern

<mark> 2</mark>

---

## Key Takeaways | <mark></mark>

Here are the key takeaways:

<mark></mark>

- Parallelization is a pattern for executing independent tasks concurrently to improve efficiency.

<mark>。</mark>

- It is particularly useful when tasks involve waiting for external resources, such as API calls.

<mark> API。</mark>

- The adoption of a concurrent or parallel architecture introduces substantial complexity and cost, impacting key development phases such as design, debugging, and system logging.

<mark>、。</mark>

- Frameworks like LangChain and Google ADK provide built-in support for defining and managing parallel execution.

<mark> LangChain Google ADK 。</mark>

- In LangChain Expression Language (LCEL), RunnableParallel is a key construct for running multiple runnables side-by-side.

<mark> LangChain LCELRunnableParallel 。</mark>

- Google ADK can facilitate parallel execution through LLM-Driven Delegation, where a Coordinator agent's LLM identifies independent sub-tasks and triggers their concurrent handling by specialized sub-agents.

<mark>Google ADK 。</mark>

- Parallelization helps reduce overall latency and makes agentic systems more responsive for complex tasks.

<mark>。</mark>

---

## Conclusion | <mark></mark>

The parallelization pattern is a method for optimizing computational workflows by concurrently executing independent sub-tasks. This approach reduces overall latency, particularly in complex operations that involve multiple model inferences or calls to external services.

<mark>。。</mark>

Frameworks provide distinct mechanisms for implementing this pattern. In LangChain, constructs like RunnableParallel are used to explicitly define and execute multiple processing chains simultaneously. In contrast, frameworks like the Google Agent Developer Kit (ADK) can achieve parallelization through multi-agent delegation, where a primary coordinator model assigns different sub-tasks to specialized agents that can operate concurrently.

<mark>。 LangChain RunnableParallel 。Google ADK 。</mark>

By integrating parallel processing with sequential (chaining) and conditional (routing) control flows, it becomes possible to construct sophisticated, high-performance computational systems capable of efficiently managing diverse and complex tasks.

<mark>。</mark>

---

## References | <mark></mark>

Here are some resources for further reading on the Parallelization pattern and related concepts:

<mark></mark>

1. LangChain Expression Language (LCEL) Documentation (Parallelism): [https://python.langchain.com/docs/concepts/lcel/](https://python.langchain.com/docs/concepts/lcel/)

<mark>LangChain [https://python.langchain.com/docs/concepts/lcel/](https://python.langchain.com/docs/concepts/lcel/)</mark>

2. Google Agent Developer Kit (ADK) Documentation (Multi-Agent Systems): [https://google.github.io/adk-docs/agents/multi-agents/](https://google.github.io/adk-docs/agents/multi-agents/)

<mark>Google ADK [https://google.github.io/adk-docs/agents/multi-agents/](https://google.github.io/adk-docs/agents/multi-agents/)</mark>

3. Python asyncio Documentation: [https://docs.python.org/3/library/asyncio.html](https://docs.python.org/3/library/asyncio.html)

<mark>Python asyncio [https://docs.python.org/3/library/asyncio.html](https://docs.python.org/3/library/asyncio.html)</mark>
