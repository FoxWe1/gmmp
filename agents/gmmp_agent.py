"""ReAct Agent实现 - 推理与行动结合的智能体"""

import re
from typing import Optional, List, Tuple
from ..core.agent import Agent
from ..core.llm import HelloAgentsLLM
from ..core.config import Config
from ..core.message import Message
from ..tools.registry import ToolRegistry
from hello_agents.core import Agent

DEFAULT_REACT_PROMPT = "你是一个小助手"


class GmmpAgent(Agent):
    """
    GmmpAgent 
    结合推理和行动的智能体，能够：
    1. 分析问题并制定行动计划
    2. 调用外部工具获取信息，functioncall调用
    3. 基于观察结果进行推理
    4. 迭代执行直到得出最终答案
    5. human-in-loop
    6. 根据用户交互继续循环
    
    这是一个基于React的范式，特别适合需要外部信息的任务。
    """
    
    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        tool_registry: Optional[ToolRegistry] = None,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
        max_steps: int = 5,
        custom_prompt: Optional[str] = None
    ):
        """
        初始化Agent

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
        self.prompt_template = custom_prompt if custom_prompt else DEFAULT_REACT_PROMPT

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
        运行 Agent
        
        Args:
            input_text: 用户问题
            **kwargs: 其他参数
            
        Returns:
            最终答案
        """
        self.current_history = []
        current_step = 0
        
        print(f"\n🤖 {self.name} 开始处理问题: {input_text}")
        
        while current_step < self.max_steps:
            current_step += 1
            print(f"\n--- 第 {current_step} 步 ---")
            
            # 构建提示词
            tools_desc = self.tool_registry.get_tools_description()
            history_str = "\n".join(self.current_history)
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






# class FunctionCallAgent(Agent):
#     """基于OpenAI原生函数调用机制的Agent"""

#     def __init__(
#         self,
#         name: str,
#         llm: HelloAgentsLLM,
#         system_prompt: Optional[str] = None,
#         config: Optional[Config] = None,
#         tool_registry: Optional["ToolRegistry"] = None,
#         enable_tool_calling: bool = True,
#         default_tool_choice: Union[str, dict] = "auto",
#         max_tool_iterations: int = 3,
#     ):
#         super().__init__(name, llm, system_prompt, config)
#         self.tool_registry = tool_registry
#         self.enable_tool_calling = enable_tool_calling and tool_registry is not None
#         self.default_tool_choice = default_tool_choice
#         self.max_tool_iterations = max_tool_iterations

#     def _get_system_prompt(self) -> str:
#         """构建系统提示词，注入工具描述"""
#         base_prompt = self.system_prompt or "你是一个可靠的AI助理，能够在需要时调用工具完成任务。"

#         if not self.enable_tool_calling or not self.tool_registry:
#             return base_prompt

#         tools_description = self.tool_registry.get_tools_description()
#         if not tools_description or tools_description == "暂无可用工具":
#             return base_prompt

#         prompt = base_prompt + "\n\n## 可用工具\n"
#         prompt += "当你判断需要外部信息或执行动作时，可以直接通过函数调用使用以下工具：\n"
#         prompt += tools_description + "\n"
#         prompt += "\n请主动决定是否调用工具，合理利用多次调用来获得完备答案。"
#         return prompt

#     def _build_tool_schemas(self) -> list[dict[str, Any]]:
#         '''
#         将ToolRegistry 里注册的所有工具，转换成一份符合 OpenAI “tools / function calling” 规范的 JSON Schema 列表
#         供后续调用
#         '''
#         if not self.enable_tool_calling or not self.tool_registry:
#             return []

#         schemas: list[dict[str, Any]] = []

#         # Tool对象 schema生成
#         for tool in self.tool_registry.get_all_tools():
#             properties: Dict[str, Any] = {}
#             required: list[str] = []

#             try:
#                 parameters = tool.get_parameters()
#             except Exception:
#                 parameters = []

#             for param in parameters:
#                 properties[param.name] = {
#                     "type": _map_parameter_type(param.type),
#                     "description": param.description or ""
#                 }
#                 if param.default is not None:
#                     properties[param.name]["default"] = param.default
#                 if getattr(param, "required", True):
#                     required.append(param.name)

#             schema: dict[str, Any] = {
#                 "type": "function",
#                 "function": {
#                     "name": tool.name,
#                     "description": tool.description or "",
#                     "parameters": {
#                         "type": "object",
#                         "properties": properties
#                     }
#                 }
#             }
#             if required:
#                 schema["function"]["parameters"]["required"] = required
#             schemas.append(schema)

