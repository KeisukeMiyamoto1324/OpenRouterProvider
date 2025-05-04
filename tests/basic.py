from src.OpenRouterProvider.Chatbot_manager import *


ai = Chatbot_manager(system_prompt="Please answer in English.")
query = Chat_message(text="Introduce yourself, please.")
response = ai.invoke(model=gpt_4o_mini, query=query)
ai.print_memory()

