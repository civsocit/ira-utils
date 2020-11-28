import asyncio
import re
from dataclasses import dataclass
from datetime import date
from os.path import isfile
from typing import List

from aiohttp import ClientSession

from settings import Settings


@dataclass
class Bot:
    user: str
    registration_date: date


class AntiIraApi:
    def __init__(self, session: ClientSession):
        """
        Класс реализует общение с сервисами команды по поиску ботов
        Тут же общение с конфигами которые могут лежать локально на ПК
        :param session: Текущия сессия
        """
        self._session = session

    async def _request(self, link: str) -> str:
        async with self._session.get(link) as resp:
            return await resp.text()

    async def get_bot_list(self) -> List[Bot]:
        """
        Получить список известных youtube кремлеботов
        :return: Список ботов
        """
        texts = await asyncio.gather(
            *[self._request(link) for link in Settings.bot_list_links()]
        )
        text = "\n".join(texts)
        return [
            Bot(r[0], date.fromisoformat(r[1]))
            for r in re.findall(r"(?P<id>UC.+)=(?P<date>\d\d\d\d-\d\d-\d\d)", text)
        ]

    @classmethod
    def _read_file_list(cls, path: str) -> List[str]:
        """
        Прочитать абстрактный список из файла
        :param path:
        :return:
        """
        if not isfile(path):
            return []
        with open(path, "r") as file:
            return list(
                {  # повторяющиеся фразы будут удалены
                    line.strip()
                    for line in file.readlines()
                    if line.strip() and not line.startswith("#")
                }
            )

    @classmethod
    def get_channels_list(cls) -> List[str]:
        """
        Получить список идентификаторв youtube каналов для мониторинга
        :return: Список каналов
        """
        return cls._read_file_list("channels.txt")

    @classmethod
    def get_videos_list(cls) -> List[str]:
        """
        Получить список идентификаторов youtube видео для мониторинга
        :return: Список видео
        """
        return cls._read_file_list("videos.txt")


async def main():
    async with ClientSession() as session:
        api = AntiIraApi(session)
        bots = await api.get_bot_list()
        print(bots)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
