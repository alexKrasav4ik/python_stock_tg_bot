import requests
import time
import concurrent.futures
import sqlite3
import json
from bs4 import BeautifulSoup
from pprint import PrettyPrinter
pp = PrettyPrinter(indent=1)

from getdata import Data, Ticker
from database import Database
from telegram import Telegram

token = "5302332695:AAEsA62KVI1nYwF6SVM6j1cOgkdh2bBH23o"
menu = {'keyboard': [[{'text': 'Gainers'}, {'text': 'Losers'}, {'text': 'Popular'}], [{'text': 'Watchlist'}, {'text': 'My stocks'}], [{'text': 'History of transactions'}, {"text": "Menu"}]]}


def send_to_menu(id, name, pretext=""):
    global db, tg, data
    balance = db.get_balance()
    text = f"Hello, {name}. Your balance is ${balance}.\nSend stock ticker to get up-to-date information about it, or use keyboards to navigate"
    tg.send(id, pretext + "\n\n" + text, reply_markup=menu)

def get_stocks_info(tickers):
    text = ""
    buttons = []
    for ticker in tickers:
        row = f"*{ticker.name}*:   {ticker.regular_market_price}   _{ticker.regular_market_change} ({ticker.regular_market_change_percent})_\n"
        text += row
        button = {
            "text": ticker.name,
            "callback_data": ticker.name
        }
        buttons.append(button)
    keyboard = []
    for i in range(0, len(buttons), 5):
        keyboard.append(buttons[i:min(len(buttons), i+5)])
    return (text, {"inline_keyboard": keyboard})
    
def get_particular_stock_info(symbol):
    ticker = data.get_ticker(symbol)
    text = f"""
*{ticker.name}*:   {ticker.regular_market_price}   _{ticker.regular_market_change} ({ticker.regular_market_change_percent})_
Open:   __{ticker.open}__
Close:   __{ticker.previous_close}__
Day's range:   __{ticker.range[0]} - {ticker.range[1]}__
Volume:   __{ticker.volume}__
Market Cap:   __{ticker.market_cap}__
"""
    keyboard = {"inline_keyboard":[[{"text": "Source", "url": f"https://finance.yahoo.com/quote/{ticker.name}"}]]}
    watchlist = db.get_watchlist().split(',')
    if symbol in watchlist:
        keyboard["inline_keyboard"].append([{"text": "Delete from watchlist", "callback_data": "del"}])
    else:
        keyboard["inline_keyboard"].append([{"text": "Add to watchlist", "callback_data": "add"}])
    bought = [elem.split(':')[0] for elem in db.get_bought().split(',')]
    keyboard["inline_keyboard"].append([{"text": f"Buy", "callback_data": "buy"}, {"text": f"Sell", "callback_data": "sell"}])
    
    pp.pprint(keyboard)
    return (text, keyboard)

