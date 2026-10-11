"""Offline model of inspected OEM translation branches; no camera-clearance claim."""
import math
import struct


def f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def translation_by_axes(width, height, axes, rotation):
    """AiPetsPagView.getTranslationByAxes, preserving Java float arithmetic/casts."""
    if rotation not in (0, 2):
        raise ValueError('Only the native even rotations are modeled')
    if width <= 0 or height <= 0 or len(axes) != 4 or not all(math.isfinite(v) for v in axes):
        raise ValueError('Invalid source dimensions/axes')
    left, top, right, bottom = map(f32, axes)
    extra_y, extra_x = f32(height - 1392), f32(width - 1208)
    center_x = f32(f32(right + left) / 2)
    x = f32(f32(f32(334.75 if rotation == 0 else 213.97998) + f32(329.58252)) - center_x)
    if x > 0:
        x = 0.0
    if abs(x) > extra_x:
        x = -extra_x
    y = f32(1392 - bottom)
    if y > 0:
        y = 0.0
    if abs(y) > extra_y:
        y = -extra_y
    correction = f32(357.5 - f32(top + y))
    y = f32(y + (correction if correction <= 0 else 0))
    if abs(y) > extra_y:
        y = -extra_y
    return int(x), int(y)


def systemui_translation(template, width, height, rotation):
    """Both positionInfo values must exist to bypass the first-frame fallback."""
    if rotation not in (0, 2):
        raise ValueError('Unsupported rotation')
    positions = [(template.get(key) or {}).get('positionInfo')
                 for key in ('wallpaperInfo0', 'wallpaperInfo180')]
    if all(position is not None for position in positions):
        p = positions[rotation // 2]
        return 'positionInfo', (int(-p['left']), int(-p['top']))
    a = template['pets']['aiPetsData']['firstFrameCoordinateAxes']
    axes = [a[key] for key in ('leftX', 'leftY', 'rightX', 'rightY')]
    return 'firstFrameAxes', translation_by_axes(width, height, axes, rotation)


def editor_position(width, height, axes, rotation, logical_width=1208):
    """TinyEditorAiPetsView.Companion.getWallpaperInfo before any later crop edit."""
    x, y = translation_by_axes(width, height, axes, rotation)
    scale = f32(logical_width / 1208)
    # PositionInfo(Matrix, x, y, width, height) stores NEGATED translation.
    return dict(left=-x, top=-y, right=1208-x, bottom=1392-y,
                matrixArr=[scale, 0, f32(x * scale), 0, scale, f32(y * scale), 0, 0, 1])
