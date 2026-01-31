import ui
from scene import *
import time
import dialogs 
import console
import sound

# 导入自定义模块
from model import MinesweeperModel
from view import GameRenderer
from utils import ScoreManager, HapticFeedback

class MinesweeperGame(Scene):
    """游戏主场景控制器"""
    
    def __init__(self, diff_name, rows, cols, mines):
        super().__init__()
        # 保存游戏参数,用于"重玩"功能
        self.diff_name = diff_name
        self.rows = rows
        self.cols = cols
        self.mines = mines
        
        # 初始化模型
        self.model = MinesweeperModel(diff_name, rows, cols, mines)
        
        # 交互状态变量
        self.last_tap = {'pos': None, 'time': 0} # 用于判断双击
        self.grid_origin = (0, 0) # 网格屏幕坐标偏移量
        self.record_saved = False # 防止重复保存记录
        self.busy = False # 防连点锁
        
        # 按钮点击区域 (在 draw_overlay 中计算)
        self.btn_restart_rect = Rect(0,0,0,0)
        self.btn_menu_rect = Rect(0,0,0,0)

    def setup(self):
        """Scene 初始化时调用"""
        # 计算适配当前屏幕的格子大小
        self.tile_size = min(self.size.w / self.model.cols, (self.size.h - 60) / self.model.rows)
        # 初始化渲染器
        self.renderer = GameRenderer(self, self.model)

    def draw(self):
        """每帧刷新 (60FPS)"""
        background('#2c3e50')
        self.renderer.render() # 绘制游戏界面
        
        # 如果游戏结束,绘制覆盖层
        if self.model.game_over: 
            self.draw_overlay("GAME OVER", '#e74c3c')
        elif self.model.won:
            self.draw_overlay("YOU WIN!", '#27ae60')
            if not self.record_saved: self.handle_win()

    def draw_overlay(self, msg, color):
        """绘制结算界面的遮罩和按钮"""
        fill(0, 0, 0, 0.7); rect(0, 0, self.size.w, self.size.h)
        tint(color); text(msg, 'Helvetica-Bold', 60, self.size.w/2, self.size.h/2 + 80)
        
        # 计算按钮位置
        btn_w, btn_h = 160, 60
        spacing = 40
        start_x = (self.size.w - (btn_w * 2 + spacing)) / 2
        btn_y = self.size.h/2 - 60
        
        self.btn_restart_rect = Rect(start_x, btn_y, btn_w, btn_h)
        self.btn_menu_rect = Rect(start_x + btn_w + spacing, btn_y, btn_w, btn_h)
        
        # 绘制重玩按钮
        fill('#3498db'); stroke('white'); stroke_weight(2)
        path = ui.Path.rounded_rect(self.btn_restart_rect.x, self.btn_restart_rect.y, btn_w, btn_h, 10)
        path.fill(); path.stroke()
        tint('white'); text('🔄 重玩', 'Helvetica-Bold', 24, self.btn_restart_rect.x + btn_w/2, self.btn_restart_rect.y + btn_h/2)
        
        # 绘制菜单按钮
        fill('#7f8c8d')
        path = ui.Path.rounded_rect(self.btn_menu_rect.x, self.btn_menu_rect.y, btn_w, btn_h, 10)
        path.fill(); path.stroke()
        tint('white'); text('🏠 菜单', 'Helvetica-Bold', 24, self.btn_menu_rect.x + btn_w/2, self.btn_menu_rect.y + btn_h/2)

    def handle_win(self):
        """处理胜利逻辑:播放音效、保存记录"""
        self.record_saved = True
        sound.play_effect('digital:PowerUp7')
        HapticFeedback.notification(0) # 震动:成功
        
        duration = self.model.get_duration()
        def show_input():
            if not self.model.won: return
            # 弹出名字输入框
            name = dialogs.input_alert('恭喜胜利!', f'耗时: {int(duration)}秒', '玩家1')
            if name:
                is_best = ScoreManager.save_score(self.model.diff_name, name, duration)
                console.hud_alert('新纪录!' if is_best else '记录已保存')
        ui.delay(show_input, 0.2)
        
    def restart_game(self):
        """原地重开游戏"""
        sound.play_effect('ui:switch33')
        # 重置 Model 和 Renderer
        self.model = MinesweeperModel(self.diff_name, self.rows, self.cols, self.mines)
        self.renderer = GameRenderer(self, self.model)
        self.record_saved = False
        self.last_tap = {'pos': None, 'time': 0}
        self.busy = False

    def touch_began(self, touch):
        """处理触摸事件"""
        if self.busy: return # 防止连点

        # --- 游戏结束状态下的点击 ---
        if self.model.game_over or self.model.won:
            if self.btn_restart_rect.contains_point(touch.location):
                self.busy = True; self.restart_game()
            elif self.btn_menu_rect.contains_point(touch.location):
                self.busy = True; sound.play_effect('ui:switch33')
                self.view.close()
                
                # 动态导入 main 以避免循环引用 (Controller -> Main -> Controller)
                import main
                def safe_open():
                    try: main.show_menu()
                    except: ui.delay(safe_open, 0.5)
                ui.delay(safe_open, 0.5)
            return
            
        # --- 游戏进行中的点击 ---
        ox, oy = self.grid_origin
        tx, ty = touch.location.x, touch.location.y
        # 边界检查
        if tx < ox or ty < oy: return
        
        # 屏幕坐标 -> 网格坐标转换
        c = int((tx - ox) / self.tile_size)
        r = self.model.rows - 1 - int((ty - oy) / self.tile_size)
        if not (0 <= r < self.model.rows and 0 <= c < self.model.cols): return

        curr_time = time.time()
        
        # 1. 逻辑:点击已翻开的数字 -> 尝试自动开雷 (Chord)
        if (r, c) in self.model.revealed and self.model.grid[r][c] > 0:
            self.try_auto_reveal(r, c)
            
        # 2. 逻辑:双击 -> 强制翻开
        elif self.last_tap['pos'] == (r, c) and (curr_time - self.last_tap['time'] < 0.3):
            # 如果双击了插旗/问号的格子,先移除标记再翻开
            if (r, c) in self.model.flags: self.model.flags.remove((r, c))
            if (r, c) in self.model.questions: self.model.questions.remove((r, c))
            self.do_reveal(r, c)
            
        # 3. 逻辑:单击 -> 切换标记状态 (三段循环)
        elif not ((r, c) in self.model.revealed):
            state = self.model.toggle_flag(r, c)
            # 播放对应的音效和震动
            if state == 'flag': 
                sound.play_effect('ui:switch9'); HapticFeedback.impact(1)
            elif state == 'question': 
                sound.play_effect('ui:switch10'); HapticFeedback.impact(0)
            else: 
                sound.play_effect('ui:click1')
            
        self.last_tap = {'pos': (r, c), 'time': curr_time}

    def do_reveal(self, r, c):
        """执行翻开并播放结果音效"""
        self.model.reveal(r, c)
        if self.model.game_over:
            sound.play_effect('arcade:Explosion_1'); HapticFeedback.notification(2)
        else:
            sound.play_effect('ui:click2'); HapticFeedback.impact(0)

    def try_auto_reveal(self, r, c):
        """数字自动翻开逻辑"""
        flags_cnt = self.model.count_around(r, c, lambda nr, nc: (nr, nc) in self.model.flags)
        if flags_cnt == self.model.grid[r][c]:
            sound.play_effect('ui:click2'); HapticFeedback.impact(1)
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < self.model.rows and 0 <= nc < self.model.cols:
                        if (nr, nc) not in self.model.flags and (nr, nc) not in self.model.questions:
                            self.model.reveal(nr, nc)
            if self.model.game_over:
                sound.play_effect('arcade:Explosion_1'); HapticFeedback.notification(2)
