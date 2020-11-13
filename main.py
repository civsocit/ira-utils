import asyncio
import logging
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
        videos_groups = await asyncio.gather(*tasks)
        for channel, videos_in_channel in zip(channels, videos_groups):
            logging.info(
                "Channel " + channel + " has " + str(len(videos_in_channel)) + " videos"
            )
        videos: Iterable[ChannelVideo] = chain(*videos_groups)

        # Теперь найти комментарии под каждым видео
        tasks = [
            youtube_api.list_comments_full_list(video.code, video.channel)
            for video in videos
        ]
        comments: Iterable[Comment] = chain(*await asyncio.gather(*tasks))

    # Теперь собрать статистику по комментариям!
    stat = get_statistics(comments, bot_list)

    # И экспортировать её
    export_statistics(stat, "stat.csv")

    logging.info("Done")


def run_callback(window: Gui):
    """
    Callback для кнопки "начать" в gui
    """
    # Запретить повторный запуск
    window.disable()

    loop = asyncio.get_event_loop()

    # Добавить задачу на выгрузку данных
    loop.create_task(main(window.api, window.date))


def close_callback():
    """
    Callback для кнопки "закрыть" gui
    :return:
    """
    loop = asyncio.get_event_loop()
    loop.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    loop = asyncio.get_event_loop()

    gui = Gui(run_callback, close_callback)
    # Добавить задачу на работу интерфейса главного окна
    loop.create_task(gui.run())

    loop.run_forever()
