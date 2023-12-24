from justwatch import JustWatch
from typing import List, Tuple
from aiohttp import ClientSession


class Searcher:
    def __init__(self, tmdb_token: str):
        # self._tmdb_header = {
        #     'Accept': 'application/json',
        #     'Authorization': f'Bearer {tmdb_token}'   
        # }
        self._tmdb_token = tmdb_token

        self._tmdb_search_url = 'https://api.themoviedb.org/3/search/movie'
        self._tmdb_watch_providers_url = 'https://api.themoviedb.org/3/movie/{}/watch_providers'

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
        print(response_data)
        return []
