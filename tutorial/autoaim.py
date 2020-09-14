''''''''''''''''''''''''''''''
'''       IMPORTS          '''
''''''''''''''''''''''''''''''
# test
import os
import time
import struct
import math
import random

try:
    import win32api
    import win32gui
    import win32process
except:
    print("Installing pywin32, remember to reload!")
    os.system('python -m pip install pywin32')

from ctypes import *
from pymem import *
from offsets import *

''''''''''''''''''''''''''''''
'''  OPENING CSGO PROCESS  '''
''''''''''''''''''''''''''''''
hWnd = win32gui.FindWindow(0, ("counter-Strike: Global Offensive"))
if (hWnd):
    pid = win32process.GetWindowThreadProcessId(hWnd)
    handle = pymem.Pymem()
    handle.open_process_from_id(pid[1])
    csgo_entry = handle.process_base
else:
    print("CSGO wasn't found")
    os.system("pause")
    sys.exit()

'''GETTING CLIENT DLL MODULE ENTERY ADDRESS'''
list_of_modules = handle.list_modules()
while (list_of_modules != None):
    tmp = next(list_of_modules)
    if (tmp[0].name == "client_panorama.dll"):
        off_clientdll = tmp[1]
        break

list_of_modules = handle.list_modules()
while (list_of_modules != None):
    tmp = next(list_of_modules)
    if (tmp[0].name == "engine.dll"):
        off_enginedll = tmp[1]
        break

OpenProcess = windll.kernel32.OpenProcess
CloseHandle = windll.kernel32.CloseHandle
PROCESS_ALL_ACCESS = 0x1F0FFF

game = windll.kernel32.OpenProcess(PROCESS_ALL_ACCESS, 0, pid[1])
ReadProcessMemory = windll.kernel32.ReadProcessMemory
WriteProcessMemory = windll.kernel32.WriteProcessMemory

aimonoff = True
rcsonoff = True
test = True

aimbone = 1  # 1: head
aimfov = 3


def getlenght(type):
    if type == "i":
        return 4
    elif type == "f":
        return 4
    elif type == "c":
        return 1


def float_to_hex(f):
    return struct.pack('f', f)


def read_memory(game, address, type):
    buffer = (ctypes.c_byte * getlenght(type))()
    bytesRead = ctypes.c_ulonglong(0)
    readlenght = getlenght(type)
    ReadProcessMemory(game, address, buffer, readlenght, byref(bytesRead))
    return struct.unpack(type, buffer)[0]


def write_memory(game, address, data, type):
    count = c_ulong(0)
    if type == "f":
        buffer = (float_to_hex(data))

    elif type == "i":
        buffer = struct.pack("i", data)

    elif type == "c":
        buffer = chr(data)

    lenght = getlenght(type)
    WriteProcessMemory(game, address, buffer, lenght, byref(count))


def normalizeAngles(viewAngleX, viewAngleY):
    if viewAngleX > 89:
        viewAngleX -= 360
    if viewAngleX < -89:
        viewAngleX += 360
    if viewAngleY > 180:
        viewAngleY -= 360
    if viewAngleY < -180:
        viewAngleY += 360

    return viewAngleX, viewAngleY


def checkangles(x, y):
    if x > 89:
        return False
    elif x < -89:
        return False
    elif y > 360:
        return False
    elif y < -360:
        return False
    else:
        return True


def nanchecker(first, second):
    if math.isnan(first) or math.isnan(second):
        return False
    else:
        return True


def calc_distance(current_x, current_y, new_x, new_y):
    distancex = new_x - current_x
    if distancex < -89:
        distancex += 360
    elif distancex > 89:
        distancex -= 360
    if distancex < 0.0:
        distancex = -distancex

    distancey = new_y - current_y
    if distancey < -180:
        distancey += 360
    elif distancey > 180:
        distancey -= 360
    if distancey < 0.0:
        distancey = -distancey

    return distancex, distancey


activateTrigger = False
activateGlow = False
activateAimbot = False
key_press = False

