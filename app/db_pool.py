import psycopg2
from psycopg2 import pool

class DBPool:
    def __init__(self, config):
        self.threaded_connection_pool = None
        self.config = config
    
    def connect(self):
        try:
            self.threaded_connection_pool = psycopg2.pool.ThreadedConnectionPool(1,90,
                host = self.config["host"],
                dbname = self.config["dbname"], 
                port = self.config["port"],
                user = self.config["user"],
                password = self.config["password"]
                )
        except (Exception, psycopg2.DatabaseError) as error:
            print ("Error while connecting to PostgreSQL", error)
        
    def get_conn(self):
        if not self.threaded_connection_pool:
            self.connect()
        return self.threaded_connection_pool.getconn()
    
    def put_conn(self, conn):
        if self.threaded_connection_pool:
            self.threaded_connection_pool.putconn(conn)