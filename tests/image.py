from src.OpenRouterProvider.Chatbot_manager import *
from PIL import Image


dog = Image.open("tests/images/dog.jpg")
cat = Image.open("tests/images/cat.jpg")

ai = Chatbot_manager(system_prompt="Please answer in English.")
query = Chat_message(text="What can you see in the images?", images=[dog, cat])
response = ai.invoke(model=gpt_4o_mini, query=query)
ai.print_memory()

