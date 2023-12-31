from http import HTTPStatus

import pytest
from orjson import orjson
from redis.asyncio import Redis

from tests.functional.settings import movies_settings
from tests.functional.testdata.film_data import (COMEDY_FILMS,
                                                 DOCUMENTARY_FILMS,
                                                 LAST_PAGE_FILMS, SORTED_FILMS,
                                                 STAR_WARS_FILM)
from tests.functional.utils.helpers import get_data


@pytest.mark.parametrize(
    'query, expected_answer',
    [
        (
                '',
                {'status': HTTPStatus.OK, 'length': 25}
        ),
        (
                '/' + STAR_WARS_FILM['id'],
                {'status': HTTPStatus.OK, 'length': 9}
        ),
    ]
)
@pytest.mark.asyncio
async def test_get_request_status(api_session, query, expected_answer):
    """
    Тест на статус длину возвращаемого объекта по запросу
    :param query:
    :param expected_answer:
    :return: {'status': ..., 'length': ...}
    """

    response = await get_data(api_session=api_session, query=query, query_params=None, settings=movies_settings)

    assert expected_answer == response.validation


@pytest.mark.parametrize(
    'query, expected_answer',
    [
        (
                "/None",
                {"detail": "film not found"}
        ),
    ]
)
@pytest.mark.asyncio
async def test_get_film_by_id(api_session, query, expected_answer):
    """
    Тест на запрос несуществующего фильма
    :param query:
    :param expected_answer:
    :return: GenreFull.as_dict
    """
    response = await get_data(api_session=api_session, query=query, query_params=None, settings=movies_settings)

    assert expected_answer == response.data


@pytest.mark.parametrize(
    'query_params, expected_answer',
    [
        (
                {
                    "page_number": 2,
                    "page_size": 10,
                    "sort_by_rating": "desc"
                }
                , SORTED_FILMS
        )
    ]
)
@pytest.mark.asyncio
async def test_get_sorted_films(api_session, query_params, expected_answer):
    """
    Тесты на получение второй страницы отсортированных фильмов при размере странице 10
    :param query_params:
    :param expected_answer:
    :return: GenreFull.as_dict
    """

    response = await get_data(api_session=api_session, query='', query_params=query_params, settings=movies_settings)

    assert expected_answer == response.data


@pytest.mark.parametrize(
    'query_params, expected_answer',
    [
        (
                {
                    "page_number": 1,
                    "page_size": 2,
                    "sort_by_rating": "desc",
                    "filter[genre]": "6d141ad2-d407-4252-bda4-95590aaf062a"
                }
                , DOCUMENTARY_FILMS
        ),
        (
                {
                    "page_number": 1,
                    "page_size": 2,
                    "sort_by_rating": "desc",
                    "filter[genre]": "5373d043-3f41-4ea8-9947-4b746c601bbd"
                }
                , COMEDY_FILMS
        )
    ]
)
@pytest.mark.asyncio
async def test_get_film_by_genre(api_session, query_params, expected_answer):
    """
    Тесты с фильтрацией фильмов по жанрам. Возвращает 2 фильма, отсортированных по рейтингу
    :param query_params:
    :param expected_answer:
    :return: GenreFull.as_dict
    """

    response = await get_data(api_session=api_session, query='', query_params=query_params, settings=movies_settings)

    assert expected_answer == response.data


@pytest.mark.parametrize(
    'query_params, expected_answer',
    [
        (
                {
                    "page_number": 41,
                    "page_size": 25,
                    "sort_by_rating": "desc"
                }
                , LAST_PAGE_FILMS
        ),
        (
                {
                    "page_number": 1000,
                    "page_size": 25,
                    "sort_by_rating": "desc"
                }
                , LAST_PAGE_FILMS
        )
    ]
)
@pytest.mark.asyncio
async def test_get_film_by_genre(api_session, query_params, expected_answer):
    """
    Тесты на валидацию последней страницы
    :param query_params:
    :param expected_answer:
    :return: GenreFull.as_dict
    """

    response = await get_data(api_session=api_session, query='', query_params=query_params, settings=movies_settings)

    assert expected_answer == response.data


@pytest.mark.parametrize(
    'query, expected_answer',
    [
        (
                '/' + STAR_WARS_FILM['id'],
                STAR_WARS_FILM
        ),
    ]
)
@pytest.mark.asyncio
async def test_cache_film(api_session, redis_client: Redis, query: str, expected_answer):
    """Тест на поиск фильма по ID + на работу кэша"""

    key = f'movies::{query.strip("/")}'

    await redis_client.delete(key)

    assert await redis_client.exists(key) == 0

    response = await get_data(api_session=api_session, query=query, query_params=None, settings=movies_settings)

    assert await redis_client.exists(key)

    data_from_cache = await redis_client.get(key)

    assert expected_answer == response.data == orjson.loads(data_from_cache)
