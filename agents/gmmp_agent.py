'''
init
add_tool
run
_parse_output
_parse_action
_parse_action_input
'''
from typing import Optional, List
from hello_agents.core.agent import Agent
from hello_agents.core.llm import HelloAgentsLLM
from hello_agents.core.config import Config
from hello_agents.core.message import Message
from hello_agents.tools.registry import ToolRegistry
from hello_agents.agents.react_agent import ReActAgent
from hello_agents.agents.reflection_agent import ReflectionAgent


class GmmpAgent(Agent):
    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        tool_registry: ToolRegistry,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
        max_react_steps: int = 5,
    ):
        super().__init__(name, llm, system_prompt, config)
        self.tool_registry = tool_registry
        # 初始化react Agent
        self.react = ReActAgent(
            name=f"{name}-react",
            llm=llm,
            tool_registry=tool_registry,
            max_steps=max_react_steps,
            custom_prompt=
        )


    def run(self, input_text: str, **kwargs) -> str:
        '''
        React
        '''
        self.react.run(input_text, **kwargs)


        
        return final