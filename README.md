# 🚩 Pythonista Minesweeper Pro | 扫雷大师

> A professional iOS Minesweeper game built with Pythonista 3, featuring MVC architecture, Haptic Feedback, and immersive audio.
> 
> 这是一个专为 iOS 设备设计的扫雷游戏，基于 Pythonista 3 开发。采用 MVC 架构，集成了 iOS 原生震动反馈与沉浸式音效。

---

## ✨ Features (功能亮点)

### 🏗 Architecture (架构设计)
* **MVC Pattern**: Clean separation of Model, View, and Controller.
    * **MVC 模式**：逻辑、渲染与交互分离，代码清晰易维护。
* **Modular Code**: Organized into 5 separate modules for scalability.
    * **模块化**：分为 5 个独立模块，易于扩展。

### 📱 iOS Experience (极致体验)
* **Haptic Feedback**: Uses `objc_util` to trigger the Taptic Engine for clicks, flags, and explosions.
    * **触感反馈**：调用 iOS Taptic Engine，插旗、点击、爆炸均有细腻的物理震动。
* **Immersive Audio**: Integrated system sound effects.
    * **沉浸音效**：内置点击、标记、胜利及爆炸音效。
* **Adaptive Layout**: Perfectly fits both iPhone and iPad screens.
    * **自适应布局**：自动计算网格大小，完美适配 iPhone 和 iPad。

### 🎮 Gameplay (硬核玩法)
* **Tri-State Marking**: Tap to cycle: `Empty` -> `🚩 Flag` -> `❓ Question` -> `Empty`.
    * **三段式标记**：单击循环切换 `⬜️ 空` -> `🚩 旗帜` -> `❓ 问号` -> `⬜️ 空`。
* **Quick Reveal**: Double-tap a tile to reveal it.
    * **双击开雷**：双击未开启的方块可快速翻开。
* **Smart Chording**: Tap a revealed number to auto-open neighbors if flags match.
    * **数字智能扫雷**：点击已翻开的数字，若周围旗帜数符合，自动翻开剩余格子（清图神器）。
* **First-Click Safety**: The first click is guaranteed to be safe.
    * **首发防雷**：保证第一步绝对安全，不会踩雷。

---

## 🛠️ Installation (安装与运行)

1.  **Requirements**: iPhone/iPad with [Pythonista 3](http://omz-software.com/pythonista/).
    * **环境**：需要安装了 Pythonista 3 的 iPhone 或 iPad。
2.  **Setup**: Create a folder (e.g., `Minesweeper`) and paste the 5 source files:
    * **部署**：新建文件夹（如 `Minesweeper`），放入以下 5 个文件：
    * `main.py`, `controller.py`, `model.py`, `view.py`, `utils.py`
3.  **Run**: Open `main.py` and press the Play button (▶).
    * **运行**：打开 `main.py` 并点击运行按钮。

---

## 🕹 Controls (操作说明)

| Action (动作) | Effect (效果) | Description (说明) |
| :--- | :--- | :--- |
| **Tap Tile**<br>单击方块 | **Marking**<br>标记 | Cycle: Empty → 🚩 Flag → ❓ Question<br>循环切换：空 → 旗 → 问号 |
| **Double Tap**<br>双击方块 | **Reveal**<br>翻开 | Open the tile (Game Over if mine)<br>翻开格子（踩雷则结束） |
| **Tap Number**<br>单击数字 | **Auto-Clear**<br>自动扫雷 | Reveal neighbors if flags match the number<br>当旗帜数达标时，自动翻开周围格子 |

---

## 📂 File Structure (文件结构)

```text
Minesweeper/
├── main.py           # [Entry] App launcher & Menu / 程序入口与菜单
├── controller.py     # [Controller] Logic, Audio & Input / 控制器
├── model.py          # [Model] Game Logic & Algorithms / 纯游戏逻辑
├── view.py           # [View] Drawing & Rendering / 界面渲染
├── utils.py          # [Utils] iOS Haptics & Storage / 硬件交互与存档
└── minesweeper_records.json  # [Data] High Scores / 最高分存档
