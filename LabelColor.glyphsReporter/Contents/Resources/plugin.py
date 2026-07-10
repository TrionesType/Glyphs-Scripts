# language: python
# encoding: utf-8
from __future__ import division, print_function, unicode_literals

import objc
from GlyphsApp import *
from GlyphsApp.plugins import *
from AppKit import NSBezierPath, NSRect

class ColorLabelsReporter(ReporterPlugin):

    @objc.python_method
    def settings(self):
        self.menuName = "Color Labels"
        self.screenHeightPx = 8  # 高度固定为屏幕像素点

    @objc.python_method
    def __file__(self):
        return __file__
	
    @objc.python_method
    def background(self, layer):
        self.draw_layer(layer)

        return
    
    @objc.python_method
    def inactiveLayerBackground(self, layer):
        self.draw_layer(layer)

        return
    
    def draw_layer(self, layer):
        layerColor = layer.colorObject
        glyphColor = layer.parent.colorObject

        if glyphColor is None and layerColor is None:
                return

        y_origin = layer.descender - 16
        height = self.screenHeightPx / self.controller.scale
        if glyphColor is not None:
            if layerColor is not None:
                # 同时存在两种颜色：glyph color 占左半
                left_rect = NSRect((0, y_origin - height), (layer.width/2, height))
            else:
                # 只有 glyph color：占满整个宽度
                left_rect = NSRect((0, y_origin - height), (layer.width, height))
            glyphColor.setFill()
            NSBezierPath.bezierPathWithRect_(left_rect).fill()

        # 绘制右区（layer color）
        if layerColor is not None:
            right_rect = NSRect((layer.width/2, y_origin - height), (layer.width/2, height))
            layerColor.setFill()
            NSBezierPath.bezierPathWithRect_(right_rect).fill()

        return