from hello_agents import HelloAgentsLLM, ReActAgent, ToolRegistry
from dotenv import load_dotenv
# 加载环境变量
load_dotenv()

'''
使用ReActAgent范式作为该项目的agent
'''

# 创建LLM
llm = HelloAgentsLLM(
    temperature=0,
    timeout=60,
    max_tokens=2048
)

# 创建工具注册表
registry = ToolRegistry()

# 创建ReActAgent（使用默认提示词）
agent = ReActAgent(
    name="运算助手",
    llm=llm,
    tool_registry=registry,
    max_steps=3,
)

# 使用工具解决问题
response = agent.run("3*5+2^2的结果是多少？")
# print(response)