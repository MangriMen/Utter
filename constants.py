from enum import Enum


class ChannelPrefix(Enum):
    VK = "vk_"
    TELEGRAM = "tg_"


class Consts(Enum):
    CONFIG_FILE = "config.ini"

    VK_TOKEN_KEY = "VK_TOKEN"
    VK_GROUP_ID_KEY = "VK_GROUP_ID"

    TELEGRAM_TOKEN_KEY = "TELEGRAM_TOKEN"
