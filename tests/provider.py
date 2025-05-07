# python3 -m tests.basic

from src.OpenRouterProvider.Chatbot_manager import *


ai = Chatbot_manager(system_prompt="Please answer in English.")
query = Chat_message(text="Introduce yourself, please.")
provider = ProviderConfig(sort="throughput")
response = ai.invoke(model=llama_4_scout, query=query, provider=provider)
ai.print_memory()

