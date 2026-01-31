import ui
from scene import *
import sound

# 导入我们的自定义模块
from controller import MinesweeperGame
from utils import ScoreManager

def show_menu():
    """显示难度选择菜单"""
    v = ui.View(name='扫雷大师')
    v.background_color = '#ecf0f1'
    
    # 标题
    lbl = ui.Label(frame=(0, 40, 400, 60))
    lbl.text = 'Minesweeper'
    lbl.alignment = ui.ALIGN_CENTER
    lbl.font = ('Futura-Medium', 40)
    lbl.text_color = '#2c3e50'
    v.add_subview(lbl)

    def start_game(sender):
        """点击难度按钮后的回调"""
        sound.play_effect('ui:click3')
        diff = sender.difficulty
        v.close() # 关闭菜单视图
        
        # 安全启动游戏,防止 View 冲突
        def safe_launch():
            try:
                run(MinesweeperGame(diff['name'], diff['r'], diff['c'], diff['m']))
            except Exception as e:
                # 如果菜单关闭动画未结束,0.5秒后重试
                ui.delay(safe_launch, 0.5)
        ui.delay(safe_launch, 0.5)

    # 难度配置表
    configs = [
        {'name': '初级', 'r': 9, 'c': 9, 'm': 10},
        {'name': '中级', 'r': 16, 'c': 16, 'm': 40},
        {'name': '高级', 'r': 16, 'c': 30, 'm': 99}
    ]

    start_y = 130
    for cfg in configs:
        # 创建难度按钮
        btn = ui.Button(title=cfg['name'])
        btn.frame = (40, start_y, 120, 50)
        btn.background_color = '#3498db'; btn.tint_color = 'white'
        btn.font = ('<system-bold>', 18); btn.corner_radius = 8
        btn.difficulty = cfg # 绑定难度数据到按钮对象
        btn.action = start_game
        v.add_subview(btn)
        
        # 创建最高分标签
        score_lbl = ui.Label(frame=(180, start_y, 200, 50))
        score_lbl.text = ScoreManager.get_best_text(cfg['name'])
        score_lbl.text_color = '#7f8c8d'; score_lbl.font = ('<system>', 14)
        v.add_subview(score_lbl)
        
        start_y += 70

    v.frame = (0, 0, 400, 400)
    v.present('sheet')

# 程序入口判断
if __name__ == '__main__':
    show_menu()
