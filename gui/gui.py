import tkinter as tk
from asyncio import sleep
from datetime import date
from typing import Callable

from tkcalendar import DateEntry


class Gui:
    interval = 0.3  # Период обновления окна в секундах

    def __init__(self, run_callback: Callable):
        self._root = tk.Tk()
        self._root.wm_title("YouTube статистика")

        label = tk.Label(width=40)
        label["text"] = "Дата отсечки:"
        label.pack()

        self._date = DateEntry(master=self._root, width=38)
        self._date.pack()

        label = tk.Label(width=40)
        label["text"] = "Google API ключ:"
        label.pack()

        self._api = tk.Entry(master=self._root, width=40)
        self._api.pack()

        tk.Button(
            master=self._root, text="Начать", command=lambda: run_callback(self)
        ).pack()

    @property
    def date(self) -> date:
        return self._date.get_date()

    @property
    def api(self) -> str:
        return self._api.get()

    async def run(self):
        # По образцу https://gist.github.com/Lucretiel/e7d9a50b7b1960a56a1c
        try:
            while True:
                self._root.update()
                await sleep(self.interval)
        except tk.TclError as e:
            if "application has been destroyed" not in e.args[0]:
                raise