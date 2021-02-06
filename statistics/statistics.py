import csv
from typing import Dict, Iterable, List, Optional

from youtube import Comment

"""
Имя пользователя, на какие каналы подписан, 
сколько комментариев оставил под видео на данном канале
Т.е.
{
    "user1": {
        "channel1": {
            "video1": 42,
            "video2": 99
        },
        "channel2": {
            "video3": 11,
            "video5": 88,
            "video6": 88
        },

    },
    "user2": {
        "channel1": {
            "video9": 0,
        },
        "channel9": {
            "video16": 54
        }
    },
}
"""

Statistics = Dict[str, Dict[str, Dict[str, int]]]


def get_statistics(
    comments: Iterable[Comment],
    ignore_users: Optional[Iterable[str]] = None,
    use_only_users: Optional[Iterable[str]] = None,
) -> Statistics:
    """
    Собрать статистику по комментариям из аргумента
    :param comments: асинхронный генератор, берёт комментарии по одному
    :param ignore_users: список пользователей, которых нужно игнорировать
    :param use_only_users: список пользователей для составления статистики; пользователи не из списка будут
                           игнорироваться
    :return: Статистика
    """
    stat = dict()
    for comment in comments:
        # Это бот, игнорировать его
        if ignore_users and comment.author in ignore_users:
            continue
        # Пользователь не из списка, игнорировать
        if use_only_users and comment.author not in use_only_users:
            continue
        # Это канал комментирует сам себя, игнорировать
        if comment.author == comment.channel:
            continue
        if comment.author not in stat:
            stat[comment.author] = dict()
        if comment.channel not in stat[comment.author]:
            stat[comment.author][comment.channel] = dict()
        if comment.video not in stat[comment.author][comment.channel]:
            stat[comment.author][comment.channel][comment.video] = 0

        stat[comment.author][comment.channel][comment.video] += 1

    return stat


def export_statistics(stat: Statistics, path: str, export_videos: bool = False):
    """
    Экспортировать статистику в файл
    :param stat: статистика
    :param path: файл таблицы
    :param export_videos: экспоритровать статистику по видео тоже
    :return:
    """
    with open(path, "w", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter="\t")

        if not export_videos:
            writer.writerow(["user_id", "channel", "comments"])
            for user, channels in stat.items():
                for channel, videos in channels.items():
                    total_channel_count = sum(videos.values())
                    writer.writerow([user, channel, total_channel_count])
        else:
            writer.writerow(["user_id", "channel", "video", "comments"])
            for user, channels in stat.items():
                for channel, videos in channels.items():
                    for video, count in videos.items():
                        writer.writerow([user, channel, video, count])


# Просто список комментариев по каждому пользователю
CommentsTextStatistics = Dict[str, List[str]]


def get_comments_text_statistics(comments: Iterable[Comment]) -> CommentsTextStatistics:
    """
    Собрать комментарии пользователей
    :param comments:
    :return:
    """
    statistics = dict()
    for comment in comments:
        if comment.author not in statistics:
            statistics[comment.author] = []
        statistics[comment.author].append(comment.comment)
    return statistics


def export_comments_text_statistics(stat: CommentsTextStatistics, path: str):
    """
    Экспортировать тексты комментариев
    :param stat:
    :param path:
    :return:
    """
    with open(path, "w", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter="\t")
        writer.writerow(["user_id", "comment"])
        for user, comments in stat.items():
            for comment in comments:
                writer.writerow([user, comment])
