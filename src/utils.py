from typing import List, Tuple

from aiogram import Bot
from aiogram.filters.callback_data import CallbackData
from aiogram.types import BotCommand
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardBuilder


class SearchData(CallbackData, prefix='mv'):
    movie_id: int
    movie_nm: str


async def setup_bot_commands(bot: Bot):
    bot_commands = [
        BotCommand(command="/help", description="Get info about me"),
        BotCommand(command="/start", description="Allow me to introduce myself"),
        BotCommand(command="/stats", description="Display your stats"),
        BotCommand(command="/history", description="Display search history"),
    ]
    await bot.set_my_commands(bot_commands)


async def construct_reply_for_variants(movie_variants: List[Tuple[int, str, str]]) \
        -> Tuple[str, InlineKeyboardMarkup | None]:
    naming_pattern = '{}, {}'
    kb_builder = InlineKeyboardBuilder()
    if len(movie_variants) > 1:
        reply_txt = 'Here is what I managed to find:'
        for index, variant in enumerate(movie_variants):
            name = naming_pattern.format(variant[1], variant[2])
            button_txt = f'{index + 1}. {name}'
            reply_txt += ('\n' + button_txt)
            kb_builder.button(text=button_txt[:16] + '...',
                              callback_data=SearchData(movie_id=int(variant[0]), movie_nm=name.replace(':', ',')[:48]))
        reply_txt += '\nPlease pick your movie'
        kb_builder.button(text='None', callback_data='none')
    elif len(movie_variants) == 1:
        variant = movie_variants[0]
        reply_txt = 'Is this the movie you are searching?'
        name = naming_pattern.format(variant[1], variant[2])
        button_txt = name
        reply_txt += ('\n' + button_txt)
        kb_builder.button(text=button_txt[:16] + '...',
                          callback_data=SearchData(movie_id=int(variant[0]), movie_nm=name.replace(':', ',')[:48]))
        kb_builder.button(text='No', callback_data='none')
    else:
        reply_txt = 'Unfortunately, I have not managed to find this movie.'

    return reply_txt, kb_builder.as_markup()
