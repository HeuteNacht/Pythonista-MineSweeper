import ui
from scene import *
import random
import time
import json
import os
import dialogs 
import console
import sound  # <--- 新增: 音效模块
from objc_util import ObjCClass # <--- 新增: 调用iOS原生震动

# ==========================================
# 0. HARDWARE: 硬件控制 (震动反馈)
# ==========================================
class HapticFeedback:
    """调用 iOS Taptic Engine 实现物理震动"""
    _generator = None
    
    @classmethod
    def impact(cls, style=0):
        # style: 0=Light(轻), 1=Medium(中), 2=Heavy(重)
        try:
            UIImpactFeedbackGenerator = ObjCClass('UIImpactFeedbackGenerator')
            gen = UIImpactFeedbackGenerator.alloc().initWithStyle_(style)
            gen.prepare()
            gen.impactOccurred()
        except:
            pass #以此兼容非iOS设备或旧设备

    @classmethod
    def notification(cls, type_id=0):
        # type_id: 0=Success, 1=Warning, 2=Error
        try:
            UINotificationFeedbackGenerator = ObjCClass('UINotificationFeedbackGenerator')
            gen = UINotificationFeedbackGenerator.alloc().init()
            gen.prepare()
            gen.notificationOccurred_(type_id)
        except:
            pass

# ==========================================
# 1. STORAGE: 数据持久化
# ==========================================
class ScoreManager:
    FILE_PATH = 'minesweeper_records.json'
    
    @classmethod
    def load_scores(cls):
        if not os.path.exists(cls.FILE_PATH):
            return {}
        try:
            with open(cls.FILE_PATH, 'r') as f:
                return json.load(f)
        except:
            return {}

    @classmethod
    def save_score(cls, difficulty, name, duration):
        scores = cls.load_scores()
        current_data = scores.get(difficulty, {})
        current_best = current_data.get('time', 999999)
        
        if duration < current_best:
            scores[difficulty] = {'name': name, 'time': duration}
            with open(cls.FILE_PATH, 'w') as f:
                json.dump(scores, f)
            return True
        return False

    @classmethod
    def get_best_text(cls, difficulty):
        data = cls.load_scores().get(difficulty)
        if data:
            return f"🏆 {data['name']}: {int(data['time'])}s"
        return "🏆 暂无纪录"

# ==========================================
# 2. MODEL: 游戏逻辑层
# ==========================================
class MinesweeperModel:
    def __init__(self, difficulty_name, rows, cols, mines):
        self.diff_name = difficulty_name
        self.rows = rows
        self.cols = cols
        self.mines = mines
        self.grid = [[0 for _ in range(cols)] for _ in range(rows)]
        self.revealed = set()
        self.flags = set()
        self.questions = set() # <--- 新增: 存储问号位置
        self.game_over = False
        self.won = False
        self.first_move = True
        self.start_time = None
        self.end_time = None

    def _generate_board(self, safe_r, safe_c):
        candidates = [(r, c) for r in range(self.rows) for c in range(self.cols) if (r, c) != (safe_r, safe_c)]
        mine_pos = random.sample(candidates, self.mines)
        for r, c in mine_pos:
            self.grid[r][c] = -1
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == -1: continue
                self.grid[r][c] = self.count_around(r, c, lambda nr, nc: self.grid[nr][nc] == -1)

    def count_around(self, r, c, condition_func):
        count = 0
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0: continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    if condition_func(nr, nc): count += 1
        return count

    def start_timer_if_needed(self):
        if self.start_time is None: self.start_time = time.time()

    def get_duration(self):
        if self.start_time is None: return 0
        if self.end_time: return self.end_time - self.start_time
        return time.time() - self.start_time

    def toggle_flag(self, r, c):
        """三段循环:空 -> 旗 -> 问号 -> 空"""
        self.start_timer_if_needed()
        if (r, c) in self.revealed: return
        
        state = 'none'
        
        if (r, c) in self.flags:
            # 旗 -> 问号
            self.flags.remove((r, c))
            self.questions.add((r, c))
            state = 'question'
        elif (r, c) in self.questions:
            # 问号 -> 空
            self.questions.remove((r, c))
            state = 'none'
        else:
            # 空 -> 旗
            self.flags.add((r, c))
            state = 'flag'
            
        return state # 返回当前状态以便播放对应音效

    def reveal(self, r, c):
        self.start_timer_if_needed()
        if self.first_move:
            self._generate_board(r, c)
            self.first_move = False
        
        # 保护:旗帜和问号都不能被点开
        if (r, c) in self.revealed or (r, c) in self.flags or (r, c) in self.questions: return
        
        self.revealed.add((r, c))
        if self.grid[r][c] == -1:
            self.game_over = True
            self.end_time = time.time()
        elif self.grid[r][c] == 0:
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols: self.reveal(nr, nc)
        self._check_win()

    def _check_win(self):
        if not self.game_over and len(self.revealed) == (self.rows * self.cols - self.mines):
            self.won = True
            self.end_time = time.time()

