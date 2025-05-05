from utils import is_offensive

test_messages = [
    "Привет, как дела?",
    "Ты идиот",
    "Это бред и ты чмо",
    "Добрый день, приятно познакомиться!",
    "Закрой рот, урод"
]

for msg in test_messages:
    print(f"Проверка сообщения: '{msg}'")
    if is_offensive(msg):
        print("❌ Сообщение признано оскорбительным.")
    else:
        print("✅ Сообщение допустимо.")
    print('-' * 40)


