from api import *
from message_queue import *

api = CSAPI()
queue = Queue()
"""
execute.py脚本应该第一个启动。
队列为：RMQ  网址:http://47.94.143.151:15672 用户：guest 密码:8088178
随后启动计算端的main.py
最后再启动up_load.py
"""

while True:
    list = api.get_aim_situation()
    queue.push_g2m(list)
    # print(list)
    time.sleep(1/64)
