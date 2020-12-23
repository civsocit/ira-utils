import tkinter as tk
from asyncio import sleep
from datetime import date
from typing import Callable, List

from idlelib.tooltip import Hovertip
from tkcalendar import DateEntry

from settings import Settings


class Gui:
    interval = 0.1  # Период обновления окна в секундах

    def __init__(self, run_callback: Callable, close_callback: Callable):
        self._root = tk.Tk()
        self._root.wm_title("YouTube статистика")

        label = tk.Label(width=40)
        label["text"] = "Дата отсечки:"
        label.pack()

        self._date = DateEntry(master=self._root, width=38)
        self._date.pack()

        Hovertip(
            self._date,
            text="Программа будет искать видео на каналах из списка channels.txt, которые вышли \n"
            "после указанной даты. На анализ видео из списка videos.txt этот параметр не влияет",
        )

        label = tk.Label(width=40)
        label["text"] = "Google API ключ:"
        label.pack()

        self._api = tk.StringVar()
        key_entry = tk.Entry(master=self._root, textvariable=self._api, width=40)
        key_entry.pack()
        self._api.set(Settings.api_key())
        Hovertip(key_entry, text="Ваш Google API Key для доступа к YouTube")

        self._bots_frame = tk.LabelFrame(self._root, text="Группы ботов", width=40)
        Hovertip(
            self._bots_frame, "Какие категории ботов будут учитываться при анализе"
        )

        self._bot_groups = dict()

        for bot_group in Settings.bot_list_links().keys():
            self._bot_groups[bot_group] = tk.IntVar(value=0)
            check = tk.Checkbutton(
                self._bots_frame,
                text=bot_group,
                width=38,
                variable=self._bot_groups[bot_group],
            )
            check.pack()

        self._bots_frame.pack(padx=5, pady=5)

        self._bot_list_inverted = tk.IntVar(value=0)
        inverter = tk.Checkbutton(
            text="Только из указанных списков", variable=self._bot_list_inverted
        )
        inverter.pack()
        Hovertip(
            inverter,
            "Если этот пункт выбран, в статистике будут учитываться только акаунты ботов из выбранных\n"
            "выше списков (групп). Если этот пункт не выбран, в статистике будут учитываться аккаунты\n"
            "всех пользователей, кроме тех, которые есть в выбранных списках",
        )

        self._start_btn = tk.Button(
            master=self._root, text="Начать", command=lambda: run_callback(self)
        )
        self._start_btn.pack()

        self._root.protocol("WM_DELETE_WINDOW", close_callback)

    def disable(self):
        self._start_btn.config(state=tk.DISABLED)

    @property
    def date(self) -> date:
        return self._date.get_date()

    @property
    def ignore_bots(self) -> bool:
        return not bool(self._bot_list_inverted.get())

    @property
    def selected_bot_groups(self) -> List[str]:
        return [key for key, value in self._bot_groups.items() if value.get()]

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
