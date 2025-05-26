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


d = ServerData('localhost', 8765)


async def handle_msg(websocket: WebSocketServerProtocol, path):
    username = None
    try:
        async for msg in websocket:
            print(msg)
            data = json.loads(msg)
            if username is None:
                if data.get("type") == "login":
                    username = data.get("username")
                    password = data.get("password")
                    if not username or not password:
                        await websocket.send(json.dumps({"state": "error", "error": "Need username or password"}))
                        await websocket.close()
                        return

                    # 注册或验证用户
                    if username in d.users_dic:
                        if d.users_dic[username] != password:
                            await websocket.send(json.dumps({"state": "error", "error": "Wrong password"}))
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
                    d.save_all()
                    await websocket.send(json.dumps({"state": "success"}))
                else:
                    await websocket.send(json.dumps({"state": "error", "error": "Invalid JSON format"}))
            else:
                if data.get("type") == "update":
                    if not (username in d.text):
                        d.text[username] = {"title": "", "questions": [], "answers": []}
                        d.users_rela[username] = [username] + d.users_rela[username]
                    d.text[username]["title"] = data.get("title")
                    await websocket.send(json.dumps({"state": "success"}))
                elif data.get("type") == "request":
                    if data.get("box") in d.text:
                        questions = d.text[data.get("box")]["questions"]
                        if data.get("question") is None:
                            await websocket.send(json.dumps({"state": "success", "question": questions}))
                        else:
                            await websocket.send(json.dumps(
                                {"state": "success", "question": questions[data.get("question_index")],
                                 "answer": d.text[data.get("box")]["answers"][int(data.get("question_index"))]}))
                    else:
                        follows = d.users_rela[username]
                        titles = []
                        qs = []
                        ans = []
                        for i in follows:
                            titles.append(d.text[i]["title"])
                            qs.append(d.text[i]["questions"])
                            ans.append(d.text[i]["answers"])
                        await websocket.send(json.dumps(
                            {"state": "success", "follows": follows, "titles": titles, "questions": qs,
                             "answers": ans}))
                elif data.get("type") == "submit":
                    if "box" in data:
                        box = data.get("box")
                        if box in d.text:
                            question = data.get("question")
                            d.text[box]["questions"].append(question)
                            d.text[box]["answers"].append("")
                            if not (box in d.users_rela[username]):
                                d.users_rela[username].append(box)
                            await websocket.send(json.dumps({"state": "success"}))
                        else:
                            await websocket.send(json.dumps({"state": "error", "error": "box don't exist"}))
                    else:
                        index = data.get("question_index")
                        d.text.get(username).get("answers")[index] = data.get("answer")
                        await websocket.send(json.dumps({"state": "success"}))
                elif data.get("type") == "follow":
                    box = data.get("box")
                    if box in d.text:
                        if box in d.users_rela[username]:
                            await websocket.send(json.dumps({"state": "error", "error": "Already subscribed"}))
                        else:
                            d.users_rela[username].append(box)
                            await websocket.send(json.dumps({"state": "success"}))
                    else:
                        await websocket.send(json.dumps({"state": "error", "error": "Do not exist"}))
                elif data.get("type") == "test":
                    print("test mode")
                    await websocket.send(json.dumps({"state": "success"}))
                elif data.get("type") == "logout":
                    d.save_all()
                    del d.online_users[username]
                    username = None
                    await websocket.send(json.dumps({"state": "success"}))
                else:
                    await websocket.send(json.dumps({"state": "error", "error": "Invalid JSON format"}))
                d.save_all()
    except json.JSONDecodeError:
        await websocket.send(json.dumps({"state": "error", "error": "Invalid JSON format"}))
    finally:
        d.save_all()
        if username:
            print(username + " lose connection")
        if username and d.online_users.get(username) == websocket:
            del d.online_users[username]


async def main(host, post):
    async with websockets.serve(handle_msg, host, post):
        await asyncio.Future()


asyncio.run(main(d.host, d.post))
