# -*- coding: utf-8 -*-
"""
KardsAFK4EXP —— KARDS 自动挂机脚本（图像识别 + 键鼠模拟）

原始版本：https://github.com/  （trash team made trash game, good job 1939）
本版本：修复了原始版本中会导致「脚本永久停摆 / 崩溃 / 满核空转 / 区域错位」的
        若干致命缺陷，并补齐日志与容错。详见 CHANGELOG.md 与 docs/逻辑解读.md

运行前提（与原始版本一致）：
    1. 游戏分辨率 2220x1271，窗口化 / 无边框
    2. 游戏内语言中文，官方启动器语言英文（用于「外部开始游戏」按钮识别）
    3. pip install -r requirements.txt
"""

import datetime
import logging
import random
import threading
import time

import pyautogui
import pygetwindow as gw  # noqa: F401  （保留：扩展窗口激活逻辑时使用）

# ---------------------------------------------------------------------------
# 日志：原始版本只 import 了 logging 却从未使用，出问题只能靠肉眼盯屏幕。
# ---------------------------------------------------------------------------
LOG_FILE = "kards.log"
log = logging.getLogger("kards")
log.setLevel(logging.INFO)
if not log.handlers:
    _fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S")
    _fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    _fh.setFormatter(_fmt)
    _sh = logging.StreamHandler()
    _sh.setFormatter(_fmt)
    log.addHandler(_fh)
    log.addHandler(_sh)

# ---------------------------------------------------------------------------
# 配置区：原始版本把这些数字散落在函数体里，改分辨率就得全文搜索。
# 坐标系说明：BOX_* 一律是 (x1, y1, x2, y2) 的「左上角 + 右下角」语义，
# 使用时必须经 to_region() 转成 pyautogui 需要的 (x, y, width, height)。
#                  ↑ 这就是原始版本最隐蔽的一个 bug，见 CHANGELOG Bug#5
# ---------------------------------------------------------------------------

# --- 图像资源文件名 ---
CONFIRM_IMG = "confirm.png"                      # 出战/选派确认
MAIN_MENU_BTN_IMG = "mainButton.png"             # 主菜单按钮
START_BATTLE_IMG = "startBattle.png"             # 开始匹配
CLICKED_START_BATTLE_IMG = "clickedstartBattle.png"  # 已点击态的开始匹配
END_TURN_IMG = "endTurn.png"                     # 结束回合
PASS_TURN_IMG = "clickedEndTurn.png"             # 空过（已点击态的结束回合）
OPPONENT_TURN_IMG = "opponent_turn_button.png"   # 对手回合中标识
BOT_BATTLE_IMG = "renj.png"                      # 人机对战
RESTART_IMG = "restart.png"                      # 重连/重新开始
CLICKED_RESTART_IMG = "clickedRestart.png"
START_GAME_OUT_IMG = "start_gameOut.png"         # 启动器上的开始按钮
MAIN_MENU_START_IMG = "mainMenuStart.png"        # 主菜单「开始」
CLICKED_MAIN_MENU_IMG = "clickedMainMenu.png"    # 主菜单「开始」被选中态
MAIN_MENU_START_MID_IMG = "mainMenuStartMidle.png"
CONTINUE_IMG = "continue.png"                    # 结算 → 继续
SURRENDER_IMG = "surrender.png"                  # 投降
SURRENDER2_IMG = "surrender2.png"                # 投降二次确认
EXIT_IMG = "exit.png"                            # 退出游戏
FRIEND_ACCEPT_IMG = "friendAccept.png"           # 好友对战准备
FRIENDS_BATTLE_IMG = "friendsBattle.png"         # 好友对战界面
GET_REWARD_IMG = "getReward.png"                 # 领取奖励
DAILY_MISSION_IMG = "daily_mission.png"          # 每日任务红点
CLOSE_AD_IMG = "closeAd.png"                     # 关闭结算广告
LEAVE_BATTLE_IMG = "leaveBattle.png"             # 离开战场回顾
CHECK_BATTLE_IMG = "checkBattle.png"             # 战场回顾（仅悬停消 tooltip）
ENEMY_HQ_IMG = "enemy_headquarters.png"          # 敌方总部
BOMBER_IMG = "bomber.png"                        # 轰炸机
FIGHTER_IMG = "fighter.png"                      # 战斗机
MORTAR_IMG = "mortar.png"                        # 迫击炮
GUARD_IMG = "guard.png"                          # 守护单位（当前未启用）

