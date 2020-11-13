import win32api
import win32gui
import win32process
import pymem
import ctypes
import time,json

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
        print("player {p}  : {x}  y: {y}".format(p=player, x=view_x, y=view_y))
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

                    # # 敌军
                    aimplayerbones = self.handle.read_int(entity + self.m_dwBoneMatrix)
                    enemypos1 = self.handle.read_float(aimplayerbones + 0x30 * 1 + 0x0C)
                    enemypos2 = self.handle.read_float(aimplayerbones + 0x30 * 1 + 0x1C)
                    enemypos3 = self.handle.read_float(aimplayerbones + 0x30 * 1 + 0x2C)
                    list.append(enemypos1)
                    list.append(enemypos2)
                    list.append(enemypos3)
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
                    # todo: 敌人血量，开局应重置为100
                    # # 敌军
                    # 获取当前人物血量
                    health = self.handle.read_bytes(entity + self.m_iHealth, 4)
                    health = int.from_bytes(health, byteorder='little')
                    list.append(health)
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

    def set_aim(self,list):
        # [pitch, yaw]
        # +-90  +-180
        pitch = list[0]
        yaw = list[1]
        enginepointer = self.handle.read_int(self.off_enginedll + self.dwClientState)
        self.handle.write_float((enginepointer + self.dwClientState_ViewAngles), pitch)
        self.handle.write_float((enginepointer + self.dwClientState_ViewAngles + 0x4), yaw)

    def set_walk(self,list):
        # wasd jump attack
        # 下蹲还没有做，正在探讨方法
        if len(list)!=5:
            print("WASD长度不为5")
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
            reward += i
            total_blood += 100
        return total_blood-reward



if __name__ == '__main__':
    handle = CSAPI()

    for i in range(100000):
        action=[1,0,1,0,6]
        list=handle.set_aim([float(-45),float(+0)])
        print(list)
        time.sleep(1)



