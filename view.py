from scene import *

class GameRenderer:
    """负责具体的绘图工作"""
    
    def __init__(self, scene_instance, model):
        self.s = scene_instance # 持有 Scene 对象 (为了获取屏幕尺寸)
        self.m = model          # 持有 Model 对象 (为了获取数据)
        
        # 颜色配置表
        self.colors = {
            'bg': '#2c3e50', 
            'hud_bg': '#34495e',
            'tile_closed': '#7f8c8d', 
            'tile_open': '#bdc3c7',
            'mine': '#c0392b', 
            'flag': '#f39c12', 
            'question': '#27ae60',
            # 数字 1-6 的颜色
            'nums': ['#2980b9', '#27ae60', '#d35400', '#8e44ad', '#c0392b', '#7f8c8d']
        }
        self.hud_height = 60 # 顶部信息栏高度

    def render(self):
        """主渲染循环,每帧调用"""
        
        # 1. 绘制顶部 HUD 背景
        fill(self.colors['hud_bg'])
        rect(0, self.s.size.h - self.hud_height, self.s.size.w, self.hud_height)
        
        # 2. 绘制时间
        tint('white')
        text(f"⏱ {int(self.m.get_duration())}s", 'Helvetica-Bold', 20, 50, self.s.size.h - 30)
        
        # 3. 绘制剩余雷数
        mines_left = self.m.mines - len(self.m.flags)
        text(f"💣 {mines_left}", 'Helvetica-Bold', 20, self.s.size.w - 50, self.s.size.h - 30)

        # 4. 计算网格居中位置
        grid_w = self.m.cols * self.s.tile_size
        grid_h = self.m.rows * self.s.tile_size
        start_x = (self.s.size.w - grid_w) / 2
        start_y = (self.s.size.h - self.hud_height - grid_h) / 2
        
        # 将原点保存回 Scene,供 Controller 计算点击坐标使用
        self.s.grid_origin = (start_x, start_y)

        # 5. 遍历绘制每个格子
        for r in range(self.m.rows):
            for c in range(self.m.cols):
                # 计算像素坐标
                x = start_x + c * self.s.tile_size
                # 注意:Scene坐标系 y=0 在底部,所以行号 r 需要反转
                y = start_y + (self.m.rows - 1 - r) * self.s.tile_size
                self._draw_single_tile(r, c, x, y)

    def _draw_single_tile(self, r, c, x, y):
        size = self.s.tile_size
        is_rev = (r, c) in self.m.revealed
        
        # 绘制方块背景
        fill(self.colors['tile_open'] if is_rev else self.colors['tile_closed'])
        stroke(1, 1, 1, 0.2) # 边框颜色
        stroke_weight(1)
        rect(x, y, size, size)
        
        cx, cy = x + size/2, y + size/2 # 中心点
        
        # 绘制内容
        if is_rev:
            val = self.m.grid[r][c]
            if val == -1: 
                self._draw_text('💣', cx, cy, size, self.colors['mine'])
            elif val > 0: 
                col = self.colors['nums'][min(val-1, 5)]
                self._draw_text(str(val), cx, cy, size, col)
        elif (r, c) in self.m.flags:
            self._draw_text('🚩', cx, cy, size, self.colors['flag'])
        elif (r, c) in self.m.questions:
             self._draw_text('❓', cx, cy, size, self.colors['question'])

    def _draw_text(self, txt, cx, cy, size, color):
        """辅助函数:绘制居中文字"""
        tint(color)
        text(txt, 'Helvetica-Bold', size * 0.6, cx, cy)
