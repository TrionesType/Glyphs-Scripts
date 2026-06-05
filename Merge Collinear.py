#MenuTitle: Merge Collinear Contours
# -*- coding: utf-8 -*-
from GlyphsApp import *
import math
import re

def __merge_collinear_main():
    # -------------------------
    # Configuration
    # -------------------------
    # Tolerances and thresholds (adjust as needed)
    COORD_TOLERANCE = 0.5          # Coordinate tolerance for same horizontal/vertical line (units)
    MIN_OVERLAP = 0.5              # Minimum projection overlap length (units)
    COLLINEAR_NODE_TOLERANCE = 0.05  # Leniency for removing collinear points (smaller = stricter)
    # -------------------------
    # Helper functions
    # -------------------------
    def safe_attr(obj, name, default=None):
        try:
            return getattr(obj, name, default)
        except Exception:
            return default

    def pt_x(p):
        return p.x if hasattr(p, "x") else p[0]
    def pt_y(p):
        return p.y if hasattr(p, "y") else p[1]

    # -------------------------
    # Path/segment detection functions
    # -------------------------
    def segments_of_path(path):
        """
        Return a simplified list of horizontal or vertical segments in the path that can be treated as straight lines:
        Each item is ('h' or 'v', constant_coord, start, end)
        """
        results = []
        try:
            segs = path.segments
        except Exception:
            return results

        for seg in segs:
            if len(seg) != 2:
                continue
            p0, p1 = seg[0], seg[1]
            x0, y0 = pt_x(p0), pt_y(p0)
            x1, y1 = pt_x(p1), pt_y(p1)
            if abs(y0 - y1) <= COORD_TOLERANCE:
                y_mid = (y0 + y1) / 2.0
                xmin, xmax = sorted([x0, x1])
                results.append(('h', y_mid, xmin, xmax))
            elif abs(x0 - x1) <= COORD_TOLERANCE:
                x_mid = (x0 + x1) / 2.0
                ymin, ymax = sorted([y0, y1])
                results.append(('v', x_mid, ymin, ymax))
        return results

    def intervals_overlap(a_min, a_max, b_min, b_max):
        return min(a_max, b_max) - max(a_min, b_min)

    def paths_pair_collinear_in_layer(path_a, path_b):
        """Check if two paths have horizontal or vertical overlapping segments in the same layer (satisfying tolerance and minimum overlap)."""
        segs_a = segments_of_path(path_a)
        segs_b = segments_of_path(path_b)
        for sa in segs_a:
            for sb in segs_b:
                if sa[0] != sb[0]:
                    continue
                if abs(sa[1] - sb[1]) > COORD_TOLERANCE:
                    continue
                overlap = intervals_overlap(sa[2], sa[3], sb[2], sb[3])
                if overlap >= MIN_OVERLAP:
                    return True
        return False

    def pair_is_collinear_across_layers(index_a, index_b, layers):
        """Check if the path pair satisfies the collinear overlap condition across all given layers."""
        for layer in layers:
            paths = layer.paths
            if index_a >= len(paths) or index_b >= len(paths):
                return False
            if not paths_pair_collinear_in_layer(paths[index_a], paths[index_b]):
                return False
        return True

    def paths_same_direction_across_layers(index_a, index_b, layers):
        """Require that on each layer, both paths are closed and have the same direction (conservative strategy)."""
        for layer in layers:
            paths = layer.paths
            if index_a >= len(paths) or index_b >= len(paths):
                return False
            pa = paths[index_a]
            pb = paths[index_b]
            try:
                if not pa.closed or not pb.closed:
                    return False
                dir_a = safe_attr(pa, "direction", None)
                dir_b = safe_attr(pb, "direction", None)
                if dir_a is None or dir_b is None:
                    return False
                if int(dir_a) != int(dir_b):
                    return False
            except Exception:
                return False
        return True

    # -------------------------
    # Collinear point cleanup and merging
    # -------------------------
    def remove_collinear_nodes_from_path(path, col_tol=COLLINEAR_NODE_TOLERANCE):
        """
        Remove collinear middle points from the path (only considers line-type nodes).
        Uses a ratio of triangle area to side length for the test.
        """
        try:
            nodes = list(path.nodes)
        except Exception:
            return
        n = len(nodes)
        if n < 3:
            return
        closed = bool(path.closed)
        indices_to_remove = []

        for i in range(n):
            if not closed and (i == 0 or i == n - 1):
                continue
            prev = nodes[(i - 1) % n]
            curr = nodes[i]
            nxt = nodes[(i + 1) % n]
            try:
                if prev.type != 'line' or curr.type != 'line' or nxt.type != 'line':
                    continue
            except Exception:
                continue
            Ax, Ay = prev.x, prev.y
            Bx, By = curr.x, curr.y
            Cx, Cy = nxt.x, nxt.y
            area = abs((Bx - Ax) * (Cy - By) - (By - Ay) * (Cx - Bx))
            len_ab = math.hypot(Bx - Ax, By - Ay)
            len_bc = math.hypot(Cx - Bx, Cy - By)
            denom = max(len_ab, len_bc, 1e-6)
            if area / denom <= col_tol:
                indices_to_remove.append(i)

        for idx in sorted(set(indices_to_remove), reverse=True):
            try:
                del path.nodes[idx]
            except Exception:
                pass

    def paths_are_compatible(path_a, path_b):
        """Check if two paths are compatible (prefer Glyphs API, otherwise compare node types and counts)."""
        try:
            result = path_a.isCompatible(path_b)
            if isinstance(result, bool):
                return result
            if result is not None:
                return bool(result)
        except Exception:
            pass

        try:
            nodes_a = list(path_a.nodes)
            nodes_b = list(path_b.nodes)
            if len(nodes_a) != len(nodes_b):
                return False
            for na, nb in zip(nodes_a, nodes_b):
                if getattr(na, "type", None) != getattr(nb, "type", None):
                    return False
                if getattr(na, "smooth", False) != getattr(nb, "smooth", False):
                    return False
            return True
        except Exception:
            return False

    def simulate_merge_paths_for_layer(layer, idx_a, idx_b):
        """Simulate merging two paths without modifying the original layer, and return the merged result list."""
        try:
            path_a = layer.paths[idx_a]
            path_b = layer.paths[idx_b]
        except Exception:
            return None

        try:
            tmp = GSLayer()
            copies = []
            for original in (path_a, path_b):
                try:
                    copies.append(original.copy())
                except Exception:
                    copies.append(original)
            tmp.shapes = copies
            tmp.removeOverlap()
            merged = []
            for p in tmp.paths:
                try:
                    cp = p.copy()
                except Exception:
                    cp = p
                merged.append(cp)
            for mp in merged:
                try:
                    remove_collinear_nodes_from_path(mp)
                except Exception:
                    pass
            return merged
        except Exception:
            return None

    def merge_preserves_compatibility(idx_a, idx_b, layers):
        """Check if merging two paths still preserves compatibility across all candidate layers."""
        if len(layers) <= 1:
            return True

        previews = []
        for layer in layers:
            merged = simulate_merge_paths_for_layer(layer, idx_a, idx_b)
            if not merged:
                return False
            previews.append(merged)

        expected_count = len(previews[0])
        for merged in previews[1:]:
            if len(merged) != expected_count:
                return False

        for path_index in range(expected_count):
            base_path = previews[0][path_index]
            for other in previews[1:]:
                if not paths_are_compatible(base_path, other[path_index]):
                    return False
        return True

    def merge_two_paths_in_layer(layer, idx_a, idx_b):
        """
        Merge two paths at indices idx_a and idx_b on a single layer:
        - Use a temporary GSLayer's removeOverlap to perform the merge
        - Remove the original shapes and add the merged result
        - Run remove_collinear_nodes_from_path on the new paths
        Returns True/False indicating success
        """
        try:
            shapes = list(layer.shapes)
        except Exception:
            return False

        # Check index validity
        if idx_a >= len(layer.paths) or idx_b >= len(layer.paths):
            return False

        path_a = layer.paths[idx_a]
        path_b = layer.paths[idx_b]

        # Merge using a temporary layer
        try:
            tmp = GSLayer()
            # Copy shapes (prefer copy when possible)
            try:
                tmp.shapes = [s.copy() for s in (path_a, path_b)]
            except Exception:
                tmp.shapes = [path_a, path_b]
            tmp.removeOverlap()
            merged_paths = list(tmp.paths)
        except Exception:
            return False

        if not merged_paths:
            return False

        # Try to delete original shapes by object index (fall back to path index if not found)
        try:
            idx_shape_a = shapes.index(path_a)
            idx_shape_b = shapes.index(path_b)
        except ValueError:
            try:
                for del_idx in sorted([idx_a, idx_b], reverse=True):
                    if del_idx < len(layer.shapes):
                        del layer.shapes[del_idx]
            except Exception:
                return False
        else:
            for del_idx in sorted([idx_shape_a, idx_shape_b], reverse=True):
                try:
                    del layer.shapes[del_idx]
                except Exception:
                    pass

        # Add merged paths and clean up collinear points
        before_count = len(layer.paths)
        for m in merged_paths:
            layer.shapes.append(m)
        after_count = len(layer.paths)

        # Clean up collinear points on newly added paths
        for pi in range(before_count, after_count):
            try:
                remove_collinear_nodes_from_path(layer.paths[pi])
            except Exception:
                pass

        return True

    # -------------------------
    # Layer recognition rules
    # -------------------------
    BRACE_BRACKET_RE = re.compile(r'^\{.*\}$|^\[.*\]$|<[^>]+>')

    def layer_is_treatment_candidate(layer, font_master_ids):
        """
        Determine if a layer should be treated (master / interpolation intermediate / interpolation replacement layer).
        Rules:
        - For special layers, don't skip all; accept if name/attributes/associated indicates brace/bracket/interpolation layer;
        - Master layers (isMasterLayer == True) are always accepted;
        - Layers with associatedMasterId matching an existing font master id are accepted (common intermediate/replacement layers);
        - Layers with names matching braces/brackets or containing angle brackets (e.g., "{...}", "[550 < wg]" or containing "<...>") are accepted;
        - Layers with "coordinates" in attributes are locked as brace layers (also accepted).
        - Layers without outlines are skipped (checked at the call site).
        """
        try:
            # Basic info
            name = safe_attr(layer, "name", "") or ""
            name = name.strip()
            is_brace_or_bracket = bool(BRACE_BRACKET_RE.search(name))
            assoc = safe_attr(layer, "associatedMasterId", None)
            attrs = safe_attr(layer, "attributes", None)
            has_coordinates = isinstance(attrs, dict) and "coordinates" in attrs
            is_special = bool(safe_attr(layer, "isSpecialLayer", False))

            # If it's a special layer: only accept if it has interpolation-related features
            if is_special:
                if is_brace_or_bracket or (assoc and assoc in font_master_ids) or has_coordinates:
                    return True
                return False

            # Non-special layer checks
            if bool(safe_attr(layer, "isMasterLayer", False)):
                return True
            if assoc and assoc in font_master_ids:
                return True
            if is_brace_or_bracket:
                return True
            if has_coordinates:
                return True

        except Exception:
            return False

        return False

    # -------------------------
    # Main flow
    # -------------------------
    def layers_have_equal_path_counts(layers):
        if not layers:
            return True
        counts = [len(l.paths) for l in layers]
        return all(c == counts[0] for c in counts)

    # Start of main flow
    font = Glyphs.font
    if not font:
        return

    selected_layers = font.selectedLayers
    if not selected_layers:
        return

    master_ids = [m.id for m in font.masters]
    processed = set()

    for sel in selected_layers:
        glyph = sel.parent
        if glyph.name in processed:
            continue
        processed.add(glyph.name)

        # Collect candidate layers (require non-empty paths)
        candidate_layers = []
        try:
            for layer in glyph.layers:
                if len(layer.paths) == 0:
                    continue
                if layer_is_treatment_candidate(layer, master_ids):
                    candidate_layers.append(layer)
        except Exception:
            # Fall back to master layer lookup (defensive)
            for m in font.masters:
                layer = glyph.layers[m.id]
                if len(layer.paths) > 0:
                    candidate_layers.append(layer)

        if not candidate_layers:
            continue

        if not layers_have_equal_path_counts(candidate_layers):
            continue

        undo_started = False
        try:
            glyph.beginUndo()
            undo_started = True

            while True:
                ref_layer = candidate_layers[0]
                num_paths = len(ref_layer.paths)
                found_pair = None

                for i in range(num_paths):
                    for j in range(i + 1, num_paths):
                        if pair_is_collinear_across_layers(i, j, candidate_layers) and \
                        paths_same_direction_across_layers(i, j, candidate_layers):
                            if not merge_preserves_compatibility(i, j, candidate_layers):
                                continue
                            found_pair = (i, j)
                            break
                    if found_pair:
                        break

                if not found_pair:
                    break

                i, j = found_pair

                any_failed = False
                for layer in candidate_layers:
                    ok = merge_two_paths_in_layer(layer, i, j)
                    if not ok:
                        any_failed = True

                if any_failed:
                    break

                # Recalculate candidate layers after merge (keep only layers that still have paths)
                candidate_layers = []
                for layer in glyph.layers:
                    if len(layer.paths) == 0:
                        continue
                    if layer_is_treatment_candidate(layer, master_ids):
                        candidate_layers.append(layer)

                if not layers_have_equal_path_counts(candidate_layers):
                    break

        except Exception:
            pass
        finally:
            if undo_started:
                glyph.endUndo()

__merge_collinear_main()