import os
import sqlite3
from datetime import datetime
from typing import Tuple, List


class Scribe:
    def __init__(self, db_filename: str):
        if os.path.exists(db_filename):
            self.connection = sqlite3.connect(db_filename)
        else:
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
                    movie_nm varchar(256),
                    UNIQUE (movie_id)
                )
                """
            )

    def record_query(self, chat_id: int, query_txt: str, movie_id: int, movie_nm: str) -> None:
        self.connection.execute(
            """
            insert into queries (chat_id, query_dttm, query_txt, movie_id) 
            values (?, ?, ?, ?)
            """, (chat_id, datetime.now(), query_txt, movie_id)
        )

        self.connection.execute(
            """
            insert or ignore into movies (movie_id, movie_nm)
            values (?, ?)
            """, (movie_id, movie_nm)
        )

        self.connection.commit()

    def get_last_n(self, chat_id: int, n: int) -> List[Tuple[str, str, datetime]]:
        return self.connection.execute(
            """
            select q.query_txt, m.movie_nm, q.query_dttm  from queries q
            inner join movies m
            on m.movie_id = q.movie_id
            and chat_id == ?
            order by q.query_dttm desc
            limit ?
            """, (chat_id, n)
        ).fetchall()

    def get_stats(self, chat_id: int) -> List[Tuple[str, str, datetime]]:
        return self.connection.execute(
            """
            select m.movie_nm, count(*) as cnt from queries q
            inner join movies m
            on m.movie_id = q.movie_id
            and chat_id == ?
            group by m.movie_nm
            order by cnt desc
            limit ?
            """, (chat_id, 5)
        ).fetchall()
