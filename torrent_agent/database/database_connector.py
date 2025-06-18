import asyncio
from mysql.connector import pooling, Error
from threading import Lock
from torrent_agent.common.configuration import Configuration  # Import the Configuration class

class DatabaseConnector:
    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DatabaseConnector, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            config = Configuration()
            db_config = config.get_database_config()

            # Use configuration values
            self.host = db_config["host"]
            self.user = db_config["user"]
            self.password = db_config["password"]
            self.database = db_config["name"]
            self.pool_size = 5

            self.connection_pool = pooling.MySQLConnectionPool(
                pool_name="mypool",
                pool_size=self.pool_size,
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
            )
            self._initialized = True

    async def query(self, sql, retry_count=0):
        loop = asyncio.get_event_loop()
        try:
            def execute_query():
                conn = self.connection_pool.get_connection()
                try:
                    with conn.cursor() as mycursor:
                        mycursor.execute(sql)
                        return mycursor.fetchall()
                finally:
                    conn.close()

            return await loop.run_in_executor(None, execute_query)
        except Error as e:
            retry_count += 1
            if retry_count < 3:
                return await self.query(sql, retry_count)
            raise e

    async def insert(self, sql, params=None, retry_count=0):
        loop = asyncio.get_event_loop()
        try:
            def execute_query():
                conn = self.connection_pool.get_connection()
                try:
                    with conn.cursor() as mycursor:
                        if params:
                            mycursor.execute(sql, params)
                        else:
                            mycursor.execute(sql)
                        conn.commit()
                        return mycursor.lastrowid
                finally:
                    conn.close()

            return await loop.run_in_executor(None, execute_query)
        except Error as e:
            retry_count += 1
            if retry_count < 3:
                return await self.insert(sql, params, retry_count)
            raise e
        
    async def fetch_one(self, table, id, retry_count=0):
        loop = asyncio.get_event_loop()
        try:
            def execute_query():
                conn = self.connection_pool.get_connection()
                try:
                    with conn.cursor() as mycursor:
                        sql = f"SELECT * FROM {table} WHERE id = %s"
                        mycursor.execute(sql, (id,))
                        return mycursor.fetchone()
                finally:
                    conn.close()

            return await loop.run_in_executor(None, execute_query)
        except Error as e:
            retry_count += 1
            if retry_count < 3:
                return await self.fetch_one(table, id, retry_count)
            raise e

    async def delete(self, table, id, retry_count=0):
        loop = asyncio.get_event_loop()
        try:
            def execute_query():
                conn = self.connection_pool.get_connection()
                try:
                    with conn.cursor() as mycursor:
                        sql = f"DELETE FROM {table} WHERE id = %s"
                        mycursor.execute(sql, (id,))
                        conn.commit()
                finally:
                    conn.close()

            await loop.run_in_executor(None, execute_query)
        except Error as e:
            retry_count += 1
            if retry_count < 3:
                return await self.delete(table, id, retry_count)
            raise e

    async def fetch_all(self, table, page, page_size=10, retry_count=0):
        loop = asyncio.get_event_loop()
        try:
            def execute_query():
                conn = self.connection_pool.get_connection()
                try:
                    with conn.cursor() as mycursor:
                        offset = (page - 1) * page_size
                        sql = f"SELECT * FROM {table} LIMIT %s OFFSET %s"
                        mycursor.execute(sql, (page_size, offset))
                        return mycursor.fetchall()
                finally:
                    conn.close()

            return await loop.run_in_executor(None, execute_query)
        except Error as e:
            retry_count += 1
            if retry_count < 3:
                return await self.fetch_all(table, page, page_size, retry_count)
            raise e