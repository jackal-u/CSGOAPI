import win32api
import win32gui
import win32process
import pymem
import ctypes
import time


class CSAPI:

    def __init__(self):
        self.dwEntityList = 81064444
        self.m_iHealth = 256
        self.dwClientState_GetLocalPlayer = 384
        self.client_dll = 0
        self.handle = 0
        self.m_hMyWeapons = 11768
        self.m_angEyeAnglesX = 45948
        self.m_angEyeAnglesY = 45952
        self.off_enginedll = 0
        self.dwClientState = 5807572
        self.dwClientState_ViewAngles = 19848
        self.m_vecOrigin = 312
        self.m_vecViewOffset = 264
        self.dwLocalPlayer = 13872220
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
        # todo: 武器内容比较复杂，每个武器都是个单独的对象，每个人物都拥有一个武器列表
            # 获取当前人物武器
            player=0
            # 如果p 为0 则为 当前 人的血量
            # entity = self.handle.read_bytes(self.client_dll + self.dwEntityList + player * 0x10, 4)  # 10为每个实体的偏移
            # entity = int.from_bytes(entity, byteorder='little')
            # if entity != 0:
            # 获取local基地址
            local_add = self.handle.read_bytes(self.client_dll + self.dwClientState_GetLocalPlayer, 4)
            local_add = int.from_bytes(local_add, byteorder='little')
            weapon = self.handle.read_bytes(local_add + self.m_hMyWeapons, 4)
            weapon = int.from_bytes(weapon, byteorder='little')
            print("player P %d : %d", player, weapon)


    def get_current_xy(self):
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
        handle.get_current_position()
        time.sleep(0.1)