#         # register_function 注册的工具（直接访问内部结构）
#         function_map = getattr(self.tool_registry, "_functions", {})
#         for name, info in function_map.items():
#             schemas.append(
#                 {
#                     "type": "function",
#                     "function": {
#                         "name": name,
#                         "description": info.get("description", ""),
#                         "parameters": {
#                             "type": "object",
#                             "properties": {
#                                 "input": {
#                                     "type": "string",
#                                     "description": "输入文本"
#                                 }
#                             },
#                             "required": ["input"]
#                         }
#                     }
#                 }
#             )

#         return schemas

#     @staticmethod
#     def _extract_message_content(raw_content: Any) -> str:
#         """从OpenAI响应的message.content中安全提取文本"""
#         if raw_content is None:
#             return ""
#         if isinstance(raw_content, str):
#             return raw_content
#         if isinstance(raw_content, list):
#             parts: list[str] = []
#             for item in raw_content:
#                 text = getattr(item, "text", None)
#                 if text is None and isinstance(item, dict):
#                     text = item.get("text")
#                 if text:
#                     parts.append(text)
#             return "".join(parts)
#         return str(raw_content)

#     @staticmethod
#     def _parse_function_call_arguments(arguments: Optional[str]) -> dict[str, Any]:
#         """解析模型返回的JSON字符串参数"""
#         if not arguments:
#             return {}

#         try:
#             parsed = json.loads(arguments)
#             return parsed if isinstance(parsed, dict) else {}
#         except json.JSONDecodeError:
#             return {}

#     def _convert_parameter_types(self, tool_name: str, param_dict: dict[str, Any]) -> dict[str, Any]:
#         """根据工具定义尽可能转换参数类型"""
#         if not self.tool_registry:
#             return param_dict

#         tool = self.tool_registry.get_tool(tool_name)
#         if not tool:
#             return param_dict

#         try:
#             tool_params = tool.get_parameters()
#         except Exception:
#             return param_dict

#         type_mapping = {param.name: param.type for param in tool_params}
#         converted: dict[str, Any] = {}

#         for key, value in param_dict.items():
#             param_type = type_mapping.get(key)
#             if not param_type:
#                 converted[key] = value
#                 continue

#             try:
#                 normalized = param_type.lower()
#                 if normalized in {"number", "float"}:
#                     converted[key] = float(value)
#                 elif normalized in {"integer", "int"}:
#                     converted[key] = int(value)
#                 elif normalized in {"boolean", "bool"}:
#                     if isinstance(value, bool):
#                         converted[key] = value
#                     elif isinstance(value, (int, float)):
#                         converted[key] = bool(value)
#                     elif isinstance(value, str):
#                         converted[key] = value.lower() in {"true", "1", "yes"}
#                     else:
#                         converted[key] = bool(value)
#                 else:
#                     converted[key] = value
#             except (TypeError, ValueError):
#                 converted[key] = value

#         return converted

#     def _execute_tool_call(self, tool_name: str, arguments: dict[str, Any]) -> str:
#         """执行工具调用并返回字符串结果"""
#         if not self.tool_registry:
#             return "❌ 错误：未配置工具注册表"

#         tool = self.tool_registry.get_tool(tool_name)
#         if tool:
#             try:
#                 typed_arguments = self._convert_parameter_types(tool_name, arguments)
#                 return tool.run(typed_arguments)
#             except Exception as exc:
#                 return f"❌ 工具调用失败：{exc}"

#         func = self.tool_registry.get_function(tool_name)
#         if func:
#             try:
#                 input_text = arguments.get("input", "")
#                 return func(input_text)
#             except Exception as exc:
#                 return f"❌ 工具调用失败：{exc}"

#         return f"❌ 错误：未找到工具 '{tool_name}'"

#     def _invoke_with_tools(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]], tool_choice: Union[str, dict], **kwargs):
#         """调用底层OpenAI客户端执行函数调用"""
#         client = getattr(self.llm, "_client", None)
#         if client is None:
#             raise RuntimeError("HelloAgentsLLM 未正确初始化客户端，无法执行函数调用。")

#         client_kwargs = dict(kwargs)
#         client_kwargs.setdefault("temperature", self.llm.temperature)
#         if self.llm.max_tokens is not None:
#             client_kwargs.setdefault("max_tokens", self.llm.max_tokens)

#         return client.chat.completions.create(
#             model=self.llm.model,
#             messages=messages,
#             tools=tools,
#             tool_choice=tool_choice,
#             **client_kwargs,
#         )

