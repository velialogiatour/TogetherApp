import openai
from config import Connect

openai.api_key = Connect.OPENAI_API_KEY

def is_offensive(text):
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты фильтр для токсичных сообщений. Отвечай только 'да' или 'нет'."},
                {"role": "user", "content": f"Сообщение: '{text}'. Оно оскорбительное? Да или нет?"}
            ]
        )
        answer = response.choices[0].message.content.lower()
        return 'да' in answer
    except Exception as e:
        print(f"[OpenAI Error]: {e}")
        return False
