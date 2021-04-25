#!/usr/bin/env python3

import asyncio
import csv
import fileinput
import re
import sys
from collections import defaultdict
from typing import Tuple

from aiohttp import ClientSession

SEARCH_URL = 'https://www.t30p.ru/sd.asmx/MoreSearch'
RE_LINK = re.compile(r'href=\"http://youtube\.com/watch\?v=([\w-]+)&amp;lc=')


async def fetch(client: ClientSession, user_id: str, pos: int = 0) -> Tuple[str, str]:
    params = {
        'sParams': f'"blogname:{user_id}"',
        'pos': pos,
        'numeration': '0'
    }
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    async with client.get(SEARCH_URL, params=params, headers=headers) as resp:
        data = await resp.json()
        page: str = data['d']
        if page:
            next_page = await fetch(client, user_id, pos + 30)
            return user_id, page + next_page[1]
        else:
            return user_id, page


async def main() -> None:
    result = defaultdict(int)
    async with ClientSession() as client:
        awaitables = []
        for line in fileinput.input():
            awaitables.append(fetch(client, user_id=line.strip()))
        fetch_results = await asyncio.gather(*awaitables)
        for user_id, html in fetch_results:
            for m in RE_LINK.finditer(html):
                result[user_id,m.group(1)] += 1
    writer = csv.writer(sys.stdout, csv.excel_tab)
    writer.writerow(['userID', '', 'videoID', 'counter'])
    for key, val in result.items():
        writer.writerow([key[0], '', key[1], val])


if __name__ == '__main__':
    asyncio.run(main())
