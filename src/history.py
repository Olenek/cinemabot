from typing import Tuple, List
from sqlite3 import Connection
from datetime import datetime


async def record_query(db_connection: Connection, chat_id: int, query_dttm: datetime, query_txt: str, result_txt: str) -> None:
    db_connection.execute(
        """
        insert into queries (chat_id, query_dttm, query_txt, result_txt) 
        values (?, ?, ?, ?)
        """, (chat_id, query_dttm, query_txt, result_txt)
    )
    db_connection.commit()


async def get_last_n(db_connection: Connection, chat_id: int, n: int) -> List[Tuple[str, str, datetime]]:
    return db_connection.execute(
        """
        select query_txt, result_txt, query_dttm from queries 
        where chat_id == ?
        """, (chat_id,)
    ).fetchmany(n)


async def get_stats(db_connection: Connection, chat_id: int) -> List[Tuple[str, str, datetime]]:
    return db_connection.execute(
        """
        select query_txt, result_txt, query_dttm from queries 
        where chat_id == ?
        """, (chat_id,)
    ).fetchma
