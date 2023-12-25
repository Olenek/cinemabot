from typing import List, Tuple, Dict, Iterable, Any
from aiohttp import ClientSession
from bs4 import BeautifulSoup


# user_agents = [
#     'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36 OPR/72.0.3815.465 (Edition Yx GX)',
#     'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
#     'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
#     'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15',
#     'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36',
#     'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15',
#     'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36 Edg/87.0.664.75',
#     'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.3 Safari/605.1.15',
#     'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59',
# ]
locales = {
    'RU': {
        'pattern': '{} смотреть на {}'
    },
    'US': {
        'pattern': '{} watch on {}'
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
        self._google_search_url = 'https://www.google.com/search'

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
            json = await response.json()
            for translation in await json['translations']:
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

    async def _construct_offers(self, movie_id: int, movie_nm: str, loc_options: Dict[str, Dict[Any, Any]]) -> Dict[str, str | None]:
        translations = await self._get_translated_titles(movie_id, movie_nm)
        offers: Dict[str, str | None] = {}
        for locale_nm, option in loc_options.items():
            offers[locale_nm] = await self._construct_loc_offer(locale_nm, option, translations)
        return offers

    async def _try_provider(self, movie_nm: str, provider_nm: str, locale: str) -> str | None:
        query = locales[locale].format(movie_nm, provider_nm)
        async with self._session.get(
                url=self._google_search_url, params={'q': query},
        ) as response:
            response_text = await response.text()
            soup = BeautifulSoup(response_text, 'html.parser')
            first_link = soup.find(id='search').find('a')
            if first_link.get('href', None) is not None:
                return first_link['href']
            return None
