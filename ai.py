import json
import random
import streamlit as st
from const import SESS
from dataclasses import dataclass, field
from functools import reduce
from natal import Data
from natal.stats import AIContext
from openai import OpenAI
from typing import Literal, TypedDict
from utils import i, lang_num, scroll_to_bottom

MODELS = {
    "google/gemma-3-27b-it:free": (
        "Google Gemma 3: Fast all-rounder 🌟",
        "Google Gemma 3: 快速全能型 🌟",
    ),
    "meta-llama/llama-4-maverick:free": (
        "Meta LLama 4 Maverick: ok speed, concise answers 🤠",
        "Meta LLama 4 Maverick: 中等速度, 簡潔回答 🤠",
    ),
    "meituan/longcat-flash-chat:free": (
        "Meituan LongCat Flash Chat: Fast and powerful 🚀",
        "美團 LongCat Flash Chat: 快速且強大 🚀",
    ),
    "meta-llama/llama-4-scout:free": (
        "Meta LLama 4 Scout: For quick and short answers 💨",
        "Meta LLama 4 Scout: 用於快速且簡短的回答 💨",
    ),
    "mistralai/mistral-small-3.2-24b-instruct:free": (
        "Mistral Small 3.2: moderate speed, good performance 👌",
        "Mistral Small 3.2: 中等速度，表現不錯 👌",
    ),
    "qwen/qwen3-235b-a22b:free": ("Qwen 3 235B: Slow but detail 🐌", "Qwen 3 235B: 慢但詳細 🐌"),
    "deepseek/deepseek-chat-v3.1:free": (
        "DeepSeek Chat V3.1: Moderate speed, average performance ⚖️",
        "DeepSeek Chat V3.1: 中等速度, 表現平均 ⚖️",
    ),
    "meta-llama/llama-3.3-70b-instruct:free": (
        "Meta LLama 3.3 70B: Fast simple answer 🏃",
        "Meta LLama 3.3 70B: 快速簡單回答 🏃",
    ),
    "openai/gpt-oss-20b:free": (
        "OpenAI GPT-OSS: Super busy, average performance 🤷‍♀️",
        "OpenAI GPT-OSS: 超級忙碌，表現還好 🤷‍♀️",
    ),
}

SYS_PROMPT = """\
You are an expert astrologer. You answer questions about this astrological {chart_type} chart data:

Please reply in {lang}.

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
"""


