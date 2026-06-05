#MenuTitle: Combine Radicals for All Layers
# -*- coding: utf-8 -*-

def __combine_two_main():
    def get_component_bound_guide(layer):
        for guide in layer.guides:
            if guide.name == 'cb':
                return guide
        return None

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
        
    target_glyph = target_layer.parent
    target_glyph.beginUndo()
    
    for current_target in target_glyph.layers:
        try:
            if layer1.parent.layers[current_target.name] is None or layer2.parent.layers[current_target.name] is None:
                continue
            current_layer1 = layer1.parent.layers[current_target.name]
            current_layer2 = layer2.parent.layers[current_target.name]
            current_target_guide = get_component_bound_guide(current_target) or target_guide
            current_layer1_guide = get_component_bound_guide(current_layer1) or layer1_guide
            current_layer2_guide = get_component_bound_guide(current_layer2) or layer2_guide
            if target_guide.angle % 180 == 90: # LR
                current_target.shapes.clear()

                layer1_shapes = shape_left_to(current_layer1, current_layer1_guide.position.x)
                layer2_shapes = shape_right_to(current_layer2, current_layer2_guide.position.x)
                for shape in layer1_shapes + layer2_shapes:
                    current_target.shapes.append(shape.copy())

                for shape in current_target.shapes: shape.selected = False
                for i in range(len(layer1_shapes)):
                    current_target.shapes[i].selected = True
                Foreglow.processLayer(current_target, {
                    "morph_scale_x": current_target_guide.position.x/current_layer1_guide.position.x,
                    "align": "cl"
                })
                for shape in current_target.shapes: shape.selected = False
                for i in range(len(layer1_shapes), len(current_target.shapes)):
                    current_target.shapes[i].selected = True
                Foreglow.processLayer(current_target, {
                    "morph_scale_x": (current_target.width - current_target_guide.position.x)/(current_layer2.width - current_layer2_guide.position.x),
                    "align": "cr"
                })
                for shape in current_target.shapes: shape.selected = False

            elif target_guide.angle % 180 == 0: # TB
                current_target.shapes.clear()

                layer1_shapes = shape_top_to(current_layer1, current_layer1_guide.position.y)
                layer2_shapes = shape_bottom_to(current_layer2, current_layer2_guide.position.y)
                for shape in layer1_shapes + layer2_shapes:
                    current_target.shapes.append(shape.copy())

                for shape in current_target.shapes: shape.selected = False
                for i in range(len(layer1_shapes)):
                    current_target.shapes[i].selected = True
                Foreglow.processLayer(current_target, {
                    "morph_scale_y": (current_target.ascender - current_target_guide.position.y)/(current_layer1.ascender - current_layer1_guide.position.y),
                    "align": "tc"
                })
                for shape in current_target.shapes: shape.selected = False
                for i in range(len(layer1_shapes), len(current_target.shapes)):
                    current_target.shapes[i].selected = True
                Foreglow.processLayer(current_target, {
                    "morph_scale_y": (current_target_guide.position.y - current_target.descender)/(current_layer2_guide.position.y - current_layer2.descender),
                    "align": "bc"
                })
                for shape in current_target.shapes: shape.selected = False
        except Exception as e:
            print(f"Error when handling {current_target.name}: {e}")
            continue

    target_glyph.endUndo()

__combine_two_main()