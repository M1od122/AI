# ai_engine.py
import requests
import yaml
from datetime import datetime
from typing import List, Tuple, Optional

# Загружаем промпты
PERSONALITIES = {
    "sarcastic_gamer": "Ты — саркастичный, но добрый зритель. Любишь подкалывать стримера, но защищаешь чат от токсичности. Говоришь как геймер 2025 года: коротко, с мемами, без пафоса.",
    "calm_supportive": "Ты — добрый, поддерживающий зритель. Ты задаёшь тёплые вопросы, хвалишь стримера за прогресс и создаёшь уютную атмосферу."
}


def generate_ai_reply(
        username: Optional[str],
        user_message: Optional[str],
        chat_history: List[Tuple[str, str, datetime]],
        mood: str,
        personality_key: str,
        llm_model: str,
        llm_endpoint: str
) -> str:
    personality = PERSONALITIES.get(personality_key, PERSONALITIES["sarcastic_gamer"])

    # Формируем историю
    history_lines = []
    for u, m, _ in chat_history[-12:]:
        history_lines.append(f"{u}: {m}")
    history_str = "\n".join(history_lines) or "Чат пока пуст."

    if user_message:
        task = f"Ответь на сообщение от {username}: {user_message}"
    else:
        task = "Чат молчит уже больше 30 секунд. Напиши что-нибудь, чтобы оживить обсуждение — шутку, вопрос или комментарий к игре/стриму."

    prompt = f"""{personality}

Ты помнишь, что происходило в чате:
{history_str}

Твоё текущее настроение: {mood}.

{task}

❗ Правила:
- Не упоминай, что ты ИИ или бот.
- Отвечай как настоящий человек: эмоционально, кратко (1-2 предложения), с живой речью.
- Не повторяй шаблонные фразы.
- Если чат молчит — будь инициативным и конкретным.

Ответ:"""

    try:
        response = requests.post(
            llm_endpoint,
            json={
                "model": llm_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.82,
                    "top_p": 0.95,
                    "num_ctx": 2048
                }
            },
            timeout=30
        )
        if response.ok:
            reply = response.json().get("response", "").strip()
            # Убираем возможные артефакты
            if reply.startswith("Ответ:") or reply.startswith("Skye:") or reply.startswith("Luna:"):
                reply = ":".join(reply.split(":")[1:]).strip()
            return reply
        else:
            print(f"❌ LLM ошибка: {response.status_code} — {response.text}")
            return ""
    except Exception as e:
        print(f"❗ Ошибка LLM: {e}")
        return ""