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

def str_to_float_list(str_li):
    str_li = str_li.replace("b'[", "")
    str_li = str_li.replace("]'", "")
    str_li = str_li.replace(" ", "")
    li = str_li.split(',')
    for i in range(len(li)):
        li[i] = float(li[i])
    return  li


def execute_action_list(a,b,c,str_li):
    """
     接受模型传来的数据然后执行杀人！
        [wasd x 4 ,  space , attack,      view_y(pitch),view_x(yaw)]  8
        规则：
        [1,1,1,1    1,      1\0,          +-90,  +-180 ]
     1.转换类型
     2.调用api 执行功能
    :param str_li:
    :return:
    """
    real_list = str_to_float_list(str(str_li))

    walk_list = real_list[:6]
    for i in range(len(walk_list)):
        walk_list[i] = int(walk_list[i])
    aim_list = real_list[-2:]
    print(walk_list, aim_list)
    api.set_walk(walk_list)
    api.set_aim(aim_list)


def execute_action_aim_list(a, b, c, str_li):
    """
     接受模型传来的数据然后执行杀人！
        [1,     +-90 , +- 180     ,    is_reset  0/1]      3
        规则：

     1.转换类型
     2.调用api 执行功能
    :param str_li:
    :return:
    """
    real_list = str_to_float_list(str(str_li))

    is_fire = real_list[:1]
    aim_list = real_list[-3:]
    print(is_fire, aim_list)
    api.set_attack(int(is_fire[0]))
    api.set_aim(aim_list)



if __name__ == '__main__':
    # 消费数组并执行数组中的操作
    queue.consume_m2g(execute_action_aim_list)