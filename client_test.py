import json
import asyncio
import websockets


async def send_message():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        # 向服务器发送消息
        await websocket.send(json.dumps({"username": "test","password":"test"}))
        print("id sent to server.")
        # 接收服务器返回的消息
        data=await websocket.recv()
        print(data)
        response = json.loads(data)
        print(response)
        print(f"Received from server:" + response["state"])
        await websocket.send(json.dumps({"type": "test"}))
        data = await websocket.recv()
        print(data)
        response = json.loads(data)
        print(response)
        print(f"Received from server:" + response["state"])



# 启动事件循环
asyncio.run(send_message())