# ==========================================
# 3. VIEW: 渲染层
# ==========================================
class GameRenderer:
    def __init__(self, scene_instance, model):
        self.s = scene_instance
        self.m = model
        self.colors = {
            'bg': '#2c3e50', 'hud_bg': '#34495e',
            'tile_closed': '#7f8c8d', 'tile_open': '#bdc3c7',
            'mine': '#c0392b', 'flag': '#f39c12', 'question': '#27ae60', # <--- 新增问号颜色
            'nums': ['#2980b9', '#27ae60', '#d35400', '#8e44ad', '#c0392b', '#7f8c8d']
        }
        self.hud_height = 60

    def render(self):
        fill(self.colors['hud_bg'])
        rect(0, self.s.size.h - self.hud_height, self.s.size.w, self.hud_height)
        
        tint('white')
        time_str = f"⏱ {int(self.m.get_duration())}s"
        text(time_str, 'Helvetica-Bold', 20, 50, self.s.size.h - 30)
        
        mines_left = self.m.mines - len(self.m.flags)
        mine_str = f"💣 {mines_left}"
        text(mine_str, 'Helvetica-Bold', 20, self.s.size.w - 50, self.s.size.h - 30)

        grid_w = self.m.cols * self.s.tile_size
        grid_h = self.m.rows * self.s.tile_size
        start_x = (self.s.size.w - grid_w) / 2
        start_y = (self.s.size.h - self.hud_height - grid_h) / 2
        self.s.grid_origin = (start_x, start_y)

        for r in range(self.m.rows):
            for c in range(self.m.cols):
                x = start_x + c * self.s.tile_size
                y = start_y + (self.m.rows - 1 - r) * self.s.tile_size
                self._draw_single_tile(r, c, x, y)

    def _draw_single_tile(self, r, c, x, y):
        size = self.s.tile_size
        is_rev = (r, c) in self.m.revealed
        
        fill(self.colors['tile_open'] if is_rev else self.colors['tile_closed'])
        stroke(1, 1, 1, 0.2); stroke_weight(1)
        rect(x, y, size, size)
        
        cx, cy = x + size/2, y + size/2
        
        if is_rev:
            val = self.m.grid[r][c]
            if val == -1: 
                self._draw_text('💣', cx, cy, size, self.colors['mine'])
            elif val > 0: 
                col = self.colors['nums'][min(val-1, 5)]
                self._draw_text(str(val), cx, cy, size, col)
        # 绘制旗帜
        elif (r, c) in self.m.flags:
            self._draw_text('🚩', cx, cy, size, self.colors['flag'])
        # 绘制问号
        elif (r, c) in self.m.questions:
             self._draw_text('❓', cx, cy, size, self.colors['question'])

    def _draw_text(self, txt, cx, cy, size, color):
        tint(color)
        text(txt, 'Helvetica-Bold', size * 0.6, cx, cy)

