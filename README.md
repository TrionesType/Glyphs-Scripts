# Glyphs Scripts from TrionesType

This is the repository for Glyphs scripts from TrionesType.

## Scripts

### Merge Collinear

```
Merge Collinear.py
```

<img width="1814" height="918" src="https://github.com/user-attachments/assets/99ca96d6-e4b2-4990-bdb1-48e1a26b591c" />


This script merges all contours with collinear segments while keeping compatibility.

该脚本用于合并带有共线线段的轮廓，同时保持兼容性。

### Combine Radicals (for All Layers)

```
Combine Radicals.py
Combine Radicals for All Layers.py
```

<p align="center" width="100%">
<video src="https://github.com/user-attachments/assets/22917f09-ca5a-4618-8668-c46987fd45b4" width="80%" controls></video>
</p>

This script depends on [Foreglow](https://jaderipple.com/foreglow/) and enables combining radicals from two source glyphs to generate a new composite glyph. For example: extracting the left radical from 桥 and the right radical from 酬 produces the new glyph 栦.

Workflow:

1. **Open glyphs for editing**: Load all three glyphs—栦, 桥, 酬—into edit view, with the target glyph (栦) being empty (ready to receive radical paths).
2. **Add component-boundary guide**: For each of the three glyphs, add a vertical guide named `cb` (short for component bound) to mark the boundary between left and right radicals.
3. **Execute combination**: Using the Text tool, select all three glyphs, then run the script Combine radicals (for all layers). The script will automatically extract the left radical from 桥 and the right radical from 酬, then compose them into the target glyph 栦.

本脚本依赖[「参数化变形」](https://jaderipple.com/foreglow/)，功能是将两个汉字的偏旁组合生成新字形。例如：取「桥」的左偏 +「酬」的右旁 → 组合成新字「栦」。

操作流程：

1. **打开字形**：同时打开「栦桥酬」三个字形进入编辑视图，目标字形「栦」为空字形（待填充状态）。
2. **添加参考线**：为这三个字形分别添加一条名为 cb（component bound，部件边界）的参考线，用于标记左右部首的分界位置。
3. **执行组合**：使用文本工具选中这三个字形，运行脚本 Combine radicals (for all layers)。脚本将自动提取「桥」的左部首与「酬」的右部首，组合生成新字形「栦」。

## Find Similar Han

```
Find Similar Han.py
Find Similar Han.pkl
```

Find similar CJK ideographs. This script searches the exported glyphs for Hanzi that are visually similar to the currently active glyph, returning 10 results by default. Note that this similarity does not necessarily mean the glyphs share the same radicals — they simply “look alike”.

**Note: Please ensure that the `.pkl` file and the `.py` file are placed in the same directory, and avoid renaming them.**

查找形态相似的汉字。该脚本会从已导出的字形中找出与当前活跃字形比较相似的汉字，默认查找 10 个。这种相似未必意味着一定包含相同的汉字部件，而仅仅是「看起来很像」。

**注意：请确保 .pkl 文件和 .py 文件在同一目录下，且不要轻易修改文件名。**

## Plugins

### Show Color Labels

```
LabelColor.glyphsReporter
```

<img width="409" height="262" src="https://github.com/user-attachments/assets/54f10209-db88-4fd6-9851-6732204d2d37" />


Show color labels for layers and glyphs in the edit view with colored underlines. Control visibility via “Scripts → Show Color Labels”.

在编辑界面上一目了然地用下划线展示图层和字符颜色标签。在「脚本 → 显示 Color Labels」控制显示与否。

### Quick Access

```
Quick Access.glyphsPalette
```

<img width="511" height="288" src="https://github.com/user-attachments/assets/f1e707d8-0f48-434b-8c51-462dbaa22b8b" />

Show a palette with quick access to menu items.

将菜单项添加至右侧栏，方便快速调用。


## License
Apache License Version 2.0
