# Utter
## Описание
Бот для пересылки сообщение между Vk и Telegram. Планировал использовать в личных целях, но решил развить бота чтобы удобно было пользоваться любому.

### Возможности:
* Пересылка текстовых сообщение в обе стороны
* Пересылка файлов/фото (пока что только из Vk в Telegram)
* Файл конфигурации для удобной настройки бота

## Установка
#### Установка зависимостей
```
pip install -r requirements.txt
```
#### Запуск
```
python ./main.py
```

## Настройка
Создать файл .env и заполнить его в соответствие с примером (.env.example)
В файл config.ini в раздел [channels] добавить связь между группами. Например:
```
[channels]
vk_1=tg_-7218425
tg_-7218425=vk_1
```
