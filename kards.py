import pyautogui
import pygetwindow as gw
import cv2
import numpy as np
import time
import datetime
import logging
import threading

# 定义卡牌图片文件路径
card_images = []#["card1.png", "card2.png", "card3.png"""]
#选派确认按钮
confirm_button_image = "confirm.png"
#主菜单按钮
main_menu_button_image = "mainButton.png"
#开始匹配按钮
start_battle_button_image = "startBattle.png"
#结束回合按钮
end_turn_button_image = "endTurn.png"
pass_turn_button_image = "clickedEndTurn.png"
opponent_turn_button_image = "opponent_turn_button.png"
clicked_start_game_button = "clickedstartBattle.png"
#人机对战
bot_battle_button_image = "renj.png"
#重新开始游戏
restart_button_image = "restart.png"
clicked_restart_button_image = "clickedRestart.png"
#外部开始菜单按钮
start_gameOut_button_image = "start_gameOut.png"
#主菜单开始按钮
main_menu_start_button_image = "mainMenuStart.png"
#被点击的主菜单按钮
clicked_main_menu_button_image = "clickedMainMenu.png"
#被鼠标指向的主菜单按钮
main_menu_start_button_middle_image = "mainMenuStartMidle.png"
#结算画面
continue_button_image = "continue.png"
#投降
surrender_button_image = "surrender.png"
#投降2
surrender2_button_image = "surrender2.png"
#退出按钮
exit_button_image = "exit.png"
clicked_exit_button_image = "clickedExit.png"
#好友模式准备按钮
friends_accept_button_image = "friendAccept.png"
#好友模式
friendsBattle_button_image = "friendsBattle.png"
#领取奖励
getReward_button_image = "getReward.png"
#可选开始页面“战斗”标识
In_Window_Main_Menu_Battle_image = "In_Window_Main_Menu_Battle.png"
#登录每日任务
daily_mission_button_image = "daily_mission.png"
#关闭结算广告
close_Ad_button_image = "closeAd.png"
#关闭战场回顾
leaveBattle_button_image = "leaveBattle.png"
#查看战场回顾
checkBattle_button_image = "checkBattle.png"
#敌方总部
enemy_headquarters_image = "enemy_headquarters.png"
#轰炸机
bomber_image = "bomber.png"
#战斗机
fighter_image = "fighter.png"
#迫击炮
mortar_image = "mortar.png"
#守护单位
guard_image = "guard.png"

#阵营识别范围
#我方支援阵线
pos_of_mine = (501, 733, 1704, 988)
#敌方支援阵线
pos_of_enemy = (437, 150, 1760, 397)
#出牌区
pos_of_hand_card = (550, 1037, 1725, pyautogui.size()[1])
#可以打出的牌的费用颜色
coast_color_True = (232, 180, 78)


#主页防检测模拟点击开关
swith = True
#投降开关
surrenderSwitch = False

