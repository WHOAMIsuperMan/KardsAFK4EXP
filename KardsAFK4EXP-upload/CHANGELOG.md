# CHANGELOG · Bug 修复记录

对照上游原始 `kards.py`（481 行）逐条记录。行号均指**上游原始版本**的行号。

---

## 🔴 Bug#1 — 投降失败导致主循环永久停摆（最致命）

**位置**：原 `surrender()` 第 88–103 行，配合 `main()` 第 408 行

**原代码**：
```python
def surrender():
    time.sleep(240)
    global surrenderSwitch
    surrenderSwitch = True                                  # ① 先上锁
    surrender_button_pos = pyautogui.locateCenterOnScreen("surrender.png", confidence=0.7)
    pyautogui.click(surrender_button_pos)                   # ② 可能是 None
    ...
    surrenderSwitch = False                                 # ③ 永远走不到

while not surrenderSwitch:                                  # ④ 永久空转
```

**现象**：挂机几小时后发现游戏停在结算界面或对局中，鼠标完全不动，脚本进程还活着但不干活。日志（如果有）为空。

**根因**：`locateCenterOnScreen` 找不到模板时返回 `None`，`pyautogui.click(None)` 抛 `TypeError`。异常发生在后台线程 → 线程静默死亡，而 `surrenderSwitch` 已在上一步被置为 `True`，且没有任何 `finally` 负责复位。主循环 `while not surrenderSwitch` 从此无限空转。

**修复**：
- `surrenderSwitch` 换成 `threading.Event`（`surrender_event`），语义明确、线程安全。
- 整个投降流程包在 `try / except / finally` 中，**`finally` 必清事件**。
- 每一步 `locate` 都判空，找不到就记 `WARNING` 并正常返回（本局不投降，但主循环继续）。

**验证**：`tests/test_logic.py::test_surrender_missing_button_releases_lock`

---

## 🔴 Bug#2 — 投降线程堆叠

**位置**：原 `click_confirm_button()` 第 119–120 行

**原代码**：
```python
request_thread = threading.Thread(target=surrender)
request_thread.start()
```
每次点「确认」都无条件起一个新线程。

**根因**：上一局的 240 秒计时线程还没结束时又开了一局，两个线程先后醒来，同时抢鼠标点投降，造成拖拽错位、误点。

**修复**：`start_surrender_timer()` 用 `_surrender_guard` + `_surrender_pending` 去重，重复调用直接跳过并记日志；线程 `daemon=True`。

**验证**：`test_surrender_timer_not_duplicated`

---

## 🔴 Bug#3 — 未判空就点击（崩溃点）

**位置**：原 `click_start_game_button()` 第 147–148 行

**原代码**：
```python
clciked_start_game_button_pos = pyautogui.locateCenterOnScreen("clickedstartBattle.png", confidence=0.7)
if start_battle_button_pos:
    ...
    pyautogui.click(clciked_start_game_button_pos)   # 没判空
```

**根因**：`confidence=0.7` 的模板匹配在动画/悬停态下经常失败，返回 `None` → `TypeError` → 主循环崩掉（原版没有异常兜底，见 Bug#8）。

**修复**：先判空再点击；同时把这类「找不到图」的预期内情况统一收进 `_safe_locate()` 兼容层。

---

## 🟠 Bug#4 — 两处 `while` 轮询没有 `sleep`

**位置**：原 `click_pass_button()` 第 218–222 行、`main()` 第 408 行

**原代码**：
```python
while pyautogui.locateCenterOnScreen(...) and not ...:
    if switch:
        switch = False
    #time.sleep(1)        ← 被注释掉了
```

**现象**：风扇狂转、一个核心 100%、`locateCenterOnScreen` 每轮都做全屏截图导致响应极慢。

**根因**：等待循环里 `time.sleep` 被注释（有意思的是 `click_end_turn_button()` 第 195 行的同款循环反而有 `sleep(1)`，两处不一致）。

**修复**：抽出 `_wait_opponent_turn()`，统一用 `POLL_INTERVAL = 0.3` 轮询；主循环加 `MAIN_LOOP_PAUSE = 0.2`。

---

## 🟠 Bug#5 — `region` 参数语义错配（最隐蔽）

**位置**：原第 74–78 行

**原代码**：
```python
pos_of_mine  = (501, 733, 1704, 988)
pos_of_enemy = (437, 150, 1760, 397)
pos_of_hand_card = (550, 1037, 1725, pyautogui.size()[1])
```

**根因**：作者写的是 **(x1, y1, x2, y2)**（左上角 + 右下角），但 `pyautogui` 的 `region` 参数是 **(x, y, width, height)**。

- 按作者意图：`pos_of_mine` 是 x 501–1704、y 733–988 的一个 1203×255 的框 —— 正好压在我方支援阵线上，**完全合理**，且全部落在 2220×1271 内。
- 按 pyautogui 实际解释：`(501, 733, w=1704, h=988)` → 右下角 (2205, 1721)，**高度越出屏幕 450px**。

