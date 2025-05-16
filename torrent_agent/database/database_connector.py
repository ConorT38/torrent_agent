import mysql.connector

class DatabaseConnector:
    def __init__(self):
        self.host = "192.168.0.23"
        self.user = "root"
        self.password = "raspberry"
        self.database = "homemedia"

    def query(self, sql, retry_count=0):
        try:
            with mysql.connector.connect(host=self.host, user=self.user, password=self.password, database=self.database) as conn:
                with conn.cursor() as mycursor:
                    mycursor.execute(sql)
                    return mycursor.fetchall()
        except mysql.connector.Error as e:
            retry_count += 1
            if retry_count < 3:
                return self.query(sql, retry_count)
            raise e

    def insert(self, sql, retry_count=0):
        try:
            with mysql.connector.connect(host=self.host, user=self.user, password=self.password, database=self.database) as conn:
                with conn.cursor() as mycursor:
                    mycursor.execute(sql)
                    conn.commit()
        except mysql.connector.Error as e:
            retry_count += 1
            if retry_count < 3:
                return self.insert(sql, retry_count)
            raise e