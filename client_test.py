import json
import asyncio
import websockets


async def send_message():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        # 向服务器发送消息
        await websocket.send(json.dumps({"type":"login","username": "test","password":"test"}))
        print("id sent to server.")
        # 接收服务器返回的消息
        data=await websocket.recv()
        print(data)
        await websocket.send(json.dumps({"type": "test"}))
        data = await websocket.recv()
        print(data)
        await websocket.send(json.dumps({"type": "test"}))
        data = await websocket.recv()
        print(data)
        await websocket.send(json.dumps({"type": "test"}))
        data = await websocket.recv()
        print(data)
        await websocket.send(json.dumps({"type": "logout"}))
        data = await websocket.recv()
        print(data)
        await websocket.send(json.dumps({"type": "test"}))
        data = await websocket.recv()
        print(data)
        await websocket.send(json.dumps({"type": "login", "username": "test", "password": "test"}))
        print("id sent to server.")
        data = await websocket.recv()
        print(data)

# 启动事件循环
asyncio.run(send_message())
