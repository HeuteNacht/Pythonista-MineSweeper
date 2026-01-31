import random
import time

class MinesweeperModel:
    """扫雷游戏的核心逻辑大脑"""
    
    def __init__(self, difficulty_name, rows, cols, mines):
        self.diff_name = difficulty_name
        self.rows = rows
        self.cols = cols
        self.mines = mines
        
        # 初始化网格:0代表空,-1代表雷,1-8代表数字
        self.grid = [[0 for _ in range(cols)] for _ in range(rows)]
        
        # 集合(Set)用于快速查找,存储坐标元组 (row, col)
        self.revealed = set()   # 已翻开的格子
        self.flags = set()      # 已插旗的格子
        self.questions = set()  # 标记问号的格子
        
        # 游戏状态
        self.game_over = False
        self.won = False
        self.first_move = True  # 标记是否是第一步
        self.start_time = None
        self.end_time = None

    def _generate_board(self, safe_r, safe_c):
        """
        生成雷区。
        关键逻辑:确保玩家点击的第一个格子 (safe_r, safe_c) 绝对不是雷。
        """
        # 生成所有可能的坐标列表,排除掉玩家点击的那个点
        candidates = [(r, c) for r in range(self.rows) for c in range(self.cols) if (r, c) != (safe_r, safe_c)]
        # 随机抽取地雷位置
        mine_pos = random.sample(candidates, self.mines)
        
        # 布雷 (-1)
        for r, c in mine_pos:
            self.grid[r][c] = -1
            
        # 计算非雷格子周围的雷数
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == -1: continue # 跳过地雷本身
                # 计算周围8格中有多少个 -1
                self.grid[r][c] = self.count_around(r, c, lambda nr, nc: self.grid[nr][nc] == -1)

    def count_around(self, r, c, condition_func):
        """通用辅助函数:计算(r,c)周围8个格子中,满足 condition_func 条件的个数"""
        count = 0
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0: continue # 跳过自己
                nr, nc = r + dr, c + dc
                # 检查边界
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    if condition_func(nr, nc): count += 1
        return count

    def start_timer_if_needed(self):
        """首次操作时启动计时器"""
        if self.start_time is None:
            self.start_time = time.time()

    def get_duration(self):
        """计算游戏耗时"""
        if self.start_time is None: return 0
        if self.end_time: return self.end_time - self.start_time
        return time.time() - self.start_time

    def toggle_flag(self, r, c):
        """
        切换标记状态:三段循环逻辑
        无 -> 旗帜 -> 问号 -> 无
        返回新的状态字符串,以便 Controller 播放对应音效
        """
        self.start_timer_if_needed()
        if (r, c) in self.revealed: return # 已翻开的不能标记
        
        state = 'none'
        if (r, c) in self.flags:
            self.flags.remove((r, c))
            self.questions.add((r, c))
            state = 'question'
        elif (r, c) in self.questions:
            self.questions.remove((r, c))
            state = 'none'
        else:
            self.flags.add((r, c))
            state = 'flag'
        return state

    def reveal(self, r, c):
        """
        翻开格子 (核心逻辑)
        包含递归泛洪算法 (Flood Fill)
        """
        self.start_timer_if_needed()
        
        # 如果是第一步,现在才生成雷区,保证第一步不死
        if self.first_move:
            self._generate_board(r, c)
            self.first_move = False
            
        # 保护:已翻开、插旗或问号的格子不能被翻开
        if (r, c) in self.revealed or (r, c) in self.flags or (r, c) in self.questions: return
        
        self.revealed.add((r, c))
        
        # 踩雷判断
        if self.grid[r][c] == -1:
            self.game_over = True
            self.end_time = time.time()
        # 空格判断 (0)
        elif self.grid[r][c] == 0:
            # 递归翻开周围所有格子
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols:
                        self.reveal(nr, nc)
                        
        self._check_win()

    def _check_win(self):
        """检查胜利条件:所有非雷格子都已翻开"""
        if not self.game_over and len(self.revealed) == (self.rows * self.cols - self.mines):
            self.won = True
            self.end_time = time.time()
