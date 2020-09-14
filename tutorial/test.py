import win32api
import win32gui
import win32process
import pymem
import sys
import os

# 需要offest 自动获取[采用dumper来手动获取，dumper是rust写的，生成json文件，里面存储偏移]


local_offset = 13872220

dwGlowObjectManager = 86601648

m_iGlowIndex = 42040

m_iTeamNum = 244
dwEntityList = 81064444

hWnd = win32gui.FindWindow(0, ("counter-Strike: Global Offensive"))
if (hWnd):
    pid = win32process.GetWindowThreadProcessId(hWnd)
    print(pid)
    handle = pymem.Pymem()
    handle.open_process_from_id(pid[1])
else:
    print("CSGO wasn't found")
    os.system("pause")
    sys.exit()

list_of_modules = handle.list_modules()

# 遍历获得当前client.dll的基地址
while (list_of_modules != None):
    tmp = next(list_of_modules)
    if (tmp.name == "client.dll"):
        client_dll = tmp.lpBaseOfDll
        break;


# 得到当前玩家基地址，以4字节读出，然后转化为整型
local_player_ptr = 0
local_player_ptr = handle.read_bytes(client_dll + local_offset, 4)
while (local_player_ptr == 0):
    local_player_ptr = handle.read_bytes(client_dll + local_offset, 4)
local_player_ptr = int.from_bytes(local_player_ptr, byteorder='little')


F6 = win32api.GetKeyState(0x75)
while (win32api.GetKeyState(0x75) == F6):
    glow_obj = handle.read_bytes(client_dll + dwGlowObjectManager, 4)
    glow_obj = int.from_bytes(glow_obj, byteorder='little')
    my_team = handle.read_int(local_player_ptr + m_iTeamNum)

    # 遍历当前场景下所有实体
    for i in range(64):
        entity = handle.read_bytes(client_dll + dwEntityList + i * 0x10, 4)  # 10为每个实体的偏移
        entity = int.from_bytes(entity, byteorder='little')
        if (entity != 0): # 实体非空，则进行处理
            team = handle.read_int(entity + m_iTeamNum)
            # 实体 + 队伍偏移 == local_player + 队伍偏移 来判断是否是友军

            # 当前实体 存储是否 发光的 变量位置
            gindex = handle.read_int(entity + m_iGlowIndex)
            if (my_team == team):
                # 如果是队友，利用glow_manager 对四个
                handle.write_float(glow_obj + ((gindex * 0x38) + 0x4), 0.0)
                handle.write_float(glow_obj + ((gindex * 0x38) + 0x8), 0.0)
                handle.write_float(glow_obj + ((gindex * 0x38) + 0xc), 2.0)
                handle.write_float(glow_obj + ((gindex * 0x38) + 0x10), 1.7)
            else:
                handle.write_float(glow_obj + ((gindex * 0x38) + 0x4), 2.0)
                handle.write_float(glow_obj + ((gindex * 0x38) + 0x8), 0.0)
                handle.write_float(glow_obj + ((gindex * 0x38) + 0xc), 0.0)
                handle.write_float(glow_obj + ((gindex * 0x38) + 0x10), 1.7)
            handle.write_uchar(glow_obj + ((gindex * 0x38) + 0x24), 1)
            handle.write_uchar(glow_obj + ((gindex * 0x38) + 0x25), 0)