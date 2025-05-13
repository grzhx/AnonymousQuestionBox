1.登录/注册：
{
"username":your_name,
"password":your_password
}
返回值：
用户名或密码缺失时
{
"state":"error",
"error": "需要用户名和密码"
}
密码错误时
{
"state":"error",
"error": "密码错误"
}
成功登录时
{
"state": "登录成功",
"follow":follows,   #列表，包含该用户订阅的所有提问箱的创建者名字
"title":titles      #列表，包含上述提问箱的所有标题，一一对应
}
2.创建/更新提问箱：
{
"type":"update",
"title":your_title
}
返回值：
{"state": "更新/创建成功"}
3.请求数据：
{
"type":"request",
"box":username,   #表示要请求哪个用户的提问箱数据
"question_index":index #一个整数，表示问题在问题列表中的索引，本行可有可无，没有本行表示只请求提问箱中的所有问题，有本行表示请求特定问题和其回答
}
返回值：
未找到提问箱时
{
"state":"error",
"error": "请求对象不存在"
}
请求所有问题时
{"state": "请求成功", "question": questions}
请求某个问题及其回答时：
{"state": "请求成功", "question": question,"answer":answer}
4.提交文本（提问/回答)：
提问时
{
"type":"submit",
"box":your_targetBox_owner, #目标提问箱的用户名
"question":your_question
}
回答时：
{
"type":"submit",
"question_index":index, #问题在问题列表中的索引
"answer":your_answer
}
返回值：
{"state": "提交成功"}
5.订阅提问箱：
{
"type":"follow",
"box":box_username
}
返回值：
重复订阅时
{
"state":"error",
"error": "已订阅"
}
成功订阅时
{
"state":"error",
"state": "订阅成功"
}




text.json:
{
username:{"title":title,"questions":[],"answers":[]}
}
users_relation.json:
{
username:[]
}
users_info.json:
{
username:password
}