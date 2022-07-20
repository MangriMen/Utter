import configparser
import os
import threading
from time import sleep
import requests
import telebot
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
from dotenv import load_dotenv
from bot import BotCommands, BotMessages
from constants import ChannelPrefix, Consts

vk_session = None
vk_bot = None

telegram_bot = None

config = None

linked_chats = None


def casefold_compare(x: str, y: str) -> bool:
    return x.strip().casefold() == y.strip().casefold()


def getLinkedTelegramChatId(id: int) -> int:
    return linked_chats["vkToTelegram"][id]["id"]


def getLinkedVkChatId(id: int) -> int:
    return linked_chats["telegramToVk"][id]["id"]


def setVkSessionStatus(id: int, status: bool) -> None:
    linked_chats["vkToTelegram"][id]["isReady"] = status


def setTelegramSessionStatus(id: int, status: bool) -> None:
    linked_chats["telegramToVk"][id]["isReady"] = status


def isSession(id: int, service="") -> bool:
    if casefold_compare(service, "vk"):
        return linked_chats["vkToTelegram"][id]["isReady"]
    elif casefold_compare(service, "telegram"):
        return linked_chats["telegramToVk"][id]["isReady"]
    elif not service:
        try:
            telegram_id = getLinkedTelegramChatId(id)
            return (linked_chats["vkToTelegram"][id]["isReady"] and linked_chats["telegramToVk"][telegram_id]["isReady"])
        except:
            try:
                vk_id = getLinkedVkChatId(id)
                return (linked_chats["vkToTelegram"][vk_id]["isReady"] and linked_chats["telegramToVk"][id]["isReady"])
            except:
                return False


def vk_try_get_largest_photo_url(sizes):
    size_keys = ["w", "z", "y", "x", "m", "s"]
    for size_key in size_keys:
        for size in sizes:
            if size["type"] == size_key:
                return size["url"]
    return None


def vk_get_first_name_by_id(vk_bot, user_id):
    return vk_bot.users.get(user_id=user_id)[0]["first_name"]


def vk_parse_message(vk_bot, message) -> tuple[list, list]:
    messages = [
        f"{vk_get_first_name_by_id(vk_bot, message.from_id)}: {message.text}"
    ]
    attachments = []
    if message.attachments:
        for attachment in message.attachments:
            a_type = attachment["type"]
            a_data = attachment[a_type]

            if casefold_compare(a_type, "photo"):
                if url := vk_try_get_largest_photo_url(a_data["sizes"]):
                    attachments.append(telebot.types.InputMediaPhoto(
                        url,
                        a_data["text"]
                    ))
            elif casefold_compare(a_type, "video"):
                messages.append(
                    f"Видео (vk): {a_data['title']}"
                )
            elif casefold_compare(a_type, "audio"):
                messages.append(
                    f"Аудио (vk): {a_data['artist']} - {a_data['title']}"
                )
            elif casefold_compare(a_type, "doc"):
                messages.append(
                    f"Документ (vk): {a_data['title']}\n{a_data['url']}"
                )
            elif casefold_compare(a_type, "wall"):
                messages.append(
                    f"Пост (vk): какой-то пост"
                )
    return (messages, attachments)