AI_Q = {
    "birth_page": [
        [
            "What does my birth chart reveal about my personality, strengths, and challenges?",
            "我的本命盤對我的個性、優勢和挑戰有何啟示？",
        ],
        [
            "What is my career opportunities, and how can I make the most of them?",
            "我的職業發展有哪些可能性？我應如何有效利用這些機會？",
        ],
        [
            "Any advice on my love life and relationships?",
            "關於我的愛情生活和兩性關係，有什麼建議嗎？",
        ],
        [
            "How does my chart describe my relationship with money and my potential for wealth?",
            "我的星盤如何描述我與金錢的關係和致富潛力？",
        ],
        [
            "What challenges will I encounter in interpersonal relationships?",
            "我在人際關係上會遇到什麼挑戰？",
        ],
        [
            "How can I improve my relationship with my family of origin?",
            "我如何能改善與原生家庭的關係？",
        ],
        [
            "How about my health? Any potential health issues?",
            "我的健康狀況如何，有任何潛在的健康問題嗎？",
        ],
        [
            "How can I unleash my creativity or inspiration?",
            "我該如何發揮我的創造力和靈感？",
        ],
        [
            "What challenges or life lessons do the birth chart show for me?",
            "我的本命盤給我揭示了哪些挑戰或人生課題？",
        ],
        [
            "What kind of investment strategy is right for me?",
            "什麼類型的投資策略比較適合我？",
        ],
        [
            "How can I best fulfill my spiritual and emotional needs?",
            "我該如何最好地滿足我的靈性與情感需求？",
        ],
        [
            "How can I best use my natural talents to create abundance?",
            "我如何最好地運用我的天賦來創造豐盛？",
        ],
        [
            "What should I be aware of in romantic relationships?",
            "在戀愛關係中，我該注意些什麼？",
        ],
        [
            "What area will bring me the most success or fulfillment?",
            "哪一方面能帶給我最大的成功和成就感？",
        ],
        [
            "Am I better suited to start my own business or work for someone else?",
            "我比較適合自己創業，還是為他人工作？",
        ],
        [
            "What kind of partner is most compatible with me?",
            "哪種類型的伴侶最適合我？",
        ],
        [
            "What is the best approach to achieve my financial goals?",
            "達成財務目標的最佳途徑是什麼？",
        ],
        [
            "Which fields offer potential for career development?",
            "哪些領域有發展事業的潛力？",
        ],
        [
            "What potential difficulties or obstacles do I need to overcome?",
            "我有什麼需要克服的潛在困難或障礙？",
        ],
        [
            "What natural strengths or talents does my birth chart show?",
            "我的本命盤顯示我有哪些天生的優勢或才能？",
        ],
        [
            "How can I feel more at ease and comfortable in my social circle?",
            "我該如何在社交圈中讓自己感到更自在與舒適？",
        ],
        [
            "Which area of life can give me more sense of security or stability?",
            "生命中的哪個領域，可以讓我覺得更穩定或更有安全感或？",
        ],
        [
            "How to improve my communication style?",
            "如何改善我的溝通風格？",
        ],
        [
            "Any hidden talents or potential that I might not be aware of?",
            "有哪些我可能沒有意識到的隱藏才能或潛力？",
        ],
        [
            "How will my journey of self-healing unfold?",
            "我的自我療癒之路如何展開？",
        ],
        [
            "What kind of partner do I truly need in a romantic relationship?",
            "在愛情中，我真正需要什麼樣的伴侶？",
        ],
    ],
    "synastry_page": [],
    "transit_page": [],
    "solar_return_page": [
        [
            "What are my advantages and challenges this year?",
            "這一年我有什麼優勢和挑戰？",
        ],
        [
            "What is my career opportunities, and how can I make the most of them?",
            "我的職業發展有哪些可能性？我應如何有效利用這些機會？",
        ],
        [
            "Any advice on my love life and relationships?",
            "對於我的愛情生活和兩性關係，有什麼建議嗎？",
        ],
        [
            "What is the best investment strategy this year?",
            "這一年最佳的理財策略是什麼？",
        ],
        [
            "How about my health? Any potential health issues?",
            "我的健康狀況如何，有任何潛在的健康問題嗎？",
        ],
        [
            "What challenges will I encounter in interpersonal relationships?",
            "我在人際關係上會遇到什麼挑戰？",
        ],
        [
            "How can I expand my social circle?",
            "如何擴大我的社交圈子？",
        ],
        [
            "Which field has the greatest potential for career development?",
            "哪個領域最有發展事業的潛力？",
        ],
        [
            "Is this a good year to start a business?",
            "這一年適合創業嗎？",
        ],
        [
            "How can I improve my relationship with my family of origin?",
            "我如何能改善與原生家庭的關係？",
        ],
        [
            "How can I best fulfill my spiritual and emotional needs?",
            "我該如何最好地滿足我的靈性與情感需求？",
        ],
        [
            "How can I best use my natural talents to create abundance this year?",
            "這一年我如何最好地運用我的天賦來創造豐盛？",
        ],
        [
            "Any advice on achieving my financial goals this year?",
            "關於我今年要如何達成財務目標，有什麼建議嗎？",
        ],
        [
            "How can I unleash my creativity or inspiration?",
            "我該如何發揮我的創造力和靈感？",
        ],
        [
            "What potential difficulties or obstacles do I need to overcome?",
            "我有什麼需要克服的潛在困難或障礙？",
        ],
        [
            "What area will bring me the most success or fulfillment?",
            "哪一方面會讓我最容易成功或獲得成就感？",
        ],
        [
            "How will my journey of self-healing unfold?",
            "我的自我療癒之路如何展開？",
        ],
        [
            "What should I be aware of in romantic relationships?",
            "在戀愛關係中，我該注意些什麼？",
        ],
    ],
}


