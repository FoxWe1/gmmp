from hello_agents import ReActAgent, ToolRegistry
# from hello_agents.tools.builtin import calculate
from hello_agents import HelloAgentsLLM, SimpleAgent
from dotenv import load_dotenv
load_dotenv()
# 读取配置文件
#ollama
OLLAMA_LLM_BASE_URL=os.getenv("OLLAMA_LLM_BASE_URL")
OLLAMA_LLM_MODEL_ID=os.getenv("OLLAMA_LLM_MODEL_ID")
OLLAMA_LLM_API_KEY=os.getenv("OLLAMA_LLM_API_KEY")

# deepseek
CHATANYWHERE_LLM_API_KEY=os.getenv("CHATANYWHERE_LLM_API_KEY")
CHATANYWHERE_LLM_MODEL_ID=os.getenv("CHATANYWHERE_LLM_MODEL_ID")
CHATANYWHERE_LLM_BASE_URL=os.getenv("CHATANYWHERE_LLM_BASE_URL")


# 注册工具
registry = ToolRegistry()
# registry.register_function("calculate", "计算工具", calculate)

# 查找文献用ReActAgent
agent = ReActAgent("工具助手", llm_2, registry)
response = agent.run("计算 123 * 456")


# main.py - 智能旅行助手完整流程
def main():
    # 初始化LLM和Agent
    llm_1 = HelloAgentsLLM(model = CHATANYWHERE_LLM_MODEL_ID, api_key = CHATANYWHERE_LLM_API_KEY, base_url = CHATANYWHERE_LLM_BASE_URL)  
    llm_2 = HelloAgentsLLM(model = OLLAMA_LLM_MODEL_ID, api_key = OLLAMA_LLM_API_KEY, base_url = OLLAMA_LLM_BASE_URL)  
    agents = {
        "planner": PlannerAgent(llm=llm_1),
        "info": InfoAgent(llm=llm_1),
        "booking": BookingAgent(llm=llm_1),
        "user": UserAgent(llm=llm_1)
    }
    
    #  创建协作工作流
    workflow = create_travel_workflow(agents)
    
    # 3. 初始化状态
    initial_state = TravelState(
        user_request="规划厦门3日游，预算5000元，喜欢历史文化",
        constraints={"budget": 5000, "days": 3, "interests": ["history"]}
    )
    
    # 4. 执行工作流
    final_state = workflow.invoke(initial_state)
    
    # 5. 输出结果
    print("最终行程方案：")
    print(json.dumps(final_state.itinerary_draft, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()