# --- 识别置信度（集中管理，避免同一种图在不同地方用不同阈值）---
CONF_STRICT = 0.90   # 场上单位
CONF_LOOSE = 0.70    # UI 按钮

# --- 识别区域，(x1, y1, x2, y2)，基于 2220x1271 ---
BOX_MINE = (501, 733, 1704, 988)        # 我方支援阵线
BOX_ENEMY = (437, 150, 1760, 397)       # 敌方支援阵线

# --- 手牌盲打的点击位置 ---
HAND_CARD_COUNT = 6
HAND_CARD_X0 = 800
HAND_CARD_DX = 100
HAND_CARD_Y_OFFSET = 100                # 距屏幕底部

# --- 时序 ---
SURRENDER_DELAY = 240                   # 开局后多少秒自动投降（4 分钟经验封顶）
SURRENDER_SETTLE = 2.0                  # 置位后等主循环手头动作做完
WAIT_CONFIRM_TIMEOUT = 120              # 等「确认」按钮出现的超时
WAIT_OPPONENT_TIMEOUT = 180             # 等对手回合结束的超时（防止死等）
MAIN_LOOP_PAUSE = 0.2                   # 主循环空转间隔
POLL_INTERVAL = 0.3                     # 状态轮询间隔

# --- 行为 ---
HUMANIZE = True                         # 点击加随机抖动/延迟，降低机械特征
HUMAN_JITTER = 3                        # 抖动像素半径
MOVE_DURATION = 0.5                     # 鼠标移动耗时

# --- 开关 ---
SURRENDER_ENABLED = True                # README：关闭可防封但升级效率暴跌


# ---------------------------------------------------------------------------
# 兼容层：pyautogui 0.9.54 + pyscreeze 0.1.29 找不到图时返回 None；
# 而 pyautogui >=0.9.55 + pyscreeze >=1.0 会抛 ImageNotFoundException。
# 原始版本只考虑了前者，换个环境就整个脚本崩掉。
# ---------------------------------------------------------------------------
_IMAGE_NOT_FOUND = getattr(pyautogui, "ImageNotFoundException", None)


def _safe_locate(func, image, **kwargs):
    """统一吞掉「找不到图」这一预期内异常，其余异常照常抛出让日志记录。"""
    try:
        return func(image, **kwargs)
    except Exception as exc:  # noqa: BLE001
        if _IMAGE_NOT_FOUND is not None and isinstance(exc, _IMAGE_NOT_FOUND):
            return None
        if isinstance(exc, (FileNotFoundError, OSError)):
            log.warning("图像资源缺失或不可读: %s", image)
            return None
        raise


def find_center(image, confidence=CONF_LOOSE, region=None):
    """locateCenterOnScreen 的安全包装，找不到返回 None。"""
    return _safe_locate(
        pyautogui.locateCenterOnScreen, image, confidence=confidence, region=region
    )


def find_all(image, confidence=CONF_STRICT, region=None):
    """locateAllOnScreen 的安全包装，返回 list（原始版本直接迭代生成器，
    边迭代边点击会导致后续坐标失效指向错误目标）。"""
    found = _safe_locate(
        pyautogui.locateAllOnScreen, image, confidence=confidence, region=region
    )
    return list(found) if found else []


def find_on(image, confidence=CONF_STRICT, region=None):
    """locateOnScreen，返回 Box 或 None（仅用于判断存在性）。"""
    return _safe_locate(
        pyautogui.locateOnScreen, image, confidence=confidence, region=region
    )


