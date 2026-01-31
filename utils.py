import os
import json
from objc_util import ObjCClass  # Pythonista 专用库,用于调用 iOS 原生 API

# ==========================================
# 硬件交互:震动反馈 (Taptic Engine)
# ==========================================
class HapticFeedback:
    """
    封装 iOS 的 UIImpactFeedbackGenerator 和 UINotificationFeedbackGenerator。
    让游戏拥有物理触感。
    """
    
    @classmethod
    def impact(cls, style=0):
        """
        模拟物理撞击感 (如点击、插旗)。
        :param style: 震动强度 -> 0:轻(Light), 1:中(Medium), 2:重(Heavy)
        """
        try:
            # 通过 objc_util 获取 iOS 原生类
            UIImpactFeedbackGenerator = ObjCClass('UIImpactFeedbackGenerator')
            gen = UIImpactFeedbackGenerator.alloc().initWithStyle_(style)
            gen.prepare()  # 预加载以减少延迟
            gen.impactOccurred()  # 触发震动
        except:
            pass # 如果是在非 iOS 设备或旧设备上运行,忽略错误

    @classmethod
    def notification(cls, type_id=0):
        """
        模拟系统通知震动 (如胜利、失败)。
        :param type_id: 类型 -> 0:成功(Success), 1:警告(Warning), 2:错误(Error)
        """
        try:
            UINotificationFeedbackGenerator = ObjCClass('UINotificationFeedbackGenerator')
            gen = UINotificationFeedbackGenerator.alloc().init()
            gen.prepare()
            gen.notificationOccurred_(type_id)
        except:
            pass

# ==========================================
# 数据存储:分数管理
# ==========================================
class ScoreManager:
    """负责读取和保存游戏记录到本地 JSON 文件"""
    FILE_PATH = 'minesweeper_records.json'
    
    @classmethod
    def load_scores(cls):
        """从文件加载所有记录"""
        if not os.path.exists(cls.FILE_PATH):
            return {} # 如果文件不存在,返回空字典
        try:
            with open(cls.FILE_PATH, 'r') as f:
                return json.load(f)
        except:
            return {} # 如果文件损坏,返回空字典

    @classmethod
    def save_score(cls, difficulty, name, duration):
        """
        尝试保存新分数。
        只有当用时 (duration) 比当前最高纪录更短时,才会保存。
        :return: True 表示打破了纪录,False 表示未打破。
        """
        scores = cls.load_scores()
        current_data = scores.get(difficulty, {})
        # 获取当前最快时间,默认为 999999 秒
        current_best = current_data.get('time', 999999)
        
        if duration < current_best:
            # 更新记录
            scores[difficulty] = {'name': name, 'time': duration}
            with open(cls.FILE_PATH, 'w') as f:
                json.dump(scores, f)
            return True
        return False

    @classmethod
    def get_best_text(cls, difficulty):
        """获取格式化好的最高分字符串,用于在菜单显示"""
        data = cls.load_scores().get(difficulty)
        if data:
            return f"🏆 {data['name']}: {int(data['time'])}s"
        return "🏆 暂无纪录"
