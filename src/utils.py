from typing import List, Tuple

from aiogram import Bot
from aiogram.filters.callback_data import CallbackData
from aiogram.types import BotCommand
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardBuilder


class SearchData(CallbackData, prefix='mv'):
    movie_nm: str
    movie_id: int


async def setup_bot_commands(bot: Bot):
    bot_commands = [
        BotCommand(command="/help", description="Get info about me"),
        BotCommand(command="/start", description="Allow me to introduce myself"),
        BotCommand(command="/stats", description="Display your stats"),
        BotCommand(command="/history", description="Display search history"),
    ]
    await bot.set_my_commands(bot_commands)


async def build_keyboard(movie_variants: List[Tuple[int, str, str]], chat_id: int, query: str):
    builder = InlineKeyboardBuilder()
    for variant in movie_variants:
        name = f'{variant[1]}, {variant[2]}'
        builder.button(text=name,
                       callback_data=SearchData(chat_id=chat_id,
                                                query=query,
                                                movie_nm=name,
                                                movie_id=int(variant[0])))
    builder.button(text='None of this are what I need', callback_data='none')
    return builder


async def construct_reply_for_variants(movie_variants: List[Tuple[int, str, str]]) -> Tuple[str, InlineKeyboardMarkup | None]:
    naming_pattern = '{}, {}'
    kb_builder = InlineKeyboardBuilder()
    if len(movie_variants) > 1:
        reply_txt = 'Here is what I managed to find:'
        for variant in movie_variants:
            name = naming_pattern.format(variant[1], variant[2])
            reply_txt += ('\n' + name)
            kb_builder.button(text=name,
                              callback_data=SearchData(movie_nm=name[:52],
                                                       movie_id=int(variant[0])))
        kb_builder.button(text='None of this are what I need', callback_data='none')
    elif len(movie_variants) == 1:
        variant = movie_variants[0]
        reply_txt = 'Is this the movie you are searching?'
        name = naming_pattern.format(variant[1], variant[2])
        reply_txt += ('\n' + name)
        kb_builder.button(text=name,
                          callback_data=SearchData(movie_nm=name[:56],
                                                   movie_id=int(variant[0])))
        kb_builder.button(text='No', callback_data='none')
    else:
        reply_txt = 'Unfortunately, I have not managed to find this movie.'

    return reply_txt, kb_builder.as_markup()
