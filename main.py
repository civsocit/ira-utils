import asyncio
from datetime import date, datetime
from itertools import chain
from statistics import export_statistics, get_statistics
from typing import Iterable

from aiohttp import ClientSession

from antikremlebot import AntiIraApi
from gui import Gui
from youtube import ChannelVideo, Comment, YouTubeApi


async def main(api_key: str, video_date: date):
    """
    Запустить алгоритм выгрузки и анализа
    :param api_key: google API ключ
    :param video_date: отсечка по дате публикации видео
    :return:
    """
    # Взять список каналов для анализа
    channels = AntiIraApi.get_channels_list()
    video_datetime = datetime(video_date.year, video_date.month, video_date.day)

    async with ClientSession() as session:
        # Взять список ботов
        bot_list_fetcher = AntiIraApi(session)
        bot_list = [bot.user for bot in await bot_list_fetcher.get_bot_list()]

        youtube_api = YouTubeApi(api_key, session)

        # Скачать идентификаторы видео для каждого канала
        tasks = [
            youtube_api.list_videos(channel, video_datetime) for channel in channels
        ]
        videos: Iterable[ChannelVideo] = chain(*await asyncio.gather(*tasks))

        # Теперь найти комментарии под каждым видео
        tasks = [
            youtube_api.list_comments_full_list(video.code, video.channel)
            for video in videos
        ]
        comments: Iterable[Comment] = chain(*await asyncio.gather(*tasks))

    print("Total channels: " + str(len(channels)))
    print("Total comments: " + str(len([c for c in comments])))
    print("Total videos: " + str(len([v for v in videos])))

    # Теперь собрать статистику по комментариям!
    stat = get_statistics(comments, bot_list)

    # И экспортировать её
    export_statistics(stat, "stat.csv")


def run_callback(window: Gui):
    """
    Callback для кнопки "начать" в gui
    """
    loop = asyncio.get_event_loop()
    # Добавить задачу на выгрузку данных
    loop.create_task(main(window.api, window.date))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    gui = Gui(run_callback)
    # Добавить задачу на работу интерфейса главного окна
    loop.create_task(gui.run())

    loop.run_forever()
