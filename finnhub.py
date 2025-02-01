# Copied from Finnhub documentation with modification

#https://pypi.org/project/websocket_client/
import websocket
import json



def on_message(ws, message):
    # print(message)
    try:
        j = json.loads(message)
        if j["type"] == "trade":
            last_trade = j["data"][-1]
            price = last_trade["p"]
            stock = last_trade["s"]
            print(f"{stock}: {price}")
    except:
        pass

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    # ws.send('{"type":"subscribe","symbol":"^IXIC"}')
    ws.send('{"type":"subscribe","symbol":"AAPL"}')
    ws.send('{"type":"subscribe","symbol":"BINANCE:BTCUSDT"}')
    ws.send('{"type":"subscribe","symbol":"IC MARKETS:1"}')

def ws_connect():
    with open("data/finnhub_token.config") as fp:
        token = fp.read()
    token.strip()

    # websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://ws.finnhub.io?token=" + token,
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close)
    ws.on_open = on_open
    ws.run_forever()

if __name__ == "__main__":
    ws_connect()

