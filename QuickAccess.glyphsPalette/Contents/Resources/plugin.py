# encoding: utf-8
import objc
from GlyphsApp import *
import traceback
from GlyphsApp.plugins import *
import vanilla
from AppKit import NSBundle

no_menu_item_selected_locale = Glyphs.localize({
    "en": "No menu item selected",
    "zh-Hans": "未选择菜单项",
    "zh-Hant": "未選擇菜單項"
})

select_menu_item_locale = Glyphs.localize({
    "en": "Select menu item",
    "zh-Hans": "选择菜单项",
    "zh-Hant": "選擇菜單項"
})

def get_system_button_title(key, fallback):
    bundle = NSBundle.bundleWithIdentifier_("com.apple.AppKit")
    title = str(bundle.localizedStringForKey_value_table_(key, None, None))
    if title == key or not title or title.lower() == key.lower():
        return fallback
    return title

# 递归构建菜单树，跳过分隔符
def build_menu_tree(ns_menu):
    tree = []
    for item in ns_menu.itemArray():
        if item.isSeparatorItem():
            continue
        node = {
            'title': item.title(),
            'nsitem': item,
            'children': build_menu_tree(item.submenu()) if item.submenu() else []
        }
        tree.append(node)
    return tree

# --- flatten_menu_tree 保证每项都带完整 path ---
def flatten_menu_tree(tree, prefix=None):
    prefix = prefix or []
    result = []
    for node in tree:
        path = prefix + [node['title']]
        indent = '    ' * len(prefix)
        result.append({
            'title': indent + node['title'],
            'path': path,
            'nsitem': node['nsitem'],
        })
        if node['children']:
            result.extend(flatten_menu_tree(node['children'], path))
    return result

# 展平树结构为带缩进的列表，方便 vanilla.List 展示
# prefix 记录路径
# 只依赖 tree 结构，不再判断 title
# 只传递 nsitem
class MenuSelectorWindow(vanilla.Window):
    def __init__(self, menu_tree, on_select, selected_path=None):
        super().__init__((400, 400), select_menu_item_locale, minSize=(300, 200))
        flat_tree = flatten_menu_tree(menu_tree)
        self._on_select = on_select
        self._selected_path = None
        self.flat_tree = flat_tree
        self.treeList = vanilla.List((10, 10, -10, -50), flat_tree,
            columnDescriptions=[{"title": "菜单项", "key": "title"}],
            selectionCallback=self.on_select_item)
        if hasattr(self.treeList, '_tableView'):
            self.treeList._tableView.setDoubleAction_(self._treeListDoubleClick_)
        ok_title = get_system_button_title("OK", "确定")
        cancel_title = get_system_button_title("Cancel", "取消")
        self.cancelButton = vanilla.Button((-180, -35, 80, 25), cancel_title, callback=lambda s: self.cancel())
        self.selectButton = vanilla.Button((-90, -35, 80, 25), ok_title, callback=lambda s: self.confirm())
        try:
            self.selectButton._nsObject.setBezelStyle_(1)  # NSRoundedBezelStyle
            self.selectButton._nsObject.setKeyEquivalent_("\r")  # 回车为快捷键
        except Exception as e:
            pass
        # 自动定位到已选项（通过 path）
        sel_index = 0
        if selected_path:
            for i, row in enumerate(flat_tree):
                if row['path'] == selected_path:
                    sel_index = i
                    break
        if flat_tree:
            self.treeList.setSelection([sel_index])
            self._selected_path = flat_tree[sel_index]['path']
            # 滚动到可见
            try:
                if hasattr(self.treeList, '_tableView'):
                    self.treeList._tableView.scrollRowToVisible_(sel_index)
            except Exception:
                pass

    def on_select_item(self, sender):
        sel = sender.getSelection()
        if sel:
            self._selected_path = sender[sel[0]]['path']

    def confirm(self):
        # 如果没有选中，尝试取当前高亮项或第一项
        if not self._selected_path and self.treeList.get():
            sel = self.treeList.getSelection()
            self._selected_path = self.treeList[sel[0]]['path'] if sel else self.treeList[0]['path']
        if self._selected_path:
            self._on_select(self._selected_path)
        self.close()

    def cancel(self):
        self.close()

    def _treeListDoubleClick_(self, sender):
        self.confirm()

