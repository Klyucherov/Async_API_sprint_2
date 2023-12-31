from dataclasses import asdict
from functools import lru_cache
from typing import List, Optional

from api.v1.models.api_query_params_model import (FilmListSearch,
                                                  SearchQueryParams)
from db.db_data_getter import DBDataGetter
from db.elastic import get_elastic
from db.redis import get_redis
from db.storage import BaseStorage
from services.base_service import BaseDataService

from fastapi import Depends


class FilmService(BaseDataService):
    """
    Класс позволяет взаимодействовать с ElasticSearch и Redis для поиска информации по фильму, включая четкий и
    нечеткий (полнотекстовый) поиск.
    """

    def __init__(self, cache_storage: BaseStorage, search_engine: DBDataGetter):
        super().__init__(search_engine, cache_storage)
        self.index_name = 'movies'

    async def get_list_films(self, query: FilmListSearch) -> Optional[List[dict]]:
        """
        Метод возвращает все фильмы по параметрам и фильтрации
        :param query: номер страницы
        :return: list[Film]
        """

        body = dict()

        if query.genre_id:
            body["query"] = {
                "nested": {
                    "path": "genres",
                    "query": {
                        "bool": {
                            "must": [{
                                "term": {
                                    "genres.id": {
                                        "value": query.genre_id
                                    }
                                }
                            }]
                        }
                    }
                }
            }

        query.page = await self._validation_page(query.page, query.size, body)

        body["from"] = (query.page - 1) * query.size
        body["size"] = query.size
        body["sort"] = [{"imdb_rating": {"order": query.sort_imdb}}]

        return await self.get_list_of_items(api_query_params=asdict(query), elastic_query=body)

    async def search_films(self, query: SearchQueryParams) -> Optional[List[dict]]:
        """
        Полнотекстовый поиск по query
        :param query: запрос
        :return: list[Film]
        """
        body = {
            "query": {
                "function_score": {
                    "query": {
                        "multi_match": {
                            "query": query.query,
                            "fields": [
                                "title^2",
                                "description"
                            ],
                            "fuzziness": "AUTO"
                        }
                    }
                }
            }
        }

        query.page = await self._validation_page(query.page, query.size, body)

        body["from"] = (query.page - 1) * query.size
        body["size"] = query.size

        return await self.get_list_of_items(api_query_params=asdict(query), elastic_query=body)


@lru_cache()
def get_film_service(cache_storage: BaseStorage = Depends(get_redis),
                     search_engine: DBDataGetter = Depends(get_elastic), ) -> FilmService:
    return FilmService(cache_storage, search_engine)
