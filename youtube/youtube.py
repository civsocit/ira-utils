"""
Этот модуль использует YouTube API чтобы вытаскивать комментарии под видео, а также искать видео в каналах
"""
import asyncio
from asyncio import get_event_loop
from dataclasses import dataclass
from datetime import datetime
from typing import AsyncGenerator, Dict, Iterable, List, Optional

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


@dataclass
class ChannelInfo:
    channel: str  # Идентификатор канала
    registration_date: datetime  # Дата регистрации
    video_count: int  # Количество роликов на канале
    title: str  # Название
    subscribers_count: int  # Количество подписчиков
    view_count: int  # Количество просмотров


class _SessionWrap(ClientSession):
    """
    Этот класс может пригодиться для отладки расходов по квотам API.
    Он считает количество обращений по ссылке и собирает статистику.
    """

    def __init__(self, *args, **kwargs):
        self._calls = {}
        super(_SessionWrap, self).__init__(*args, **kwargs)

    def get(self, link, *args, **kwargs):
        if link not in self._calls:
            self._calls[link] = 0
        self._calls[link] += 1
        return super(_SessionWrap, self).get(link, *args, **kwargs)

    @property
    def stat(self):
        return self._calls


class YouTubeError(Exception):
    def __init__(self, code: int, message: str):
        self._code = code
        self._message = message
        super(YouTubeError, self).__init__(message + " (error code " + str(code) + ")")

    @property
    def message(self):
        return self._message

    @property
    def code(self):
        return self._code


class YouTubeApi:
    def __init__(self, key: str, session: ClientSession):
        """
        YouTube API класс
        :param key: API ключ
        :param session: aiohttp session object
        """
        self._session = session
        self._key = key

    async def _api_get(self, link: str, params: Optional[Dict] = None) -> Dict:
        """
        Отправить get-запрос и проверить JSON на ошибки
        :param link: ссылка
        :return: json словарь
        """
        async with self._session.get(link, params=params) as resp:
            data = await resp.json()
        if "error" in data:
            raise YouTubeError(data["error"]["code"], data["error"]["message"])

        return data

    async def list_videos_by_ids(self, ids: Iterable[str]) -> List[ChannelVideo]:
        """
        Получить идентификатор канала для каждого видео из списка
        :param ids: идентификаторы видео
        :return: Список видео (с идентификаторами каналов)
        """
        link = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            "key": self._key,
            "part": "snippet",
            "maxResults": 500,
            "id": ",".join(ids),
        }

        videos = []
        while True:

            data = await self._api_get(link, params)

            videos += [
                ChannelVideo(video["snippet"]["channelId"], video["id"])
                for video in data["items"]
                if "video" in video["kind"]
            ]

            # Видео много, нужно скачать их со следующей страницы
            if "nextPageToken" in data:
                params["pageToken"] = data["nextPageToken"]
                continue
            else:
                break

        return videos

    async def get_channel_info(self, channel: str) -> ChannelInfo:
        """
        Получить информацию по каналу
        :param channel: ID канала
        :return: информация
        """

        link = "https://www.googleapis.com/youtube/v3/channels"
        params = {"key": self._key, "id": channel, "part": "snippet,statistics"}

        data = await self._api_get(link, params)
        item = data["items"][0]

        info = ChannelInfo(
            channel=channel,
            registration_date=datetime.strptime(
                item["snippet"]["publishedAt"], "%Y-%m-%dT%H:%M:%SZ"
            ),
            video_count=int(item["statistics"]["videoCount"]),
            title=item["snippet"]["title"],
            subscribers_count=int(item["statistics"]["subscriberCount"]),
            view_count=int(item["statistics"]["viewCount"]),
        )
        return info

    async def list_videos_by_channel(
        self,
        channel: str,
        date_clamp: Optional[datetime] = None,
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

        videos = []
        while True:

            data = await self._api_get(link, params)

            videos += [
                ChannelVideo(channel, video["id"]["videoId"])
                for video in data["items"]
                if "video" in video["id"]["kind"]
            ]

            if "nextPageToken" in data:
                params["pageToken"] = data["nextPageToken"]
                continue
            else:
                break

        return videos

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
        self, parent: str, channel: str, video: str
    ) -> AsyncGenerator:
        """
        Скачать список дочерних комментариев (reply ответов на комментарий)
        :param parent: родительский комментарий
        :param channel: ссылка на канал (для заполнения свойства channel)
        :param video: ссылка на видео (для заполнения свойства video)
        :return: Генератор комментариев
        """
        link = "https://www.googleapis.com/youtube/v3/comments"
        params = {
            "key": self._key,
            "maxResults": 500,
            "parentId": parent,
            "part": "snippet,id",
        }

        while True:

            data = await self._api_get(link, params)

            for raw_comment in data["items"]:
                yield self.__to_comment(raw_comment, channel, video)

            if "nextPageToken" in data:
                params["pageToken"] = data["nextPageToken"]
                continue
            else:
                break

    async def list_comments(self, video: str, channel: str) -> AsyncGenerator:
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

        while True:
            try:
                data = await self._api_get(link, params)
            except YouTubeError as err:
                # Комментарии отключены
                if "disabled comments" in err.message:
                    return
                raise

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
                params["pageToken"] = data["nextPageToken"]
                continue
            else:
                break

    async def list_comments_full_list(
        self, video: str, channel: str, limit: Optional[int] = None
    ) -> List[Comment]:
        """
        То же, что и list_comments, но стащить сразу весь лист, без генераторов
        """
        comments = []
        count = 0
        async for comment in self.list_comments(video, channel):
            comments.append(comment)
            count += 1
            if limit and count > limit:
                break
        return comments


async def process_video(channel: str, video: str, api: YouTubeApi):
    comments = []
    async for comment in api.list_comments(video, channel=channel):
        comments.append(comment)
    print("Comments for " + video + " " + str(len(comments)))


async def main():
    async with _SessionWrap() as session:
        api = YouTubeApi(Settings.api_key(), session)
        channel = "UCWjEiMNZv4g3P9BWbrtMjyA"
        videos = await api.list_videos_by_channel(channel)
        videos = videos[:3]

        await asyncio.gather(
            *[process_video(channel, video.code, api) for video in videos]
        )

        print(session.stat)


if __name__ == "__main__":
    loop = get_event_loop()
    loop.run_until_complete(main())
