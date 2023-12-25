from typing import List, Tuple, Dict, Any

from aiohttp import ClientSession
from duckduckgo_search import AsyncDDGS

locales = {
    'RU': {
        'pattern': '{} смотреть на {}',
        'emoji': '🇷🇺'
    },
    'US': {
        'pattern': '{} watch on {}',
        'emoji': '🇺🇸'
    }
}


class Searcher:
    def __init__(self, tmdb_token: str):
        # self._tmdb_header = {
        #     'Accept': 'application/json',
        #     'Authorization': f'Bearer {tmdb_token}'   
        # }
        self._tmdb_token = tmdb_token

        self._tmdb_search_url = 'https://api.themoviedb.org/3/search/movie'
        self._tmdb_watch_providers_url = 'https://api.themoviedb.org/3/movie/{}/watch/providers'
        self._tmdb_translations_url = 'https://api.themoviedb.org/3/movie/{}/translations'
        self._google_search_url = 'https://duckduckgo.com'
        self._duckduckgo_search = None
        self._session = None

    async def begin_session(self):
        self._session: ClientSession = ClientSession()
        self._duckduckgo_search: AsyncDDGS = AsyncDDGS()

    async def search_tmdb(self, query: str) -> List[Tuple[int, str, str]]:
        tmdb_response = await self._session.get(self._tmdb_search_url,
                                                params={'query': query, 'api_key': self._tmdb_token},
                                                )
        response_data = (await tmdb_response.json())['results']

        if response_data:
            return [(item['id'], item['title'], item['release_date'][:4]) for item in response_data[:3]]
        return []

    async def search_offers(self, movie_id: int, movie_nm: str) -> Dict[str, str]:
        """
        Used to search for streaming offers for the movie
        :param movie_nm: name of the movie
        :param movie_id: tmdb movie id
        :return: Dict[Locale_nm, URL]
        """
        tmdb_response = await self._session.get(
            self._tmdb_watch_providers_url.format(movie_id),
            params={'api_key': self._tmdb_token},
        )
        response_data = await tmdb_response.json()
        providers = response_data['results']
        options = {locale_nm: providers.get(locale_nm, {}) for locale_nm in locales.keys()}
        return await self._construct_offers(movie_id, movie_nm, options)

    async def _get_translated_titles(self, movie_id: int, movie_nm: str):
        translations: Dict[str, str] = {}
        async with self._session.get(
                url=self._tmdb_translations_url.format(movie_id), params={'api_key': self._tmdb_token},
        ) as response:
            response_data = await response.json()
            for translation in response_data['translations']:
                if translation['iso_3166_1'] in locales.keys():
                    if translation['data']['title'] != '':
                        translations[translation['iso_3166_1']] = translation['data']['title']

        for locale_nm in locales.keys():
            if locale_nm not in translations.keys():
                translations[locale_nm] = movie_nm

        return translations

    async def _construct_loc_offer(self, locale_nm: str,
                                   options: Dict[str, Any],
                                   translations: Dict[str, str]) -> str | None:
        watch_variants = ['flatrate', 'rent', 'buy']
        for variant in watch_variants:
            for provider_offer in options[variant]:
                result = await self._try_provider(translations[locale_nm], provider_offer['provider_name'], locale_nm)
                if result is not None:
                    return result
        return None

    async def _construct_offers(self, movie_id: int, movie_nm: str, loc_options: Dict[str, Dict[Any, Any]]) -> Dict[
        str, str | None]:
        translations = await self._get_translated_titles(movie_id, movie_nm)
        offers: Dict[str, str | None] = {}
        for locale_nm, option in loc_options.items():
            offers[locale_nm] = await self._construct_loc_offer(locale_nm, option, translations)
        print(offers)
        return offers

    async def _try_provider(self, movie_nm: str, provider_nm: str, locale: str) -> str | None:
        query = locales[locale]['pattern'].format(movie_nm, provider_nm)
        results = [r async for r in self._duckduckgo_search.text(query, max_results=3)]
        for result in results:
            if provider_nm.lower().replace(' ', '') in result['href']:
                return result['href']
        return None
