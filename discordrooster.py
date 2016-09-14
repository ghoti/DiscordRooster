import logging
import asyncio
import aiohttp
import discord
from time import sleep
import websockets
import configparser
import modules.ballotbox
import modules.fweight
import modules.time
import modules.trivia
import modules.who

from discord.ext import commands

from discord.ext import commands

class MyBot(commands.Bot):

    async def sane_connect(self):
        self.gateway = await self._get_gateway()
        await self._make_websocket()

        while not self.is_closed:
            msg = await self.ws.recv()
            if msg is None:
                if self.ws.close_code == 1012:
                    await self.redirect_websocket(self.gateway)
                    continue
                else:
                    # Connection was dropped, break out
                    break

            await self.received_message(msg)

bot = MyBot(command_prefix='!', description='Rooster knows all...')

@bot.command()
async def hello():
    await bot.say('hello')

loop = asyncio.get_event_loop()

while True:
    try:
        task = bot.login('rooster@mailinator.com', 'celery')
        loop.run_until_complete(task)

    except (discord.HTTPException, aiohttp.ClientError):
        logging.exception("Discord.py pls")
        loop.run_until_complete(sleep(10))

    else:
        break

while not bot.is_closed:
    try:
        loop.run_until_complete(bot.sane_connect())

    except (discord.HTTPException, aiohttp.ClientError, discord.GatewayNotFound,
            websockets.InvalidHandshake, websockets.WebSocketProtocolError):
        logging.exception("Discord.py pls")
        loop.run_until_complete(sleep(10))


