import csv
from typing import Dict, Iterable, Optional

from youtube import Comment

"""
Имя пользователя, на какие каналы подписан, 
сколько комментариев оставил под видео на данном канале
Т.е.
{
    "user1": {
        "channel1": 43,
        "channel2": 14,
        ...
    },
    "user2": {
        "channel1": 95,
        "channel9": 2,
        ...
    },
    ...
} 
"""
Statistics = Dict[str, Dict[str, int]]


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
            stat[comment.author][comment.channel] = 1
        else:
            stat[comment.author][comment.channel] += 1

    return stat


def export_statistics(stat: Statistics, path: str):
    """
    Экспортировать статистику в файл
    :param stat: статистика
    :param path: файл таблицы
    :return:
    """
    with open(path, "w", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter="\t")
        writer.writerow(["user_id", "channel", "comments"])
        for user, channels in stat.items():
            for channel, count in channels.items():
                writer.writerow([user, channel, count])
