# -*- coding: utf-8 -*-
"""无游戏环境下的逻辑自测。

用一个假的 pyautogui 模块替换真实依赖，从而在不打开游戏、不装配
pyautogui 的情况下验证 kards.py 的关键修复点：

    python tests/test_logic.py

覆盖的回归点：
    1. to_region() 的 (x1,y1,x2,y2) -> (x,y,w,h) 语义修正
    2. 找不到图时返回 None 而不是抛异常
    3. 投降按钮缺失时不再让 surrender_event 永久卡死（原始版最致命 bug）
    4. human_click(None) 安全跳过，不再 TypeError
    5. 敌方总部未识别到时 play_cards() 不崩
    6. 等待对手回合有超时，不会死等
"""

import os
import sys
import time
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ---------------------------------------------------------------------------
# 假 pyautogui
# ---------------------------------------------------------------------------
class FakeBox:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.width, self.height = x, y, w, h
        self.left, self.top = x, y
        self.tx, self.ty = x + w // 2, y + h // 2

    def __getitem__(self, i):
        return (self.x, self.y, self.width, self.height)[i]

    def __repr__(self):
        return f"FakeBox({self.x},{self.y},{self.width},{self.height})"


class FakePyAutoGUI(types.ModuleType):
    def __init__(self):
        super().__init__("pyautogui")
        self.visible = {}      # 图像名 -> 是否"出现在屏幕上"
        self.found = {}        # 图像名 -> [FakeBox, ...]
        self.calls = []
        self.size_value = (2220, 1271)
        self.FailSafeException = type("FailSafeException", (Exception,), {})

    # --- 屏幕信息 ---
    def size(self):
        return self.size_value

    # --- 识别 ---
    def locateCenterOnScreen(self, image, confidence=0.9, region=None):
        self.calls.append(("locateCenter", image))
        boxes = self.found.get(image)
        if boxes:
            return boxes[0].tx, boxes[0].ty
        return None

    def locateOnScreen(self, image, confidence=0.9, region=None):
        self.calls.append(("locate", image))
        boxes = self.found.get(image)
        return boxes[0] if boxes else None

    def locateAllOnScreen(self, image, confidence=0.9, region=None):
        self.calls.append(("locateAll", image))
        return iter(self.found.get(image) or [])

    # --- 动作 ---
    def moveTo(self, *args, **kwargs):
        self.calls.append(("moveTo", args))

    def click(self, *args, **kwargs):
        if any(a is None for a in args):
            raise TypeError("click() 收到 None 坐标")
        self.calls.append(("click", args))

    def dragTo(self, *args, **kwargs):
        if any(a is None for a in args):
            raise TypeError("dragTo() 收到 None 坐标")
        self.calls.append(("dragTo", args))

    def reset(self):
        self.found.clear()
        self.calls.clear()


fake = FakePyAutoGUI()
sys.modules["pyautogui"] = fake
sys.modules["pygetwindow"] = types.ModuleType("pygetwindow")

import kards  # noqa: E402


