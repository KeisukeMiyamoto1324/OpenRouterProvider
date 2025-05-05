# python3 -m tests.image

from src.OpenRouterProvider.Chatbot_manager import Chat_message, Chatbot_manager
from src.OpenRouterProvider.LLMs import gpt_4o_mini
from PIL import Image


dog = Image.open("tests/images/dog.jpg")
cat = Image.open("tests/images/cat.jpg")

ai = Chatbot_manager(system_prompt="Please answer in English.")
query = Chat_message(text="What can you see in the images?", images=[dog, cat])
response = ai.invoke(model=gpt_4o_mini, query=query)
ai.print_memory()

