import requests
from pprint import PrettyPrinter
pp = PrettyPrinter(indent=1)
import json


class Telegram():
    def __init__(self, token, update_func):
        self.token = token
        self.update_func = update_func
    
    def update(self):
        with open('update_id.txt') as f:
            update_id = f.readline()
        data = {
            'offset': update_id,
            'timeout': 1
        }

        r = requests.get(f"https://api.telegram.org/bot{self.token}/getUpdates", data=data)
        if not r.ok:
            return
        response = r.json()
        for event in response['result']:
            open('update_id.txt', 'w').write(str(event['update_id'] + 1))
            self.update_func(event)

    def send(self, id, text, reply=0, reply_markup=False, parse_mode=False):
        data = {}
        data['chat_id'] = id
        data['text'] = text
        if reply:
            data['reply_to_message_id'] = reply
        if reply_markup:
            data['reply_markup'] = json.dumps(reply_markup)
        if parse_mode:
            data['parse_mode'] = "MarkdownV2"
            text = text.replace('.', '\\.')
            text = text.replace('+', '\\+')
            text = text.replace('(', '\\(')
            text = text.replace(')', '\\)')
            text = text.replace('-', '\\-')
            print(text)
            data['text'] = text

        r = requests.get(f"https://api.telegram.org/bot{self.token}/sendMessage", data=data)
        pp.pprint(r.json())


if __name__ == '__main__':
    token = "5212004253:AAG-6DKE4KBkR9ZqmD77WthnQGq4tYnSz1M"
    tg = Telegram(token=token, update_func=print)
    id = 417678664
    text = """
*bold \*text*
_italic \*text_
__underline__
~strikethrough~
||spoiler||
*bold _italic bold ~italic bold strikethrough ||italic bold strikethrough spoiler||~ __underline italic bold___ bold*
[inline URL](http://www.example.com/)
[inline mention of a user](tg://user?id=123456789)
`inline fixed-width code`
```
pre-formatted fixed-width code block
```
```python
pre-formatted fixed-width code block written in the Python programming language
```
    """
    button = {"text": "AAPL", "callback_data": "1"}
    # button = {"text": "AAPL"}
    keyboard = [
        [button, button, button, button],
        [button, button, button, button],
        [button, button, button, button],
        [button, button, button, button],
        [button, button, button, button],
    ]
    keyboard = {"inline_keyboard": keyboard}
    # while True:
    #     tg.update()
    tg.send(id, text, reply_markup=keyboard, parse_mode=True)