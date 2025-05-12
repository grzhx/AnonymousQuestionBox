import json
import asyncio
import websockets
from websockets.server import WebSocketServerProtocol


class ServerData:
    def __init__(self, host, post):
        self.host = host
        self.post = post
        with open('users_info.json', 'r') as f:
            self.users_dic = json.load(f)
        with open('users_relation.json', 'r') as f:
            self.users_rela = json.load(f)
        with open('text.json', 'r') as f:
            self.text = json.load(f)
        self.online_users = {}

    def save_all(self):
        with open('users_info.json', 'w') as f:
            f.write(json.dumps(self.users_dic))
        with open('users_relation.json', 'w') as f:
            f.write(json.dumps(self.users_rela))
        with open('text.json', 'w') as f:
            f.write(json.dumps(self.text))


d = ServerData('0.0.0.0', 8765)


async def handle_msg(websocket: WebSocketServerProtocol):
    username = None
    try:
        auth_data = await websocket.recv()
        auth = json.loads(auth_data)
        username = auth.get("username")
        password = auth.get("password")

        if not username or not password:
            await websocket.send(json.dumps({"error": "需要用户名和密码"}))
            await websocket.close()
            return

        # 注册或验证用户
        if username in d.users_dic:
            if d.users_dic[username] != password:
                await websocket.send(json.dumps({"error": "密码错误"}))
                await websocket.close()
                return
        else:
            d.users_dic[username] = password
            d.users_rela[username] = []

        # 处理重复登录
        if username in d.online_users:
            old_connection = d.online_users[username]
            try:
                await old_connection.close()
            except Exception:
                pass
            del d.online_users[username]

        d.online_users[username] = websocket
        follows = d.users_rela[username]
        follows = [username] + follows
        titles = []
        for i in follows:
            titles.append(d.text[i]["title"])
        await websocket.send(json.dumps({"status": "登录成功", "follow": follows, "title": titles}))
        async for msg in websocket:
            data = json.loads(msg)
            if data["type"] == "update":
                if not (username in d.text):
                    d.text[username] = {"title": "", "questions": [], "answers": []}
                d.text[username]["title"] = data["title"]
                await websocket.send(json.dumps({"status": "更新/创建成功"}))
            elif data["type"] == "request":
                if data["box"] in d.text:
                    questions = d.text[data["box"]]["questions"]
                    if not ("question_index" in data):
                        await websocket.send(json.dumps({"state": "请求成功", "question": questions}))
                    else:
                        await websocket.send(json.dumps(
                            {"state": "请求成功", "question": questions[data["question_index"]],
                             "answer": d.text[data["box"]]["answers"][data["question_index"]]}))
                else:
                    await websocket.send(json.dumps({"error": "请求对象不存在"}))
            elif data["type"] == "submit":
                if "box" in data:
                    box = data["box"]
                    question = data["question"]
                    d.text[box]["questions"].appand(question)
                    d.text[box]["answers"].appand("")
                    if not (box in d.users_rela[username]):
                        d.users_rela[username].append(box)
                else:
                    index = data["question_index"]
                    d.text[username]["answers"][index] = data["answer"]
                await websocket.send(json.dumps({"state": "提交成功"}))
            elif data["type"] == "follow":
                box = data["box"]
                if box in d.users_rela[username]:
                    await websocket.send(json.dumps({"error": "已订阅"}))
                else:
                    d.users_rela[username].append(box)
                    await websocket.send(json.dumps({"state": "订阅成功"}))
            else:
                await websocket.send(json.dumps({"error": "无效的JSON格式"}))
    except json.JSONDecodeError:
        await websocket.send(json.dumps({"error": "无效的JSON格式"}))
    finally:
        if username and d.online_users.get(username) == websocket:
            del d.online_users[username]


async def main(host, post):
    async with websockets.serve(handle_msg, host, post):
        await asyncio.Future()


asyncio.run(main(d.host, d.post))
