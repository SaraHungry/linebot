import json
from typing import Dict, List, Type

from litellm import completion

from tools.base_tool import BaseTool

LOOP_LIMIT = 3

# TODO: make tool call work for sync and async
# TODO(?): consider maintaining error message with const or conf?

class Agent:
    def __init__(self, system_prompt: str, model_name: str):
        """
        Initializes the Agent with a system prompt.

        Args:
            system_prompt: The system prompt to guide the OpenAI model's behavior.
        """
        self.system_prompt = system_prompt
        self.model_name = model_name
        self.registered_tools: Dict[str, BaseTool] = {}

    def register_tool(self, tool: Type[BaseTool]):
        """
        Registers a tool with the agent.

        Args:
            tool_class: The class of the tool to register (must inherit from BaseTool).
        """
        tool_definition = tool.get_tool_definition()
        self.registered_tools[tool_definition["function"]["name"]] = tool

    def _call_tool(self, tool_call: Dict):
        """
        Executes a single tool call.

        Args:
            tool_call: The tool call object from the OpenAI API response.

        Returns:
            A message dictionary representing the tool's result, or None if an error occurs.
        """
        tool_name = tool_call["function"]["name"]
        if tool_name not in self.registered_tools:
            print(f"Warning: Unknown tool '{tool_name}' requested.")
            return {
                "tool_call_id": tool_call["id"],
                "role": "tool",
                "name": tool_name,
                "content": "Error: Tool not found.",
            }

        tool = self.registered_tools[tool_name]
        tool_args = json.loads(tool_call["function"]["arguments"])
        try:
            tool_result = tool(**tool_args)
            return {
                "tool_call_id": tool_call["id"],
                "role": "tool",
                "name": tool_name,
                "content": str(tool_result),
            }
        except Exception as e:
            print(f"Error executing tool '{tool_name}': {e}")
            return {
                "tool_call_id": tool_call["id"],
                "role": "tool",
                "name": tool_name,
                "content": f"Error: {e}",
            }
        
    def _get_tool_call_results(self, tool_calls, messages):
        for tool_call in tool_calls:
            tool_result_message = self._call_tool(tool_call)
            print(tool_result_message)
            if tool_result_message:
                messages.append(tool_result_message)
            else:
                # Handle potential errors in tool execution more explicitly
                messages.append(
                    {
                        "tool_call_id": tool_call["id"],
                        "role": "tool",
                        "name": tool_call["function"]["name"],
                        "content": "Error occurred during tool execution.",
                    }
                )


    async def generate_response(self, recent_messages: List[Dict[str, str]]):
        """
        Generates a response based on the recent messages, potentially using registered tools.

        Args:
            recent_messages: A list of recent messages in the conversation. The last message
                             is considered the current user query.

        Returns:
            The final text response from the agent.
        """
        messages = [{"role": "system", "content": self.system_prompt}] + recent_messages
        tools = (
            [tool.get_tool_definition() for tool in self.registered_tools.values()]
            if self.registered_tools
            else None
        )

        try:
            for _ in range(LOOP_LIMIT):# limit the number of calls 
                response = completion(
                    model=self.model_name,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                )
                response_message = response["choices"][0]["message"]

                if response_message.get("tool_calls"):
                    messages.append(response_message)  # Assistant's tool call
                    tool_calls = response_message["tool_calls"]
                    self._get_tool_call_results(tool_calls, messages)
                else:
                    return response_message["content"]
            else:
                return "call depth exceeded"

        except Exception as e:  # Catch general exceptions from litellm
            print(f"LiteLLM Error: {e}")
            return "An error occurred while processing your request."

if __name__ == "__main__":
    import asyncio

    from tools.dad_joke import DadJokeTool
    system_prompt = "you are a helpful chatbot. Use the tools provided to respond."
    model_name = "o4-mini"
    agent = Agent(system_prompt=system_prompt, model_name=model_name)
    dad_joke_tool = DadJokeTool()

    

    agent.register_tool(dad_joke_tool)
    res = asyncio.run(agent.generate_response([{"role": "user", "content": "please tell me a dad joke"}]))
    print("OUTPUT", "*" * 5, res)

