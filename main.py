from hello_agents import ReActAgent, ToolRegistry
from hello_agents.agents.function_call_agent import FunctionCallAgent
# from hello_agents.tools.builtin import calculate
from hello_agents import HelloAgentsLLM, SimpleAgent
from tools.paper_search_tool import PaperSearchTool
from dotenv import load_dotenv
load_dotenv()
# 导入yaml提示词
import os
import yaml
from typing import Optional, List, Tuple
# 注册工具
from hello_agents.tools.registry import ToolRegistry
from hello_agents.tools.base import Tool, ToolParameter

import json


# 读取配置文件
#ollama
OLLAMA_LLM_BASE_URL=os.getenv("OLLAMA_LLM_BASE_URL")
OLLAMA_LLM_MODEL_ID=os.getenv("OLLAMA_LLM_MODEL_ID")
OLLAMA_LLM_API_KEY=os.getenv("OLLAMA_LLM_API_KEY")

# deepseek
CHATANYWHERE_LLM_API_KEY=os.getenv("CHATANYWHERE_LLM_API_KEY")
CHATANYWHERE_LLM_MODEL_ID=os.getenv("CHATANYWHERE_LLM_MODEL_ID")
CHATANYWHERE_LLM_BASE_URL=os.getenv("CHATANYWHERE_LLM_BASE_URL")





def _load_system_template(role: str) -> str:
    '''
    从prompts模版文件中读取指定角色的system prompt模版
    '''
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "prompts"))
    yaml_path = os.path.join(base_dir, "system_prompts.yaml")
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    entry = data.get(role)
    if not entry or "template" not in entry:
        raise ValueError(f"system_prompts.yaml missing template for role: {role}")
    return entry["template"]



# main.py - 智能旅行助手完整流程
def main():
    # 初始化LLM和Agent
    # llm_1 = HelloAgentsLLM(model = CHATANYWHERE_LLM_MODEL_ID, api_key = CHATANYWHERE_LLM_API_KEY, base_url = CHATANYWHERE_LLM_BASE_URL)  
    llm_2 = HelloAgentsLLM(model = OLLAMA_LLM_MODEL_ID, api_key = OLLAMA_LLM_API_KEY, base_url = OLLAMA_LLM_BASE_URL,timeout=600)  
    
    # 配置提示词
    search_prompt = _load_system_template("search_agent")

    # 注册工具
    registry = ToolRegistry()
    registry.register_tool(PaperSearchTool())

    # 创建Agent
    agents = {
        "search": ReActAgent(name="search_agent",system_prompt=search_prompt, llm=llm_2,tool_registry=registry),
        "FunctionCallAgent": FunctionCallAgent(name="function_call_agent", llm=llm_2, tool_registry=registry),
        # "info": InfoAgent(llm=llm_1),
        # "booking": BookingAgent(llm=llm_1),
        # "user": UserAgent(llm=llm_1)
    }


    #  创建协作工作流
    # workflow = create_travel_workflow(agents)
    
    # 3. 初始化状态
    # initial_state = TravelState(
    #     user_request="规划厦门3日游，预算5000元，喜欢历史文化",
    #     constraints={"budget": 5000, "days": 3, "interests": ["history"]}
    # )
    
    # 4. 执行工作流
    # final_state = workflow.invoke(initial_state)
    
    # 5. 输出结果
    result = agents["FunctionCallAgent"].run("关于Remote Sensing Visual Grounding 的论文有哪些，展示所有")
    print(f"最终行程方案：{result}")

if __name__ == "__main__":
    main()