# The actual palette!
class QuickAccess(PalettePlugin):
    @objc.python_method
    def settings(self):
        try:
            self.generation = 0
            self.name = Glyphs.localize({
                "en": "Quick Access",
                "zh-Hans": "快捷访问",
                "zh-Hant": "快捷訪問"
            })
            self.rowCount = 0
            self.rowControls = []
            self.height = 200
            self.paletteView = vanilla.Window((300, self.height))
            self.paletteView.group = vanilla.Group((0, 0, 0, 0))
            self.stackView = self.paletteView.group.stackView = vanilla.VerticalStackView("auto", views=[], spacing=4)
            self.paletteView.group.addAutoPosSizeRules([
                "H:|-margin-[stackView]-margin-|",
                "V:|-margin-[stackView]-margin-|"
            ], { "margin": 8 })
            self.dialog = self.paletteView.group.getNSView()
            self.menu_tree = build_menu_tree(Glyphs.menu[APP_MENU].menu())
            self.selected_path = None
            self.addRowButton = vanilla.Button("auto", "添加行", callback=self.addRowCallback)
            for _ in range(6):
                self.addRowCallback(self.addRowButton)
            self.update()
        except Exception as e:
            self.logError(traceback.format_exc())

    @objc.python_method
    def createRow(self, selected_path=None):
        group = vanilla.Group((0, 0, -0, 30))
        text = selected_path[-1] if selected_path else no_menu_item_selected_locale
        group.menuPathButton = vanilla.Button("auto", text, callback=lambda s: self.runMenuItem(group))
        group.execButton = vanilla.Button("auto", "⋮", callback=lambda s: self.openMenuSelector(group))
        group.addAutoPosSizeRules([
            "H:|-margin-[menuPathButton(==150)]-[execButton]-margin-|"
        ], { "margin": 4 })
        # 设置省略号显示
        try:
            nsbtn = group.menuPathButton._nsObject
            nsbtn.setLineBreakMode_(4)  # NSLineBreakByTruncatingTail
        except Exception as e:
            pass
        group.selected_path = selected_path
        self.rowControls.append(group)
        return group

    @objc.python_method
    def openMenuSelector(self, group):
        def on_select(path):
            text = path[-1] if path else no_menu_item_selected_locale
            group.selected_path = path
            group.menuPathButton.setTitle(text)
            try:
                group.menuPathButton._nsObject.display()
                self.paletteView.group.getNSView().setNeedsDisplay_(True)
                self.paletteView.getNSView().setNeedsDisplay_(True)
            except Exception as e:
                pass
            group._menuSelectorWindow = None
        win = MenuSelectorWindow(self.menu_tree, on_select, selected_path=group.selected_path)
        group._menuSelectorWindow = win
        win.open()

    @objc.python_method
    def updateRowUI(self, group):
        text = u" > ".join(group.selected_path) if getattr(group, 'selected_path', None) else no_menu_item_selected_locale
        try:
            if hasattr(group.menuPathText, 'setText'):
                group.menuPathText.setText(text)
            else:
                group.menuPathText.set(text)
            nsview = group.menuPathText.getNSView()
            nsview.setStringValue_(text)
            nsview.display()
            group.getNSView().setNeedsDisplay_(True)
        except Exception as e:
            self.logError(f"[DEBUG] updateRowUI set failed: {e}")

    @objc.python_method
    def addRowCallback(self, sender):
        new_row = self.createRow()
        self.stackView.appendView(new_row)
        self.rowCount += 1
        self.update()

    @objc.python_method
    def runMenuItem(self, group):
        path = getattr(group, 'selected_path', None)
        if not path:
            # self.logError("[QuickAccess] No path in group.selected_path")
            return
        ns_menu = None
        try:
            ns_menu = Glyphs.menu[APP_MENU].menu()
        except Exception as e:
            # self.logError(f"[QuickAccess] Failed to get main menu: {e}")
            return
        nsitem = find_nsitem_by_path(ns_menu, path)
        if not nsitem:
            # self.logError(f"[QuickAccess] Cannot find NSMenuItem for path: {path}")
            return
        origTarget = nsitem.target()
        origAction = nsitem.action()
        # self.logError(f"[QuickAccess] path={path}, nsitem={nsitem}, target={origTarget}, action={origAction}")
        from AppKit import NSApp
        if origTarget and origAction:
            try:
                import objc
                objc.super(type(origTarget), origTarget).performSelectorOnMainThread_withObject_waitUntilDone_(origAction, nsitem, False)
            except Exception as e:
                # self.logError(f"[QuickAccess] Exception when performing action: {e}")
                pass
        elif origAction:
            try:
                NSApp.sendAction_to_from_(origAction, None, nsitem)
            except Exception as e:
                # self.logError(f"[QuickAccess] Exception when sendAction_to_from_: {e}")
                pass
        # else:
        #     self.logError("[QuickAccess] NSMenuItem has no target or action")

    @objc.python_method
    def update(self, sender=None):
        self.height = (self.rowCount + 1) * 30 - 4
        self.paletteView.group.resize(300, self.height)
        self.paletteView.resize(300, self.height)

    @objc.python_method
    def __file__(self):
        return __file__

def find_nsitem_by_path(ns_menu, path):
    """递归在当前 ns_menu 下按 title 路径查找 NSMenuItem"""
    if not path:
        return None
    for item in ns_menu.itemArray():
        if item.title() == path[0]:
            if len(path) == 1:
                return item
            submenu = item.submenu()
            if submenu:
                return find_nsitem_by_path(submenu, path[1:])
    return None
