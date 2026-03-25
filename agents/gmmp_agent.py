from typing import Optional, List
from hello_agents.core.agent import Agent
from hello_agents.core.llm import HelloAgentsLLM
from hello_agents.core.config import Config
from hello_agents.core.message import Message
from hello_agents.tools.registry import ToolRegistry
# 导入yaml提示词
import os
import yaml
from typing import Optional, List, Tuple

class GmmpAgent(Agent):
    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        tool_registry: Optional[ToolRegistry] = None,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
        max_steps: int = 5,
        custom_prompt: Optional[str] = None,
        role : str = ""
    ):
        """
        初始化ReActAgent

        Args:
            name: Agent名称
            llm: LLM实例
            tool_registry: 工具注册表（可选，如果不提供则创建空的工具注册表）
            system_prompt: 系统提示词
            config: 配置对象
            max_steps: 最大执行步数
            custom_prompt: 自定义提示词模板
        """
        super().__init__(name, llm, system_prompt, config)

        # 如果没有提供tool_registry，创建一个空的
        if tool_registry is None:
            self.tool_registry = ToolRegistry()
        else:
            self.tool_registry = tool_registry

        self.max_steps = max_steps
        self.current_history: List[str] = []

        # 设置提示词模板：用户自定义优先，否则使用默认模板
        self.prompt_template = custom_prompt if custom_prompt else _load_system_template(role)
        
    def add_tool(self, tool):
        """
        添加工具到工具注册表
        支持MCP工具的自动展开

        Args:
            tool: 工具实例(可以是普通Tool或MCPTool)
        """
        # 检查是否是MCP工具
        if hasattr(tool, 'auto_expand') and tool.auto_expand:
            # MCP工具会自动展开为多个工具
            if hasattr(tool, '_available_tools') and tool._available_tools:
                for mcp_tool in tool._available_tools:
                    # 创建包装工具
                    from ..tools.base import Tool
                    wrapped_tool = Tool(
                        name=f"{tool.name}_{mcp_tool['name']}",
                        description=mcp_tool.get('description', ''),
                        func=lambda input_text, t=tool, tn=mcp_tool['name']: t.run({
                            "action": "call_tool",
                            "tool_name": tn,
                            "arguments": {"input": input_text}
                        })
                    )
                    self.tool_registry.register_tool(wrapped_tool)
                print(f"✅ MCP工具 '{tool.name}' 已展开为 {len(tool._available_tools)} 个独立工具")
            else:
                self.tool_registry.register_tool(tool)
        else:
            self.tool_registry.register_tool(tool)

    def run(self, input_text: str, **kwargs) -> str:
        """
        运行ReAct Agent
        
        Args:
            input_text: 用户问题
            **kwargs: 其他参数
            
        Returns:
            最终答案
        """
        self.current_history = []
        current_step = 0
        
        print(f"\n🤖 {self.name} 开始处理问题: {input_text}")

        #
        while True:
            current_step += 1
            print(f"\n--- 第 {current_step} 步 ---")
            
            # 构建提示词
            tools_desc = self.tool_registry.get_tools_description() #获得工具描述
            history_str = "\n".join(self.current_history) # 该对话的历史信息
            prompt = self.prompt_template.format(
                tools=tools_desc,
                question=input_text,
                history=history_str
            )
            
            # 调用LLM
            messages = [{"role": "user", "content": prompt}]
            response_text = self.llm.invoke(messages, **kwargs)
            
            if not response_text:
                print("❌ 错误：LLM未能返回有效响应。")
                break
            
            # 解析输出
            thought, action = self._parse_output(response_text)
            
            if thought:
                print(f"🤔 思考: {thought}")
            
            if not action:
                print("⚠️ 警告：未能解析出有效的Action，流程终止。")
                break
            
            # 检查是否完成
            if action.startswith("Finish"):
                final_answer = self._parse_action_input(action)
                print(f"🎉 最终答案: {final_answer}")
                
                # 保存到历史记录
                self.add_message(Message(input_text, "user"))
                self.add_message(Message(final_answer, "assistant"))
                
                return final_answer
            
            # 执行工具调用
            tool_name, tool_input = self._parse_action(action)
            if not tool_name or tool_input is None:
                self.current_history.append("Observation: 无效的Action格式，请检查。")
                continue
            
            print(f"🎬 行动: {tool_name}[{tool_input}]")
            
            # 调用工具
            observation = self.tool_registry.execute_tool(tool_name, tool_input)
            print(f"👀 观察: {observation}")
            
            # 更新历史
            self.current_history.append(f"Action: {action}")
            self.current_history.append(f"Observation: {observation}")
        
        print("⏰ 已达到最大步数，流程终止。")
        final_answer = "抱歉，我无法在限定步数内完成这个任务。"
        
        # 保存到历史记录
        self.add_message(Message(input_text, "user"))
        self.add_message(Message(final_answer, "assistant"))
        
        return final_answer
    
    def _parse_output(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """解析LLM输出，提取思考和行动"""
        thought_match = re.search(r"Thought: (.*)", text)
        action_match = re.search(r"Action: (.*)", text)
        
        thought = thought_match.group(1).strip() if thought_match else None
        action = action_match.group(1).strip() if action_match else None
        
        return thought, action
    
    def _parse_action(self, action_text: str) -> Tuple[Optional[str], Optional[str]]:
        """解析行动文本，提取工具名称和输入"""
        match = re.match(r"(\w+)\[(.*)\]", action_text)
        if match:
            return match.group(1), match.group(2)
        return None, None
    
    def _parse_action_input(self, action_text: str) -> str:
        """解析行动输入"""
        match = re.match(r"\w+\[(.*)\]", action_text)
        return match.group(1) if match else ""


def _load_system_template(role: str) -> str:
    '''
    从prompts模版文件中读取指定角色的system prompt模版
    '''
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "prompts"))
    yaml_path = os.path.join(base_dir, "system_prompts.yaml")
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    entry = data.get(role)
    if not entry or "template" not in entry:
        raise ValueError(f"system_prompts.yaml missing template for role: {role}")
    return entry["template"]