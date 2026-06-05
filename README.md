# Glyphs Scripts from TrionesType

This is the repository for Glyphs scripts from TrionesType.

## Scripts Included

### Merge Collinear

```
Merge Collinear.py
```

This script merges all contours with collinear segments while keeping compatibility.

改脚本用于合并带有共线线段的轮廓，同时保持兼容性。

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

## License
Apache License Version 2.0