**后果**：
1. 扫描面积放大 ~4 倍，`locateAllOnScreen` 明显变慢，恶化 Bug#4 的时序；
2. 放大后的框 `y = 733 → 1721` **把手牌区（y ≈ 1037–1271）也框了进去**。手牌里的战斗机/轰炸机图标会被当成「场上单位」命中，脚本于是去点手牌位置并往敌方总部拖 → 乱拖、误操作。

**修复**：新增 `to_region(box)`，显式把 `(x1,y1,x2,y2)` 转成 `(x,y,w,h)` 并裁剪到屏幕内；`BOX_MINE` / `BOX_ENEMY` 保持作者原本的直觉语义，注释写明。

**验证**：`test_to_region_semantics`、`test_region_does_not_cover_hand`

---

## 🟠 Bug#6 — 等待对手回合没有超时

**位置**：原 `click_end_turn_button()` 第 193 行、`click_pass_button()` 第 218 行

**根因**：`while 还在对手回合 and 我方按钮都不在` 没有上界。对手拔线、客户端卡住、模板误判为「对手回合中」时，脚本永久挂住。

**修复**：`_wait_opponent_turn(timeout=WAIT_OPPONENT_TIMEOUT)`，超时记 `WARNING` 后返回，让主循环重新评估局面。

**验证**：`test_wait_opponent_turn_timeout`

---

## 🟡 Bug#7 — `locateAllOnScreen` 边迭代边点击

**位置**：原 `play_cards()` 第 252、269、296、310 行

**根因**：`locateAllOnScreen` 返回生成器，一边迭代一边点击/拖拽，游戏画面已经变化，后续迭代产出的坐标基于旧画面 → 重复点击同一个点或点到错误目标。

**修复**：`find_all()` 一律 `list(...)` 物化后再遍历；同时把三段重复的「找到单位 → 选目标 → 拖拽」逻辑抽成 `_bomber_strike` / `_mortar_strike` / `_fighter_strike`。

---

## 🟡 Bug#8 — 主循环无任何异常兜底

**位置**：原 `main()` 第 407–478 行

**根因**：任何一次预期外异常（模板缺失、坐标越界、Win32 焦点切换）都会让整个脚本退出。挂机场景下这等于「跑了一晚上，两点半挂了，你不知道」。

**修复**：`tick()` 包在 `try` 里，捕获 `pyautogui.FailSafeException` / `KeyboardInterrupt` 正常退出，其余异常 `log.exception()` 记录后 2 秒继续。**脚本现在不会因为单次异常而死。**

---

## 🟡 Bug#9 — `logging` 导入未使用，全凭 `print` 且大部分被注释

**位置**：原第 7 行 import，全文

**根因**：几乎所有诊断 `print` 都被注释掉了，出问题无法定位。

**修复**：配置 `logging`，同时输出到 `kards.log`（UTF-8）与控制台，时间戳精确到秒。投降、异常、识别失败等关键路径全部记日志。

---

## 其他工程化改动

| 项 | 说明 |
|---|---|
| **配置集中** | 40+ 个图像名、置信度、坐标、时序常量全部提到文件顶部「配置区」 |
| **`None` 坐标安全** | `human_move` / `human_click` 对 `None` 返回 `False` 而不是让 pyautogui 抛 `TypeError` |
| **识别函数兼容层** | `_safe_locate()` 同时兼容 `pyscreeze 0.1.29`（返回 `None`）与 `pyscreeze >=1.0`（抛 `ImageNotFoundException`），换环境不会崩 |
| **分辨率自检** | 启动时比对 `pyautogui.size()` 与 2220×1271，不符直接 `WARNING` |
| **人类化点击** | `HUMANIZE` 开关：随机 ±3px 抖动 + 随机耗时 ±15%，比原版机械的 `moveTo(中心) → moveTo(目标)` 更自然 |
| **去硬编码** | `daily_mission()` 里写死的 `1150` 改为按屏幕高度推导（1271 时等价） |
| **`start.bat`** | 加 `chcp 65001`、依赖自动检查安装、出错 `pause` 停留 |
| **自测** | 新增 `tests/test_logic.py`，11 个用例，无需装 pyautogui / 无需开游戏 |
| **文档** | 新增 `README.md`（重写）、`docs/逻辑解读.md`、本文件 |

---

## 明确**没有**修的东西（属于功能，不是 bug）

- **出牌不会赢**：手牌一律拖向敌方总部，不辨别「部署到己方阵线」还是「攻击敌方目标」，也不看费用。这是上游的设计选择（目标是拖满 4 分钟拿经验），重构方案见 `docs/逻辑解读.md`。
- `coast()` / `coast_color_True` / `pos_of_hand_card` 仍是死代码，保留原样并标注，供后续恢复费用检测时使用。
- `guard.png`（守护单位）识别未启用；`In_Window_Main_Menu_Battle.png` / `clickedExit.png` 在仓库中缺失，相关代码本就是注释状态。
