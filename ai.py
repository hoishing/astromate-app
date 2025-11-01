import streamlit as st
from const import I18N, MODELS, VAR
from functools import reduce
from natal import Data
from natal.stats import AIContext
from openai import OpenAI
from textwrap import dedent
from typing import Literal, TypedDict


class Message(TypedDict):
    role: Literal["developer", "user", "assistant"]
    content: str


class OpenRouterChat:
    def __init__(self, client: OpenAI, model: str, system_message: str):
        self.client = client
        self.model = model
        self.messages = [Message(role="developer", content=system_message)]

    def send_message_stream(self, prompt: str):
        """Send message and return streaming response"""
        self.messages.append(Message(role="user", content=prompt))

        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            stream=True,
        )

        full_response = ""
        for chunk in response:
            if content := chunk.choices[0].delta.content:
                full_response += content
                yield content

        # Add assistant response to history
        self.messages.append(Message(role="assistant", content=full_response))


def new_chat(data1: Data, data2: Data = None) -> OpenRouterChat:
    ai_context = AIContext(
        data1=data1, data2=data2, city1=VAR.city1, city2=VAR.city2, tz1=VAR.tz1, tz2=VAR.tz2
    )
    chart_data = reduce(
        lambda x, y: x + y,
        (ai_context.ai_md(tb) for tb in ["celestial_bodies", "houses", "aspects"]),
    )
    lang = "Traditional Chinese" if VAR.lang_num else "English"
    chart_type = I18N[VAR.chart_type][0]
    sys_prompt = dedent(f"""\
            You are an expert astrologer. You answer {chart_type} questions about this astrological chart data:
            
            <chart_data>
            {chart_data}
            </chart_data>

            # Chart Data Tables Description
            - Celestial Bodies: sign, house and dignity of specific celestial body
            - Signs: distribution of celestial bodies in the 12 signs
            - Houses: distribution of celestial bodies in the 12 houses
            - Elements: distribution of celestial bodies in the 4 elements
            - Modalities: distribution of celestial bodies in the 3 modalities
            - Polarities: distribution of celestial bodies in the 2 polarities
            - Aspects: aspects between celestial bodies
            - Quadrants: distribution of celestial bodies in the 4 quadrants
            - Hemispheres: distribution of celestial bodies in the 4 hemispheres

            # Instructions
            - Answer the user's questions based on the chart data.
            - think about the followings when answering the user's questions:
              - do celestial bodies concentrate in certain signs, houses, elements, modality, polarity, quadrant, or hemisphere?
              - do aspects between celestial bodies form certain patterns?
            - Use {lang} to reply.
            """)
    # st.text(sys_prompt)
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1", api_key=st.secrets["OPENROUTER_API_KEY"]
    )
    model = MODELS[1]  # Use x-ai/grok-4-fast:free instead of Gemini
    return OpenRouterChat(client, model, sys_prompt)
