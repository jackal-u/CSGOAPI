import win32api
import win32gui
import win32process
import pymem
import ctypes
import time, json, math, random, numpy

from message_queue import *
from tutorial.autoaim import normalizeAngles

"""
用于测试的csgo账号（不要登录公网VAC服务器）:
账号:mmye252570
密码：ojpd6n9z

"""

class CSAPI:

    def __init__(self):
        with open("./csgo.json") as conf:
            off_set_dict=json.load(conf)
        self.dwEntityList = int(off_set_dict["signatures"]["dwEntityList"])
        self.m_iHealth = int(off_set_dict["netvars"]["m_iHealth"])
        self.dwClientState_GetLocalPlayer = int(off_set_dict["signatures"]["dwClientState_GetLocalPlayer"])
        self.client_dll = 0
        self.handle = 0
        self.m_hMyWeapons = int(off_set_dict["netvars"]["m_hMyWeapons"])
        self.m_angEyeAnglesX = int(off_set_dict["netvars"]["m_angEyeAnglesX"])
        self.m_angEyeAnglesY = int(off_set_dict["netvars"]["m_angEyeAnglesY"])
        self.off_enginedll = 0
        self.m_dwBoneMatrix = int(off_set_dict["netvars"]["m_dwBoneMatrix"])
        self.m_iTeamNum = int(off_set_dict["netvars"]["m_iTeamNum"])
        self.dwClientState = int(off_set_dict["signatures"]["dwClientState"])
        self.dwClientState_ViewAngles = int(off_set_dict["signatures"]["dwClientState_ViewAngles"])
        self.m_vecOrigin = int(off_set_dict["netvars"]["m_vecOrigin"])
        self.m_vecViewOffset = int(off_set_dict["netvars"]["m_vecViewOffset"])
        self.dwLocalPlayer = int(off_set_dict["signatures"]["dwLocalPlayer"])
        self.dwForceAttack = int(off_set_dict["signatures"]["dwForceAttack"])
        self.dwForceAttack2 = int(off_set_dict["signatures"]["dwForceAttack2"])
        self.dwForceBackward = int(off_set_dict["signatures"]["dwForceBackward"])
        self.dwForceForward = int(off_set_dict["signatures"]["dwForceForward"])
        self.dwForceLeft = int(off_set_dict["signatures"]["dwForceLeft"])
        self.dwForceRight = int(off_set_dict["signatures"]["dwForceRight"])
        self.dwForceJump = int(off_set_dict["signatures"]["dwForceJump"])
        self.m_iItemDefinitionIndex=int(off_set_dict["netvars"]["m_iItemDefinitionIndex"])


        # todo:自动导入csgo.json为本类属性

        # Counter-Strike: Global Offensive 窗口标题 获得窗口句柄
        window_handle = win32gui.FindWindow(None, u"Counter-Strike: Global Offensive")
        if window_handle:
            print(window_handle)
            # 获得窗口句柄获得进程ID
            process_id = win32process.GetWindowThreadProcessId(window_handle)
            print(process_id)
            handle = pymem.Pymem()
            handle.open_process_from_id(process_id[1])
            self.handle = handle
            # 遍历当前进程调用的dll，获得client.dll的基地址
            list_of_modules = handle.list_modules()
            while list_of_modules is not None:
                tmp = next(list_of_modules)
                if tmp.name == "client.dll":
                    self.client_dll = tmp.lpBaseOfDll
                if tmp.name == "engine.dll":
                    self.off_enginedll = tmp.lpBaseOfDll
                if self.off_enginedll != 0 and self.client_dll != 0:
                    break
        else:
            print("didn't get the window handle")
            exit()
        # todo:已经得到了基地址，加上任意偏移就可读写表地址的数值
        list = self.get_current_xy()
        self.aim_x = list[1]
        self.aim_y = list[0]
        self.steps = 0
        total_blood = 0
        for h in self.get_enemy_health():
            total_blood+=h
        self.enemy_heath = total_blood
        self.last_shangxia = 0
        self.last_zuoyou   = 0



    def get_health(self):
            # 获取当前人物血量
            player=0
            # 如果p 为0 则为 当前 人的血量
            entity = self.handle.read_bytes(self.client_dll + self.dwEntityList + player * 0x10, 4)  # 10为每个实体的偏移
            entity = int.from_bytes(entity, byteorder='little')
            if entity != 0:
                health = self.handle.read_bytes(entity + self.m_iHealth, 4)
                health = int.from_bytes(health, byteorder='little')
                return [health]

    def get_weapon(self):
            # todo: 武器内容比较复杂，每个武器都是个单独的对象，每个人物都拥有一个武器64位的指针列表
            """
                The m_hMyWeapons array contains handles to all weapons equipped by the local player.
                We can apply skin and model values to those weapons' entities independent to which weapon the local player is holding in hands.
                self.client_dll+self.dwLocalPlayer 获得当前用户的引用LOCAL
                LOCAL+m_hMyWeapons 获得当前用户的武器数组array。
                for 遍历（10）当前用户武器数组，获得武器实体的引用V（每个元素添加偏移0x4）
                V指针通过 dwEntityList + (currentWeapon - 1) * 0x10 获得当前武器的元信息；
                currentWeapon + m_iItemDefinitionIndex获得当前武器的 具体型号。

                C4:49
                匪徒刀：59
                CT刀：42
                p2000:32
                glock：4
                :return 返回长度为8的一个list
            """

            # if entity != 0:
            # 获取local基地址 self.client_dll + self.dwEntityList + 0*0x10
            local_add = self.handle.read_bytes(self.client_dll+self.dwLocalPlayer, 4)
            local_add = int.from_bytes(local_add, byteorder='little')
            # print(local_add)
            weapon_list=[0 for _ in range(8)]
            for i in range(8):
                # 武器数组array遍历获得武器引用。
                weapon_each = self.handle.read_bytes(local_add + self.m_hMyWeapons + i * 0x4, 4)
                weapon_each = int.from_bytes(weapon_each, byteorder='little') & 0xfff               # 我也不知道为什么按位与 1111
                # print("waepon_each:  " +  str(weapon_each))
                # 武器引用获得武器元信息。
                weapon_meta = self.handle.read_bytes(self.client_dll + self.dwEntityList + (weapon_each - 1) * 0x10, 4)
                weapon_meta = int.from_bytes(weapon_meta, byteorder='little')
                # print("weapon_meta:  " + str(weapon_meta))
                if weapon_meta == 0:
                    continue
                # # 武器元信息获得武器index。
                weapon_index = self.handle.read_int(weapon_meta+self.m_iItemDefinitionIndex)
                # print("weapon_index", weapon_index)
                weapon_list[i] = weapon_index
            return weapon_list

    def get_current_xy(self):
        """
        用于获得当前人物指针的指向，x轴(+180-180)，y轴(+-90)
        :return 返回长度为2的一个list
        """
        player = 0
        entity = self.handle.read_bytes(self.client_dll + self.dwEntityList + player * 0x10, 4)  # 10为每个实体的偏移
        entity = int.from_bytes(entity, byteorder='little')

        engine_pointer = self.handle.read_int((self.off_enginedll+self.dwClientState))
        view_x = self.handle.read_float((engine_pointer + self.dwClientState_ViewAngles))
        view_y = self.handle.read_float((engine_pointer + self.dwClientState_ViewAngles + 0x4))

        list = []
        # if entity != 0:
        #     x = self.handle.read_int((entity + self.m_angEyeAnglesX))
        #     x&=0x8000
        #
        #     y = self.handle.read_int(entity + self.m_angEyeAnglesY)
        #     y&=0x8000

        view_x,view_y = normalizeAngles(view_x,view_y)



        list.append(view_x)
        list.append(view_y)
        return list
    
    def get_current_position(self):
        """
        获得当前玩家的所在位置，两个维度
        :return:
        """

        list =[]
        aimlocalplayer = self.handle.read_int(self.client_dll+self.dwLocalPlayer)
        vecorigin = self.handle.read_int(aimlocalplayer + self.m_vecOrigin)

        localpos1 = self.handle.read_float(( aimlocalplayer + self.m_vecOrigin))  #+ self.handle.read_float(vecorigin + self.m_vecViewOffset + 0x104)
        localpos2 = self.handle.read_float(( aimlocalplayer + self.m_vecOrigin+0x4))   #+ self.handle.read_float(vecorigin + self.m_vecViewOffset + 0x108)
        localpos3 = self.handle.read_float((aimlocalplayer + self.m_vecOrigin + 0x8))  #+ self.handle.read_float(vecorigin + self.m_vecViewOffset + 0x10C)
        list.append(localpos1)
        list.append(localpos2)
        list.append(localpos3)
        return list

    def get_enemy_position(self):
        """
        输出 长度为15的数组，每三个代表一个敌人的位置，他们按照内存顺序排序

        :return:
        """
        # list=[0 for i in range(15)]
        list = []
        counter = 0
        aimlocalplayer = self.handle.read_int(self.client_dll+self.dwLocalPlayer)
        # 得到敌人的偏移
        my_team = self.handle.read_int(aimlocalplayer + self.m_iTeamNum)
        enemy_num = 0
        for i in range(64):

            entity = self.handle.read_bytes(self.client_dll + self.dwEntityList + i * 0x10, 4)  # 10为每个实体的偏移
            entity = int.from_bytes(entity, byteorder='little')
            if (entity != 0):  # 实体非空，则进行处理
                team = self.handle.read_int(entity + self.m_iTeamNum)
                # 实体 + 队伍偏移 == local_player + 队伍偏移 来判断是否是友军
                if (my_team == team):
                    # 友军
                    # 敌军
                    pass
                    # aimplayerbones = self.handle.read_int(entity + self.m_dwBoneMatrix)
                    # enemypos1 = self.handle.read_float(aimplayerbones + 0x30 * 1 + 0x0C)
                    # enemypos2 = self.handle.read_float(aimplayerbones + 0x30 * 1 + 0x1C)
                    # enemypos3 = self.handle.read_float(aimplayerbones + 0x30 * 1 + 0x2C)
                    #
                    # list.append(enemypos1)
                    # list.append(enemypos2)
                    # list.append(enemypos3)
                    # enemy_num += 3
                else:
                    if counter < 5:
                        # # 敌军
                        aimplayerbones = self.handle.read_int(entity + self.m_dwBoneMatrix)
                        enemypos1 = self.handle.read_float(aimplayerbones + 0x30 * 1 + 0x0C)
                        enemypos2 = self.handle.read_float(aimplayerbones + 0x30 * 1 + 0x1C)
                        enemypos3 = self.handle.read_float(aimplayerbones + 0x30 * 1 + 0x2C)
                        list.append(enemypos1)
                        list.append(enemypos2)
                        list.append(enemypos3)
                        counter += 1
        return  list

    def get_enemy_position_single(self):
        """
        输出 长度为15的数组，每三个代表一个敌人的位置，他们按照内存顺序排序

        :return:
        """
        # list=[0 for i in range(15)]
        list = []
        counter = 0
        aimlocalplayer = self.handle.read_int(self.client_dll+self.dwLocalPlayer)
        # 得到敌人的偏移
        my_team = self.handle.read_int(aimlocalplayer + self.m_iTeamNum)
        enemy_num = 0
        for i in range(64):

            entity = self.handle.read_bytes(self.client_dll + self.dwEntityList + i * 0x10, 4)  # 10为每个实体的偏移
            entity = int.from_bytes(entity, byteorder='little')
            if (entity != 0):  # 实体非空，则进行处理
                team = self.handle.read_int(entity + self.m_iTeamNum)
                # 实体 + 队伍偏移 == local_player + 队伍偏移 来判断是否是友军
                if (my_team == team):
                    # 友军
                    # 敌军
                    pass
                    # aimplayerbones = self.handle.read_int(entity + self.m_dwBoneMatrix)
                    # enemypos1 = self.handle.read_float(aimplayerbones + 0x30 * 1 + 0x0C)
                    # enemypos2 = self.handle.read_float(aimplayerbones + 0x30 * 1 + 0x1C)
                    # enemypos3 = self.handle.read_float(aimplayerbones + 0x30 * 1 + 0x2C)
                    #
                    # list.append(enemypos1)
                    # list.append(enemypos2)
                    # list.append(enemypos3)
                    # enemy_num += 3
                else:
                    if counter < 1:
                        # # 敌军
                        aimplayerbones = self.handle.read_int(entity + self.m_dwBoneMatrix)
                        enemypos1 = self.handle.read_float(aimplayerbones + 0x30 * 1 + 0x0C)
                        enemypos2 = self.handle.read_float(aimplayerbones + 0x30 * 1 + 0x1C)
                        enemypos3 = self.handle.read_float(aimplayerbones + 0x30 * 1 + 0x2C)
                        list.append(enemypos1)
                        list.append(enemypos2)
                        list.append(enemypos3)
                        counter += 1
        return  list


    def get_friendly_position(self):
        """
        输出 长度为15的数组，每三个代表一个敌人的位置，他们按照内存顺序排序
        友军位置，包括自己的位置
        :return:
        """
        # list=[0 for i in range(15)]
        list = []

        aimlocalplayer = self.handle.read_int(self.client_dll+self.dwLocalPlayer)
        # 得到人类的偏移
        my_team = self.handle.read_int(aimlocalplayer + self.m_iTeamNum)
        for i in range(64):
            entity = self.handle.read_bytes(self.client_dll + self.dwEntityList + i * 0x10, 4)  # 10为每个实体的偏移
            entity = int.from_bytes(entity, byteorder='little')
            if (entity != 0):  # 实体非空，则进行处理
                team = self.handle.read_int(entity + self.m_iTeamNum)
                # 实体 + 队伍偏移 == local_player + 队伍偏移 来判断是否是友军
                if (my_team == team):
                    # 友军
                    aimplayerbones = self.handle.read_int(entity + self.m_dwBoneMatrix)
                    pos1 = self.handle.read_float(aimplayerbones + 0x30 * 1 + 0x0C)
                    pos2 = self.handle.read_float(aimplayerbones + 0x30 * 1 + 0x1C)
                    pos3 = self.handle.read_float(aimplayerbones + 0x30 * 1 + 0x2C)
                    list.append(pos1)
                    list.append(pos2)
                    list.append(pos3)
                else:
                    # # 敌军
                   pass
        return  list

    def get_enemy_health(self):
        """
                输出 长度为5的数组,内存顺序排序
                :return:
                """
        # list=[0 for i in range(15)]
        list = []
        counter = 0
        aimlocalplayer = self.handle.read_int(self.client_dll + self.dwLocalPlayer)
        # 得到敌人的偏移
        my_team = self.handle.read_int(aimlocalplayer + self.m_iTeamNum)
        for i in range(64):
            entity = self.handle.read_bytes(self.client_dll + self.dwEntityList + i * 0x10, 4)  # 10为每个实体的偏移
            entity = int.from_bytes(entity, byteorder='little')
            if (entity != 0):  # 实体非空，则进行处理
                team = self.handle.read_int(entity + self.m_iTeamNum)
                # 实体 + 队伍偏移 == local_player + 队伍偏移 来判断是否是友军
                if (my_team == team):
                    # 友军
                    pass

                else:
                    if counter < 5:
                        # todo: 敌人血量，开局应重置为100
                        # # 敌军
                        # 获取当前人物血量
                        health = self.handle.read_bytes(entity + self.m_iHealth, 4)
                        health = int.from_bytes(health, byteorder='little')
                        list.append(health)
                        counter+=1
        return list

    def get_friendly_health(self):
        """
                输出 长度为5的数组,内存顺序排序
                :return:
                """
        # list=[0 for i in range(15)]
        list = []

        aimlocalplayer = self.handle.read_int(self.client_dll + self.dwLocalPlayer)
        # 得到敌人的偏移
        my_team = self.handle.read_int(aimlocalplayer + self.m_iTeamNum)
        for i in range(64):
            entity = self.handle.read_bytes(self.client_dll + self.dwEntityList + i * 0x10, 4)  # 10为每个实体的偏移
            entity = int.from_bytes(entity, byteorder='little')
            if (entity != 0):  # 实体非空，则进行处理
                team = self.handle.read_int(entity + self.m_iTeamNum)
                # 实体 + 队伍偏移 == local_player + 队伍偏移 来判断是否是友军
                if (my_team == team):
                    # 友军
                    # 获取当前人物血量
                    health = self.handle.read_bytes(entity + self.m_iHealth, 4)
                    health = int.from_bytes(health, byteorder='little')
                    list.append(health)
                else:
                    pass
        return list

    def set_attack2(self):
        # 测试中，无作用
        self.handle.write_int(self.client_dll + self.dwForceAttack2, -1)

    def set_attack(self,i):
        # 测试中，无作用
        self.handle.write_int(self.client_dll + self.dwForceAttack, i)

    def set_aim(self, list):
        # [pitch, yaw]
        # +-90  +-180
        pitch = self.aim_y + list[0]
        yaw = self.aim_x + list[1]
        print("pitch  yaw",pitch,yaw)
        # self.aim_y = list[0]
        # self.aim_x = list[1]
        self.aim_y = pitch
        self.aim_x = yaw
        # 下面是重置代码，用于reset极端情况，避免不必要的训练
        if pitch >= +80.0:
            print("protected!")
            self.aim_y = 80.0
        if pitch <= -80.0:
            self.aim_y = -80.0

        if yaw >= +180:
            print("protected!")
            self.aim_x = 180.0
        if yaw <= -180:
            print("protected!")
            self.aim_x = -180.0
        print("俯仰角   ",self.aim_y ,'方位角：  ' , self.aim_x)
        enginepointer = self.handle.read_int(self.off_enginedll + self.dwClientState)
        self.handle.write_float((enginepointer + self.dwClientState_ViewAngles), self.aim_y)
        self.handle.write_float((enginepointer + self.dwClientState_ViewAngles + 0x4), self.aim_x)

        pos = self.get_current_position()
        posx = pos[0]
        posy = pos[1]
        posz = pos[2]
        e_pos = self.get_enemy_position()
        e_posx = e_pos[0]
        e_posy = e_pos[1]
        e_posz = e_pos[2]
        targetline1 = e_posx - posx
        targetline2 = e_posy - posy
        targetline3 = e_posz - posz

        if targetline2 == 0 and targetline1 == 0:
            yaw = 0
            if targetline3 > 0:
                pitch = 270
            else:
                pitch = 90
        else:
            yaw = (math.atan2(targetline2, targetline1) * 180 / math.pi)
            if yaw < 0:
                yaw += 360
            hypotenuse = math.sqrt(
                (targetline1 * targetline1) + (targetline2 * targetline2) + (targetline3 * targetline3))
            pitch = (math.atan2(-targetline3, hypotenuse) * 180 / math.pi)
            if pitch < 0:
                pitch += 360

        pitch, yaw = normalizeAngles(pitch, yaw)
        cur = self.get_current_xy()
        cur_shang_xia = cur[0]
        cur_zuoyou = cur[1]
        #如果训练经过200步，角度差距还大于10，则进行重置；重置到敌人脑袋附近
        if self.steps%120==0 : # and ( abs(cur_zuoyou - yaw) > 10  or abs(cur_shang_xia - pitch) > 20) and random.random()<0.3
            print("RESET!!!!")
            self.aim_x = yaw + random.random() * 5
            self.aim_y = pitch + random.random() * 3
            print("【重置！！】俯仰角   ", self.aim_y, '方位角：  ', self.aim_x)
            self.steps += 1
            return
        # if abs(cur_zuoyou - yaw) < 5 and abs(cur_shang_xia - pitch) < 10 and random.random()<0.1:
        #     print("RESET!!!!")
        #     self.aim_x = yaw + random.random() * 5
        #     self.aim_y = pitch + random.random() * 3
        #     self.steps += 1
        #     return

        self.steps+=1
        print("steps: ",self.steps)




    def set_reset_aim(self,is_reset,list):
        if is_reset:
            pass
            # self.aim_x = list [0]
            # self.aim_y = list [1]
            # enginepointer = self.handle.read_int(self.off_enginedll + self.dwClientState)
            # self.handle.write_float((enginepointer + self.dwClientState_ViewAngles), self.aim_y)
            # self.handle.write_float((enginepointer + self.dwClientState_ViewAngles + 0x4), self.aim_x)

    def set_walk(self,list):
        # wasd jump attack
        # 下蹲还没有做，正在探讨方法
        if len(list)!=6:
            print("WASD长度不为6")
        self.handle.write_int(self.client_dll + self.dwForceForward, list[0])
        self.handle.write_int(self.client_dll + self.dwForceBackward, list[1])
        self.handle.write_int(self.client_dll + self.dwForceLeft, list[2])
        self.handle.write_int(self.client_dll + self.dwForceRight, list[3])
        self.handle.write_int(self.client_dll + self.dwForceJump, list[4])
        if list[5]:
            self.handle.write_int(self.client_dll + self.dwForceAttack, 6)


    def get_reward(self):

        reward = 0
        total_blood = 0
        list = self.get_enemy_health()
        for i in list:
            total_blood += i
        # 这里计算血量减少的值作为奖赏
        reward = abs(self.enemy_heath - total_blood)*80
        self.enemy_heath = total_blood

        print('blood_reawrd: ', reward)

        # todo:如果瞄准准星很靠近预期方向那就基于更多的reward，且reward最好取连续值
        pos = self.get_current_position()
        posx = pos[0]
        posy = pos[1]
        posz = pos[2]
        e_pos = self.get_enemy_position()
        e_posx = e_pos[0]
        e_posy = e_pos[1]
        e_posz = e_pos[2]
        targetline1 = e_posx - posx
        targetline2 = e_posy - posy
        targetline3 = e_posz - posz

        if targetline2 == 0 and targetline1 == 0:
            yaw = 0
            if targetline3 > 0:
                pitch = 270
            else:
                pitch = 90
        else:
            yaw = (math.atan2(targetline2, targetline1) * 180 / math.pi)
            if yaw < 0:
                yaw += 360
            hypotenuse = math.sqrt(
                (targetline1 * targetline1) + (targetline2 * targetline2) + (targetline3 * targetline3))
            pitch = (math.atan2(-targetline3, hypotenuse) * 180 / math.pi)
            if pitch < 0:
                pitch += 360

        pitch, yaw = normalizeAngles(pitch, yaw)
        cur = self.get_current_xy()
        cur_shang_xia = cur[0]
        cur_zuoyou = cur[1]
        # print("x_grad",pitch,"y_grad",yaw)
        print("当前俯仰角：",cur_shang_xia , "当前方位角",cur_zuoyou )
        print("正确俯仰角",pitch , "正确方位角", yaw)



        # # 如果 位置没有达到期望值 就基于惩罚
        # if abs(cur_zuoyou - yaw) > 30 :
        #     reward -= (abs(cur_zuoyou - yaw)-30)*(abs(cur_zuoyou - yaw)-30)
        # if abs(cur_shang_xia - pitch) > 80 :
        #     # reward -= (abs(cur_shang_xia - pitch)-15)*(abs(cur_shang_xia - pitch)-15)*5
        #     reward = 0
        #
        reward += 100/(abs(   min( (cur_zuoyou - yaw), (360-(cur_zuoyou - yaw))))  + abs(cur_shang_xia - pitch)*1.5 ) # 这个可求导的奖励函数是一切的关键！  这个水平角的计算有问题，不应该是取顺时针角，而应该是取最小夹角。
        reward -= (abs(cur_shang_xia - pitch))*(abs(cur_shang_xia - pitch))*0.005
        reward -= abs(   min( (cur_zuoyou - yaw), (360-(cur_zuoyou - yaw))))*0.005

        # # 下面添加 基于行为的奖励，而不是基于状态的奖励。
        # if cur_shang_xia > pitch:
        #     # 当前瞄准位置比较大，对减小的行为给予奖励，增大的行为给予惩罚
        #     if cur_shang_xia > self.last_shangxia:
        #         reward -= 20
        #     elif cur_shang_xia < self.last_shangxia:
        #         reward += 20
        #     else:
        #         reward -= 10
        #
        # else:
        #     # 当前瞄准位置比较小，对加大的行为给予奖励，减小的行为给予惩罚
        #     if cur_shang_xia > self.last_shangxia:
        #         reward += 20
        #     elif cur_shang_xia < self.last_shangxia:
        #         reward -= 20
        #     else:
        #         reward -= 10
        #
        #
        # if cur_zuoyou > yaw:
        #     # 当前瞄准位置比较大，对减小的行为给予奖励，增大的行为给予惩罚
        #     if cur_zuoyou > self.last_zuoyou:
        #         reward -= 20
        #     elif cur_zuoyou < self.last_zuoyou:
        #         reward += 20
        #     else:
        #         reward -= 10
        # else:
        #     # 当前瞄准位置比较小，对加大的行为给予奖励，减小的行为给予惩罚
        #     if cur_zuoyou > self.last_zuoyou:
        #         reward += 20
        #     elif cur_zuoyou < self.last_zuoyou:
        #         reward -= 20
        #     else:
        #         reward -= 10

        self.last_shangxia = cur_shang_xia
        self.last_zuoyou = cur_zuoyou

        #reward -=1
        # if abs(cur_shang_xia - pitch) > 20:
        #     reward -= abs(cur_shang_xia)*2
        #     print("p偏移惩罚！！", reward)

        # if self.steps % 50 == 0 and (abs(cur_zuoyou - yaw) > 10 or abs(cur_shang_xia - pitch) > 20):
        #     print("RESET 惩罚 !!!!")
        #     reward -= (abs(cur_zuoyou - yaw)+ abs(cur_shang_xia - pitch) )

        print("STEPS:",self.steps)
        # print('aim_reward: ',reward)
        print("FINAL REWARD",reward)
        self.steps += 1
        reward -= 5
        return reward


    def get_all_situation(self):
        """
        [hp, view_y(pitch),view_x(yaw),  pos1,pos2,pos3  ,  my_weapon x 8 ,  enemy_position X 15 , enemy_health x 5]

        :return:
        """
        list = self.get_health() + self.get_current_xy() + self.get_current_position() + self.get_weapon() + self.get_enemy_position() + self.get_enemy_health()
        return list

    def get_aim_situation(self):
        """
        由于目前我们技术比较菜，之前的那个all_situation明显过于复杂，我们现在假设一个简单的情景：
        我们拿着AK，站立不动，操作维度仅仅为：是否开火，瞄准位置
                [1,     +-90 , +- 180]      3
                            反馈维度：瞄准位置，自己位置，单个敌人位置，敌人健康
                [view_y(pitch),view_x(yaw),  pos1,pos2,pos3  , enemy_position X 3 , reward x 1。 ] 9 维度

                :return:
                """
        list =  self.get_current_xy() + self.get_current_position() + self.get_enemy_position_single() + [self.get_reward()]
        return list

if __name__ == '__main__':
    handle = CSAPI()


    while True:
        print(handle.get_aim_situation())
        time.sleep(0.1)



