from asyncio import get_event_loop

from aiohttp import ClientSession

from antikremlebot import Bot, BotList


async def main():
    async with ClientSession() as session:
        bot_list_fetcher = BotList(session)
        bot_list = await bot_list_fetcher.get_bot_list()
    print(bot_list)


if __name__ == "__main__":
    loop = get_event_loop()
    loop.run_until_complete(main())
