#MenuTitle: Combine Radicals
# -*- coding: utf-8 -*-

def __combine_two_main():
    def get_possible_component_bound_guide(layer):
        for guide in layer.guides:
            if guide.name == 'cb':
                return guide
        for other_layer in layer.parent.layers:
            for guide in other_layer.guides:
                if guide.name == 'cb':
                    return guide
        return None

    def shape_left_to(layer, x):
        return [
            shape 
            for shape in layer.shapes
            if shape.bounds.origin.x + shape.bounds.size.width/2 <= x
        ]

    def shape_right_to(layer, x):
        return [
            shape 
            for shape in layer.shapes
            if shape.bounds.origin.x + shape.bounds.size.width/2 >= x
        ]

    def shape_top_to(layer, y):
        return [
            shape 
            for shape in layer.shapes
            if shape.bounds.origin.y + shape.bounds.size.height/2 >= y
        ]

    def shape_bottom_to(layer, y):
        return [
            shape 
            for shape in layer.shapes
            if shape.bounds.origin.y + shape.bounds.size.height/2 <= y
        ]

    layers = Glyphs.font.selectedLayers

    if len(layers) < 3:
        raise Exception("Not enough layers selected")

    target_layer = layers[0]
    layer1 = layers[1]
    layer2 = layers[2]

    target_guide = get_possible_component_bound_guide(target_layer)
    if target_guide is None:
        raise Exception("Missing 'cb' guide")

    layer1_guide = get_possible_component_bound_guide(layer1)
    layer2_guide = get_possible_component_bound_guide(layer2)
    for layer_guide in [layer1_guide, layer2_guide]:
        if layer_guide is None:
            raise Exception("Missing 'cb' guide in one of the component layers")
        if layer_guide.angle % 180 != target_guide.angle % 180:
            raise Exception("Guide angle does not match between target and component layers")

    for layer in [layer1, layer2]:
        possible_guide = get_possible_component_bound_guide(layer)
        if possible_guide is None:
            raise Exception("Missing 'cb' guide")
        if possible_guide.angle % 180 != target_guide.angle % 180:
            raise Exception("Guide angle does not match")
        
    target_layer.parent.beginUndo()
    if target_guide.angle % 180 == 90: # LR
        target_layer.shapes.clear()

        layer1_shapes = shape_left_to(layer1, layer1_guide.position.x)
        layer2_shapes = shape_right_to(layer2, layer2_guide.position.x)
        for shape in layer1_shapes + layer2_shapes:
            target_layer.shapes.append(shape.copy())

        for shape in target_layer.shapes: shape.selected = False
        for i in range(len(layer1_shapes)):
            target_layer.shapes[i].selected = True
        Foreglow.processLayer(target_layer, {
            "morph_scale_x": target_guide.position.x/layer1_guide.position.x,
            "align": "cl"
        })
        for shape in target_layer.shapes: shape.selected = False
        for i in range(len(layer1_shapes), len(target_layer.shapes)):
            target_layer.shapes[i].selected = True
        Foreglow.processLayer(target_layer, {
            "morph_scale_x": (target_layer.width - target_guide.position.x)/(layer2.width - layer2_guide.position.x),
            "align": "cr"
        })
        for shape in target_layer.shapes: shape.selected = False

    elif target_guide.angle % 180 == 0: # TB
        target_layer.shapes.clear()

        layer1_shapes = shape_top_to(layer1, layer1_guide.position.y)
        layer2_shapes = shape_bottom_to(layer2, layer2_guide.position.y)
        for shape in layer1_shapes + layer2_shapes:
            target_layer.shapes.append(shape.copy())

        for shape in target_layer.shapes: shape.selected = False
        for i in range(len(layer1_shapes)):
            target_layer.shapes[i].selected = True
        Foreglow.processLayer(target_layer, {
            "morph_scale_y": (target_layer.ascender - target_guide.position.y)/(layer1.ascender - layer1_guide.position.y),
            "align": "tc"
        })
        for shape in target_layer.shapes: shape.selected = False
        for i in range(len(layer1_shapes), len(target_layer.shapes)):
            target_layer.shapes[i].selected = True
        Foreglow.processLayer(target_layer, {
            "morph_scale_y": (target_guide.position.y - target_layer.descender)/(layer2_guide.position.y - layer2.descender),
            "align": "bc"
        })
        for shape in target_layer.shapes: shape.selected = False

    target_layer.parent.endUndo()

__combine_two_main()