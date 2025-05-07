from .Chat_message import *
from .Tool import tool_model
from .LLMs import *

from openai import OpenAI
from dotenv import load_dotenv
import os
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Literal
import json


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
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )

    def make_prompt(self, system_prompt: Chat_message,
                querys: list[Chat_message]) -> list[dict]:
        messages = [{"role": "system", "content": system_prompt.text}]

        for query in querys:
            # ----- USER -----
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

            # ----- ASSISTANT -----
            elif query.role == Role.ai or query.role == Role.tool:
                assistant_msg = {"role": "assistant"}
                assistant_msg["content"] = query.text or None      # ← content は明示必須

                # ① tool_calls を付与（あれば）
                if query.tool_calls:
                    assistant_msg["tool_calls"] = [
                        {
                            "id": str(t.id),
                            "type": "function",
                            "function": {
                                "name": t.name,
                                "arguments": t.arguments          # JSON 文字列
                            }
                        }
                        for t in query.tool_calls
                    ]
                messages.append(assistant_msg)

            # ② tool メッセージを assistant の直後に並べる
            for t in query.tool_calls:
                messages.append({
                    "role": "tool",
                    "tool_call_id": str(t.id),
                    "content": str(t.result)                  # 実行結果（文字列）
                })
        return messages


    def invoke(self, model: LLMModel, system_prompt: Chat_message, querys: list[Chat_message], tools:list[tool_model]=[], provider:ProviderConfig=None) -> Chat_message:
        print(provider.to_dict())
        response = self.client.chat.completions.create(
            model=model.name,
            messages=self.make_prompt(system_prompt, querys),
            tools=[tool.tool_definition for tool in tools],
            extra_body={
                "provider": provider.to_dict() if provider else None
            }
        )
        reply = Chat_message(text=response.choices[0].message.content, role=Role.ai)
        
        if response.choices[0].message.tool_calls:
            reply.role = Role.tool
            for tool in response.choices[0].message.tool_calls:
                reply.tool_calls.append(ToolCall(id=tool.id, name=tool.function.name, arguments=tool.function.arguments))
                
        print(response)
        return reply

