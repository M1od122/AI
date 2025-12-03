import asyncio
from twitchio.ext import commands
from datetime import datetime

class TwitchChatReader:
    def __init__(self, channel_name: str, message_handler):
        self.channel_name = channel_name
        self.message_handler = message_handler

        # Создаём бота
        self.bot = commands.Bot(
            token="oauth:7lowzycgzw6682uvwr07pne2devwu9",  # Любой валидный OAuth (только для подключения к чату)
            prefix="!",
            initial_channels=[channel_name]
        )

        # Регистрируем обработчик сообщений через декоратор
        @self.bot.event()
        async def event_message(msg):
            if not msg.echo:
                await self.message_handler(
                    channel=self.channel_name,
                    username=msg.author.name,
                    message=msg.content,
                    timestamp=datetime.now()
                )

    async def start(self):

        await self.bot.start()