while True:

    locaplayer = read_memory(game, (off_clientdll + off_localplayer), "i")
    myteam = read_memory(game, (locaplayer + off_teamnum), "i")
    incrosshair = read_memory(game, (locaplayer + off_incrosshair), "i")
    if incrosshair != 0:
        incrosshair_entity = read_memory(game, (off_clientdll + off_entitylist + ((incrosshair - 1) * 0x10)), "i")
        incrosshair_team = read_memory(game, (incrosshair_entity + off_teamnum), "i")

        if myteam != incrosshair_team:
            if win32api.GetAsyncKeyState(0x39) == False:
                ctypes.windll.user32.mouse_event(2, 0, 0, 0, 0)
                time.sleep(random.uniform(0.006, 0.017))
                ctypes.windll.user32.mouse_event(4, 0, 0, 0, 0)

    glowlocalplayer = read_memory(game, (off_clientdll + off_localplayer), "i")

    glowpointer = read_memory(game, (off_clientdll + off_glowobject), "i")

    glowteam = read_memory(game, (glowlocalplayer + off_teamnum), "i")

    for i in range(1, 64):

        player = read_memory(game, (off_clientdll + off_entitylist + ((i - 1) * 0x10)), "i")

        health = read_memory(game, (player + off_health), "i")

        glowteam_enemy = read_memory(game, (player + off_teamnum), "i")

        inject = read_memory(game, (player + off_glowindex), "i")

        if health > 0 and glowteam != glowteam_enemy:

            red = ((255 - 2.55 * health) / 255)
            if red > 1:
                red = 1.0
            green = ((2.55 * health) / 255)
            if green > 1.0:
                green = 1.0

            write_memory(game, (glowpointer + (inject * 0x38 + 0x4)), red, "f")
            write_memory(game, (glowpointer + (inject * 0x38 + 0x8)), green, "f")
            write_memory(game, (glowpointer + (inject * 0x38 + 0xC)), 0.0, "f")
            write_memory(game, (glowpointer + (inject * 0x38 + 0x10)), 0.8, "f")
            write_memory(game, (glowpointer + (inject * 0x38 + 0x24)), True, "c")

    oldoffpunchx = 0.0
    oldoffpunchy = 0.0

    # time.sleep(random.uniform(0.006, 0.017))
    aimlocalplayer = read_memory(game, (off_clientdll + off_localplayer), "i")

    aimteam = read_memory(game, (aimlocalplayer + off_teamnum), "i")
    enginepointer = read_memory(game, (off_enginedll + off_clientstate), "i")

    # if win32api.GetAsyncKeyState(0x01):  # 0x04 mouse3, 0x01 : mouse1
    for y in range(1, 64):

        aimplayer = read_memory(game, (off_clientdll + off_entitylist + ((y - 1) * 0x10)), "i")

        aimplayerteam = read_memory(game, (aimplayer + off_teamnum), "i")
        aimplayerhealth = read_memory(game, (aimplayer + off_health), "i")

        if aimplayerteam != aimteam and aimplayerhealth > 0:
            vecorigin = read_memory(game, (aimlocalplayer + off_vecorigin), "i")

            localpos1 = read_memory(game, (aimlocalplayer + off_vecorigin), "f") + read_memory(game, (
                        vecorigin + off_vecviewoffset + 0x104), "f")

            localpos2 = read_memory(game, (aimlocalplayer + off_vecorigin + 0x4), "f") + read_memory(game, (
                        vecorigin + off_vecviewoffset + 0x108), "f")

            localpos3 = read_memory(game, (aimlocalplayer + off_vecorigin + 0x8), "f") + read_memory(game, (
                        aimlocalplayer + 0x10C), "f")

            vecorigin = read_memory(game, (aimplayer + off_vecorigin), "i")
            aimplayerbones = read_memory(game, (aimplayer + off_bonematrix), "i")
            enemypos1 = read_memory(game, (aimplayerbones + 0x30 * aimbone + 0x0C), "f")
            enemypos2 = read_memory(game, (aimplayerbones + 0x30 * aimbone + 0x1C), "f")
            enemypos3 = read_memory(game, (aimplayerbones + 0x30 * aimbone + 0x2C), "f")
            targetline1 = enemypos1 - localpos1
            targetline2 = enemypos2 - localpos2
            targetline3 = enemypos3 - localpos3

            viewanglex = read_memory(game, (enginepointer + off_dwviewangle), "f")
            viewangley = read_memory(game, (enginepointer + off_dwviewangle + 0x4), "f")
            offpunchx = read_memory(game, (aimlocalplayer + off_aimpunch), "f")
            offpunchy = read_memory(game, (aimlocalplayer + off_aimpunch + 0x4), "f")

            if targetline2 == 0 and targetline1 == 0:
                yaw = 0
                if targetline3 > 0:
                    pitch = 270
                else:
                    pitch = 90
            else:
                yaw = (math.atan2(targetline2, targetline1) * 180 / math.pi) - (offpunchy * 2)
                if yaw < 0:
                    yaw += 360
                hypotenuse = math.sqrt(
                    (targetline1 * targetline1) + (targetline2 * targetline2) + (targetline3 * targetline3))
                pitch = (math.atan2(-targetline3, hypotenuse) * 180 / math.pi) - (offpunchx * 2)
                if pitch < 0:
                    pitch += 360

            pitch, yaw = normalizeAngles(pitch, yaw)
            if checkangles(pitch, yaw):

                distance_x, distance_y = calc_distance(viewanglex, viewangley, pitch, yaw)

                # lock at mouse3
                if (distance_x < aimfov and distance_y < aimfov and (win32api.GetAsyncKeyState(0x01))):

                    if nanchecker(pitch, yaw):
                        write_memory(game, (enginepointer + off_dwviewangle), pitch, "f")
                        write_memory(game, (enginepointer + (off_dwviewangle + 0x4)), yaw, "f")