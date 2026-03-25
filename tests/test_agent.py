from hello_agents import (
    HelloAgentsLLM, SimpleAgent, ReActAgent, ReflectionAgent, PlanAndSolveAgent,
    ToolRegistry
)
from agents.gmmp_agent import GmmpAgent

# 1. 创建LLM
llm = HelloAgentsLLM()

# 2. 创建不同类型的Agent（使用默认配置）
paper_search_agent = GmmpAgent(
    name="论文搜索助手",
    llm=llm,
    tool_registry=ToolRegistry(),
    max_react_steps=5,
)


# 执行agent
print(react_agent.run("找找今天的RSVG论文"))
