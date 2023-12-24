import asyncio
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.methods.send_message import SendMessage
from aiogram.types import Message, CallbackQuery

from src.scribe import Scribe
from src.searcher import Searcher
from src.utils import setup_bot_commands, construct_reply_for_variants, SearchData

bot = Bot(token=os.getenv('BOT_TOKEN'))
searcher = Searcher(tmdb_token=os.getenv('TMDB_TOKEN'))
scribe = Scribe('database.db')

dp = Dispatcher()


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
                                                            f'Date: {entry[2]}\n'))


@dp.message()
async def find_movie(message: Message):
    movie_variants = await searcher.search_tmdb(message.text)
    reply_txt, reply_markup = await construct_reply_for_variants(movie_variants)
    await message.reply(reply_txt, reply_markup=reply_markup)


@dp.callback_query(F.text == 'none')
async def movie_not_found(query: CallbackQuery):
    await query.message.answer('I am sorry that I could not find your movie. Try rewriting the search query.\n'
                               'I recommend using the full title and maybe the year of release.')


@dp.callback_query(SearchData.filter(F.movie_id))
async def send_movie_offers(query: CallbackQuery):
    data = SearchData.unpack(query.data)
    await scribe.record_query(query.message.chat.id, query.message.text, data.movie_id, data.movie_nm)
    offers = await searcher.search_offers(data.movie_id,
                                          # locale_priority=('us/en_us', 'ru/ru')
                                          )
    reply_txt = 'Here are some of the places you can watch it:\n'
    for offer in offers:
        reply_txt += str(offer)
    await query.message.answer(reply_txt)


async def main():
    await searcher.begin_session()
    await setup_bot_commands(bot)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
