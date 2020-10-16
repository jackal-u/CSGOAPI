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
        self.dwClientState = int(off_set_dict["signatures"]["dwClientState"])
        self.dwClientState_ViewAngles = int(off_set_dict["signatures"]["dwClientState_ViewAngles"])
        self.m_vecOrigin = int(off_set_dict["netvars"]["m_vecOrigin"])
        self.m_vecViewOffset = int(off_set_dict["netvars"]["m_vecViewOffset"])
        self.dwLocalPlayer = int(off_set_dict["signatures"]["dwLocalPlayer"])
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
        # 调用得到client.dll基地址
        #
        #     # 获取local基地址
        #     local_add = handle.read_bytes(client_dll + dwClientState_GetLocalPlayer, 4)
        #     local_add = int.from_bytes(local_add, byteorder='little')

    def get_health(self):
            # 获取当前人物血量
            player=0
            # 如果p 为0 则为 当前 人的血量
            entity = self.handle.read_bytes(self.client_dll + self.dwEntityList + player * 0x10, 4)  # 10为每个实体的偏移
            entity = int.from_bytes(entity, byteorder='little')
            if entity != 0:
                health = self.handle.read_bytes(entity + self.m_iHealth, 4)
                health = int.from_bytes(health, byteorder='little')
                print("player P %d : %d", player, health)


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

            """

            # if entity != 0:
            # 获取local基地址 self.client_dll + self.dwEntityList + 0*0x10
            local_add = self.handle.read_bytes(self.client_dll+self.dwLocalPlayer, 4)
            local_add = int.from_bytes(local_add, byteorder='little')
            # print(local_add)
            weapon_list=[]
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
                    break
                # # 武器元信息获得武器index。
                weapon_index = self.handle.read_int(weapon_meta+self.m_iItemDefinitionIndex)
                # print("weapon_index", weapon_index)
                weapon_list.append(weapon_index)
            return weapon_list





    def get_current_xy(self):
        """
        用于获得当前人物指针的指向，x轴(+180-180)，y轴(+-90)
        :return:
        """
        player = 0
        entity = self.handle.read_bytes(self.client_dll + self.dwEntityList + player * 0x10, 4)  # 10为每个实体的偏移
        entity = int.from_bytes(entity, byteorder='little')

        engine_pointer = self.handle.read_int((self.off_enginedll+self.dwClientState))
        view_x = self.handle.read_float((engine_pointer + self.dwClientState_ViewAngles))
        view_y = self.handle.read_float((engine_pointer + self.dwClientState_ViewAngles + 0x4))

        # if entity != 0:
        #     x = self.handle.read_int((entity + self.m_angEyeAnglesX))
        #     x&=0x8000
        #
        #     y = self.handle.read_int(entity + self.m_angEyeAnglesY)
        #     y&=0x8000
        print("player {p}  : {x}  y: {y}".format(p=player, x=view_x, y=view_y))
    
    def get_current_position(self):
        """
        获得当前玩家的所在位置，两个维度
        :return:
        """


        aimlocalplayer = self.handle.read_int(self.client_dll+self.dwLocalPlayer)
        vecorigin = self.handle.read_int(( aimlocalplayer + self.m_vecOrigin))

        localpos1 = self.handle.read_float(( aimlocalplayer + self.m_vecOrigin))
                    # self.handle.read_float(( self.m_vecViewOffset+vecorigin + 0x104 ))

        localpos2 = self.handle.read_float(( aimlocalplayer + self.m_vecOrigin+0x4))
                    # self.handle.read_float((self.m_vecViewOffset+vecorigin + 0x108))

        localpos3 = self.handle.read_float(( aimlocalplayer + self.m_vecOrigin+0x8))
                    # self.handle.read_float((aimlocalplayer+ 0x10C))
        # localpos1 = self.handle.read_float(self.dwLocalPlayer + vecorigin + 0x0)
        # localpos2 = self.handle.read_float((self.dwLocalPlayer + vecorigin + 0x4))
        # localpos3 = self.handle.read_float((self.dwLocalPlayer + vecorigin + 0x8))
        print("localtion: {x}     {y}    {z}".format(x=localpos1,y=localpos2,z=localpos3))




if __name__ == '__main__':
    handle = CSAPI()

    for i in range(100000):
        list=handle.get_weapon()
        print(list)
        time.sleep(0.1)



