import re

from justwatch import JustWatch
from typing import List, Tuple
from aiohttp import ClientSession
from bs4 import BeautifulSoup

class Searcher:
    def __init__(self, tmdb_token: str):
        # self._tmdb_header = {
        #     'Accept': 'application/json',
        #     'Authorization': f'Bearer {tmdb_token}'   
        # }
        self._tmdb_token = tmdb_token

        self._tmdb_search_url = 'https://api.themoviedb.org/3/search/movie'
        self._tmdb_watch_providers_url = 'https://api.themoviedb.org/3/movie/{}/watch/providers'

        self._session = None

    async def begin_session(self):
        self._session: ClientSession = ClientSession()

    async def search_tmdb(self, query: str) -> List[Tuple[int, str, str]]:
        tmdb_response = await self._session.get(self._tmdb_search_url,
                                                params={'query': query, 'api_key': self._tmdb_token},
                                                # headers=self._tmdb_header
                                                )
        response_data = (await tmdb_response.json())['results']
        # print(response_data)

        if response_data:
            return [(item['id'], item['title'], item['release_date'][:4]) for item in response_data[:3]]
        return []

    async def search_offers(self, movie_id: int, locale_priority=('RU', 'EN')):
        tmdb_response = await self._session.get(
            self._tmdb_watch_providers_url.format(movie_id),
            params={'api_key': self._tmdb_token},
        )
        response_data = (await tmdb_response.json())
        options = response_data['results']
        any_locale = next(iter(options.keys()))
        print(any_locale)

        for locale in locale_priority:
            if options.get(locale, None) is not None:
                return await self._construct_offer(options[locale]['link'])

        fallback_url = options[any_locale]['link']
        print(fallback_url)
        return await self._construct_offer(fallback_url[:10])

    async def _construct_offer(self, tmdb_url: str):
        tmdb_response = await self._session.get(
            tmdb_url
        )

        html = await tmdb_response.read()

        soup = BeautifulSoup(html, 'html.parser')
        section = soup.find('div', {'class': 'ott_provider'})
        print(section)
        if section is None:
            return []
        print(section.find_all('a', {'class': lambda x: str.startswith(x, 'Watch')}))
        return []
