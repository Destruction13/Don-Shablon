OTHER_TEMPLATES = {
    "Приветствие": [
        "Привет, {имя}, взяла твою задачу в работу! Если появятся ещё задачи — пиши сюда :)",
        "Привет, {имя}! Задачу вижу, в работе!"
    ],
    "Благодарность за переговорку": [
        "{имя}, спасибо тебе огромное! Очень выручил(а) :)",
        "Огромное спасибо, {имя}, очень помог(ла)!",
        "{имя}, ты просто герой(иня) дня! Спасибо огромное 💪",
        "Спасибо тебе, {имя}, от всей души! Очень помог(ла) ❤️",

    ],
    "Если не поделились": [
        "Поняла, спасибо за информацию! Хорошего дня :)",
        "Спасибо! Тогда хорошей тебе работы :)",
        "Поняла, значит, придумаем что-нибудь ещё 💡"
    ],
    "Прощание": [
        "{имя}, рада была помочь! Если что то ещё понадобится — пиши :)",
        "{имя}, задача выполнена! Если понадобится ещё что — я тут",
    ],
    "Уже неактуально": [
        "Прости за беспокойство, уже неактуально!",
        "Прости, что отвлекла, но это уже неактуально для меня",
    ],
    "Получили предложение по обмену, писали по актуальности": [
        "Сейчас у меня нет в распоряжении переговорки, но если появится — обязательно обращусь!",
        "Пока нет свободных, но держу в голове 🧠",
        "Сейчас всё занято, но как освободится — крикну громко 😁",
        "Пока на руках пусто, но вдруг что — тебе сразу напишу!"
    ]
}

import random
import re


def fill_template(template: str, name: str, gender: str) -> str:
    """Подставить имя и окончание по полу в шаблон."""
    text = template.replace("{имя}", name)
    def repl(match: re.Match):
        return match.group(1) if gender == "ж" else ""
    return re.sub(r"\(([^)]+)\)", repl, text)


def generate_from_category(category: str, name: str, gender: str) -> str:
    """Сгенерировать фразу выбранной категории."""
    options = OTHER_TEMPLATES.get(category, [])
    if not options:
        return ""
    template = random.choice(options)
    return fill_template(template, name, gender)
