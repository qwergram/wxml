# Xayah Websocket Mixin

import asyncio
import websockets
import json

class XayahWebsocket:

    wss_port = 3001

    # In javascript, connect via: new WebSocket("ws://127.0.0.1:3001"); 
    def create_websocket(self):
        self._websocket = websockets.serve(self.send_move, '127.0.0.1', self.wss_port)
        asyncio.get_event_loop().run_until_complete(self._websocket)
        asyncio.get_event_loop().run_forever()

    @asyncio.coroutine
    def send_move(self, websocket, path):
        yield from websocket.send(json.dumps({
            "1": 3,
            "3": 1,
        }))
        print("> Update sent")

    @asyncio.coroutine
    def hello(self, websocket, path):
        name = yield from websocket.recv()
        print("< {}".format(name))
        greeting = "Hello {}!".format(name)
        yield from websocket.send(greeting)
        print("> {}".format(greeting))


if __name__ == "__main__":
    x = XayahWebsocket()
    x.create_websocket()