from typing import List, Tuple, Dict, Any

from aiohttp import ClientSession
from duckduckgo_search import AsyncDDGS

locales = {
    'RU': {
        'pattern': '{} смотреть на {}',
        'title_pattern': 'смотреть',
        'emoji': '🇷🇺',
        'region': 'ru-ru',
        'providers': {
            'youtube', 'ivi',
            'premier', 'okko',
            'amediateka', 'apple',
            'filmbox', 'kion',
            'start', 'viju',
            'wink',
        }
    },
    'US': {
        'pattern': '{} watch on {}',
        'title_pattern': 'watch',
        'emoji': '🇺🇸',
        'region': 'us-en',
        'providers': {
            'netflix', 'primevideo',
            'disneyplus', 'apple',
            'hulu', 'crunchyroll', 'hbomax',
            'max', 'peacocktv',
            'youtube', 'vudu'
        }
    },
    'JP': {
        'pattern': '{} {} de miru',
        'title_pattern': '',
        'emoji': '🇯🇵',
        'region': 'jp-jp',
        'providers': {
            'netflix', 'primevideo',
            'disneyplus', 'apple',
            'hulu', 'crunchyroll', 'hbomax',
            'max', 'peacocktv',
            'youtube', 'vudu'
        }
    }
}

providers = [
    'Netflix', 'Amazon Prime Video',
    'Disney Plus', 'Apple TV Plus',
    'Apple TV', 'Hulu',
    'Crunchyroll', 'HBO Max',
    'Peacock', 'Peacock Premium',
    'Youtube', 'Google Play Movies',
    'Amazon Video',
]


def _check_search_result(result: Dict[str, Any], loc_dict: Dict[str, str], provider_nm: str) \
        -> str | None:
    superdom, subdom = result['href'].split('.')[:2]
    if superdom in loc_dict['providers'] or subdom in loc_dict['providers']:
        if loc_dict['title_pattern'] in result['title'].lower():
            print(provider_nm)
            return result['href']
    return None


class Searcher:
    def __init__(self, tmdb_token: str):
        self._tmdb_token = tmdb_token

        self._tmdb_search_url = 'https://api.themoviedb.org/3/search/movie'
        self._tmdb_watch_providers_url = 'https://api.themoviedb.org/3/movie/{}/watch/providers'
        self._tmdb_translations_url = 'https://api.themoviedb.org/3/movie/{}/translations'
        self._tmdb_movies_url = 'https://api.themoviedb.org/3/movie/{}'
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

    async def get_name_year(self, movie_id: int) -> Tuple[str, str]:
        tmdb_response = await self._session.get(
            self._tmdb_movies_url.format(movie_id),
            params={'api_key': self._tmdb_token},
        )
        response_data = await tmdb_response.json()
        return response_data['original_title'], response_data['release_date'][:4]

    async def search_offers(self, movie_id: int) -> Dict[str, str]:
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
        name, year = await self.get_name_year(movie_id)
        return await self._construct_offers(movie_id, name, year, options)

    async def _get_translated_titles(self, movie_id: int, movie_nm: str, year: str):
        translations: Dict[str, str] = {}
        async with self._session.get(
                url=self._tmdb_translations_url.format(movie_id), params={'api_key': self._tmdb_token},
        ) as response:
            response_data = await response.json()
            for translation in response_data['translations']:
                if translation['iso_3166_1'] in locales.keys():
                    if translation['data']['title'] != '':
                        translations[translation['iso_3166_1']] = f"{translation['data']['title']} {year}"

        for locale_nm in locales.keys():
            if locale_nm not in translations.keys():
                translations[locale_nm] = f"{movie_nm} {year}"

        return translations

    async def _construct_loc_offer(self, locale_nm: str,
                                   options: Dict[str, Any],
                                   translations: Dict[str, str]) -> str | None:
        watch_variants = [
            'free',
            'flatrate',
            'rent',
            'buy',
        ]
        for variant in watch_variants:
            if variant in options.keys():
                for provider_offer in options[variant]:
                    if provider_offer['provider_name'] in locales[locale_nm]['providers']:
                        result = await self._try_provider(translations[locale_nm], provider_offer['provider_name'],
                                                          locale_nm)
                        if result is not None:
                            return result
        return None

    async def _construct_offers(self, movie_id: int, movie_nm: str, year: str,
                                loc_options: Dict[str, Dict[Any, Any]]) -> Dict[str, str]:
        translations = await self._get_translated_titles(movie_id, movie_nm, year)
        print(movie_nm)
        print(translations)
        offers: Dict[str, str] = {}
        for locale_nm, option in loc_options.items():
            offer = await self._construct_loc_offer(locale_nm, option, translations)
            if offer is not None:
                offers[locale_nm] = offer

        return offers

    async def _try_provider(self, movie_str: str, provider_nm: str, locale_nm: str) -> str | None:
        locale = locales[locale_nm]
        query = locale['pattern'].format(movie_str, provider_nm)
        results = [r async for r in self._duckduckgo_search.text(query, region=locale['region'], max_results=5)]
        for result in results:
            url = _check_search_result(result, locale, provider_nm)
            if url is not None:
                return url
        return None
