import re
from dataclasses import dataclass
from datetime import date
from typing import List

from aiohttp import ClientSession

from settings import Settings


@dataclass
class Bot:
    user: str
    registration_date: date


class BotList:
    def __init__(self, session: ClientSession):
        self._session = session

    async def get_bot_list(self) -> List[Bot]:
        async with self._session.get(Settings.bot_list_link()) as resp:
            text = await resp.text()
            return [
                Bot(r[0], date.fromisoformat(r[1]))
                for r in re.findall(r"(?P<id>UC.+)=(?P<date>\d\d\d\d-\d\d-\d\d)", text)
            ]