def to_region(box):
    """把 (x1, y1, x2, y2) 转成 pyautogui 需要的 (x, y, width, height)。
    pyautogui 的 region 第 3/4 个参数是「宽/高」不是「右下角坐标」，
    原始版本直接把右下角塞了进去，导致识别区域被放大约 4 倍，
    甚至把下方手牌区也框了进来。"""
    x1, y1, x2, y2 = box
    sw, sh = pyautogui.size()
    x1 = max(0, min(int(x1), sw - 1))
    y1 = max(0, min(int(y1), sh - 1))
    x2 = max(x1 + 1, min(int(x2), sw))
    y2 = max(y1 + 1, min(int(y2), sh))
    return (x1, y1, x2 - x1, y2 - y1)


# ---------------------------------------------------------------------------
# 线程状态
# ---------------------------------------------------------------------------
surrender_event = threading.Event()   # ← 替代原始版本裸奔的全局 bool
_surrender_guard = threading.Lock()   # 防止同时起多个投降线程
_surrender_pending = False


def start_surrender_timer():
    """开局确认后启动 4 分钟投降计时。原始版本每次点确认都会新起一个线程，
    若上一局线程还没跑完会堆叠出多个投降线程互相抢鼠标。"""
    global _surrender_pending
    if not SURRENDER_ENABLED:
        return
    with _surrender_guard:
        if _surrender_pending:
            log.info("投降计时已在进行中，跳过重复启动")
            return
        _surrender_pending = True
    t = threading.Thread(target=surrender, name="surrender", daemon=True)
    t.start()
    log.info("投降计时启动，%d 秒后自动投降", SURRENDER_DELAY)


