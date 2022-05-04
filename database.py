import sqlite3
import json
import time

class Database():
    def __init__(self):
        self.conn = sqlite3.connect("data.db")
        self.cursor = self.conn.cursor()
        self.id = None
    
    def create(self):
        res = self.cursor.execute(f"""
            SELECT * FROM users
            WHERE id = {self.id}
        """).fetchall()
        if len(res) > 0:
            return
        
        self.cursor.execute(f"""
            CREATE TABLE [{self.id}]
            (type BOOLEAN, ticker STRING, amount INT)
        """)
        self.cursor.execute(f"""
            INSERT INTO users
            VALUES ({self.id}, "", 10000, "menu", "", {time.time()}, "")
        """)
        self.conn.commit()
    
    def add(self, buy_or_sell, amount, ticker):
        self.cursor.execute(f"""
            INSERT INTO [{self.id}]
            VALUES ({buy_or_sell}, "{ticker}", {amount})
        """)
        self.conn.commit()
    
    def get_history(self):
        return self.cursor.execute(f"""
            SELECT * FROM [{self.id}]
        """).fetchall()
    
    def get_balance(self):
        return self.cursor.execute(f"""
            SELECT balance FROM users
            WHERE id = {self.id}
        """).fetchone()[0]
    
    def get_watchlist(self):
        return self.cursor.execute(f"""
            SELECT watchlist FROM users
            WHERE id = {self.id}
        """).fetchone()[0]
    
    def get_location(self):
        return self.cursor.execute(f"""
            SELECT location FROM users
            WHERE id = {self.id}
        """).fetchone()[0]

    def get_bought(self):
        return self.cursor.execute(f"""
            SELECT bought FROM users
            WHERE id = {self.id}
        """).fetchone()[0]

    def get_ticker(self):
        return self.cursor.execute(f"""
            SELECT ticker FROM users
            WHERE id = {self.id}
        """).fetchone()[0]

    def update_balance(self, balance):
        self.cursor.execute(f"""
            UPDATE users
            SET balance = {balance}
            WHERE id = {self.id}
        """)
        self.conn.commit()
    
    def update_watchlist(self, watchlist):
        self.cursor.execute(f"""
            UPDATE users
            SET watchlist = "{watchlist}"
            WHERE id = {self.id}
        """)
        self.conn.commit()

    def update_bought(self, bought):
        self.cursor.execute(f"""
            UPDATE users
            SET bought = "{bought}"
            WHERE id = {self.id}
        """)
        self.conn.commit()
    
    def update_location(self, location):
        self.cursor.execute(f"""
            UPDATE users
            SET location = "{location}"
            WHERE id = {self.id}
        """)
        self.conn.commit()

    def update_time(self):
        self.cursor.execute(f"""
            UPDATE users
            SET time = {time.time()}
            WHERE id = {self.id}
        """)
        self.conn.commit()

    def update_ticker(self, ticker):
        self.cursor.execute(f"""
            UPDATE users
            SET ticker = "{ticker}"
            WHERE id = {self.id}
        """)
        self.conn.commit()


if __name__ == "__main__":
    db = Database()
    db.id = "475923758"
    buy_or_sell = True
    ticker = 'AAPL'
    amount = 5
    db.create()
    #db.add(buy_or_sell, amount, ticker)
    res = db.get_history()
    print(res)
    res = db.get_balance()
    print(res)