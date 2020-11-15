import pika

# 总共两个队列：
# 队列一：game_to_model
#       用于推API读取的数组给model消费，推送之前需要合并为一个数组：
#       总长度：
#       映射关系：
#       推送频率：64/128
#
# 队列二： model_to_game
#       用于推model输出数据规则化后的执行数组，推送之前需要合并为一个数组：
#       总长度：
#       映射关系：
#       推送频率：64/128
#
from pika import PlainCredentials


class Queue:
    def __init__(self):
        self.g2m_name = 'game_to_model'
        self.m2g_name = 'model_to_game'
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='retake.jlucs.club',
                                                                       credentials=PlainCredentials(username='guest', password='8088178')))
        self.channel = connection.channel()
        self.channel.queue_declare(queue=self.g2m_name,  durable=True)
        self.channel.queue_declare(queue=self.m2g_name, durable=True)
        global g2m_data
        global m2g_data

    def str_to_float_list(self, str_li):
        str_li = str_li.replace("b'[", "")
        str_li = str_li.replace("]'", "")
        str_li = str_li.replace(" ", "")
        li = str_li.split(',')
        print(li)
        for i in range(len(li)):
            li[i] = float(li[i])
        return li


    def push_g2m(self, game_list):
        """
        这一层是用来把数据从game推向模型的
        [hp, view_y(pitch),view_x(yaw),  pos1,pos2,pos3  ,  my_weapon x 8 ,  enemy_position X 15 , enemy_health x 5]
        :param game_list:
        :return:
        """
        self.channel.basic_publish(
            exchange='',
            routing_key=self.g2m_name,
            body=str(game_list),
            properties=pika.BasicProperties(
                delivery_mode=2,
            )
        )
        # print(game_list)


    def consume_g2m(self,func):
        self.channel.basic_consume(on_message_callback=func,
                              queue=self.g2m_name,
                              auto_ack=True)
        self.channel.start_consuming()


    def push_m2g(self,game_list):
        """
        这一层是用来接受模型数据然后输出到执行器的
        [wasd x 4 ,  space , attack,      view_y(pitch),view_x(yaw)]
        在推送队列之前记得把 模型输出数据 规则化为：
        [1,1,1,1    1,      1\0,          +-90,  +-180 ]

        :param game_list:
        :return:
        """
        self.channel.basic_publish(
            exchange='',
            routing_key=self.m2g_name,
            body=str(game_list),
            properties=pika.BasicProperties(
                delivery_mode=2,
            )
        )
        # print(game_list)

    def consume_m2g(self,func):
        """
        这一层是用来接受模型传来的数据然后执行杀人的！
        [wasd x 4 ,  space , attack,      view_y(pitch),view_x(yaw)]
        规则：
        [1,1,1,1    1,      1\0,          +-90,  +-180 ]
        记得预先声明并传入执行函数！
        :param func:
        :return:
        """
        self.channel.basic_consume(on_message_callback=func,
                                   queue=self.m2g_name,
                                   auto_ack=True)
        self.channel.start_consuming()


if __name__ == '__main__':
    queue = Queue()


    for i in range(100):
        list = [1,2,2,-100]
        queue.push_g2m(list)

    print("finish putting")

    # def train(a,v,c,d):
    #     print(d)
    # queue.consume_g2m(train)