# ---------------------------------------------------------------------------
# 键鼠动作
# ---------------------------------------------------------------------------
def human_move(pos, duration=MOVE_DURATION):
    """把鼠标移过去。HUMANIZE 开启时加一点随机抖动。"""
    if pos is None:
        return False
    x, y = int(pos[0]), int(pos[1])
    sw, sh = pyautogui.size()
    pyautogui.moveTo(sw // 2, sh // 2)          # 原始版本用来「模拟真人」的回中
    if HUMANIZE:
        x += random.randint(-HUMAN_JITTER, HUMAN_JITTER)
        y += random.randint(-HUMAN_JITTER, HUMAN_JITTER)
        duration = duration * random.uniform(0.85, 1.15)
    pyautogui.moveTo(x, y, duration=duration)
    return True


def human_click(pos, clicks=1, interval=0.05):
    """移动到 pos 并点击。pos 为 None 时安全跳过——
    原始版本出现过 pyautogui.click(None) 直接抛 TypeError 的情况。"""
    if pos is None or not human_move(pos):
        return False
    pyautogui.click(pos, clicks=clicks, interval=interval)
    return True


# ---------------------------------------------------------------------------
# 投降（后台线程）
# ---------------------------------------------------------------------------
def surrender():
    """4 分钟后自动投降。

    原始版本的致命写法：
        surrenderSwitch = True
        pos = locateCenterOnScreen("surrender.png", confidence=0.7)
        pyautogui.click(pos)          # pos 为 None → TypeError
    线程带着异常死掉，而 surrenderSwitch 永远停在 True，
    主循环 `while not surrenderSwitch` 从此永久空转 → 脚本静默停摆。
    这里用 try/finally 保证事件一定被清掉。
    """
    global _surrender_pending
    try:
        time.sleep(SURRENDER_DELAY)
        surrender_event.set()
        time.sleep(SURRENDER_SETTLE)          # 让主循环手头的拖拽动作收尾

        pos = find_center(SURRENDER_IMG, CONF_LOOSE)
        if pos is None:
            log.warning("未找到投降按钮，本局放弃投降（主循环继续）")
            return
        log.info("点击投降按钮")
        human_click(pos)
        time.sleep(0.5)

        pos2 = find_center(SURRENDER2_IMG, CONF_LOOSE)
        if pos2 is None:
            log.warning("未找到投降二次确认按钮")
            return
        human_move(pos2, duration=0.3)
        pyautogui.click(pos2)
        log.info("投降完成")
        time.sleep(0.5)
    except Exception:  # noqa: BLE001
        log.exception("投降流程异常")
    finally:
        surrender_event.clear()
        with _surrender_guard:
            _surrender_pending = False


# ---------------------------------------------------------------------------
# 开局
# ---------------------------------------------------------------------------
def click_confirm_button():
    """点「确认」，并在成功后启动投降计时。"""
    pos = find_center(CONFIRM_IMG)
    if pos is None:
        return False
    human_click(pos)
    start_surrender_timer()
    return True


def click_start_game_button():
    """主菜单 → 匹配 → 人机对战 → 确认。返回是否成功进入等待确认流程。"""
    main_menu_pos = find_center(MAIN_MENU_BTN_IMG)
    friends_battle_pos = find_center(FRIENDS_BATTLE_IMG)
    if not (main_menu_pos or friends_battle_pos):
        return False

    start_pos = find_center(START_BATTLE_IMG)
    if start_pos is None:
        return False

    clicked_start_pos = find_center(CLICKED_START_BATTLE_IMG)
    human_move(start_pos)
    pyautogui.click(start_pos)
    pyautogui.click(start_pos)
    # 原始版本这里没判空就 pyautogui.click(clicked_start_pos) → 崩溃点
    if clicked_start_pos is not None:
        pyautogui.click(clicked_start_pos)
        pyautogui.click(clicked_start_pos)

    start_ts = time.time()
    while time.time() - start_ts < WAIT_CONFIRM_TIMEOUT:
        # 原始版本的判断方向是「还没离开对战选择界面就跳出」：
        # 一旦 startBattle / friendAccept 仍然可见，说明匹配还没开始。
        if find_center(START_BATTLE_IMG) or find_center(FRIEND_ACCEPT_IMG):
            log.info("仍停留在对战选择界面，等待匹配")
            return False
        bot_pos = find_center(BOT_BATTLE_IMG)
        if bot_pos is not None:
            human_move(bot_pos)
            pyautogui.click(bot_pos)
            pyautogui.click(bot_pos)
        if click_confirm_button():
            return True
        time.sleep(POLL_INTERVAL)

    log.warning("等待确认按钮超时 %ds，重试", WAIT_CONFIRM_TIMEOUT)
    return False


# ---------------------------------------------------------------------------
# 回合内：出牌 / 结束回合
# ---------------------------------------------------------------------------
def _bomber_strike(bomber_pos, enemy_hq_pos):
    """轰炸机：优先打敌方战斗机，否则打总部。"""
    enemy_fighter = find_center(FIGHTER_IMG, CONF_STRICT, region=to_region(BOX_ENEMY))
    target = enemy_fighter or enemy_hq_pos
    if target is None:
        return
    pyautogui.click(bomber_pos)
    pyautogui.dragTo(target, duration=MOVE_DURATION)
    time.sleep(0.5)


def _mortar_strike(mortar_pos, enemy_hq_pos):
    """迫击炮：直接打总部。"""
    if enemy_hq_pos is None:
        return
    pyautogui.click(mortar_pos)
    pyautogui.dragTo(enemy_hq_pos, duration=MOVE_DURATION)
    time.sleep(0.5)


def _fighter_strike(fighter_pos, enemy_hq_pos):
    """战斗机：直冲总部。"""
    if enemy_hq_pos is None:
        return
    pyautogui.click(fighter_pos)
    pyautogui.dragTo(enemy_hq_pos, duration=MOVE_DURATION)
    time.sleep(0.5)


def play_cards():
    """「出牌」逻辑。

    注意：这并不是一个真正的 AI——不认费用、不认卡牌效果、不区分
    「部署到己方阵线」和「攻击敌方目标」，所以胜率很低，
    它的设计目标是「把对局拖到 4 分钟拿经验」而不是赢。
    费用检测（coast / coast_color_True）在仓库里是死代码，见 CHANGELOG 待办。
    """
    region_mine = to_region(BOX_MINE)
    hq_region = to_region((0, 0, pyautogui.size()[0], pyautogui.size()[1] // 2))

    enemy_hq_pos = find_center(ENEMY_HQ_IMG, 0.94, region=hq_region)

    # ---- 阶段 1：场上轰炸机 / 迫击炮先手输出 ----
    if find_on(BOMBER_IMG, CONF_STRICT, region=region_mine) or find_on(
        MORTAR_IMG, CONF_STRICT, region=region_mine
    ):
        for pos in find_all(BOMBER_IMG, CONF_STRICT, region=region_mine):
            _bomber_strike(pos, enemy_hq_pos)
        for pos in find_all(MORTAR_IMG, CONF_STRICT, region=region_mine):
            _mortar_strike(pos, enemy_hq_pos)

    # ---- 阶段 2：手牌盲打 ----
    if find_center(PASS_TURN_IMG) or find_center(END_TURN_IMG):
        if enemy_hq_pos is None:
            log.warning("未定位到敌方总部，跳过手牌阶段")
        else:
            hand_y = pyautogui.size()[1] - HAND_CARD_Y_OFFSET
            for i in range(HAND_CARD_COUNT):
                pyautogui.click(x=HAND_CARD_X0 + i * HAND_CARD_DX, y=hand_y)
                pyautogui.dragTo(enemy_hq_pos, duration=MOVE_DURATION)
                time.sleep(0.5)
        time.sleep(0.5)

    # ---- 阶段 3：手牌打完后又出场的单位补刀 ----
    if find_on(FIGHTER_IMG, CONF_STRICT, region=region_mine) or find_on(
        BOMBER_IMG, CONF_STRICT, region=region_mine
    ):
        for pos in find_all(FIGHTER_IMG, CONF_STRICT, region=region_mine):
            _fighter_strike(pos, enemy_hq_pos)
        for pos in find_all(BOMBER_IMG, CONF_STRICT, region=region_mine):
            _bomber_strike(pos, enemy_hq_pos)


def _wait_opponent_turn(timeout=WAIT_OPPONENT_TIMEOUT):
    """等对手回合结束。

    原始版本两处 while 循环都没有 sleep，等于满核疯狂截图；
    而且完全没有超时，对面拔线/卡死就永久挂住。
    """
    start_ts = time.time()
    while time.time() - start_ts < timeout:
        if not find_center(OPPONENT_TURN_IMG):
            return True
        if find_center(END_TURN_IMG) or find_center(PASS_TURN_IMG):
            return True
        time.sleep(POLL_INTERVAL)
    log.warning("等待对手回合超时 %ds", timeout)
    return False


def click_end_turn_button():
    """点结束回合。"""
    pos = find_center(END_TURN_IMG)
    if pos is None:
        return False
    play_cards()
    human_click(pos)
    _wait_opponent_turn()
    return True


def click_pass_button():
    """点空过（优先），找不到就退化成结束回合。"""
    pos = find_center(PASS_TURN_IMG)
    if pos is None:
        return click_end_turn_button()
    play_cards()
    human_click(pos, clicks=2)
    _wait_opponent_turn()
    return True


# ---------------------------------------------------------------------------
# 启动器 / 主菜单 / 结算
# ---------------------------------------------------------------------------
def restart():
    """断线重连：点启动器上的重启按钮。"""
    pos = find_center(RESTART_IMG) or find_center(CLICKED_RESTART_IMG)
    if pos is None:
        return False
    human_click(pos, clicks=2)
    log.info("点击了重启按钮")
    return True


def exit_game():
    """退出游戏。"""
    pos = find_center(EXIT_IMG)
    if pos is None:
        return False
    human_click(pos, clicks=2)
    log.info("点击了退出游戏按钮")
    return True


def start_game_out():
    """点官方启动器上的「开始游戏」。"""
    pos = find_center(START_GAME_OUT_IMG)
    if pos is None:
        return False
    human_click(pos, clicks=2)
    log.info("从外部点击了开始游戏按钮")
    return True


def main_menu():
    """主菜单处于「开始」被选中态时，切回可开战状态。"""
    clicked = find_center(CLICKED_MAIN_MENU_IMG)
    if clicked is None:
        return False
    start_pos = find_center(MAIN_MENU_START_IMG)
    mid_pos = find_center(MAIN_MENU_START_MID_IMG)
    human_click(start_pos)
    if mid_pos is not None:
        pyautogui.click(mid_pos)
    log.info("点击了主菜单开始按钮")
    return True


def daily_mission():
    """点掉每日任务红点。"""
    if find_center(DAILY_MISSION_IMG) is None:
        return False
    sw, sh = pyautogui.size()
    human_move((sw // 2 + 30, sh - 121))
    pyautogui.click(sw // 2 + 30, sh - 121)
    return True


def _handle_result_screens():
    """结算界面一路点过去：继续 → 领奖 → 关广告 → 离开战场回顾。
    返回 True 表示处理过某个结算界面。"""
    pos = find_center(CONTINUE_IMG)
    if pos is not None:
        check_pos = find_center(CHECK_BATTLE_IMG)
        if check_pos is not None:
            human_move(check_pos)          # 仅悬停，消掉 tooltip 遮挡
            time.sleep(0.5)
        sw, sh = pyautogui.size()
        deadline = time.time() + 60
        while time.time() < deadline and find_center(CONTINUE_IMG):
            pyautogui.moveTo(100, sh // 2)
            pyautogui.moveTo(2000, sh // 2, duration=0.5)
            pyautogui.moveTo(sw // 2 + 30, sh - 121, duration=0.5)
            pyautogui.click(pos)
            time.sleep(3)
        return True

    pos = find_center(GET_REWARD_IMG)
    if pos is not None:
        sw, sh = pyautogui.size()
        pyautogui.moveTo(100, sh // 2)
        pyautogui.moveTo(2000, sh // 2, duration=0.5)
        pyautogui.moveTo(sw // 2 + 30, sh - 121, duration=0.5)
        pyautogui.click(pos)
        return True

    pos = find_center(CLOSE_AD_IMG)
    if pos is not None:
        deadline = time.time() + 60
        while time.time() < deadline and find_center(CLOSE_AD_IMG):
            human_click(pos)
            time.sleep(3)
        return True

    pos = find_center(LEAVE_BATTLE_IMG)
    if pos is not None:
        human_click(pos)
        return True

    return False


# ---------------------------------------------------------------------------
# 主循环
# ---------------------------------------------------------------------------
def tick():
    """一轮「扫描器」：把所有已知按钮都试一遍，谁在就点谁。

    这仍然是原始版本的设计（不是状态机），好处是实现简单，
    坏处是依赖「找不到图」来兜底，误点风险高。重构方向见 docs/逻辑解读.md
    """
    # 投降进行中：把鼠标让给投降线程
    if surrender_event.is_set():
        return

    start_game_out()
    daily_mission()
    main_menu()
    restart()
    exit_game()
    click_pass_button()
    _handle_result_screens()

    if not click_start_game_button():
        return


def main():
    log.info("KardsAFK4EXP 启动，屏幕分辨率 %sx%s", *pyautogui.size())
    if pyautogui.size() != (2220, 1271):
        log.warning(
            "当前分辨率 %sx%s 与推荐的 2220x1271 不一致，识别坐标可能错位",
            *pyautogui.size(),
        )
    log.info("鼠标移至屏幕左上角可随时中止（PyAutoGUI FAILSAFE）")
    time.sleep(10)

    while True:
        try:
            if surrender_event.is_set():
                time.sleep(MAIN_LOOP_PAUSE)
                continue
            tick()
            time.sleep(MAIN_LOOP_PAUSE)
        except pyautogui.FailSafeException:
            log.warning("触发 FAILSAFE，脚本退出")
            break
        except KeyboardInterrupt:
            log.warning("收到中断，脚本退出")
            break
        except Exception:  # noqa: BLE001
            # 原始版本任何一次异常都会让整个脚本退出，挂机一晚上等于白挂
            log.exception("主循环异常，2 秒后继续")
            time.sleep(2)

    log.info("脚本已停止 %s", datetime.datetime.now())


if __name__ == "__main__":
    main()