def surrender():
     time.sleep(240)
     global surrenderSwitch
     surrenderSwitch = True
     surrender_button_pos = pyautogui.locateCenterOnScreen(surrender_button_image,confidence=0.7)
     pyautogui.moveTo(pyautogui.size()[0] // 2, pyautogui.size()[1] // 2)
     pyautogui.moveTo(surrender_button_pos, duration=0.5)
     pyautogui.click(surrender_button_pos)
     #pyautogui.click(surrender_button_pos)
     time.sleep(0.5)
     surrender2_button_pos = pyautogui.locateCenterOnScreen(surrender2_button_image,confidence=0.7)
     pyautogui.moveTo(surrender2_button_pos,duration=0.3)
     pyautogui.click(surrender2_button_pos)
     #pyautogui.click(surrender2_button_pos)
     surrenderSwitch = False
     time.sleep(0.5)


# 函数：在游戏开始前点击确认按钮
def click_confirm_button():
    #game_window = gw.getWindowsWithTitle("kards  ")[0]
    #game_window.activate()  # 激活游戏窗口
    confirm_button_pos = pyautogui.locateCenterOnScreen(confirm_button_image)
    if confirm_button_pos:
        pyautogui.moveTo(pyautogui.size()[0] // 2, pyautogui.size()[1] // 2)
        pyautogui.moveTo(confirm_button_pos, duration=0.5)
        #time.sleep(1)
        pyautogui.click(confirm_button_pos)
        #print(str(now)+"点击了确认按钮")
        #time.sleep(3)  # 等待一段时间确保动作完成
        #投降计时
        request_thread = threading.Thread(target=surrender)
        request_thread.start()
        return True
    else:
        #print("未找到确认按钮")
        return False

# 函数：在游戏开始前点击开始游戏按钮
def click_start_game_button():
    #game_window = gw.getWindowsWithTitle("kards  ")[0]
    #game_window.activate()  # 激活游戏窗口
    main_menu_button_pos = pyautogui.locateCenterOnScreen(main_menu_button_image)
    friends_battle_pos = pyautogui.locateCenterOnScreen(friendsBattle_button_image)
    if main_menu_button_pos or friends_battle_pos:
        #pyautogui.click(main_menu_button_pos)
        #print("点击了主菜单按钮")
        ##time.sleep(1)  # 等待一段时间确保动作完成
        start_battle_button_pos = pyautogui.locateCenterOnScreen(start_battle_button_image,confidence=0.7)
        clciked_start_game_button_pos = pyautogui.locateCenterOnScreen(clicked_start_game_button,confidence=0.7)
        #friends_accept_button_pos = pyautogui.locateCenterOnScreen(friends_accept_button_image)
        if start_battle_button_pos :
            pyautogui.moveTo(pyautogui.size()[0] // 2, pyautogui.size()[1] // 2)
            #pyautogui.moveTo(start_game_button_pos, duration=0.5)
            pyautogui.moveTo(start_battle_button_pos, duration=0.5)
            #pyautogui.moveTo(friends_accept_button_pos, duration=0.5)
            #time.sleep(1)
            pyautogui.click(start_battle_button_pos)
            pyautogui.click(start_battle_button_pos)
            pyautogui.click(clciked_start_game_button_pos)
            pyautogui.click(clciked_start_game_button_pos)
            #pyautogui.click(friends_accept_button_pos)
            #pyautogui.click(friends_accept_button_pos)
            #print(str(now)+"点击了开始游戏按钮")
            #time.sleep(1)
            # 等待出现确认按钮，最长等待时间2分钟
            start_time = time.time()
            while time.time() - start_time < 120 and not (pyautogui.locateCenterOnScreen(start_battle_button_image) or pyautogui.locateCenterOnScreen(friends_accept_button_image)):
                bot_battle_button_pos = pyautogui.locateCenterOnScreen(bot_battle_button_image)
                if bot_battle_button_pos:
                    pyautogui.moveTo(pyautogui.size()[0] // 2, pyautogui.size()[1] // 2)
                    pyautogui.moveTo(bot_battle_button_pos, duration=0.5)
                    #time.sleep(1)
                    pyautogui.click(bot_battle_button_pos)
                    pyautogui.click(bot_battle_button_pos)
                if click_confirm_button():
                    break
                #time.sleep(1)
            else:
                #print("超过等待时间未找到确认按钮，重新开始...")
                return False
        else:
            #print("未找到开始游戏按钮")
            return False
    else:
        #print("未找到主菜单按钮")
        return False
    return True

# 函数：点击结束回合按钮
def click_end_turn_button():
    #game_window = gw.getWindowsWithTitle("kards  ")[0]
    #game_window.activate()  # 激活游戏窗口
    #pyautogui.moveTo(pyautogui.size()[0] // 2, pyautogui.size()[1] // 2)
    #pyautogui.dragTo(end_turn_button_image, duration=0.5)
    end_turn_button_pos = pyautogui.locateCenterOnScreen(end_turn_button_image,confidence=0.7)
    if end_turn_button_pos:
        play_cards()
        pyautogui.moveTo(pyautogui.size()[0] // 2, pyautogui.size()[1] // 2)
        pyautogui.moveTo(end_turn_button_pos, duration=0.5)
        pyautogui.click(end_turn_button_pos)
        #pyautogui.moveTo(pyautogui.size()[0] // 2, pyautogui.size()[1] // 2)
        #print(str(now)+"点击了结束回合按钮")
        #time.sleep(1)  # 等待一段时间确保动作完成
        #pyautogui.click(pyautogui.size()[0] // 2, pyautogui.size()[1] // 2)
        while pyautogui.locateCenterOnScreen(opponent_turn_button_image, confidence=0.7) and not pyautogui.locateCenterOnScreen(end_turn_button_image,confidence=0.7) and not pyautogui.locateCenterOnScreen(pass_turn_button_image,confidence=0.7):
            #print(str(now)+"等待对手回合...")
            time.sleep(1)
        #print(str(now)+"对手回合结束，继续出牌逻辑")
        #time.sleep(1)
    #else:
    #    print("未找到结束回合按钮")

# 函数：点击空过按钮
def click_pass_button():
    #game_window = gw.getWindowsWithTitle("kards  ")[0]
    #game_window.activate()  # 激活游戏窗口
    pass_button_pos = pyautogui.locateCenterOnScreen(pass_turn_button_image,confidence=0.7)
    if pyautogui.locateCenterOnScreen(pass_turn_button_image,confidence=0.7):
        play_cards()
        #time.sleep(1)
        pyautogui.moveTo(pyautogui.size()[0] // 2, pyautogui.size()[1] // 2)
        pyautogui.moveTo(pass_button_pos, duration=0.5)
        #time.sleep(1)
        pyautogui.click(pass_button_pos)
        pyautogui.click(pass_button_pos)
        #pyautogui.moveTo(pyautogui.size()[0] // 2, pyautogui.size()[1] // 2)
        #print(str(now)+"点击了空过按钮")
        #让等待只输出一次
        switch = True
        while pyautogui.locateCenterOnScreen(opponent_turn_button_image, confidence=0.7) and not pyautogui.locateCenterOnScreen(end_turn_button_image,confidence=0.7) and not pyautogui.locateCenterOnScreen(pass_turn_button_image,confidence=0.7):
            if switch:
                #print(str(now)+"等待对手回合...")
                switch = False
            #time.sleep(1)
        #print(str(now)+"对手回合结束，继续出牌逻辑")
        #time.sleep(1)  # 等待一段时间确保动作完成
    else:
        click_end_turn_button()
        #print("未找到空过按钮")

#按相对位置计算场上每张卡牌的费用区域
def coast(x,y):
    region_top = (x-91,y-206)
    region_bottom = (region_top[0]+30,region_top[1]+45)
    region = (region_top[0],region_top[1],region_bottom[0],region_bottom[1])
    return region

# 函数：从手牌中打出指定卡牌
def play_cards():
    #time.sleep(1)
    global coast_color_True
    global pos_of_mine
    global pos_of_enemy
    bomber_pos = pyautogui.locateOnScreen(bomber_image, confidence=0.9, region=pos_of_mine)
    mortar_pos = pyautogui.locateOnScreen(mortar_image, confidence=0.9, region=pos_of_mine)
    enemy_headquarters_pos = pyautogui.locateCenterOnScreen(enemy_headquarters_image, confidence=0.94 , region=(0,0,pyautogui.size()[0],pyautogui.size()[1] // 2))
    #检测支援阵线是否有可出兵
    #卡牌费用区域

    #出牌逻辑（场上随从攻击部分）
    if bomber_pos or mortar_pos:
        #轰炸机逻辑
        #mine_bomber = pyautogui.locateAllOnScreen(bomber_image, confidence=0.9, region=pos_of_mine)
        for posBomber in pyautogui.locateAllOnScreen(bomber_image, confidence=0.9, region=pos_of_mine):
            #检查费用是否可用
            #coast_tmp = pyautogui.screenshot(region=(coast(posBomber[0],posBomber[1])))
            #for x in range(coast_tmp.width):
                #for y in range(coast_tmp.height):
                    #if pyautogui.pixelMatchesColor(x, y, (coast_color_True), tolerance=10):
                        enemy_fighter_pos = pyautogui.locateCenterOnScreen(fighter_image, confidence=0.9, region=pos_of_enemy)
                        if enemy_fighter_pos:
                            pyautogui.click(posBomber)
                            pyautogui.dragTo(enemy_fighter_pos, duration=0.5)
                        else:
                            pyautogui.click(posBomber)
                            pyautogui.dragTo(enemy_headquarters_pos, duration=0.5)
                        #break
                        time.sleep(0.5)
        #迫击炮逻辑
        #mine_posortar = pyautogui.locateAllOnScreen(mortar_image, confidence=0.9, region=pos_of_mine)
        for posortar in pyautogui.locateAllOnScreen(mortar_image, confidence=0.9, region=pos_of_mine):
            #coast_tmp = pyautogui.screenshot(region=(coast(posortar[0],posortar[1])))
            #for x in range(coast_tmp.width):
                #for y in range(coast_tmp.height):
                    #if pyautogui.pixelMatchesColor(x, y, (coast_color_True), tolerance=10):
                        pyautogui.click(posortar)
                        pyautogui.dragTo(enemy_headquarters_pos, duration=0.5)
                        #break
                        time.sleep(0.5)
    # 假设有6张卡牌需要出牌
    enemy_headquarters_pos = pyautogui.locateCenterOnScreen(enemy_headquarters_image, confidence=0.94 , region=(0,0,pyautogui.size()[0],pyautogui.size()[1] // 2))
    if pyautogui.locateCenterOnScreen(pass_turn_button_image,confidence=0.7) or pyautogui.locateCenterOnScreen(end_turn_button_image,confidence=0.7):
        #hand_card = pyautogui.locateAllOnScreen()
        for i in range(6):
            # 假设卡牌初始位置在屏幕底部，依次点击并拖拽到屏幕中央
            pyautogui.click(x=800 + i * 100, y=pyautogui.size()[1]-100)  # 假设卡牌之间的间距为100像素
            #pyautogui.dragTo(1100, 300, duration=0.5)  # 将卡牌拖动到屏幕中央
            pyautogui.dragTo(enemy_headquarters_pos, duration=0.5)
            time.sleep(0.5)  # 等待一段时间模拟打出牌的动作
            #print(f"打出了第 {i+1} 张卡牌")
            #出兵逻辑（没做完）
        time.sleep(0.5)
            #战斗机逻辑
        #mine_fighter = pyautogui.locateAllOnScreen(fighter_image, confidence=0.9, region=pos_of_mine)
    bomber_pos = pyautogui.locateOnScreen(bomber_image, confidence=0.9, region=pos_of_mine)
    fighter_pos = pyautogui.locateOnScreen(fighter_image, confidence=0.9, region=pos_of_mine)
    if fighter_pos or bomber_pos:
        for posfighter in pyautogui.locateAllOnScreen(fighter_image, confidence=0.9, region=pos_of_mine):
            #coast_tmp = pyautogui.screenshot(region=(coast(posfighter[0],posfighter[1])))
            #for x in range(coast_tmp.width):
                #for y in range(coast_tmp.height):
                    #if pyautogui.pixelMatchesColor(x, y, (coast_color_True), tolerance=10):
                        #enemy_guard_pos = pyautogui.locateCenterOnScreen(guard_image, confidence=0.9, region=pos_of_enemy)
                        #if enemy_guard_pos:
                            #pyautogui.click(posfighter)
                            #pyautogui.dragTo(enemy_guard_pos, duration=0.5)
                        #else:
                            pyautogui.click(posfighter)
                            pyautogui.dragTo(enemy_headquarters_pos, duration=0.5)
                        #break
                            time.sleep(0.5)
        for posBomber in pyautogui.locateAllOnScreen(bomber_image, confidence=0.9, region=pos_of_mine):
            #检查费用是否可用
            #coast_tmp = pyautogui.screenshot(region=(coast(posBomber[0],posBomber[1])))
            #for x in range(coast_tmp.width):
                #for y in range(coast_tmp.height):
                    #if pyautogui.pixelMatchesColor(x, y, (coast_color_True), tolerance=10):
                        enemy_fighter_pos = pyautogui.locateCenterOnScreen(fighter_image, confidence=0.9, region=pos_of_enemy)
                        if enemy_fighter_pos:
                            pyautogui.click(posBomber)
                            pyautogui.dragTo(enemy_fighter_pos, duration=0.5)
                        else:
                            pyautogui.click(posBomber)
                            pyautogui.dragTo(enemy_headquarters_pos, duration=0.5)
                        #break
                        time.sleep(0.5)

def restart():
    restart_button_pos = pyautogui.locateCenterOnScreen(restart_button_image,confidence=0.7)
    clicked_restart_button_pos = pyautogui.locateCenterOnScreen(clicked_restart_button_image,confidence=0.7)
    if restart_button_pos :
        pyautogui.moveTo(pyautogui.size()[0] // 2, pyautogui.size()[1] // 2)
        pyautogui.moveTo(restart_button_pos, duration=0.5)
        #time.sleep(1)
        pyautogui.click(restart_button_pos)
        pyautogui.click(restart_button_pos)
        print(str(datetime.datetime.now())+"点击了重启按钮")
    elif clicked_restart_button_pos:
        pyautogui.moveTo(pyautogui.size()[0] // 2, pyautogui.size()[1] // 2)
        pyautogui.moveTo(clicked_restart_button_pos, duration=0.5)
        #time.sleep(1)
        pyautogui.click(clicked_restart_button_pos)
        pyautogui.click(clicked_restart_button_pos)
        print(str(datetime.datetime.now())+"点击了重启按钮")
       
def exit():
    exit_button_pos = pyautogui.locateCenterOnScreen(exit_button_image,confidence=0.7)
    #clicked_exit_button_pos = pyautogui.locateCenterOnScreen(clicked_exit_button_image,confidence=0.77)
    if exit_button_pos:
        pyautogui.moveTo(pyautogui.size()[0] // 2, pyautogui.size()[1] // 2)
        pyautogui.moveTo(exit_button_pos, duration=0.5)
        #time.sleep(1)
        pyautogui.click(exit_button_pos)
        pyautogui.click(exit_button_pos)
        print(str(datetime.datetime.now())+"点击了退出游戏按钮")
    '''
    elif clicked_exit_button_pos:
        pyautogui.moveTo(pyautogui.size()[0] // 2, pyautogui.size()[1] // 2)
        pyautogui.moveTo(clicked_exit_button_pos, duration=0.5)
        pyautogui.click(clicked_exit_button_pos)
        print(str(now)+"点击了退出游戏按钮")
    '''

def startGameOut():
    start_gameOut_button_pos = pyautogui.locateCenterOnScreen(start_gameOut_button_image,confidence=0.7)
    #clicked_start_gameOut_button_pos = pyautogui.locateCenterOnScreen(clicked_start_gameOut_button_image,confidence=0.7)
    if start_gameOut_button_pos:
        pyautogui.moveTo(pyautogui.size()[0] // 2, pyautogui.size()[1] // 2)
        pyautogui.moveTo(start_gameOut_button_pos, duration=0.5)
        #time.sleep(1)
        pyautogui.click(start_gameOut_button_pos)
        pyautogui.click(start_gameOut_button_pos)
        print(str(datetime.datetime.now())+"从外部点击了开始游戏按钮")

    #time.sleep(30)
    #pyautogui.click(pyautogui.size()[0] // 2, pyautogui.size()[1] // 2)
    #if clicked_start_gameOut_button_pos:
    #    pyautogui.moveTo(pyautogui.size()[0] // 2, pyautogui.size()[1] // 2)
    #    pyautogui.moveTo(clicked_start_gameOut_button_pos, duration=0.5)
    #    pyautogui.click(clicked_start_gameOut_button_pos)
    #    print("从外部点击了开始游戏按钮")

def mainMenu():
    main_menu_start_button_pos = pyautogui.locateCenterOnScreen(main_menu_start_button_image, confidence=0.7)
    clicked_main_menu_button_pos = pyautogui.locateCenterOnScreen(clicked_main_menu_button_image, confidence=0.7)
    main_menu_start_button_middle_pos = pyautogui.locateCenterOnScreen(main_menu_start_button_middle_image, confidence=0.7)
    #In_Window_Main_Menu_Battle_pos = pyautogui.locateCenterOnScreen(In_Window_Main_Menu_Battle_image, confidence=0.75)
    #如果主菜单按钮处于被选中状态则切换到开始按钮
    if clicked_main_menu_button_pos :
        pyautogui.moveTo(pyautogui.size()[0] // 2, pyautogui.size()[1] // 2)
        pyautogui.moveTo(main_menu_start_button_pos, duration=0.5)
        #time.sleep(1)
        pyautogui.click(main_menu_start_button_pos)
        #pyautogui.click(main_menu_start_button_pos)
        pyautogui.click(main_menu_start_button_middle_pos)
        print(str(datetime.datetime.now())+"点击了主菜单开始按钮")
    #time.sleep(1)  # 等待一段时间确保动作完成
        
def dailyMission():
    daily_mission_button_pos = pyautogui.locateCenterOnScreen(daily_mission_button_image,confidence=0.7)
    if daily_mission_button_pos:
        pyautogui.moveTo(pyautogui.size()[0] // 2, pyautogui.size()[1] // 2)
        pyautogui.moveTo(pyautogui.size()[0] // 2 + 30, 1150, duration=0.5)
        pyautogui.click(pyautogui.size()[0] // 2 + 30, 1150)

# 主循环，模拟游戏操作
def main():
    time.sleep(10)
    while True:
        while not surrenderSwitch:
            # 点击结束回合按钮
            #click_end_turn_button()
            #time.sleep(1)  # 等待对手出牌
            #game_window = gw.getWindowsWithTitle("kards  ")[0]
            #game_window.activate()  # 激活游戏窗口
            #time.sleep(1)
            # 点击空过按钮

            startGameOut()

            dailyMission()

            mainMenu()
            
            restart()

            exit()

            click_pass_button()

            #click_end_turn_button()

            #else:
                #click_end_turn_button()  # 如果所有卡牌都无法打出，则点击结束回合按钮
            if pyautogui.locateCenterOnScreen(continue_button_image, confidence=0.7):
            # 如果三个按钮都找不到，则连续点击游戏屏幕中间，直到出现主菜单按钮
            # 设置超时时间为30秒
                continue_button_pos = pyautogui.locateCenterOnScreen(continue_button_image, confidence=0.7)
                if pyautogui.locateCenterOnScreen(checkBattle_button_image):
                    checkBattle_button_pos = pyautogui.locateCenterOnScreen(checkBattle_button_image)
                    pyautogui.moveTo(pyautogui.size()[0] // 2, pyautogui.size()[1] // 2)
                    pyautogui.moveTo(checkBattle_button_pos, duration=0.5)
                    time.sleep(0.5)
                while pyautogui.locateCenterOnScreen(continue_button_image, confidence=0.7):
                    pyautogui.moveTo(100, pyautogui.size()[1] // 2)
                    pyautogui.moveTo(2000, pyautogui.size()[1] // 2, duration=0.5)
                    pyautogui.moveTo(pyautogui.size()[0] // 2 + 30, 1150, duration=0.5)
                    #time.sleep(1)
                    #pyautogui.click(pyautogui.size()[0] // 2 + 30, 1150)
                    #pyautogui.click(pyautogui.size()[0] // 2 + 30, 1150)
                    #pyautogui.moveTo(continue_button_pos, duration=0.5)
                    pyautogui.click(continue_button_pos)
                    time.sleep(3)  # 间隔1秒点击一次
            elif pyautogui.locateCenterOnScreen(getReward_button_image, confidence=0.7):
                getReward_button_pos = pyautogui.locateCenterOnScreen(getReward_button_image, confidence=0.7)
                pyautogui.moveTo(100, pyautogui.size()[1] // 2)
                pyautogui.moveTo(2000, pyautogui.size()[1] // 2, duration=0.5)
                #time.sleep(1)
                #pyautogui.moveTo(getReward_button_image, duration=0.5)
                pyautogui.moveTo(pyautogui.size()[0] // 2 + 30, 1150, duration=0.5)
                pyautogui.click(getReward_button_pos)
            elif pyautogui.locateCenterOnScreen(close_Ad_button_image):
                close_Ad_button_pos = pyautogui.locateCenterOnScreen(close_Ad_button_image)
                while pyautogui.locateCenterOnScreen(close_Ad_button_image):
                    pyautogui.moveTo(pyautogui.size()[0] // 2, pyautogui.size()[1] // 2)
                    #time.sleep(1)
                    #pyautogui.moveTo(getReward_button_image, duration=0.5)
                    pyautogui.moveTo(close_Ad_button_pos, duration=0.5)
                    pyautogui.click(close_Ad_button_pos)
                    time.sleep(3)
            elif pyautogui.locateCenterOnScreen(leaveBattle_button_image):
                leaveBattle_button_pos = pyautogui.locateCenterOnScreen(leaveBattle_button_image)
                pyautogui.moveTo(pyautogui.size()[0] // 2, pyautogui.size()[1] // 2)
                #time.sleep(1)
                #pyautogui.moveTo(getReward_button_image, duration=0.5)
                pyautogui.moveTo(leaveBattle_button_pos, duration=0.5)
                pyautogui.click(leaveBattle_button_pos)
            # 查找主菜单按钮并继续循环
            if not click_start_game_button():
                continue

if __name__ == "__main__":
    main()