class TestLogic(unittest.TestCase):
    def setUp(self):
        fake.reset()
        kards.surrender_event.clear()
        kards._surrender_pending = False
        kards.SURRENDER_DELAY = 0.05
        kards.SURRENDER_SETTLE = 0.01
        kards.WAIT_OPPONENT_TIMEOUT = 0.4
        kards.POLL_INTERVAL = 0.02

    # ---- 1. 区域语义 ----
    def test_to_region_semantics(self):
        # 原始版本把右下角当成宽高，得到 (501,733,1704,988) 这样的越界区域
        self.assertEqual(kards.to_region((501, 733, 1704, 988)), (501, 733, 1203, 255))
        self.assertEqual(kards.to_region((437, 150, 1760, 397)), (437, 150, 1323, 247))
        # 越界要被裁剪到屏幕内
        x, y, w, h = kards.to_region((0, 0, 9999, 9999))
        self.assertEqual((x, y, x + w, y + h), (0, 0, 2220, 1271))

    def test_region_does_not_cover_hand(self):
        """修复后，我方支援阵线区域不应再覆盖到手牌区（y>=1037）。"""
        _x, _y, _w, h = kards.to_region(kards.BOX_MINE)
        self.assertLess(_y + h, 1037)

    # ---- 2. 找不到图返回 None ----
    def test_find_center_missing_returns_none(self):
        self.assertIsNone(kards.find_center("nothing.png"))
        self.assertIsNone(kards.find_on("nothing.png"))
        self.assertEqual(kards.find_all("nothing.png"), [])

    # ---- 3. 投降流程不再锁死 ----
    def test_surrender_missing_button_releases_lock(self):
        """原始版本：找不到投降按钮 -> click(None) TypeError ->
        surrender_event 永远为 True -> 主循环永久空转。"""
        kards.SURRENDER_ENABLED = True
        kards.start_surrender_timer()
        deadline = time.time() + 5
        while kards._surrender_pending and time.time() < deadline:
            time.sleep(0.02)
            if kards.surrender_event.is_set():
                self.fail("事件未复位，脚本会永久停摆")
        self.assertFalse(kards.surrender_event.is_set(), "surrender_event 未被清除")
        self.assertFalse(kards._surrender_pending, "_surrender_pending 未被复位")

    def test_surrender_success_path(self):
        fake.found[kards.SURRENDER_IMG] = [FakeBox(100, 100, 10, 10)]
        fake.found[kards.SURRENDER2_IMG] = [FakeBox(200, 200, 10, 10)]
        kards.SURRENDER_ENABLED = True
        kards.start_surrender_timer()
        deadline = time.time() + 5
        while kards._surrender_pending and time.time() < deadline:
            time.sleep(0.02)
        self.assertFalse(kards.surrender_event.is_set())
        clicked = [c for c in fake.calls if c[0] == "click"]
        self.assertEqual(len(clicked), 2, "应当点投降 + 二次确认各一次")

    def test_surrender_timer_not_duplicated(self):
        fake.found[kards.SURRENDER_IMG] = [FakeBox(100, 100, 10, 10)]
        fake.found[kards.SURRENDER2_IMG] = [FakeBox(200, 200, 10, 10)]
        kards.SURRENDER_ENABLED = True
        kards.SURRENDER_DELAY = 0.3
        kards.start_surrender_timer()
        kards.start_surrender_timer()   # 重复调用不应再起一个线程
        deadline = time.time() + 5
        while kards._surrender_pending and time.time() < deadline:
            time.sleep(0.02)
        started = [c for c in fake.calls if c[0] == "locateCenter"]
        self.assertEqual(len(started), 2, "只应有一轮投降流程（投降 + 二次确认）")

    # ---- 4. None 安全 ----
    def test_human_click_none(self):
        self.assertFalse(kards.human_click(None))

    # ---- 5. play_cards 无 HQ 不崩 ----
    def test_play_cards_without_hq(self):
        # 有可空过标识（代表轮到我方），但识别不到敌方总部
        fake.found[kards.PASS_TURN_IMG] = [FakeBox(2100, 1200, 20, 20)]
        fake.found[kards.BOMBER_IMG] = [FakeBox(600, 800, 40, 40)]
        kards.play_cards()   # 不应抛异常
        drags = [c for c in fake.calls if c[0] == "dragTo"]
        self.assertEqual(drags, [], "HQ 没识别到时不应发生拖拽")

    def test_play_cards_bomber_targets_hq(self):
        fake.found[kards.PASS_TURN_IMG] = [FakeBox(2100, 1200, 20, 20)]
        fake.found[kards.BOMBER_IMG] = [FakeBox(600, 800, 40, 40)]
        fake.found[kards.ENEMY_HQ_IMG] = [FakeBox(1100, 200, 60, 60)]
        kards.play_cards()
        drags = [c for c in fake.calls if c[0] == "dragTo"]
        self.assertTrue(drags, "识别到 HQ 后应当发生拖拽")

    # ---- 6. 等待对手回合有超时 ----
    def test_wait_opponent_turn_timeout(self):
        fake.found[kards.OPPONENT_TURN_IMG] = [FakeBox(10, 10, 10, 10)]
        t0 = time.time()
        ok = kards._wait_opponent_turn(timeout=0.4)
        self.assertFalse(ok)
        self.assertLess(time.time() - t0, 3, "超时机制未生效")

    def test_wait_opponent_turn_returns_when_my_turn(self):
        fake.found[kards.OPPONENT_TURN_IMG] = [FakeBox(10, 10, 10, 10)]
        fake.found[kards.END_TURN_IMG] = [FakeBox(2100, 1200, 20, 20)]
        self.assertTrue(kards._wait_opponent_turn(timeout=2))


if __name__ == "__main__":
    unittest.main(verbosity=2)
