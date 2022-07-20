from enum import Enum


class BotCommands(Enum):
    CHAT_ID = "chat_id"

    START_SESSION = "start_session"
    STOP_SESSION = "stop_session"

    HELP = "help"


class BotMessages(Enum):
    START_SESSION = f"Сессия начата. Для завершения введите команду /{BotCommands.STOP_SESSION.value}"
    STOP_SESSION = "Сессия завершена"
    SESSION_ALREADY_GOING = f"Сессия уже начата. Для завершения сессии введите команду /{BotCommands.STOP_SESSION.value}"

    HELP =\
        "/chat_id - узнать id чата (локальный для бота)\n"\
        "/start_session - инициировать сессию\n"\
        "/stop_session - завершить сессию\n"\