#     def run(
#         self,
#         input_text: str,
#         *,
#         max_tool_iterations: Optional[int] = None,
#         tool_choice: Optional[Union[str, dict]] = None,
#         **kwargs,
#     ) -> str:
#         """
#         执行函数调用范式的对话流程
#         """
#         # 构造提示词+第一段历史消息
#         messages: list[dict[str, Any]] = []
#         system_prompt = self._get_system_prompt()
#         messages.append({"role": "system", "content": system_prompt})

#         # 加载历史信息
#         for msg in self._history:
#             messages.append({"role": msg.role, "content": msg.content})

#         messages.append({"role": "user", "content": input_text})

#         #ToolRegistry 里注册的所有工具，转换成一份符合 OpenAI “tools / function calling” 规范的 JSON Schema 列表
#         # 供后续调用
#         tool_schemas = self._build_tool_schemas()

#         if not tool_schemas:
#             response_text = self.llm.invoke(messages, **kwargs)
#             self.add_message(Message(input_text, "user"))
#             self.add_message(Message(response_text, "assistant"))
#             return response_text

#         iterations_limit = max_tool_iterations if max_tool_iterations is not None else self.max_tool_iterations
#         effective_tool_choice: Union[str, dict] = tool_choice if tool_choice is not None else self.default_tool_choice

#         current_iteration = 0
#         final_response = ""

#         while current_iteration < iterations_limit:
#             # 执行调用函数
#             response = self._invoke_with_tools(
#                 messages,
#                 tools=tool_schemas,
#                 tool_choice=effective_tool_choice,
#                 **kwargs,
#             )

#             choice = response.choices[0]
#             assistant_message = choice.message
#             content = self._extract_message_content(assistant_message.content)
#             tool_calls = list(assistant_message.tool_calls or [])

#             if tool_calls:
#                 assistant_payload: dict[str, Any] = {"role": "assistant", "content": content}
#                 assistant_payload["tool_calls"] = []
#                 for tool_call in tool_calls:
#                     assistant_payload["tool_calls"].append(
#                         {
#                             "id": tool_call.id,
#                             "type": tool_call.type,
#                             "function": {
#                                 "name": tool_call.function.name,
#                                 "arguments": tool_call.function.arguments,
#                             },
#                         }
#                     )
#                 messages.append(assistant_payload)

#                 for tool_call in tool_calls:
#                     tool_name = tool_call.function.name
#                     arguments = self._parse_function_call_arguments(tool_call.function.arguments)
#                     # 执行函数
#                     result = self._execute_tool_call(tool_name, arguments)
#                     messages.append(
#                         {
#                             "role": "tool",
#                             "tool_call_id": tool_call.id,
#                             "name": tool_name,
#                             "content": result,
#                         }
#                     )

#                 current_iteration += 1
#                 continue

#             final_response = content
#             messages.append({"role": "assistant", "content": final_response})
#             break

#         if current_iteration >= iterations_limit and not final_response:
#             final_choice = self._invoke_with_tools(
#                 messages,
#                 tools=tool_schemas,
#                 tool_choice="none",
#                 **kwargs,
#             )
#             final_response = self._extract_message_content(final_choice.choices[0].message.content)
#             messages.append({"role": "assistant", "content": final_response})

#         self.add_message(Message(input_text, "user"))
#         self.add_message(Message(final_response, "assistant"))
#         return final_response

#     def add_tool(self, tool) -> None:
#         """便捷方法：将工具注册到当前Agent"""
#         if not self.tool_registry:
#             from ..tools.registry import ToolRegistry

#             self.tool_registry = ToolRegistry()
#             self.enable_tool_calling = True

#         if hasattr(tool, "auto_expand") and getattr(tool, "auto_expand"):
#             expanded_tools = tool.get_expanded_tools()
#             if expanded_tools:
#                 for expanded_tool in expanded_tools:
#                     self.tool_registry.register_tool(expanded_tool)
#                 print(f"✅ MCP工具 '{tool.name}' 已展开为 {len(expanded_tools)} 个独立工具")
#                 return

#         self.tool_registry.register_tool(tool)

#     def remove_tool(self, tool_name: str) -> bool:
#         if self.tool_registry:
#             before = set(self.tool_registry.list_tools())
#             self.tool_registry.unregister(tool_name)
#             after = set(self.tool_registry.list_tools())
#             return tool_name in before and tool_name not in after
#         return False

#     def list_tools(self) -> list[str]:
#         if self.tool_registry:
#             return self.tool_registry.list_tools()
#         return []

#     def has_tools(self) -> bool:
#         return self.enable_tool_calling and self.tool_registry is not None

#     def stream_run(self, input_text: str, **kwargs) -> Iterator[str]:
#         """流式调用暂未实现，直接回退到一次性调用"""
#         result = self.run(input_text, **kwargs)
#         yield result
