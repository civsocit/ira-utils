from os import getenv

from dotenv import load_dotenv

load_dotenv()


class Settings:
    @classmethod
    def api_key(cls):
        return getenv("YOUTUBE_API_KEY")

    @classmethod
    def bot_list_link(cls):
        return "https://raw.githubusercontent.com/FeignedAccomplice/YOUTUBOTS/master/SMM.CSV"