# ==========================================
# 4. CONTROLLER: 游戏主引擎
# ==========================================
class MinesweeperGame(Scene):
    def __init__(self, diff_name, rows, cols, mines):
        super().__init__()
        self.diff_name = diff_name
        self.rows = rows
        self.cols = cols
        self.mines = mines
        
        self.model = MinesweeperModel(diff_name, rows, cols, mines)
        self.last_tap = {'pos': None, 'time': 0}
        self.grid_origin = (0, 0)
        self.record_saved = False
        self.busy = False 
        
        self.btn_restart_rect = Rect(0,0,0,0)
        self.btn_menu_rect = Rect(0,0,0,0)

    def setup(self):
        self.tile_size = min(self.size.w / self.model.cols, (self.size.h - 60) / self.model.rows)
        self.renderer = GameRenderer(self, self.model)

    def draw(self):
        background('#2c3e50')
        self.renderer.render()
        
        if self.model.game_over: 
            self.draw_overlay("GAME OVER", '#e74c3c')
        elif self.model.won:
            self.draw_overlay("YOU WIN!", '#27ae60')
            if not self.record_saved: self.handle_win()

    def draw_overlay(self, msg, color):
        fill(0, 0, 0, 0.7)
        rect(0, 0, self.size.w, self.size.h)
        
        tint(color)
        text(msg, 'Helvetica-Bold', 60, self.size.w/2, self.size.h/2 + 80)
        
        btn_w, btn_h = 160, 60
        spacing = 40
        start_x = (self.size.w - (btn_w * 2 + spacing)) / 2
        btn_y = self.size.h/2 - 60
        
        self.btn_restart_rect = Rect(start_x, btn_y, btn_w, btn_h)
        self.btn_menu_rect = Rect(start_x + btn_w + spacing, btn_y, btn_w, btn_h)
        
        fill('#3498db')
        stroke('white'); stroke_weight(2)
        path = ui.Path.rounded_rect(self.btn_restart_rect.x, self.btn_restart_rect.y, btn_w, btn_h, 10)
        path.fill(); path.stroke()
        tint('white')
        text('🔄 重玩', 'Helvetica-Bold', 24, self.btn_restart_rect.x + btn_w/2, self.btn_restart_rect.y + btn_h/2)
        
        fill('#7f8c8d')
        path = ui.Path.rounded_rect(self.btn_menu_rect.x, self.btn_menu_rect.y, btn_w, btn_h, 10)
        path.fill(); path.stroke()
        tint('white')
        text('🏠 菜单', 'Helvetica-Bold', 24, self.btn_menu_rect.x + btn_w/2, self.btn_menu_rect.y + btn_h/2)

    def handle_win(self):
        self.record_saved = True
        # 胜利音效与震动
        sound.play_effect('digital:PowerUp7')
        HapticFeedback.notification(0) # Success
        
        duration = self.model.get_duration()
        def show_input():
            if not self.model.won: return
            name = dialogs.input_alert('恭喜胜利!', f'耗时: {int(duration)}秒', '玩家1')
            if name:
                is_best = ScoreManager.save_score(self.model.diff_name, name, duration)
                console.hud_alert('新纪录!' if is_best else '记录已保存')
        ui.delay(show_input, 0.2)
        
    def restart_game(self):
        # 重玩音效
        sound.play_effect('ui:switch33')
        self.model = MinesweeperModel(self.diff_name, self.rows, self.cols, self.mines)
        self.renderer = GameRenderer(self, self.model)
        self.record_saved = False
        self.last_tap = {'pos': None, 'time': 0}
        self.busy = False

    def touch_began(self, touch):
        if self.busy: return

        if self.model.game_over or self.model.won:
            if self.btn_restart_rect.contains_point(touch.location):
                self.busy = True
                self.restart_game()
            elif self.btn_menu_rect.contains_point(touch.location):
                self.busy = True
                sound.play_effect('ui:switch33') # 菜单音效
                self.view.close()
                def safe_open_menu():
                    try:
                        show_menu()
                    except:
                        ui.delay(safe_open_menu, 0.5)
                ui.delay(safe_open_menu, 0.5)
            return
            
        ox, oy = self.grid_origin
        tx, ty = touch.location.x, touch.location.y
        if tx < ox or ty < oy: return
        c = int((tx - ox) / self.tile_size)
        r = self.model.rows - 1 - int((ty - oy) / self.tile_size)
        if not (0 <= r < self.model.rows and 0 <= c < self.model.cols): return

        curr_time = time.time()
        
        # 1. 自动开雷
        if (r, c) in self.model.revealed and self.model.grid[r][c] > 0:
            self.try_auto_reveal(r, c)
            
        # 2. 双击 (点开)
        elif self.last_tap['pos'] == (r, c) and (curr_time - self.last_tap['time'] < 0.3):
            # 移除旗帜或问号
            if (r, c) in self.model.flags: self.model.flags.remove((r, c))
            if (r, c) in self.model.questions: self.model.questions.remove((r, c))
            
            self.do_reveal(r, c) # 封装了音效的翻开逻辑
            
        # 3. 单击 (插旗 -> 问号 -> 空)
        elif not ((r, c) in self.model.revealed):
            state = self.model.toggle_flag(r, c)
            # 根据状态播放不同音效和震动
            if state == 'flag':
                sound.play_effect('ui:switch9')
                HapticFeedback.impact(1) # Medium
            elif state == 'question':
                sound.play_effect('ui:switch10') # 问号音效
                HapticFeedback.impact(0) # Light
            else:
                sound.play_effect('ui:click1') # 取消音效
            
        self.last_tap = {'pos': (r, c), 'time': curr_time}

    def do_reveal(self, r, c):
        """执行翻开并播放音效"""
        self.model.reveal(r, c)
        if self.model.game_over:
            # 爆炸音效与重震动
            sound.play_effect('arcade:Explosion_1')
            HapticFeedback.notification(2) # Error/Failure
        else:
            # 普通翻开音效
            sound.play_effect('ui:click2')
            HapticFeedback.impact(0) # Light

    def try_auto_reveal(self, r, c):
        flags_cnt = self.model.count_around(r, c, lambda nr, nc: (nr, nc) in self.model.flags)
        if flags_cnt == self.model.grid[r][c]:
            sound.play_effect('ui:click2') # 自动翻开音效
            HapticFeedback.impact(1) 
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < self.model.rows and 0 <= nc < self.model.cols:
                        if (nr, nc) not in self.model.flags and (nr, nc) not in self.model.questions:
                            self.model.reveal(nr, nc)
            # 检查是否因为自动翻开导致输了
            if self.model.game_over:
                sound.play_effect('arcade:Explosion_1')
                HapticFeedback.notification(2)