def new_event(event):
    global tg, data, db
    if 'message' in event:
        message = event['message']['text']
        id = event['message']['chat']['id']
        name = event['message']['from']['first_name']
    elif 'callback_query' in event:
        message = event['callback_query']['data']
        id = event['callback_query']['from']['id']
        name = event['callback_query']['from']['first_name']
    else:
        return
    
    db.id = id
    db.create()
    db.update_time()
    location = db.get_location()
    
    if message == 'Menu':
        db.update_location("menu")
        send_to_menu(id, name)

    elif message == 'Gainers':
        db.update_location("gainers")
        pretext = "*Today's gainers:*\n\n"
        text, keyboard = get_stocks_info(data.gainers(10))
        tg.send(id, pretext + text, reply_markup=keyboard, parse_mode=True)

    elif message == 'Losers':
        db.update_location("losers")
        pretext = "*Today's losers:*\n\n"
        text, keyboard = get_stocks_info(data.losers(10))
        tg.send(id, pretext + text, reply_markup=keyboard, parse_mode=True)

    elif message == 'Popular':
        db.update_location("popular")
        pretext = "*Today's popular stocks:*\n\n"
        text, keyboard = get_stocks_info(data.popular(10))
        tg.send(id, pretext + text, reply_markup=keyboard, parse_mode=True)

    elif message == 'Watchlist':
        db.update_location("watchlist")
        symbols = db.get_watchlist()
        if not symbols:
            text = "Seems like you haven't added any stocks to your watchlist yet.\nOpen some stock info to change that."
            send_to_menu(id, name, text)
        else:
            symbols = symbols.split(',')
            pretext = "*Your watchlist:*\n\n"
            text, keyboard = get_stocks_info(data.get_many_tickers(symbols))
            tg.send(id, pretext + text, reply_markup=keyboard, parse_mode=True)

    elif message == "My stocks":
        db.update_location("bought")
        bought = db.get_bought()
        if not bought:
            text = "Seems like you haven't bought any stocks yet.\nOpen some stock info to change that."
            send_to_menu(id, name, text)
        else:
            symbols = [elem.split(':')[0] for elem in bought.split(',')]
            # print(symbols, bought)
            slov = {}
            for elem in bought.split(","):
                slov[elem.split(":")[0]] = int(elem.split(":")[1])
                # print(elem.split(":")[0], elem.split(":")[1])
            pretext = "*Your stocks:*\n\n"
            text, keyboard = get_stocks_info(data.get_many_tickers(symbols))
            rows = text.split("\n")
            new_rows = []
            for row in rows:
                if row == '':
                    continue
                name, other = row.split(":")
                new_row = f"__({slov[name[1:-1]]})__   " + name + ":" + other
                new_rows.append(new_row)
            text = '\n'.join(new_rows)

            tg.send(id, pretext + text, reply_markup=keyboard, parse_mode=True)

    elif message == "History of transactions":
        db.update_location("history")
        history = db.get_history()
        text = ""
        if len(history) == 0:
            text = "You don't have any transactions yet. Buy something first."
            send_to_menu(id, name, text)
        else:
            text = "*Your history of transactions:*\n\n"
            for event in reversed(history):
                if event[0]:
                    text += "*Buy*: "
                else:
                    text += "*Sell*: "
                text += f"{event[1]} {event[2]}\n"
            tg.send(id, text, parse_mode=True)

    elif location == "buy":
        if not message.isdigit():
            tg.send(id, "This is not a number. Please respond with a correct number, or go to menu")
            return
        amount = int(message)
        ticker = db.get_ticker()
        balance = db.get_balance()
        bought = {}
        for elem in db.get_bought().split(','):
            if elem == '':
                continue
            t, a = elem.split(':')
            bought[t] = int(a)
        price = data.map[ticker].regular_market_price
        if price * amount > balance:
            tg.send(id, f"That's would cost you ${price*amount-balance} more than you have (${balance}). Please send correct amount or get back to menu")
            return
        balance -= price * amount
        if ticker not in bought:
            bought[ticker] = 0
        bought[ticker] += amount
        pp.pprint(bought)

        print([str(elem[0])+":"+str(elem[1]) for elem in bought.items()])
        pack_up_bought = ','.join([str(elem[0])+":"+str(elem[1]) for elem in bought.items()])
        print(pack_up_bought)
        db.update_bought(pack_up_bought)
        db.update_balance(balance)
        db.add(True, amount, ticker)

        db.update_location("menu")
        tg.send(id, f"Success! Now you own {bought[ticker]} shares of ${ticker} for a price of ${price * bought[ticker]}")
        
    elif location == "sell":
        if not message.isdigit():
            tg.send(id, "This is not a number. Please respond with a correct number or go to menu")
            return
        amount = int(message)
        ticker = db.get_ticker()
        balance = db.get_balance()
        bought = {}
        for elem in db.get_bought().split(','):
            if elem == '':
                continue
            t, a = elem.split(':')
            bought[t] = int(a)
        price = data.map[ticker].regular_market_price
        if ticker not in bought:
            tg.send(id, f"You don't own any of those stocks yet")
            db.update_location("menu")
            return
        if amount > bought[ticker]:
            tg.send(id, f"You only own {bought[ticker]} shares of this stock. Please send correct amount or get back to menu")
            return
        balance += price * amount
        bought[ticker] -= amount
        if bought[ticker] == 0:
            del bought[ticker]
        
        pack_up_bought = ','.join([str(elem[0])+":"+str(elem[1]) for elem in bought.items()])
        print(pack_up_bought)
        db.update_bought(pack_up_bought)
        db.update_balance(balance)
        db.add(False, amount, ticker)

        db.update_location("menu")
        tg.send(id, f"Success! {amount} shares of {ticker} for a price of ${price * amount}")
    
    elif any([message.lower() == sym.lower() for sym in data.symbols]):
        db.update_location("particular stock")
        db.update_ticker(message.upper())
        text, keyboard = get_particular_stock_info(message.upper())
        tg.send(id, text, reply_markup=keyboard, parse_mode=True)
        
    elif location == "particular stock":
        if message == "buy":
            db.update_location("buy")
            ticker = db.get_ticker()
            tg.send(id, f"Ok, you want to buy {ticker}. How much?")

        elif message == "sell":
            db.update_location("sell")
            ticker = db.get_ticker()
            tg.send(id, f"Ok, you want to sell {ticker}. How much?")

        elif message == "add":
            watchlist = db.get_watchlist().split(',')
            if watchlist == ['']:
                watchlist = []
            ticker = db.get_ticker()
            if ticker in watchlist:
                tg.send(id, "You already have it in watchlist, fool")
                return
            watchlist.append(ticker)
            db.update_watchlist(','.join(watchlist))
            db.update_location("menu")

            tg.send(id, f"Done, {ticker} in watchlist")

        elif message == "del":
            watchlist = db.get_watchlist().split(',')
            ticker = db.get_ticker()
            if ticker not in watchlist:
                tg.send(id, "You already don't have it in watchlist, fool")
                return
            new_watchlist = []
            for elem in watchlist:
                if elem != ticker:
                    new_watchlist.append(elem)
            db.update_watchlist(','.join(new_watchlist))
            db.update_location("menu")

            tg.send(id, f"Done, {ticker} now isn't in watchlist")
        else:
            send_to_menu(id, name, "Sorry, unknown command.\nSend stock ticker to get up-to-date information about it, or use keyboard to navigate")
            db.update_location("menu")
    
    else:
        send_to_menu(id, name, "Sorry, unknown command.\nSend stock ticker to get up-to-date information about it, or use keyboard to navigate")
        db.update_location("menu")


if __name__ == '__main__':
    db = Database()
    tg = Telegram(token, new_event)
    data = Data()
    print("Bot is ready!")
    while True:
        tg.update()