from toxic_filter import is_offensive

test_messages = [
    "Привет, как дела?",
    "Ты идиот",
    "Закрой рот, урод",
    "Добрый день, приятно познакомиться!",
    "Go to hell",
    "You're a smart guy",
    "Shut up, bastard",
    "Ты очень хороший человек",
    "Ненавижу тебя",
    "Ублюдок, пошёл вон",
    "Ты лучший!",
    "Чмошник",
]

print("Тестирование фильтра токсичных сообщений:")
print("=" * 45)

for msg in test_messages:
    result = is_offensive(msg)
    label = "❌ Токсично" if result else "✅ Не токсично"
    print(f"'{msg}' — {label}")
