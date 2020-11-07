"""
Этот модуль использует YouTube API чтобы вытаскивать комментарии под видео, а также искать видео в каналах
"""
import asyncio
from asyncio import get_event_loop
from dataclasses import dataclass
from datetime import datetime
from typing import AsyncGenerator, List, Optional

from aiohttp import ClientSession

from settings import Settings


@dataclass
class ChannelVideo:
    channel: str
    code: str


@dataclass
class Comment:
    channel: str
    video: str
    author: str
    comment: str
    id: str


class SessionWrap(ClientSession):
    """
    Этот класс может пригодиться для отладки расходов по квотам API.
    Он считает количество обращений по ссылке и собирает статистику.
    """

    def __init__(self, *args, **kwargs):
        self._calls = {}
        super(SessionWrap, self).__init__(*args, **kwargs)

    def get(self, link, *args, **kwargs):
        if link not in self._calls:
            self._calls[link] = 0
        self._calls[link] += 1
        return super(SessionWrap, self).get(link, *args, **kwargs)

    @property
    def stat(self):
        return self._calls


class YouTubeApi:
    def __init__(self, key: str, session: ClientSession):
        """
        YouTube API класс
        :param key: API ключ
        :param session: aiohttp session object
        """
        self._session = session
        self._key = key

    async def list_videos(
        self, channel: str, date_clamp: Optional[datetime] = None
    ) -> List[ChannelVideo]:
        """
        Получить все видео для указанного канала
        :param channel: идентификатор канала
        :param date_clamp: дата, начиная с которой смотреть видео
        :return: Список видео
        """
        link = "https://www.googleapis.com/youtube/v3/search"
        params = {"key": self._key, "maxResults": 500, "channelId": channel}
        if date_clamp:
            params["publishedAfter"] = date_clamp.isoformat() + "Z"
        async with self._session.get(link, params=params) as resp:
            data = await resp.json()
        return [
            ChannelVideo(channel, video["id"]["videoId"])
            for video in data["items"]
            if "video" in video["id"]["kind"]
        ]

    @classmethod
    def __to_comment(cls, data, channel: str, video: str) -> Comment:
        """
        Конвертировать JSON Объект комментария в комментарий
        :param data:
        :param channel:
        :param video:
        :return:
        """
        snippet = data["snippet"]
        if "commentThread" in data["kind"]:
            snippet = snippet["topLevelComment"]["snippet"]

        return Comment(
            channel=channel,
            video=video,
            author=snippet["authorChannelId"]["value"]
            if "authorChannelId" in snippet
            else "none",
            comment=snippet["textOriginal"],
            id=data["id"],
        )

    async def list_child_comments(
        self, parent: str, channel: str, video: str, page_id: Optional[str] = None
    ) -> AsyncGenerator:
        """
        Скачать список дочерних комментариев (reply ответов на комментарий)
        :param parent: родительский комментарий
        :param channel: ссылка на канал (для заполнения свойства channel)
        :param video: ссылка на видео (для заполнения свойства video)
        :param page_id: идентификатор страницы загрузки (нужно в рекурсии для многостраничной загрузки, если
                        комментариев много)
        :return: Генератор комментариев
        """
        link = "https://www.googleapis.com/youtube/v3/comments"
        params = {
            "key": self._key,
            "maxResults": 500,
            "parentId": parent,
            "part": "snippet,id",
        }
        if page_id:
            params["pageToken"] = page_id
        async with self._session.get(link, params=params) as resp:
            data = await resp.json()
        for raw_comment in data["items"]:
            yield self.__to_comment(raw_comment, channel, video)
        if (
            "nextPageToken" in data
        ):  # Комментариев много, нужно скачать их со следующей страницы
            async for comment in self.list_child_comments(
                parent, channel, video, data["nextPageToken"]
            ):
                yield comment

    async def list_comments(
        self, video: str, channel: str, page_id: Optional[str] = None
    ) -> AsyncGenerator:
        """
        Скачать список комментариев под видео
        :param video: идентификатор видео
        :param channel: идентификатор канал (для заполнения поля channel)
        :param page_id: идентификатор следующей страницы (для многостраничной загрузки в рекурсии)
        :return: генератор комментариев
        """
        link = "https://www.googleapis.com/youtube/v3/commentThreads"
        params = {
            "key": self._key,
            "maxResults": 500,
            "videoId": video,
            "textFormat": "plainText",
            "part": "snippet, id, replies",
        }
        if page_id:
            params["pageToken"] = page_id
        async with self._session.get(link, params=params) as resp:
            data = await resp.json()
        for raw_comment in data["items"]:
            yield self.__to_comment(raw_comment, channel, video)
            replies = raw_comment["snippet"]["totalReplyCount"]
            if replies:  # У комментария есть дочерние комментарии
                if (
                    len(raw_comment["replies"]["comments"]) == replies
                ):  # Записать дочерние комментарии
                    for raw_child_comment in raw_comment["replies"]["comments"]:
                        yield self.__to_comment(raw_child_comment, channel, video)
                # TODO: Здесь возможна оптимизация, тянуть дочерние комментарии через gather
                else:  # Дочерних комментариев так много, что нужно отдельно загрузить их
                    async for child in self.list_child_comments(
                        raw_comment["id"], channel, video
                    ):
                        yield child
        if (
            "nextPageToken" in data
        ):  # Комментариев много, нужно скачать их со следующей страницы
            async for comment in self.list_comments(
                video, channel, data["nextPageToken"]
            ):
                yield comment

    async def list_comments_full_list(self, video: str, channel: str) -> List[Comment]:
        """
        То же, что и list_comments, но стащить сразу весь лист, без генераторов
        """
        comments = []
        async for comment in self.list_comments(video, channel):
            comments.append(comment)
        return comments


async def process_video(channel: str, video: str, api: YouTubeApi):
    comments = []
    async for comment in api.list_comments(video, channel=channel):
        comments.append(comment)
    print("Comments for " + video + " " + str(len(comments)))


async def main():
    async with SessionWrap() as session:
        api = YouTubeApi(Settings.api_key(), session)
        channel = "UCWjEiMNZv4g3P9BWbrtMjyA"
        videos = await api.list_videos(channel)
        videos = videos[:3]

        await asyncio.gather(
            *[process_video(channel, video.code, api) for video in videos]
        )

        print(session.stat)


if __name__ == "__main__":
    loop = get_event_loop()
    loop.run_until_complete(main())
