import asyncio
import logging
from datetime import date, datetime
from itertools import chain
from statistics import (export_comments_text_statistics, export_statistics,
                        get_comments_text_statistics, get_statistics)
from typing import Iterable, List, Optional

from aiohttp import ClientSession

from antikremlebot import AntiIraApi
from gui import Gui
from settings import Settings
from youtube import ChannelVideo, Comment, YouTubeApi


async def main(
    api_key: str,
    video_date: date,
    bot_groups: List[str],
    ignore_bots: bool,
    export_videos: bool = False,
):
    """
    Запустить алгоритм выгрузки и анализа
    :param api_key: google API ключ
    :param video_date: отсечка по дате публикации видео
    :param bot_groups: группы ботов, статистику по которым нужно собрать
    :param ignore_bots: группы ботов, которых нужно игнорировать в статистике
    :param export_videos: экспортировать статистику по видео
    :return:
    """
    async with ClientSession() as session:
        # Взять список ботов
        bot_list_fetcher = AntiIraApi(session)
        bot_list = [bot.user for bot in await bot_list_fetcher.get_bot_list(bot_groups)]

        youtube_api = YouTubeApi(api_key, session)

        # Взять список каналов для анализа
        channels = AntiIraApi.get_channels_list()
        video_datetime = datetime(video_date.year, video_date.month, video_date.day)

        logging.info("Fetch channels...")
        # Скачать идентификаторы видео для каждого канала
        tasks = [
            youtube_api.list_videos_by_channel(channel, video_datetime)
            for channel in channels
        ]
        videos_groups = await asyncio.gather(*tasks)
        for channel, videos_in_channel in zip(channels, videos_groups):
            logging.info(
                "Channel " + channel + " has " + str(len(videos_in_channel)) + " videos"
            )
        videos: Iterable[ChannelVideo] = chain(*videos_groups)

        # Теперь добавить для анализа видео из списка videos.txt
        additional_video_ids = AntiIraApi.get_videos_list()
        # TODO: убирать из списка уже найденные на каналах видео
        videos = chain(
            videos, await youtube_api.list_videos_by_ids(additional_video_ids)
        )

        logging.info("Fetch comments...")
        # Теперь найти комментарии под каждым видео
        tasks = [
            youtube_api.list_comments_full_list(
                video.code, video.channel, Settings.comments_limit()
            )
            for video in videos
        ]
        comments: Iterable[Comment] = list(chain(*await asyncio.gather(*tasks)))

    # Теперь собрать статистику по комментариям!
    if ignore_bots:
        stat = get_statistics(comments, ignore_users=bot_list)
    else:
        stat = get_statistics(comments, use_only_users=bot_list)

    # И экспортировать её
    export_statistics(
        stat,
        datetime.now().strftime("stat_%Y-%m-%d_%H%M%S.csv"),
        export_videos=export_videos,
    )

    # И ещё сохранить сами тексты комментариев
    export_comments_text_statistics(
        get_comments_text_statistics(comments),
        datetime.now().strftime("comments_%Y-%m-%d_%H%M%S.csv"),
    )

    logging.info("Done")


def run_callback(window: Gui):
    """
    Callback для кнопки "начать" в gui
    """
    # Запретить повторный запуск
    window.disable()

    loop = asyncio.get_event_loop()

    # Добавить задачу на выгрузку данных
    loop.create_task(
        main(
            window.api,
            window.date,
            window.selected_bot_groups,
            window.ignore_bots,
            window.video_stat,
        )
    )


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