class Message(TypedDict):
    role: Literal["developer", "user", "assistant"]
    content: str


class OpenRouterChat:
    def __init__(self, client: OpenAI, system_message: str):
        self.client = client
        self.messages = [Message(role="developer", content=system_message)]

    def is_retryable_error(self, error: Exception) -> bool:
        """Check if error is retryable (network, temporary issues)"""
        error_codes = ["429", "500", "502", "503", "504"]
        return any(str(error).lower().startswith(f"error code: {code}") for code in error_codes)

    def send_message_stream(self, prompt: str):
        """Send message with failover support and return streaming response"""
        self.messages.append(Message(role="user", content=prompt))

        try:
            # st.write(f"using model: {self.model}")
            response = self.client.chat.completions.create(
                model=SESS.ai_model,
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
                st.warning(f"{SESS.ai_model} {i('model_busy')}")
            else:
                st.error(f"{SESS.ai_model} {i('model_unavailable')}")
            del self.messages[-1]


@dataclass
class AI:
    chart_type: str
    data1: Data
    data2: Data | None
    city1: str | None = field(init=False)
    city2: str | None = field(init=False)
    tz1: str | None = field(init=False)
    tz2: str | None = field(init=False)
    chat: OpenRouterChat = field(init=False)
    suffled_questions: list[list[str]] = field(init=False)

    def __post_init__(self) -> None:
        ai_context = AIContext(
            data1=self.data1,
            data2=self.data2,
            city1=SESS.city1,
            city2=SESS.city2,
            tz1=SESS.tz1,
            tz2=SESS.tz2,
        )
        chart_data = reduce(
            lambda x, y: x + y,
            (ai_context.ai_md(tb) for tb in ["celestial_bodies", "houses", "aspects"]),
        )
        lang = ["English", "Traditional Chinese"][lang_num()]
        chart_type = self.chart_type
        sys_prompt = SYS_PROMPT.format(chart_type=chart_type, lang=lang, chart_data=chart_data)
        # st.text(sys_prompt)
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1", api_key=st.secrets["OPENROUTER_API_KEY"]
        )
        self.suffled_questions = AI_Q[self.chart_type]
        random.shuffle(self.suffled_questions)
        self.chat = OpenRouterChat(client, sys_prompt)

    def questions_ideas(self):
        with st.expander(i("question_ideas"), expanded=True):
            with st.container(key="question_ideas_container", height=145, border=False):
                for question in self.suffled_questions:
                    question = question[lang_num()]
                    st.button(
                        question,
                        width="stretch",
                        type="tertiary",
                        icon=":material/arrow_right:",
                        on_click=SESS.update,
                        args=({f"chat_input_{self.chart_type}": question},),
                    )

    def model_selector(self):
        st.write("")
        st.selectbox(
            i("ai_model"),
            options=MODELS,
            key="ai_model",
            format_func=lambda x: MODELS[x][lang_num()],
            # width=450,
        )

    def previous_chat_messages(self):
        for message in self.chat.messages[1:]:
            role = message["role"]
            text = message["content"]
            with st.chat_message(role, avatar="👤" if role == "user" else "💫"):
                st.markdown(text)

    def handle_user_input(self, prompt: str):
        # Display user message
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        # Generate and display assistant response
        with st.chat_message("assistant", avatar="💫"):
            try:
                response = self.chat.send_message_stream(prompt)

                with st.spinner(f"{i('thinking')}...", show_time=True):
                    scroll_to_bottom()
                    st.write_stream(chunk for chunk in response)
                    scroll_to_bottom()

            except Exception as e:
                st.error(e)
                st.stop()
