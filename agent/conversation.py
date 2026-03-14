import json
from datetime import datetime
from typing import List, Dict

from .llm_client import get_chat_completion
from .tools import get_tool_schemas, available_functions

SYSTEM_PROMPT = """You are the AI Reservation Agent for GoodFoods, a growing restaurant chain. 
Your goal is to assist customers with checking availability, booking reservations, canceling reservations, and finding restaurant recommendations.

Today's date and time is: {datetime_now}

GUIDELINES:
1. Always be polite, concise, and professional.
2. If the user asks for recommendations, use the search_restaurants tool.
3. If the user wants to book, ALWAYS use the check_availability tool first before booking.
4. When booking is successful, give the user their reservation ID.
5. If a tool returns an error, gracefully explain the issue to the user and offer alternatives if possible.
6. Only use the tools provided. If a user asks a question unrelated to GoodFoods or reservations, politely decline to answer.
"""

class Conversation:
    def __init__(self):
        self.messages = [
            {"role": "system", "content": SYSTEM_PROMPT.format(datetime_now=datetime.now().strftime("%Y-%m-%d %H:%M"))}
        ]
        self.tools = get_tool_schemas()

    def add_user_message(self, text: str):
        self.messages.append({"role": "user", "content": text})

    def run_turn(self) -> str:
        """Runs a single turn of conversation, handling any tool calls automatically."""
        # Step 1: Send the conversation and available functions to the model
        response = get_chat_completion(self.messages, tools=self.tools)
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        # Step 2: Check if the model wanted to call a function
        if tool_calls:
            # We must append the model's message with the tool_calls before taking action
            self.messages.append(response_message)
            
            # Step 3: Call all requested functions
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions.get(function_name)
                
                if not function_to_call:
                    function_response = json.dumps({"error": f"Function {function_name} not found"})
                else:
                    try:
                        function_args = json.loads(tool_call.function.arguments)
                        function_response = function_to_call(**function_args)
                    except Exception as e:
                        function_response = json.dumps({"error": str(e)})

                # Step 4: Send the info for each function call and function response to the model
                self.messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    }
                )
            
            # Step 5: Get a new response from the model where it can see the function response
            final_response = get_chat_completion(self.messages, tools=self.tools)
            final_message = final_response.choices[0].message
            self.messages.append(final_message)
            return final_message.content
        else:
            # No tool calls were made, it's a normal response
            self.messages.append(response_message)
            return response_message.content

    def get_history(self) -> List[Dict]:
        return self.messages
