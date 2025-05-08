import logging
from .Chat_message import *
from .Tool import tool_model
from .LLMs import *

from openai import OpenAI
from dotenv import load_dotenv
import os
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Literal
import json

# エラーのみ表示、詳細なトレースバック付き
logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class ProviderConfig:
    order: Optional[List[str]] = None
    allow_fallbacks: bool = None
    require_parameters: bool = None
    data_collection: Literal["allow", "deny"] = None
    only: Optional[List[str]] = None
    ignore: Optional[List[str]] = None
    quantizations: Optional[List[str]] = None
    sort: Optional[Literal["price", "throughput"]] = None
    max_price: Optional[dict] = None

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


class OpenRouterProvider:
    def __init__(self) -> None:
        load_dotenv()
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            logger.error("OPENROUTER_API_KEY is not set in environment variables.")
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )

    def make_prompt(self, system_prompt: Chat_message,
                    querys: list[Chat_message]) -> list[dict]:
        messages = [{"role": "system", "content": system_prompt.text}]

        for query in querys:
            if query.role == Role.user:
                if query.images is None:
                    messages.append({"role": "user", "content": query.text})
                else:
                    content = [{"type": "text", "text": query.text}]
                    for img in query.images[:50]:
                        content.append(
                            {"type": "image_url",
                             "image_url": {"url": f"data:image/jpeg;base64,{img}"}})
                    messages.append({"role": "user", "content": content})

            elif query.role == Role.ai or query.role == Role.tool:
                assistant_msg = {"role": "assistant"}
                assistant_msg["content"] = query.text or None

                if query.tool_calls:
                    assistant_msg["tool_calls"] = [
                        {
                            "id": str(t.id),
                            "type": "function",
                            "function": {
                                "name": t.name,
                                "arguments": t.arguments
                            }
                        }
                        for t in query.tool_calls
                    ]
                messages.append(assistant_msg)

            for t in query.tool_calls:
                messages.append({
                    "role": "tool",
                    "tool_call_id": str(t.id),
                    "content": str(t.result)
                })

        return messages

    def invoke(self, model: LLMModel, system_prompt: Chat_message, querys: list[Chat_message], tools: list[tool_model] = [], provider: ProviderConfig = None) -> Chat_message:
        try:
            messages = self.make_prompt(system_prompt, querys)

            tool_defs = [tool.tool_definition for tool in tools] if tools else None
            provider_dict = provider.to_dict() if provider else None

            response = self.client.chat.completions.create(
                model=model.name,
                messages=messages,
                tools=tool_defs,
                extra_body={"provider": provider_dict}
            )

            reply = Chat_message(text=response.choices[0].message.content, role=Role.ai, raw_response=response)

            if response.choices[0].message.tool_calls:
                reply.role = Role.tool
                for tool in response.choices[0].message.tool_calls:
                    reply.tool_calls.append(ToolCall(id=tool.id, name=tool.function.name, arguments=tool.function.arguments))
            return reply

        except Exception as e:
            logger.exception(f"An error occurred while invoking the model: {e.__class__.__name__}: {str(e)}")
            return Chat_message(text="Fail to get response. Please see the error message.", role=Role.ai, raw_response=None)
