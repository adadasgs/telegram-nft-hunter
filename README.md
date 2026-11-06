# Telegram NFT Hunter

Самописный монитор публично доступных профилей участников Telegram-групп, в которых состоит аккаунт парсера.

## Что делает
- Следит за новыми сообщениями в перечисленных вами группах.
- Проверяет отправителя через Telegram API на наличие **коллекционных подарков** (Collectible Gifts).
- Публикует в указанную группу только ссылку вида `https://t.me/username`.
- Не публикует аккаунты без username, без подтверждённого коллекционного подарка и уже опубликованные ранее.

## Важно
- Источники задаются вручную в `SOURCE_CHATS`; парсер не обходит закрытые группы и не пытается обходить ограничения Telegram.
- Telegram показывает только те подарки, которые доступны текущей сессии через API. Приватные/скрытые данные не гарантируются.
- Используйте отдельный аккаунт парсера и только группы, в которых у вас есть право состоять.
- Никогда не помещайте API_HASH, SESSION_STRING или BOT_TOKEN в GitHub.

## Переменные окружения
`API_ID`, `API_HASH`, `SESSION_STRING`, `BOT_TOKEN`, `TARGET_CHAT_ID`, `SOURCE_CHATS`.

`SOURCE_CHATS` — usernames или ID групп через запятую, например: `group_one,-1001234567890`.

## Запуск
```bash
pip install -r requirements.txt
python main.py
```

На Render создайте Background Worker, Build Command: `pip install -r requirements.txt`, Start Command: `python main.py`.
