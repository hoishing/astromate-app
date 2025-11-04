import streamlit as st
from const import I18N, MODELS, SESS
from functools import reduce
from natal import Data
from natal.stats import AIContext
from openai import OpenAI
from textwrap import dedent
from typing import Literal, TypedDict
from utils import i, lang_num, scroll_to_bottom

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


class AI:
    @staticmethod
    def new_chat(data1: Data, data2: Data = None) -> OpenRouterChat:
        ai_context = AIContext(
            data1=data1, data2=data2, city1=SESS.city1, city2=SESS.city2, tz1=SESS.tz1, tz2=SESS.tz2
        )
        chart_data = reduce(
            lambda x, y: x + y,
            (ai_context.ai_md(tb) for tb in ["celestial_bodies", "houses", "aspects"]),
        )
        lang = "Traditional Chinese" if lang_num() else "English"
        chart_type = I18N[SESS.chart_type][0]
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

    @staticmethod
    def questions_ideas():
        st.write("")
        with st.expander(i("question_ideas"), expanded=True):
            with st.container(key="question_ideas_container", height=140, border=False):
                for questions in AI_Q[SESS.chart_type]:
                    question = questions[lang_num()]
                    st.button(
                        question,
                        width="stretch",
                        type="tertiary",
                        icon=":material/arrow_right:",
                        on_click=SESS.update,
                        args=({"chat_input": question},),
                    )

    @staticmethod
    def previous_chat_messages():
        for message in SESS["chat"].messages[1:]:
            role = message["role"]
            text = message["content"]
            with st.chat_message(role, avatar="👤" if role == "user" else "💫"):
                st.markdown(text)

    @staticmethod
    def handle_user_input(prompt: str):
        # Display user message
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        # Generate and display assistant response
        with st.chat_message("assistant", avatar="💫"):
            try:
                response = SESS["chat"].send_message_stream(prompt)

                with st.spinner(f"{i('thinking')}...", show_time=True):
                    scroll_to_bottom()
                    st.write_stream(chunk for chunk in response)
                    scroll_to_bottom()

            except Exception as e:
                st.error(e)
                st.stop()