#!/usr/bin/env python3

import argparse
import asyncio
import csv
import io
import platform
import re
from collections import defaultdict
from typing import Tuple

from aiohttp import ClientSession

SEARCH_URL = 'https://www.t30p.ru/sd.asmx/MoreSearch'
RE_LINK = re.compile(r'href=\"http://youtube\.com/watch\?v=([\w-]+)&amp;lc=')
semaphore = asyncio.Semaphore(10)

# Windows OS-specific HACK to silence exception thrown on event loop being closed
# as part of the asyncio library's proactor
# Hack sourced from an issue on the aiohttp library:
#   https://github.com/aio-libs/aiohttp/issues/4324#issuecomment-733884349
if platform.system() == 'Windows':
    from functools import wraps
    from asyncio.proactor_events import _ProactorBasePipeTransport

    def silence_event_loop_closed(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except RuntimeError as e:
                if str(e) != 'Event loop is closed':
                    raise
        return wrapper

    _ProactorBasePipeTransport.__del__ = silence_event_loop_closed(_ProactorBasePipeTransport.__del__)


async def fetch(client: ClientSession, user_id: str, pos: int = 0) -> Tuple[str, str]:
    params = {
        'sParams': f'"blogname:{user_id}"',
        'pos': pos,
        'numeration': '0'
    }
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    async with semaphore, client.get(SEARCH_URL, params=params, headers=headers) as resp:
        data = await resp.json()
    page: str = data['d']
    if page:
        next_page = await fetch(client, user_id, pos + 30)
        return user_id, page + next_page[1]
    else:
        return user_id, page


async def main(infile: io.TextIOWrapper, out_filename: str) -> None:
    result = defaultdict(int)
    async with ClientSession() as client:
        awaitables = []
        for line in infile:
            awaitables.append(fetch(client, user_id=line.strip()))
        fetch_results = await asyncio.gather(*awaitables)
    for user_id, html in fetch_results:
        for m in RE_LINK.finditer(html):
            result[user_id, m.group(1)] += 1
    with open(out_filename, 'w', newline='') as outfile:
        writer = csv.writer(outfile, csv.excel_tab)
        writer.writerow(['userID', '', 'videoID', 'counter'])
        for key, val in result.items():
            writer.writerow([key[0], '', key[1], val])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'), default='user_id_list.txt')
    parser.add_argument('outfile', nargs='?', default='report.tsv')
    args = parser.parse_args()
    asyncio.run(main(args.infile, args.outfile))