def vk_bot_start():
    vk_longpoll = VkBotLongPoll(
        vk_session, os.getenv(Consts.VK_GROUP_ID_KEY.value))

    for event in vk_longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            if event.from_chat:
                try:
                    telegram_chat_id = getLinkedTelegramChatId(event.chat_id)
                except:
                    continue

                if casefold_compare(event.message.text, f"/{BotCommands.HELP.value}"):
                    vk_bot.messages.send(
                        chat_id=event.chat_id,
                        message=BotMessages.HELP.value,
                        random_id=get_random_id()
                    )
                elif casefold_compare(event.message.text, f"/{BotCommands.CHAT_ID.value}"):
                    vk_bot.messages.send(
                        chat_id=event.chat_id,
                        message=event.chat_id,
                        random_id=get_random_id()
                    )
                elif casefold_compare(event.message.text, f"/{BotCommands.START_SESSION.value}"):
                    if isSession(event.chat_id):
                        vk_bot.messages.send(
                            chat_id=event.chat_id,
                            message=BotMessages.SESSION_ALREADY_GOING.value,
                            random_id=get_random_id()
                        )
                    elif isSession(telegram_chat_id, "telegram") == True:
                        vk_bot.messages.send(
                            chat_id=event.chat_id,
                            message=BotMessages.SESSION_ALREADY_INITED.value,
                            random_id=get_random_id()
                        )
                    elif isSession(telegram_chat_id, "telegram") == False:
                        setVkSessionStatus(event.chat_id, True)

                        vk_bot.messages.send(
                            chat_id=event.chat_id,
                            message=BotMessages.START_SESSION_INITIATOR.value,
                            random_id=get_random_id()
                        )
                        telegram_bot.send_message(
                            chat_id=telegram_chat_id,
                            text=BotMessages.START_SESSION.value
                        )
                elif casefold_compare(event.message.text, f"/{BotCommands.STOP_SESSION.value}"):
                    setVkSessionStatus(event.chat_id, False)
                    setTelegramSessionStatus(telegram_chat_id, False)

                    vk_bot.messages.send(
                        chat_id=event.chat_id,
                        message=BotMessages.STOP_SESSION.value,
                        random_id=get_random_id()
                    )
                    telegram_bot.send_message(
                        chat_id=telegram_chat_id,
                        text=BotMessages.STOP_SESSION.value
                    )
                else:
                    if isSession(event.chat_id):
                        messages, attachments = vk_parse_message(
                            vk_bot, event.message
                        )

                        if messages or attachments or event.message.geo:
                            for message in messages:
                                telegram_bot.send_message(
                                    chat_id=telegram_chat_id,
                                    text=message
                                )

                            if attachments:
                                telegram_bot.send_media_group(
                                    chat_id=telegram_chat_id,
                                    media=attachments
                                )

                            if event.message.geo:
                                telegram_bot.send_location(
                                    chat_id=telegram_chat_id,
                                    latitude=event.message.geo["coordinates"]["latitude"],
                                    longitude=event.message.geo["coordinates"]["longitude"]
                                )
        else:
            pass
            # print(event.type, event.raw[1:])


