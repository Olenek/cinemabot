import os
import sqlite3
from datetime import datetime
from typing import Tuple, List

from src.utils import SearchData


class Scribe:
    def __init__(self, db_filename: str):
        if os.path.exists(db_filename):
            self.connection = sqlite3.connect(db_filename)

        self.connection = sqlite3.connect(db_filename)
        self.connection.execute(
            """
            create table queries (
                query_id integer auto_increment primary_key,
                chat_id integer,
                query_dttm datetime,
                query_txt varchar(256),
                movie_id integer
            )
            """
        )

        self.connection.execute(
            """
            create table movies (
                movie_id integer primary_key,
                movie_nm varchar(256)
            )
            """
        )

    async def record_query(self, data: SearchData) -> None:
        self.connection.execute(
            """
            insert into queries (chat_id, query_dttm, query_txt, movie_id) 
            values (?, ?, ?, ?)
            """, (data.chat_id, datetime.now(), data.query, data.movie_id)
        )

        self.connection.execute(
            """
            insert into movies (movie_id, movie_nm)
            values (?, ?)
            """, (data.movie_id, data.movie_nm)
        )

        self.connection.commit()

    async def get_last_n(self, chat_id: int, n: int) -> List[Tuple[str, str, datetime]]:
        return self.connection.execute(
            """
            select q.query_dttm, q.query_txt, q.movie_nm from queries q
            inner join movies m
            on m.movie_id = q.movie_id
            and chat_id == ?
            """, (chat_id,)
        ).fetchmany(n)

    async def get_stats(self, chat_id: int) -> List[Tuple[str, str, datetime]]:
        return self.connection.execute(
            """
            select m.movie_nm, count(*) from queries q
            inner join movies m
            on m.movie_id = q.movie_id
            and chat_id == ?
            """, (chat_id,)
        ).fetchmany(5)