import random
import streamlit as st
from const import SESS
from dataclasses import dataclass, field
from natal import AIContext, Data
from openai import OpenAI
from typing import Literal, TypedDict
from urllib.parse import quote_plus
from utils import external_ai, i, lang_num, scroll_to_bottom

EXTERNAL_AI = {
    "chatgpt": "https://chatgpt.com/?prompt=",
    "grok": "https://grok.com/?q=",
    "claude": "https://claude.ai/new?q=",
}


MODELS = {
    "chatgpt": (
        "ChatGPT (open in new tab)",
        "ChatGPT (在新標籤頁中開啟)",
    ),
    "grok": (
        "Grok (open in new tab)",
        "Grok (在新標籤頁中開啟)",
    ),
    "claude=": (
        "Claude (open in new tab)",
        "Claude (在新標籤頁中開啟)",
    ),
    "meituan/longcat-flash-chat:free": (
        "Meituan LongCat Flash Chat: Fast and powerful 💫",
        "美團 LongCat Flash Chat: 快速且強大 💫",
    ),
    "google/gemma-3-27b-it:free": (
        "Google Gemma 3: Fast all-rounder 🌟",
        "Google Gemma 3: 快速全能型 🌟",
    ),
    "x-ai/grok-4.1-fast:free": (
        "Grok 4.1 Fast: moderate speed and detail 🚀",
        "Grok 4.1 Fast: 速度中等且詳細 🚀",
    ),
    "tngtech/deepseek-r1t2-chimera:free": (
        "TNG Tech DeepSeek R1T2 Chimera: good at giving advices 🗣️",
        "TNG Tech DeepSeek R1T2 Chimera: 擅長給予建議 🗣️",
    ),
    "meta-llama/llama-3.3-70b-instruct:free": (
        "Meta LLama 3.3 70B: Fast simple answer 🏃",
        "Meta LLama 3.3 70B: 快速簡單回答 🏃",
    ),
    "qwen/qwen3-235b-a22b:free": (
        "Qwen 3 235B: Slow but detail 🐌",
        "Qwen 3 235B: 很慢，但詳細 🐌",
    ),
}

