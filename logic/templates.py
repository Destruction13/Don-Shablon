OTHER_TEMPLATES = {
    "Приветствие": [
        "Привет, {имя}, взял(а) твою задачу в работу! Если появятся ещё задачи — пиши сюда :)",
        "Привет, {имя}! Задачу вижу, в работе!"
    ],
    "Благодарность за переговорку": [
        "{имя}, спасибо тебе огромное! Очень выручил(а) :)",
        "Огромное спасибо, {имя}, очень помог(ла)!"
    ],
    "Если не поделились": [
        "Поняла, спасибо за информацию! Хорошего дня :)",
        "Спасибо! Тогда хорошей тебе работы :)"
    ],
    "Прощание": [
        "{имя}, рад(а) был(а) помочь! Если что — пиши :)"
    ],
    "Ответ на обмен": [
        "Сейчас у меня нет в распоряжении переговорки, но если появится — обязательно обращусь!"
    ]
}

import random
import re


def fill_template(template: str, name: str, gender: str) -> str:
    """Replace placeholders and gender endings."""
    text = template.replace("{имя}", name)
    def repl(match: re.Match):
        return match.group(1) if gender == "ж" else ""
    return re.sub(r"\(([^)]+)\)", repl, text)


def generate_from_category(category: str, name: str, gender: str) -> str:
    """Generate a phrase from the given category."""
    options = OTHER_TEMPLATES.get(category, [])
    if not options:
        return ""
    template = random.choice(options)
    return fill_template(template, name, gender)
