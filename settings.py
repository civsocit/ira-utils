from os import getenv
from typing import Dict

from dotenv import find_dotenv, load_dotenv

dotenv_path = find_dotenv(".env") or find_dotenv("environment.env")
load_dotenv(dotenv_path)


class Settings:
    @classmethod
    def api_key(cls) -> str:
        return getenv("YOUTUBE_API_KEY")

    @classmethod
    def bot_list_links(cls) -> Dict[str, str]:
        return {
            "SMM": "https://raw.githubusercontent.com/FeignedAccomplice/YOUTUBOTS/master/SMM.CSV",
            "KB": "https://raw.githubusercontent.com/FeignedAccomplice/YOUTUBOTS/master/KB.CSV",
        }

    @classmethod
    def comments_limit(cls) -> int:
        return int(getenv("COMMENTS_LIMIT", 0))
