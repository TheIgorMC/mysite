"""
3D print quote calculator: STL mesh parsing (bounding box + real volume) and
pricing from a PrintMaterial + PrintSettings.

Only STL is supported for now (binary and ASCII) — it's the overwhelming
majority of what gets uploaded for a print quote and needs no extra
dependency. 3MF/OBJ can be added later if needed.
"""
import struct
import re


class MeshParseError(ValueError):
    """Raised when a file can't be parsed as a supported mesh format"""
    pass


def parse_stl(data: bytes):
    """
    Parse an STL file (binary or ASCII) and return (bbox, volume_mm3).

    bbox is a dict {min: (x,y,z), max: (x,y,z)}.
    volume_mm3 is the mesh's enclosed volume, assuming a closed/manifold mesh
    (standard signed-tetrahedron-from-origin method). Units follow the file
    (assumed millimeters, the de-facto convention for 3D printing).
    """
    if len(data) >= 84:
        declared_triangles = struct.unpack('<I', data[80:84])[0]
        expected_size = 84 + declared_triangles * 50
        if declared_triangles > 0 and expected_size == len(data):
            return _parse_stl_binary(data, declared_triangles)

    try:
        text = data.decode('utf-8', errors='ignore')
    except Exception:
        text = ''
    if 'facet normal' in text and 'vertex' in text:
        return _parse_stl_ascii(text)

    raise MeshParseError('File STL non riconosciuto (né binario né ASCII valido)')


def _parse_stl_binary(data: bytes, triangle_count: int):
    mins = [float('inf')] * 3
    maxs = [float('-inf')] * 3
    volume_sum = 0.0

    offset = 84
    for _ in range(triangle_count):
        # 12 floats: normal(3) + v1(3) + v2(3) + v3(3), then 2 bytes attribute
        floats = struct.unpack('<12f', data[offset:offset + 48])
        v1 = floats[3:6]
        v2 = floats[6:9]
        v3 = floats[9:12]
        volume_sum += _signed_tetra_volume(v1, v2, v3)
        for v in (v1, v2, v3):
            for i in range(3):
                if v[i] < mins[i]:
                    mins[i] = v[i]
                if v[i] > maxs[i]:
                    maxs[i] = v[i]
        offset += 50

    if mins[0] == float('inf'):
        raise MeshParseError('Nessun triangolo trovato nel file STL')

    return {'min': tuple(mins), 'max': tuple(maxs)}, abs(volume_sum)


_VERTEX_RE = re.compile(
    r'vertex\s+([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)'
)


def _parse_stl_ascii(text: str):
    coords = _VERTEX_RE.findall(text)
    if len(coords) < 3 or len(coords) % 3 != 0:
        raise MeshParseError('File STL ASCII non valido o incompleto')

    mins = [float('inf')] * 3
    maxs = [float('-inf')] * 3
    volume_sum = 0.0

    for i in range(0, len(coords), 3):
        v1 = tuple(float(c) for c in coords[i])
        v2 = tuple(float(c) for c in coords[i + 1])
        v3 = tuple(float(c) for c in coords[i + 2])
        volume_sum += _signed_tetra_volume(v1, v2, v3)
        for v in (v1, v2, v3):
            for j in range(3):
                if v[j] < mins[j]:
                    mins[j] = v[j]
                if v[j] > maxs[j]:
                    maxs[j] = v[j]

    return {'min': tuple(mins), 'max': tuple(maxs)}, abs(volume_sum)


def _signed_tetra_volume(v1, v2, v3):
    # Signed volume of the tetrahedron formed by the origin and triangle v1,v2,v3
    return (
        v1[0] * (v2[1] * v3[2] - v3[1] * v2[2])
        - v1[1] * (v2[0] * v3[2] - v3[0] * v2[2])
        + v1[2] * (v2[0] * v3[1] - v3[0] * v2[1])
    ) / 6.0


def compute_quote(bbox, volume_mm3, material, settings):
    """
    Turn a parsed bbox/volume into a printability check + price estimate.

    - bbox/volume come straight from parse_stl().
    - material is a PrintMaterial (density_g_cm3, price_per_kg).
    - settings is a PrintSettings row (infill_percent, setup_fee,
      minimum_price, max_build_*_mm).

    Returns a dict with bbox_mm, volume_cm3, weight_g, price, fits, notes.
    The printer fit check sorts both the part's dimensions and the build
    volume so the part can be attributed to any of the printer's axes
    (i.e. it doesn't have to already be oriented in the uploaded file).
    """
    dims_mm = sorted(
        maxv - minv for minv, maxv in zip(bbox['min'], bbox['max'])
    )
    build_mm = sorted([
        settings.max_build_x_mm, settings.max_build_y_mm, settings.max_build_z_mm
    ])
    fits = all(d <= b for d, b in zip(dims_mm, build_mm))

    volume_cm3 = volume_mm3 / 1000.0
    infill_fraction = max(0.0, min(1.0, (settings.infill_percent or 0) / 100.0))
    effective_volume_cm3 = volume_cm3 * infill_fraction
    weight_g = effective_volume_cm3 * material.density_g_cm3

    material_cost = (weight_g / 1000.0) * material.price_per_kg
    price = max(settings.minimum_price or 0, material_cost + (settings.setup_fee or 0))

    return {
        'bbox_mm': {
            'x': round(bbox['max'][0] - bbox['min'][0], 1),
            'y': round(bbox['max'][1] - bbox['min'][1], 1),
            'z': round(bbox['max'][2] - bbox['min'][2], 1),
        },
        'volume_cm3': round(volume_cm3, 2),
        'weight_g': round(weight_g, 1),
        'price': round(price, 2),
        'fits': fits,
    }