# ==========================================
# 5. MENU: 启动菜单
# ==========================================
def show_menu():
    v = ui.View(name='扫雷大师')
    v.background_color = '#ecf0f1'
    
    lbl = ui.Label(frame=(0, 40, 400, 60))
    lbl.text = 'Minesweeper'
    lbl.alignment = ui.ALIGN_CENTER
    lbl.font = ('Futura-Medium', 40)
    lbl.text_color = '#2c3e50'
    v.add_subview(lbl)

    def start_game(sender):
        sound.play_effect('ui:click3') # 按钮音效
        diff = sender.difficulty
        v.close() 
        def safe_launch():
            try:
                run(MinesweeperGame(diff['name'], diff['r'], diff['c'], diff['m']))
            except Exception as e:
                ui.delay(safe_launch, 0.5)
        ui.delay(safe_launch, 0.5)

    configs = [
        {'name': '初级', 'r': 9, 'c': 9, 'm': 10},
        {'name': '中级', 'r': 16, 'c': 16, 'm': 40},
        {'name': '高级', 'r': 16, 'c': 30, 'm': 99}
    ]

    start_y = 130
    for cfg in configs:
        btn = ui.Button(title=cfg['name'])
        btn.frame = (40, start_y, 120, 50)
        btn.background_color = '#3498db'; btn.tint_color = 'white'
        btn.font = ('<system-bold>', 18); btn.corner_radius = 8
        btn.difficulty = cfg
        btn.action = start_game
        v.add_subview(btn)
        
        score_lbl = ui.Label(frame=(180, start_y, 200, 50))
        score_lbl.text = ScoreManager.get_best_text(cfg['name'])
        score_lbl.text_color = '#7f8c8d'; score_lbl.font = ('<system>', 14)
        v.add_subview(score_lbl)
        start_y += 70

    v.frame = (0, 0, 400, 400)
    v.present('sheet')

if __name__ == '__main__':
    show_menu()