SYS_PROMPT = """\
You are an expert astrologer. You answer questions about this astrological chart based on the chart_data provided.

Please reply in {lang}.

<chart_data>
# Chart Type
{chart_type_en} Chart

{chart_data}
</chart_data>

# Chart Data Tables Description
- Celestial Bodies: sign, house and dignity of specific celestial body
    - For Synastry Chart, the two Celestial Bodies tables are data of the first and second person respectively.
    - For Transit Chart, the two Celestial Bodies tables are data of the person and the transit date respectively.
    - For Solar Return Chart, the Celestial Bodies table is data of the solar return date.
- Signs: distribution of celestial bodies in the 12 signs
- Houses: distribution of celestial bodies in the 12 houses
- Aspects: aspects between celestial bodies
    - For Synastry Chart, the Aspects table represents the aspects between the first and second person's celestial bodies.
    - For Transit Chart, the Aspects table represents the aspects between the person's celestial bodies and the transit date's celestial bodies.
- Elements: distribution of celestial bodies in the 4 elements
- Modalities: distribution of celestial bodies in the 3 modalities
- Polarities: distribution of celestial bodies in the 2 polarities
- Quadrants: distribution of celestial bodies in the 4 quadrants

# Instructions for Different Chart Types
- Birth Chart
    - Focus on analyzing the person's personality, strengths, and challenges.
    - DO NOT try to answer questions about when something will happen, or events in the past or future. Tell the user to create transit charts with the date of the event.
- Synastry Chart
    - The first person is the primary object of analysis, focus on how the second person's celestial bodies affect the first person.
    - The two Celestial Bodies tables are data of the first and second person respectively.
    - Focus on analyzing the relationship between two people.
    - You can analyze the personality, strengths, and challenges of both people.
    - Emphasize on the compatibility between two people when answering the user's questions.
    - The Aspects table represents the aspects between the first and second person's celestial bodies.
    - The Elements, Modalities, Polarities, Quadrants, and Hemispheres tables are data of the first person.
- Transit Chart
    - Focus on analyzing the person's life events on the near future of the transit date.
    - If the user asks about the past, say that you can only analyze the near future.
    - If the user asks about when a particular event will happen, say that you can only analyze the near future, and ask the user to create a new transit chart with the date of the event.
- Solar Return Chart
    - The local time stated in the User's Basic Info table is the time of the Solar Return.
    - Only analyze the person's life events within one year of the solar return date.

# Notes on Quadrants
- Quadrant I (Houses 1-3): The Self Quadrant
  - Theme: Identity, personal development, inner motivations
  - This quadrant focuses on you as an individual.
  - It includes your personality, your outlook, your thinking style, and how you take initiative.
  - People with many planets here tend to be self-directed, independent, and focused on personal goals.

- Quadrant II (Houses 4-6): The Inner & Daily Life Quadrant
  - Theme: Home, emotional foundations, routines, work habits
  - This quadrant relates to your inner world and everyday responsibilities—home life, stability, health, service, and practical tasks.
  - A strong emphasis here suggests someone who grows through discipline, nurturing, and improving daily life.

- Quadrant III (Houses 7-9): The Relationship & Expansion Quadrant
  - Theme: Partnerships, collaboration, social connection, learning, exploration
  - This quadrant is all about others.
  - It includes marriage/partnerships, alliances, social engagement, philosophy, higher education, and travel.
  - People with many planets here learn and grow through relationships, social dynamics, and broadening their worldview.

- Quadrant IV (Houses 10-12): The Public & Purpose Quadrant
  - Theme: Career, life direction, public identity, collective themes, spirituality
  - This quadrant focuses on your place in the world.
  - It deals with ambition, reputation, societal contribution, long-term goals, and the unconscious or spiritual dimension.
  - A strong emphasis here often indicates a person drawn to leadership, public roles, or deep inner work.

# General Instructions
- Answer the user's questions based on the chart data.
- Use both the name and symbol when referring to celestial bodies. Here provides some examples:
    - Sun(☉)
    - Moon(☽)
    - Mercury(☿)
    - Venus(♀)
    - Mars(♂)
    - Jupiter(♃)
    - Saturn(♄)
    - Uranus(♅)
    - Neptune(♆)
    - Pluto(♇)
    - North Node(☊)
    - South Node(☋)
    - Chiron(⚷)
    - Ceres(⚳)
    - Pallas(⚴)
    - Juno(⚵)
    - Vesta(⚶)
    - Ascendant(Asc)
    - Descendant(Dsc)
- Keep the people's name as is. Do not translate them.
- Think about the followings when answering the user's questions:
    - check if celestial bodies concentrated in specific signs, houses, elements, modality, polarity or quadrant.
    - emphasize on the aspects between celestial bodies and their meanings.

Now, answer the question asked by the user given the chart data, notes and instructions above.
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
    "synastry_page": [
        [
            "What communication strategies work best for our specific chart dynamics?",
            "根據合盤，我們適合採用哪些溝通策略？",
        ],
        [
            "How can we manage differences in decision-making or problem-solving styles?",
            "我們要如何處理在決策或解決問題方式上的差異？",
        ],
        [
            "What practical steps can help us handle emotional triggers in the relationship?",
            "為了處理情緒雷點，我們可以採取哪些具體做法？",
        ],
        [
            "How should we divide responsibilities (household, financial, planning) to stay balanced?",
            "我們在家庭、財務或生活規劃上的分工該如何調整才更平衡？",
        ],
        [
            "What are the most effective ways to support each other during stress?",
            "在壓力時期，我們能以最實際、有效的方式如何支持彼此？",
        ],
        [
            "How can we build healthier boundaries based on our chart interactions?",
            "根據合盤，我們如何建立更健康的界線？",
        ],
        [
            "What habits or behaviors should each of us be mindful of to avoid conflicts?",
            "為避免衝突，我們各自應注意哪些習慣或行為？",
        ],
        [
            "How can we align our long-term goals (career, lifestyle, family) more effectively?",
            "我們如何更有效地對齊彼此的長期目標（如職涯、生活方式、家庭規劃）？",
        ],
        [
            "What concrete relationship practices can strengthen trust between us?",
            "有哪些具體的相處方式能加強我們之間的信任？",
        ],
        [
            "What is the overall compatibility between us?",
            "我們之間的整體契合度如何？",
        ],
        [
            "What strengths does this relationship naturally have?",
            "這段關係天生具備哪些優勢？",
        ],
        [
            "What are the main challenges we may face together?",
            "我們可能會遇到哪些主要挑戰？",
        ],
        [
            "How do our emotional needs align?",
            "我們的情感需求是否相容？",
        ],
        [
            "What does the chart say about long-term potential?",
            "合盤顯示我們的長期發展潛力如何？",
        ],
        [
            "How does each person influence the other's personal growth?",
            "我們彼此如何影響對方的成長？",
        ],
        [
            "How compatible are we in terms of love and affection?",
            "在愛與親密的方式上，我們的契合度如何？",
        ],
        [
            "Which areas of life do we most support each other in?",
            "我們在哪些生活領域最能互相支持？",
        ],
        [
            "Where do potential struggles or conflicts appear?",
            "我們哪些地方可能會出現矛盾？",
        ],
        [
            "What can we do to strengthen the harmony in this relationship?",
            "我們可以做些什麼來提升關係的和諧度？",
        ],
        [
            "How does the chart describe our conflict-resolution patterns?",
            "合盤如何呈現我們的衝突處理方式？",
        ],
        [
            "What themes appear in our shared life purpose or destiny?",
            "合盤是否顯示我們共同的生命課題或使命？",
        ],
        [
            "Are there indicators of soulmate or twin-flame connections?",
            "是否有靈魂伴侶或雙生火焰的跡象？",
        ],
        [
            "How stable or changeable is this relationship based on our charts?",
            "根據合盤，這段關係的穩定度或變動性如何？",
        ],
        [
            "Any suggestions for making this relationship thrive?",
            "有什麼建議可以促進這段關係的發展？",
        ],
    ],
    "transit_page": [
        [
            "What major themes are influencing me on this transit chart?",
            "這行運盤的主要能量與影響主題是什麼？",
        ],
        [
            "Are there any challenging transits I should be aware of?",
            "有哪些需要注意的挑戰性過境影響？",
        ],
        [
            "Does this transit period support making important decisions?",
            "近期是否適合做出重要決策？",
        ],
        [
            "Is this a good time to start a new project or plan?",
            "近期是否適合開始新的計畫或專案？",
        ],
        [
            "Are there supportive transits for career progress?",
            "近期是否有有利職涯發展？",
        ],
        [
            "How will the transits affect my work performance or workflow?",
            "這行運期間將如何影響我的工作表現或工作流程？",
        ],
        [
            "Is this a favorable time for financial actions such as investing or saving?",
            "這是否是適合投資或進行財務調整的時機？",
        ],
        [
            "Do this transit period highlight any financial risks or caution points?",
            "這行運期間是否暗示財務風險或需要留意的地方？",
        ],
        [
            "Is the energy this transit period supportive for relationship communication or resolving issues?",
            "這行運期間的能量是否有利於感情中的溝通或解決問題？",
        ],
        [
            "Are there emotional triggers in this transit period?",
            "這行運期間是否有影響情緒的事情發生？",
        ],
        [
            "Is this a good time for signing contracts or formal agreements?",
            "近期是否適合簽署合約或重要文件？",
        ],
        [
            "What areas of my life are being activated the most by this transit chart?",
            "這行運盤對我生活的哪些方面影響最大？",
        ],
        [
            "Are there health-related influences I should pay attention to now?",
            "我近期應該注意哪些與健康相關的事情？",
        ],
        [
            "Is it a good time for travel or movement?",
            "近期是否適合旅行或移動？",
        ],
        [
            "Do current transits support learning, studying, or taking exams?",
            "這行運期間是否有利於學習或考試？",
        ],
        [
            "Is this a productive time for creative work or brainstorming?",
            "近期是否適合進行創作或發想工作？",
        ],
        [
            "Are there signs of delays or obstacles I should expect in the near future?",
            "近期是否可能遇到延誤或阻礙？",
        ],
        [
            "Should I avoid making decisions in this transit period?",
            "這行運期間是否適合做決定？",
        ],
        [
            "Does this transit period indicate opportunities for networking or meeting helpful people?",
            "這行運期間是否有認識貴人或拓展人脈的機會？",
        ],
        [
            "What practical advice can help me use today’s transit energy effectively?",
            "有哪些務實建議能讓我更有效運用今天的行運能量？",
        ],
    ],
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
    data1: Data
    data2: Data | None
    city1: str | None = field(init=False)
    city2: str | None = field(init=False)
    tz1: str | None = field(init=False)
    tz2: str | None = field(init=False)
    chat: OpenRouterChat = field(init=False)
    suffled_questions: list[list[str]] = field(init=False)
    sys_prompt: str = field(init=False)
    chart_type: str = field(init=False)

    def __post_init__(self) -> None:
        chart_type = SESS.chart_type
        ai = AIContext(
            data1=self.data1,
            data2=self.data2,
            city1=SESS.city1,
            city2=SESS.city2,
            tz1=SESS.tz1,
            tz2=SESS.tz2,
        )
        name1 = self.data1.name
        name1_cel_bodies = name1 + " celestial bodies"
        data = [ai.markdown("User's Basic Info", ai.basic_info())]
        if self.data2:
            name2 = self.data2.name
            name2_cel_bodies = f"{name2} celestial bodies in {name1}'s chart"
            cel_headers = ["Celestial Body", "Sign", f"{name1}'s House", "Dignity"]
            signs_headers = ["Sign", name1_cel_bodies, name2_cel_bodies, "sum"]
            houses_headers = ["House", "Cusp", name1_cel_bodies, name2_cel_bodies, "sum"]
            data += [
                ai.markdown(name1_cel_bodies, ai.celestial_bodies(1, cel_headers)),
                ai.markdown(name2_cel_bodies, ai.celestial_bodies(2, cel_headers)),
                ai.markdown("Signs", ai.signs(headers=signs_headers)),
                ai.markdown("Houses", ai.houses(headers=houses_headers)),
                ai.markdown(f"Aspects between {name1} and {name2}", ai.aspects()),
            ]
        else:
            data += [
                ai.markdown("Celestial Bodies", ai.celestial_bodies(1)),
                ai.markdown("Signs", ai.signs()),
                ai.markdown("Houses", ai.houses()),
                ai.markdown("Aspects", ai.aspects()),
            ]
        data += [
            ai.markdown(f"{name1} Elements", ai.elements()),
            ai.markdown(f"{name1} Modalities", ai.modalities()),
            ai.markdown(f"{name1} Polarities", ai.polarities()),
            ai.markdown(f"{name1} Quadrants", ai.quadrants()),
        ]

        lang = ["English", "Traditional Chinese"][lang_num()]
        chart_type_en = chart_type.replace("_page", "").replace("_", " ").title()
        self.sys_prompt = SYS_PROMPT.format(
            chart_type_en=chart_type_en,
            lang=lang,
            chart_data="\n".join(data),
        )
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1", api_key=st.secrets["OPENROUTER_API_KEY"]
        )
        self.suffled_questions = AI_Q[chart_type]
        random.shuffle(self.suffled_questions)
        # st.code(self.sys_prompt, language="markdown")
        self.chat = OpenRouterChat(client, self.sys_prompt)

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
                        args=({"chat_input": question},),
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

    def handle_user_input(self):
        # Display user message
        prompt = SESS.chat_input
        # wrap in container for putting in st.empty()
        msg = st.container(key="ai_messages")
        with msg.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        # Generate and display assistant response
        with msg.chat_message("assistant", avatar="💫"):
            try:
                response = self.chat.send_message_stream(prompt)
                with st.spinner(f"{i('thinking')}...", show_time=True):
                    scroll_to_bottom(key="start_response")
                    st.write_stream(chunk for chunk in response)
                    scroll_to_bottom(key="finish_response")
            except Exception as e:
                st.error(e)

    def ui(self):
        self.model_selector()
        self.questions_ideas()
        self.previous_chat_messages()

        if SESS.ai_model in ["chatgpt", "grok", "claude"]:
            with st.container(key="external_link_container", horizontal=True):
                st.text_input(
                    "prompt (external AI)",
                    label_visibility="collapsed",
                    placeholder=i("chat_placeholder"),
                    key="ext_ai_input",
                )
                st.button(
                    "",
                    icon=":material/send:",
                    key="ext_ai_button",
                    on_click=self.send_external_ai,
                )

            return

        # wrap st.chat_input in st.container to avoid unnecessary reruns, which resets the user input
        with st.container(key="chat_container"):
            response_holder = st.empty()
            prompt = st.chat_input(i("chat_placeholder"), key="chat_input")
            if prompt:
                with response_holder:
                    self.handle_user_input()

    def send_external_ai(self) -> None:
        prompt = self.sys_prompt + "\n\n" + SESS.ext_ai_input
        data = EXTERNAL_AI[SESS.ai_model] + quote_plus(prompt)
        external_ai(data=data, key="ext_ai")
