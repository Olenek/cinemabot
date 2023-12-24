import os.path
import sqlite3
from sqlite3 import Connection
from typing import List, Tuple

from aiogram import Bot, types
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton, InlineKeyboardBuilder


async def setup_bot_commands(bot: Bot):
    bot_commands = [
        types.BotCommand(command="/help", description="Get info about me"),
        types.BotCommand(command="/start", description="Allow me to introduce myself"),
        types.BotCommand(command="/stats", description="Display your stats"),
        types.BotCommand(command="/history", description="Display search history"),
    ]
    await bot.set_my_commands(bot_commands)


def setup_database(db_filename: str) -> Connection:
    if os.path.exists(db_filename):
        return sqlite3.connect(db_filename)

    connection = sqlite3.connect(db_filename)
    connection.execute(
        """
        create table queries (
            query_id integer auto_increment primary_key,
            chat_id integer,
            query_dttm datetime,
            query_txt varchar(256),
            offer_id integer
        )
        """
    )

    connection.execute(
        """
        create table offers (
            offer_id integer auto_increment primary_key,
            movie_id integer,
            movie_nm varchar(256),
            offer_url varchar(256)
        )
        """
    )

    return connection


async def build_keyboard(movie_variants: List[Tuple[int, str, int]]):
    builder = InlineKeyboardBuilder()
    for variant in movie_variants:
        builder.button(text=f'{variant[1]}, {variant[2]}', callback_data=str(variant[0]))
    return builder.as_markup()


async def make_reply_from_variants(movie_variants: List[Tuple[int, str, int]]) -> Tuple[str, InlineKeyboardMarkup | None]:
    pattern = '{}, {}'
    kb_builder = InlineKeyboardBuilder()
    if len(movie_variants) > 1:
        reply_txt = 'Here is what I managed to find:'
        for variant in movie_variants:
            option = pattern.format(variant[1], variant[2])
            reply_txt += ('\n' + option)
            kb_builder.button(text=option, callback_data=str(variant[0]))
        kb_builder.button(text='None of this are what I need', callback_data='none')
    elif len(movie_variants) == 1:
        option = pattern.format(movie_variants[0][1], movie_variants[0][2])
        reply_txt = 'Is this the movie you are searching?\n' + option
        kb_builder.button(text=option, callback_data=str(movie_variants[0][0]))
        kb_builder.button(text='No(', callback_data='none')
    else:
        reply_txt = 'Unfortunately, I have not managed to find this movie.'

    return reply_txt, kb_builder.as_markup()
