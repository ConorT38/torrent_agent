import asyncio

import mysql.connector

class DatabaseConnector:
    def __init__(self):
        self.host = "192.168.0.23"
        self.user = "root"
        self.password = "raspberry"
        self.database = "homemedia"

    async def query(self, sql, retry_count=0):
        loop = asyncio.get_event_loop()
        try:
            def execute_query():
                with mysql.connector.connect(host=self.host, user=self.user, password=self.password, database=self.database) as conn:
                    with conn.cursor() as mycursor:
                        mycursor.execute(sql)
                        return mycursor.fetchall()
            return await loop.run_in_executor(None, execute_query)
        except mysql.connector.Error as e:
            retry_count += 1
            if retry_count < 3:
                return await self.query(sql, retry_count)
            raise e

    async def insert(self, sql, retry_count=0):
        loop = asyncio.get_event_loop()
        try:
            def execute_query():
                with mysql.connector.connect(host=self.host, user=self.user, password=self.password, database=self.database) as conn:
                    with conn.cursor() as mycursor:
                        mycursor.execute(sql)
                        conn.commit()
            await loop.run_in_executor(None, execute_query)
        except mysql.connector.Error as e:
            retry_count += 1
            if retry_count < 3:
                return await self.insert(sql, retry_count)
            raise e