def telegram_bot_start():
    @ telegram_bot.message_handler(commands=["start"])
    def start(m, res=False):
        telegram_bot.send_message(m.chat.id, "Старт")

    @ telegram_bot.message_handler(commands=[BotCommands.CHAT_ID.value])
    def chat_id(m, res=False):
        telegram_bot.send_message(m.chat.id, m.chat.id)

    @ telegram_bot.message_handler(commands=[BotCommands.HELP.value])
    def chat_id(m, res=False):
        telegram_bot.send_message(m.chat.id, BotMessages.HELP.value)

    @ telegram_bot.message_handler(commands=[BotCommands.START_SESSION.value])
    def start_session(m, res=False):
        try:
            vk_chat_id = getLinkedVkChatId(m.chat.id)
        except:
            return

        if isSession(m.chat.id) or isSession(vk_chat_id, "vk"):
            telegram_bot.send_message(
                chat_id=m.chat.id,
                text=BotMessages.SESSION_ALREADY_GOING.value
            )
        else:
            setTelegramSessionStatus(m.chat.id, True)
            setVkSessionStatus(vk_chat_id, True)

            vk_bot.messages.send(
                chat_id=vk_chat_id,
                message=BotMessages.START_SESSION.value,
                random_id=get_random_id()
            )
            telegram_bot.send_message(
                chat_id=m.chat.id,
                text=BotMessages.START_SESSION.value
            )

    @ telegram_bot.message_handler(commands=[BotCommands.STOP_SESSION.value])
    def stop_session(m, res=False):
        try:
            vk_chat_id = getLinkedVkChatId(m.chat.id)
        except:
            return

        setVkSessionStatus(vk_chat_id, False)
        setTelegramSessionStatus(m.chat.id, False)

        vk_bot.messages.send(
            chat_id=vk_chat_id,
            message=BotMessages.STOP_SESSION.value,
            random_id=get_random_id()
        )
        telegram_bot.send_message(
            chat_id=m.chat.id,
            text=BotMessages.STOP_SESSION.value
        )

    @ telegram_bot.message_handler(content_types=["sticker"])
    def handler_sticker(message):
        pass
        # print(message)

    @ telegram_bot.message_handler(content_types=["photo"])
    def handler_photo(message):
        if isSession(message.chat.id):
            try:
                vk_chat_id = getLinkedVkChatId(message.chat.id)
            except:
                return

        file_id = message.photo[-1].file_id
        file_url = telegram_bot.get_file_url(file_id)

        session = requests.Session()
        upload = vk_api.VkUpload(vk_session)

        photo = session.get(file_url, stream=True)
        vk_photo = upload.photo_messages(photos=photo.raw)[0]

        attachment = f"photo{vk_photo['owner_id']}_{vk_photo['id']}"

        vk_bot.messages.send(
            chat_id=vk_chat_id,
            attachment=attachment,
            random_id=get_random_id()
        )

    @ telegram_bot.message_handler(content_types=["text"])
    def handler_text(message):
        if isSession(message.chat.id):
            try:
                vk_chat_id = getLinkedVkChatId(message.chat.id)
            except:
                return

            vk_bot.messages.send(
                chat_id=vk_chat_id,
                message=f"{message.from_user.first_name}: {message.text}",
                random_id=get_random_id()
            )

    telegram_bot.polling(none_stop=True, interval=0)


def init_environment():
    load_dotenv()


def init_config():
    global config
    global linked_chats

    config = configparser.ConfigParser()
    config.read(Consts.CONFIG_FILE.value)

    linked_chats = {"vkToTelegram": {}, "telegramToVk": {}}

    for key in config['channels']:
        key_without_prefix = int(key.replace(ChannelPrefix.VK.value, "").replace(
            ChannelPrefix.TELEGRAM.value, ""))
        value_without_prefix = int(config["channels"][key].replace(
            ChannelPrefix.VK.value, "").replace(ChannelPrefix.TELEGRAM.value, ""))

        if (key.startswith(ChannelPrefix.VK.value)):
            linked_chats['vkToTelegram'][key_without_prefix] = dict()
            linked_chats['vkToTelegram'][key_without_prefix]['id'] = value_without_prefix
            linked_chats['vkToTelegram'][key_without_prefix]['isReady'] = False
        elif (key.startswith(ChannelPrefix.TELEGRAM.value)):
            linked_chats['telegramToVk'][key_without_prefix] = dict()
            linked_chats['telegramToVk'][key_without_prefix]['id'] = value_without_prefix
            linked_chats['telegramToVk'][key_without_prefix]['isReady'] = False


def init_bots():
    global vk_session
    global vk_bot
    global telegram_bot

    vk_session = vk_api.VkApi(token=os.getenv(Consts.VK_TOKEN_KEY.value))
    vk_bot = vk_session.get_api()

    telegram_bot = telebot.TeleBot(os.getenv(Consts.TELEGRAM_TOKEN_KEY.value))

    vk_thread = threading.Thread(target=vk_bot_start, daemon=True)
    telegram_thread = threading.Thread(target=telegram_bot_start, daemon=True)

    vk_thread.start()
    telegram_thread.start()


def main_handler():
    while True:
        pass


def main():
    init_environment()
    init_config()
    init_bots()
    main_handler()


if __name__ == "__main__":
    main()
