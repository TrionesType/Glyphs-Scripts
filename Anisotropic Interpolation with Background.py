# MenuTitle: Anisotropic Interpolation with Background
# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals
__doc__ = """
Interpolates selected foreground layers against their backgrounds with separate X and Y interpolation factors.
"""

import vanilla
from Foundation import NSPoint
from GlyphsApp import Glyphs, Message, GSLayer


def interpolateValue(foregroundValue, backgroundValue, interpolationFactor):
	return float(foregroundValue) * (1.0 - interpolationFactor) + float(backgroundValue) * interpolationFactor


def interpolatePoint(foregroundPoint, backgroundPoint, xInterpolationFactor, yInterpolationFactor):
	return NSPoint(
		interpolateValue(foregroundPoint.x, backgroundPoint.x, xInterpolationFactor),
		interpolateValue(foregroundPoint.y, backgroundPoint.y, yInterpolationFactor),
	)


def interpolateDicts(dictA, dictB, interpolationFactor=0.5):
	commonKeys = set(dictA.keys()) & set(dictB.keys())
	return {
		key: interpolateValue(dictA[key], dictB[key], interpolationFactor)
		for key in commonKeys
	}


class Anisotropic(object):
	prefDomain = "com.glyphsapp.Anisotropic"
	prefDict = {
		"xInterpolation": 0.0,
		"yInterpolation": 0.0,
	}

	def __init__(self):
		self.thisFont = Glyphs.font
		self.layerData = []
		self.skippedLayers = []
		self.didApply = False

		if not self.collectSelectedLayers():
			return

		windowWidth = 360
		windowHeight = 120
		self.w = vanilla.FloatingWindow(
			(windowWidth, windowHeight),
			"Anisotropic Interpolation with Background",
			minSize=(windowWidth, windowHeight),
			maxSize=(windowWidth, windowHeight),
			autosaveName=self.domain("mainwindow"),
		)
		self.w.bind("close", self.windowClose)

		linePos, inset, lineHeight = 12, 15, 24

		self.w.xText = vanilla.TextBox((inset, linePos + 2, 40, 14), "X:", sizeStyle="small")
		self.w.xInterpolation = vanilla.Slider(
			(inset + 28, linePos, -inset - 50, 19),
			value=0.0,
			minValue=-20.0,
			maxValue=120.0,
			sizeStyle="small",
			callback=self.sliderUpdate,
		)
		self.w.xInterpolation.setToolTip("0% keeps the foreground X positions, 100% uses the background X positions. Values outside the range extrapolate.")
		self.w.xValue = vanilla.EditText((-inset - 44, linePos - 1, -inset, 19), "0", sizeStyle="small", callback=self.textUpdate)
		self.w.xValue.setToolTip("X interpolation in percent.")
		linePos += lineHeight

		self.w.yText = vanilla.TextBox((inset, linePos + 2, 40, 14), "Y:", sizeStyle="small")
		self.w.yInterpolation = vanilla.Slider(
			(inset + 28, linePos, -inset - 50, 19),
			value=0.0,
			minValue=-20.0,
			maxValue=120.0,
			sizeStyle="small",
			callback=self.sliderUpdate,
		)
		self.w.yInterpolation.setToolTip("0% keeps the foreground Y positions, 100% uses the background Y positions. Values outside the range extrapolate.")
		self.w.yValue = vanilla.EditText((-inset - 44, linePos - 1, -inset, 19), "0", sizeStyle="small", callback=self.textUpdate)
		self.w.yValue.setToolTip("Y interpolation in percent.")
		linePos += lineHeight

		self.w.resetButton = vanilla.Button((-160, -20 - inset, -90, -inset), "Reset", callback=self.reset)
		self.w.applyButton = vanilla.Button((-80, -20 - inset, -inset, -inset), "Apply", callback=self.applyInterpolation)
		self.w.setDefaultButton(self.w.applyButton)

		self.LoadPreferences()
		self.sliderUpdate()

		self.w.open()
		self.w.makeKey()

	def domain(self, prefName):
		return "%s.%s" % (self.prefDomain, prefName)

	def registerDefaults(self):
		for prefName, prefValue in self.prefDict.items():
			Glyphs.registerDefault(self.domain(prefName), prefValue)

	def pref(self, prefName):
		self.registerDefaults()
		return Glyphs.defaults[self.domain(prefName)]

	def prefFloat(self, prefName):
		return float(self.pref(prefName))

	def LoadPreferences(self):
		self.registerDefaults()
		for prefName in self.prefDict.keys():
			uiElement = getattr(self.w, prefName, None)
			if uiElement:
				uiElement.set(self.pref(prefName))

	def SavePreferences(self, sender=None):
		for prefName in self.prefDict.keys():
			uiElement = getattr(self.w, prefName, None)
			if uiElement:
				Glyphs.defaults[self.domain(prefName)] = uiElement.get()

	def usableLayer(self, thisLayer):
		return isinstance(thisLayer, GSLayer)

	def backgroundLayerForLayer(self, thisLayer):
		backgroundLayer = getattr(thisLayer, "background", None)
		if callable(backgroundLayer):
			try:
				backgroundLayer = backgroundLayer()
			except Exception:
				return None
		if isinstance(backgroundLayer, GSLayer):
			return backgroundLayer
		return None

	def collectSelectedLayers(self):
		if not self.thisFont:
			Message(title="No Font Open", message="Please open a font first.", OKButton=None)
			return False

		selectedLayers = self.thisFont.selectedLayers
		if not selectedLayers:
			Message(title="No Selection", message="Please select one or more layers.", OKButton=None)
			return False

		reportIncompatibleLayers = len(selectedLayers) == 1

		for thisLayer in selectedLayers:
			if not self.usableLayer(thisLayer):
				continue

			backgroundLayer = self.backgroundLayerForLayer(thisLayer)
			if backgroundLayer is None:
				if reportIncompatibleLayers:
					self.skippedLayers.append((self.layerName(thisLayer), ("No usable background layer.",)))
				continue

			problems = self.compatibilityProblems(thisLayer, backgroundLayer)
			if problems:
				if reportIncompatibleLayers:
					self.skippedLayers.append((self.layerName(thisLayer), problems))
				continue

			self.layerData.append({
				"liveLayer": thisLayer,
				"foregroundLayer": thisLayer.copy(),
				"backgroundLayer": backgroundLayer.copy(),
			})

		if reportIncompatibleLayers and self.skippedLayers:
			self.reportSkippedLayers()

		if not self.layerData:
			if reportIncompatibleLayers and self.skippedLayers:
				Message(
					title="Incompatible Layer",
					message="The selected layer is not compatible with its background. Details in Macro Window.",
					OKButton=None,
				)
			elif len(selectedLayers) == 1:
				Message(
					title="No Usable Layer",
					message="Please select a glyph layer, not a newline or other control layer.",
					OKButton=None,
				)
			return False

		return True

	def layerName(self, thisLayer):
		glyphName = thisLayer.parent.name if thisLayer.parent else thisLayer.name
		if thisLayer.name:
			return "%s (%s)" % (glyphName, thisLayer.name)
		return glyphName

	def compatibilityProblems(self, foregroundLayer, backgroundLayer):
		problems = []

		if not self.usableLayer(foregroundLayer) or not self.usableLayer(backgroundLayer):
			return ["No usable background layer."]

		if len(foregroundLayer.paths) != len(backgroundLayer.paths):
			problems.append("Different path counts: %i vs %i." % (len(foregroundLayer.paths), len(backgroundLayer.paths)))
		else:
			for pathIndex, (foregroundPath, backgroundPath) in enumerate(zip(foregroundLayer.paths, backgroundLayer.paths)):
				if len(foregroundPath.nodes) != len(backgroundPath.nodes):
					problems.append(
						"Path %i has different node counts: %i vs %i." % (
							pathIndex + 1,
							len(foregroundPath.nodes),
							len(backgroundPath.nodes),
						)
					)

		if len(foregroundLayer.components) != len(backgroundLayer.components):
			problems.append("Different component counts: %i vs %i." % (len(foregroundLayer.components), len(backgroundLayer.components)))
		else:
			for componentIndex, (foregroundComponent, backgroundComponent) in enumerate(zip(foregroundLayer.components, backgroundLayer.components)):
				if foregroundComponent.componentName != backgroundComponent.componentName:
					problems.append(
						"Component %i differs: %s vs %s." % (
							componentIndex + 1,
							foregroundComponent.componentName,
							backgroundComponent.componentName,
						)
					)

		return problems

	def reportSkippedLayers(self):
		Glyphs.clearLog()
		Glyphs.showMacroWindow()
		print("Anisotropic: skipped incompatible layers\n")
		for layerName, problems in self.skippedLayers:
			print("❌ %s" % layerName)
			for problem in problems:
				print("   %s" % problem)
			print()

	def valueString(self, value):
		return ("%.2f" % value).rstrip("0").rstrip(".")

	def clampedInterpolationValue(self, value):
		return min(120.0, max(-20.0, value))

	def interpolationValueFromText(self, valueString):
		cleanValue = valueString.strip()
		if cleanValue.endswith("%"):
			cleanValue = cleanValue[:-1].strip()
		if cleanValue in ("", "+", "-", ".", "+.", "-."):
			return None
		return self.clampedInterpolationValue(float(cleanValue))

	def syncValueFields(self):
		self.w.xValue.set(self.valueString(self.prefFloat("xInterpolation")))
		self.w.yValue.set(self.valueString(self.prefFloat("yInterpolation")))

	def sliderUpdate(self, sender=None):
		if sender:
			self.SavePreferences(sender)
		self.syncValueFields()
		self.previewInterpolation()

	def textUpdate(self, sender=None):
		if not sender:
			return

		try:
			value = self.interpolationValueFromText(sender.get())
			if value is None:
				return
			if sender == self.w.xValue:
				self.w.xInterpolation.set(value)
			else:
				self.w.yInterpolation.set(value)
			self.SavePreferences()
			self.syncValueFields()
			self.previewInterpolation()
		except Exception:
			self.syncValueFields()

	def updateStatus(self, message=None):
		return

	def reset(self, sender=None):
		self.w.xInterpolation.set(0.0)
		self.w.yInterpolation.set(0.0)
		self.SavePreferences()
		self.syncValueFields()
		self.sliderUpdate()

	def redraw(self):
		if self.thisFont.currentTab:
			self.thisFont.currentTab.forceRedraw()
		elif self.thisFont.fontView:
			self.thisFont.fontView.redraw()

	def previewInterpolation(self):
		try:
			xInterpolationFactor = self.prefFloat("xInterpolation") / 100.0
			yInterpolationFactor = self.prefFloat("yInterpolation") / 100.0
			scalarInterpolationFactor = (xInterpolationFactor + yInterpolationFactor) * 0.5

			self.thisFont.disableUpdateInterface()
			try:
				for layerInfo in self.layerData:
					self.applyInterpolationToLayer(
						layerInfo["liveLayer"],
						layerInfo["foregroundLayer"],
						layerInfo["backgroundLayer"],
						xInterpolationFactor,
						yInterpolationFactor,
						scalarInterpolationFactor,
					)
			finally:
				self.thisFont.enableUpdateInterface()

			self.redraw()
			self.updateStatus()
		except Exception as e:
			Glyphs.showMacroWindow()
			print("Anisotropic Preview Error: %s" % e)
			import traceback
			print(traceback.format_exc())

	def restoreOriginalLayers(self):
		self.thisFont.disableUpdateInterface()
		try:
			for layerInfo in self.layerData:
				self.applyInterpolationToLayer(
					layerInfo["liveLayer"],
					layerInfo["foregroundLayer"],
					layerInfo["foregroundLayer"],
					0.0,
					0.0,
					0.0,
				)
		finally:
			self.thisFont.enableUpdateInterface()

		self.redraw()

	def windowClose(self, sender):
		if not self.didApply:
			self.restoreOriginalLayers()

	def applyInterpolation(self, sender=None):
		try:
			if sender:
				self.SavePreferences(sender)

			self.previewInterpolation()
			self.didApply = True
			self.w.close()
		except Exception as e:
			Glyphs.showMacroWindow()
			print("Anisotropic Error: %s" % e)
			import traceback
			print(traceback.format_exc())

	def applyInterpolationToLayer(self, liveLayer, foregroundLayer, backgroundLayer, xInterpolationFactor, yInterpolationFactor, scalarInterpolationFactor):
		for livePath, foregroundPath, backgroundPath in zip(liveLayer.paths, foregroundLayer.paths, backgroundLayer.paths):
			for liveNode, foregroundNode, backgroundNode in zip(livePath.nodes, foregroundPath.nodes, backgroundPath.nodes):
				liveNode.setPosition_(
					interpolatePoint(
						foregroundNode.position,
						backgroundNode.position,
						xInterpolationFactor,
						yInterpolationFactor,
					)
				)

		foregroundAnchors = {anchor.name: anchor for anchor in foregroundLayer.anchors}
		backgroundAnchors = {anchor.name: anchor for anchor in backgroundLayer.anchors}
		for liveAnchor in liveLayer.anchors:
			foregroundAnchor = foregroundAnchors.get(liveAnchor.name)
			backgroundAnchor = backgroundAnchors.get(liveAnchor.name)
			if foregroundAnchor and backgroundAnchor:
				liveAnchor.setPosition_(
					interpolatePoint(
						foregroundAnchor.position,
						backgroundAnchor.position,
						xInterpolationFactor,
						yInterpolationFactor,
					)
				)

		for liveComponent, foregroundComponent, backgroundComponent in zip(liveLayer.components, foregroundLayer.components, backgroundLayer.components):
			liveComponent.position = interpolatePoint(
				foregroundComponent.position,
				backgroundComponent.position,
				xInterpolationFactor,
				yInterpolationFactor,
			)
			liveComponent.scale = (
				interpolateValue(foregroundComponent.scale[0], backgroundComponent.scale[0], xInterpolationFactor),
				interpolateValue(foregroundComponent.scale[1], backgroundComponent.scale[1], yInterpolationFactor),
			)
			# Scalar component settings fall back to the mean interpolation factor.
			liveComponent.rotation = interpolateValue(foregroundComponent.rotation, backgroundComponent.rotation, scalarInterpolationFactor)

			foregroundValues = dict(foregroundComponent.smartComponentValues or {})
			backgroundValues = dict(backgroundComponent.smartComponentValues or {})
			interpolatedValues = interpolateDicts(foregroundValues, backgroundValues, scalarInterpolationFactor)
			if interpolatedValues:
				liveComponent.setPieceSettings_(interpolatedValues)


Anisotropic()