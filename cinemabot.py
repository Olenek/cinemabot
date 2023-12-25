import asyncio
import os
from typing import Dict

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.methods.send_message import SendMessage
from aiogram.types import Message, CallbackQuery
from aiogram.filters.state import State, StatesGroup

from src.scribe import Scribe
from src.searcher import Searcher, locales
from src.utils import setup_bot_commands, construct_reply_for_variants, SearchData

bot = Bot(token=os.getenv('BOT_TOKEN'))
searcher = Searcher(tmdb_token=os.getenv('TMDB_TOKEN'))
scribe = Scribe('database.db')

dp = Dispatcher()

class MyDialog(StatesGroup):
    waits = State()
    none = State()

@dp.message(Command('start'))
async def send_welcome(message: Message):
    await message.reply(f"I am @Olenek0's CinemaBot! "
                        f"Designed to fetch all the best places to watch your favorite movies.\n"
                        f"To search for a specific movie, just send me a message with its title.", )


@dp.message(Command('help'))
async def send_help(message: Message):
    await message.reply(f"- Command /start, and I will introduce myself\n"
                        f"- Command /help, and I will show the list of commands\n"
                        f"- Command /stats, and I will display statistics based on your queries\n"
                        f"- Command /history, and I will send you the history of your search queries\n"
                        f"- Type in anything else, and I will do my best to find "
                        f"the best place to watch a movie based on the request.")


@dp.message(Command('history'))
async def send_history(message: Message):
    for entry in await scribe.get_last_n(message.chat.id.real, 5):
        await bot(SendMessage(chat_id=message.chat.id, text=f'Query: {entry[0]}\n'
                                                            f'Result: {entry[1]}\n'
                                                            f'Date: {entry[2]}'))


@dp.message(Command('stats'))
async def send_stats(message: Message):
    for entry in await scribe.get_stats(message.chat.id.real):
        await bot(SendMessage(chat_id=message.chat.id, text=f'Movie: {entry[0]}\n'
                                                            f'Query Count: {entry[1]}'))


@dp.message()
async def find_movie(message: Message, state: FSMContext):
    movie_variants = await searcher.search_tmdb(message.text)
    reply_txt, reply_markup = await construct_reply_for_variants(movie_variants)
    await state.set_state(MyDialog.waits)
    await state.update_data(query=message.text)
    await message.reply(reply_txt, reply_markup=reply_markup)


@dp.callback_query(F.data == 'none')
async def movie_not_found(query: CallbackQuery, state: FSMContext):
    await state.set_state(MyDialog.none)
    await query.message.answer('I am sorry that I could not find your movie. Try rewriting the search query.\n'
                               'I recommend using the full title and maybe the year of release.')


@dp.callback_query(SearchData.filter(F.movie_id))
@dp.message(MyDialog.waits)
async def send_movie_offers(query: CallbackQuery, state: FSMContext):
    data = SearchData.unpack(query.data)
    usr_query = (await state.get_data())['query']
    await scribe.record_query(query.message.chat.id, usr_query, data.movie_id, data.movie_nm)
    await state.set_state(MyDialog.none)
    offers: Dict[str, str] = await searcher.search_offers(data.movie_id)

    if len(offers) > 1:
        reply_txt = 'Here are some of the places you can watch it:'
        for locale_nm, url in offers.items():
            reply_txt += f"\n{locales[locale_nm]['emoji']} - {url}"
        await query.message.answer(reply_txt)
    elif len(offers) == 1:
        reply_txt = 'Here is where you can watch it:'
        for locale_nm, url in offers.items():
            reply_txt += f"\n{locales[locale_nm]['emoji']} - {url}"
        await query.message.answer(reply_txt)
    else:
        reply_txt = 'Unfortunately, I could not find this movie anywhere(\nContact @Olenek0 for fixes'
        await query.message.answer(reply_txt)


async def main():
    await searcher.begin_session()
    await setup_bot_commands(bot)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
