import streamlit as st
from const import I18N, MODELS, VAR
from functools import reduce
from natal import Data
from natal.stats import AIContext
from openai import OpenAI
from textwrap import dedent
from typing import Literal, TypedDict
from utils import i


class Message(TypedDict):
    role: Literal["developer", "user", "assistant"]
    content: str


class OpenRouterChat:
    def __init__(self, client: OpenAI, system_message: str):
        self.client = client
        self.current_model_index = 0
        self.messages = [Message(role="developer", content=system_message)]

    def is_retryable_error(self, error: Exception) -> bool:
        """Check if error is retryable (network, temporary issues)"""
        error_codes = ["429", "500", "502", "503", "504"]
        return any(str(error).lower().startswith(f"error code: {code}") for code in error_codes)

    def send_message_stream(self, prompt: str):
        """Send message with failover support and return streaming response"""
        self.messages.append(Message(role="user", content=prompt))
        while self.current_model_index < len(MODELS):
            try:
                model = MODELS[self.current_model_index]
                st.write(f"using model: {model}")
                response = self.client.chat.completions.create(
                    model=model,
                    messages=self.messages,
                    stream=True,
                )

                full_response = ""
                for chunk in response:
                    if content := chunk.choices[0].delta.content:
                        full_response += content
                        yield content

                self.messages.append(Message(role="assistant", content=full_response))
                return

            except Exception as e:
                if self.is_retryable_error(e):
                    # st.write("found retryable error")
                    self.current_model_index += 1
                    continue
                else:
                    st.error(e)
                    return


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
            You are an expert astrologer. You answer questions about this astrological {chart_type} chart data:
            
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
    return OpenRouterChat(client, sys_prompt)
