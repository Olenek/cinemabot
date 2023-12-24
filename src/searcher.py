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
        self._justwatch_url = 'https://apis.justwatch.com/content'
        self._session = None

    async def begin_session(self):
        self._session: ClientSession = ClientSession()

    async def search_tmdb(self, query: str) -> List[Tuple[int, str, str]]:
        tmdb_response = await self._session.get(self._tmdb_search_url,
                                                params={'query': query, 'api_key': self._tmdb_token},
                                                # headers=self._tmdb_header
                                                )
        response_data = (await tmdb_response.json())['results']

        if response_data:
            return [(item['id'], item['title'], item['release_date'][:4]) for item in response_data[:3]]
        return []

    async def search_offers(self, movie_id: int, locale_priority: Tuple):
        for locale in locale_priority:
            availability_response = await self._session.get(
                f'{self._justwatch_url}/title/movies/{movie_id}/locale/{locale}')
            offers = (await availability_response.json())['offers']
            if offers:
                return offers[:3]
        return []
