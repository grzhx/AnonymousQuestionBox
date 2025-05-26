from typing import Optional, Dict, Any, TypedDict, List
import websockets
import json
import asyncio


class QuestionEntry(TypedDict):
    content: str
    index: int


class AnswerEntry(TypedDict):
    content: str
    index: int


class Box(TypedDict):
    question_list: List[QuestionEntry]
    answer_list: List[AnswerEntry]


class Client:
    def __init__(self, server_host='localhost', server_port=8765):
        self.follows = None
        self.server_host = server_host
        self.server_port = server_port
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.username = None
        self.data = []
        self.box_ql_index = 0
        self.box_al_index = 0
        self._listener_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._background_tasks = set()

    async def websocket_connect(self) -> bool:
        uri = f"ws://{self.server_host}:{self.server_port}"  # server websocket address
        try:
            self.websocket = await websockets.connect(uri)
            return True
        except Exception as e:
            print(f"connect failed: {e}")
            return False

    async def login(self, username, password):
        await self.websocket.send(json.dumps({
            "type": "login",
            "username": username,
            "password": password
        }))
        # receive two list
        message = await self._receive_message()
        state = message.get("state")
        if state == "success":
            self.username = username
            await self.update_data()
            return True
        else:
            return False

    async def update_data(self):
        await self.websocket.send(json.dumps({
            "type": "request"
        }))
        message = await self._receive_message()
        state = message.get("state")
        if state == "success":
            self.follows = message.get("follows")
            titles = message.get("titles")
            qs = message.get("questions")
            ans = message.get("answers")
            for i in range(len(self.follows)):
                dic = {"box": self.follows[i], "title": titles[i], "questions": qs[i], "answers": ans[i]}
                self.data.append(dic)
            return True
        else:
            return False

    async def _heartbeat(self):
        while self.websocket and self.websocket.open:
            try:
                await asyncio.sleep(30)
                await self._send_message({"type": "ping"})
            except websockets.ConnectionClosed:
                break
            except Exception as e:
                print(f"heartbeat exception: {e}")

    async def start_listening(self):
        if self.websocket and self.websocket.open:
            self._listener_task = asyncio.create_task(self._listen_messages())
            self._background_tasks.add(self._listener_task)
            self._heartbeat_task = asyncio.create_task(self._heartbeat())
            self._background_tasks.add(self._heartbeat_task)

    async def close(self):
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        for task in self._background_tasks:
            task.cancel()
        try:
            await asyncio.wait(
                self._background_tasks,
                timeout=10.0,
                return_when=asyncio.ALL_COMPLETED
            )
        except asyncio.TimeoutError:
            print("partial task timeout")
        finally:
            self._background_tasks.clear()

    async def logout(self):
        await self._send_message({"type": "logout"})
        msg = await self._receive_message()
        state = msg.get("state")
        if state == "success":
            self.username = None
            return True
        else:
            return False

    async def subscribe(self, target_box: str):
        await self._send_message({
            "type": "follow",
            "box": target_box
        })
        response = await self._validate_response()
        return response

    async def submit_question(self, question: str, target_box: str) -> bool:
        await self._send_message({
            "type": "submit",
            "box": target_box,
            "question": question
        })
        return await self._validate_response()

    async def request_message(self, request_box: str, request_question_index: int = None) -> Dict[str, Any]:
        # ask for a question_index in question_list
        await self._send_message({
            "type": "request",
            "box": request_box,  # the user's username you want to search
            'question_index': request_question_index
        })
        return await self._receive_message()

    async def submit_answer(self, question_index: int, answer: str) -> bool:
        await self._send_message({
            "type": "submit",
            "question_index": question_index,
            "answer": answer
        })
        return await self._validate_response()

    async def update_box(self, title: str):
        await self._send_message({
            "type": "update",
            "title": title
        })

        return await self._validate_response()

    async def _send_message(self, data: Dict[str, Any]) -> None:
        if self.websocket:
            await self.websocket.send(json.dumps(data))

    async def _receive_message(self) -> Dict[str, Any]:
        try:
            message = await self.websocket.recv()
            return json.loads(message)
        except json.JSONDecodeError:
            print("Received invalid JSON message")
            return {}

    async def _send_command(self, data: Dict[str, Any]) -> bool:
        await self._send_message(data)
        response = await self._receive_message()
        return response.get("state") == "success"

    async def _listen_messages(self) -> None:
        try:
            while True:
                message = await self._receive_message()
                if message.get("type") == "answer":
                    print(f"\n[{message.get('type')}]: {message.get('answer')}")
                elif message.get("type") == "request":
                    print(f"\n[{message.get('type')}]: {message.get('request')}")
        except websockets.ConnectionClosed:
            print("Connection closed")

    async def _validate_response(self) -> bool:
        response = await self._receive_message()
        if response.get("state") == "success":
            return True
        print(f"operation failed: {response.get('error', 'unknown error')}")
        return False

async def main():
    c = Client()
    await c.websocket_connect()
    state=await c.login("test","test")
    print(f"follow:{state}")
    state=await c.submit_answer(0,"test.")
    print(f"submit:{state}")
    print(c.data)
    state = await c.logout()
    print(f"logout:{state}")
if __name__ == "__main__":
    asyncio.run(main())  # 启动事件循环


