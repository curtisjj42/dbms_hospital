import os
from dataclasses import dataclass
from pprint import pprint

from dotenv import load_dotenv
from strenum import StrEnum


class EnvConfig(StrEnum):
    Host = 'DB_HOST'
    User = 'DB_USER'
    Password = 'DB_PASS'
    Database = 'DB_DATABASE'


@dataclass
class Config:
    Host: str
    User: str
    Password: str
    Database: str


def load_config() -> Config:
    load_dotenv()
    # noinspection PyUnresolvedReferences
    config_entries = {i.name: i.value for i in EnvConfig}
    items = {k: os.getenv(v) for k, v in config_entries.items()}
    if None in items.values():
        raise ValueError('Invalid value in config file')
    return Config(**items)  # type: ignore


if __name__ == '__main__':
    c = load_config()
    pprint(c)
