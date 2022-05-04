import requests
import concurrent.futures
import time
import json
from bs4 import BeautifulSoup

class Data():
    def __init__(self):
        with open("tickers.json") as f:
            tickers_name = json.load(f)
        print(len(tickers_name))
        self.symbols = [elem['Symbol'] for elem in tickers_name]
        self.map = {}

        print("Started downloading data...")
        start = time.time()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            self.tickers = list(executor.map(Ticker, self.symbols))
        for ticker in self.tickers:
            self.map[ticker.name] = ticker
        print(time.time() - start)
    
    def popular(self, n=5):
        self.tickers.sort(key=lambda x: int(x.volume.replace(',', '')), reverse=True)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(self.func, [ticker.update for ticker in self.tickers[:n]])
        return self.tickers[:n]
    
    def gainers(self, n=5):
        self.tickers.sort(key=lambda x: float(x.regular_market_change_percent[:-1]), reverse=True)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(self.func, [ticker.update for ticker in self.tickers[:n]])
        return self.tickers[:n]
    
    def losers(self, n=5):
        self.tickers.sort(key=lambda x: float(x.regular_market_change_percent[:-1]), reverse=False)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(self.func, [ticker.update for ticker in self.tickers[:n]])
        return self.tickers[:n]

    def get_ticker(self, symbol):
        self.map[symbol].update()
        return self.map[symbol]

    def get_many_tickers(self, symbols):
        res = [self.map[symbol] for symbol in symbols]
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(self.func, [ticker.update for ticker in res])
        return res
    
    def func(self, update_func):
        update_func()
        

class Ticker():
    def __init__(self, name):
        self.name = name
        self.regular_market_price = 0
        self.regular_market_change = "0.00"
        self.regular_market_change_percent = "0.00%"
        self.open = "0.00"
        self.previous_close = "0.00"
        self.range = ["0.00", "0.00"]
        self.volume = "0"
        self.market_cap = "0"
        
        self.update()

    def update(self, n=0):
        print(f"Updating {self.name}...")
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"
        }
        r = requests.get(f"https://finance.yahoo.com/quote/{self.name}", headers=headers)
        soup = BeautifulSoup(r.content, 'html.parser')
        if not r.ok:
            return
        try:
            price = soup.find("fin-streamer", {"data-field": "regularMarketPrice", "data-symbol": self.name}).text
            try:
                self.regular_market_price = float(price.replace(',', ''))
            except ValueError:
                self.regular_market_price = 0
            self.regular_market_change = soup.find("fin-streamer", {"data-field": "regularMarketChange", "data-symbol": self.name}).text
            self.regular_market_change_percent = soup.find("fin-streamer", {"data-field": "regularMarketChangePercent", "data-symbol": self.name}).text[1:-1]
            self.previous_close = soup.find("td", {"data-test": "PREV_CLOSE-value"}).text
            self.range = soup.find("td", {"data-test": "DAYS_RANGE-value"}).text.split(" - ")
            self.volume = soup.find("fin-streamer", {"data-field": "regularMarketVolume"}).text
            self.market_cap = soup.find("td", {"data-test": "MARKET_CAP-value"}).text
            self.open = soup.find("td", {"data-test": "OPEN-value"}).text
        except AttributeError:
            print('!!!!!!!!!!!', self.name)

if __name__ == "__main__":
    # ticker = Ticker("TECH")
    data = Data()