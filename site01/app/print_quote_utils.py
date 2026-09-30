"""
3D print quote calculator: mesh parsing (STL + 3MF -> bounding box, real
volume, detected material/color count) and pricing from a PrintMaterial +
PrintSettings.

Pure stdlib (struct/re/zipfile/xml.etree) — no new dependency.
"""
import struct
import re
import io
import zipfile
import xml.etree.ElementTree as ET


class MeshParseError(ValueError):
    """Raised when a file can't be parsed as a supported mesh format"""
    pass


# ============================================================================
# STL (binary + ASCII)
# ============================================================================

def parse_stl(data: bytes):
    """
    Parse an STL file (binary or ASCII) and return (bbox, volume_mm3, material_count).

    bbox is a dict {min: (x,y,z), max: (x,y,z)}.
    volume_mm3 is the mesh's enclosed volume, assuming a closed/manifold mesh
    (standard signed-tetrahedron-from-origin method). Units follow the file
    (assumed millimeters, the de-facto convention for 3D printing).
    STL has no concept of per-part material/color, so material_count is
    always 1.
    """
    if len(data) >= 84:
        declared_triangles = struct.unpack('<I', data[80:84])[0]
        expected_size = 84 + declared_triangles * 50
        if declared_triangles > 0 and expected_size == len(data):
            bbox, volume = _parse_stl_binary(data, declared_triangles)
            return bbox, volume, 1

    try:
        text = data.decode('utf-8', errors='ignore')
    except Exception:
        text = ''
    if 'facet normal' in text and 'vertex' in text:
        bbox, volume = _parse_stl_ascii(text)
        return bbox, volume, 1

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
        _extend_bbox(mins, maxs, (v1, v2, v3))
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
        _extend_bbox(mins, maxs, (v1, v2, v3))

    return {'min': tuple(mins), 'max': tuple(maxs)}, abs(volume_sum)


# ============================================================================
# 3MF (core spec: zip archive containing 3D/3dmodel.model XML)
# ============================================================================

def parse_3mf(data: bytes):
    """
    Parse a 3MF file and return (bbox, volume_mm3, material_count).

    Sums volume/bbox across every build item (each object placed on the
    plate, transform applied), including one level of <components>
    assemblies. material_count is the number of distinct (pid, p1) material
    slots referenced by triangles or objects — a heuristic for "this file
    uses N materials/colors" (multi-material/multi-color prints), since the
    exact per-slot volume split is vendor-specific and not reconstructed
    here; it only drives a flat multi-material surcharge.
    """
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        raise MeshParseError('File 3MF non valido (non è un archivio ZIP)')

    model_path = None
    for name in zf.namelist():
        if name.lower() == '3d/3dmodel.model':
            model_path = name
            break
    if not model_path:
        for name in zf.namelist():
            if name.lower().endswith('.model'):
                model_path = name
                break
    if not model_path:
        raise MeshParseError('Impossibile trovare 3dmodel.model nel file 3MF')

    try:
        root = ET.fromstring(zf.read(model_path))
    except ET.ParseError:
        raise MeshParseError('3dmodel.model non è XML valido')

    ns_uri = root.tag.split('}')[0].strip('{') if root.tag.startswith('{') else ''

    def tag(name):
        return f'{{{ns_uri}}}{name}' if ns_uri else name

    resources = root.find(tag('resources'))
    if resources is None:
        raise MeshParseError('3MF senza sezione "resources"')

    objects_by_id = {obj.get('id'): obj for obj in resources.findall(tag('object'))}

    material_slots = set()
    mins = [float('inf')] * 3
    maxs = [float('-inf')] * 3
    total_volume = 0.0

    def object_volume_bbox(obj, transform, depth=0):
        """Returns (bbox_min, bbox_max, volume_mm3) for one object instance"""
        o_mins = [float('inf')] * 3
        o_maxs = [float('-inf')] * 3
        o_volume = 0.0

        mesh = obj.find(tag('mesh'))
        if mesh is not None:
            vertices_el = mesh.find(tag('vertices'))
            triangles_el = mesh.find(tag('triangles'))
            verts = []
            if vertices_el is not None:
                for v in vertices_el.findall(tag('vertex')):
                    x, y, z = float(v.get('x', 0)), float(v.get('y', 0)), float(v.get('z', 0))
                    verts.append(_apply_transform(transform, x, y, z))

            obj_pid = obj.get('pid')
            obj_pindex = obj.get('pindex')
            if obj_pid:
                material_slots.add((obj_pid, obj_pindex))

            if triangles_el is not None:
                for t in triangles_el.findall(tag('triangle')):
                    try:
                        i1, i2, i3 = int(t.get('v1')), int(t.get('v2')), int(t.get('v3'))
                        v1, v2, v3 = verts[i1], verts[i2], verts[i3]
                    except (TypeError, ValueError, IndexError):
                        continue
                    o_volume += _signed_tetra_volume(v1, v2, v3)
                    _extend_bbox(o_mins, o_maxs, (v1, v2, v3))

                    pid = t.get('pid') or obj_pid
                    p1 = t.get('p1')
                    if pid:
                        material_slots.add((pid, p1))

        # One level of assembly components (a part referencing other parts)
        if depth == 0:
            components_el = obj.find(tag('components'))
            if components_el is not None:
                for comp in components_el.findall(tag('component')):
                    ref_id = comp.get('objectid')
                    ref_obj = objects_by_id.get(ref_id)
                    if ref_obj is None:
                        continue
                    comp_transform = _compose_transform(
                        _parse_transform(comp.get('transform')), transform
                    )
                    c_min, c_max, c_vol = object_volume_bbox(ref_obj, comp_transform, depth=1)
                    o_volume += c_vol
                    for i in range(3):
                        o_mins[i] = min(o_mins[i], c_min[i])
                        o_maxs[i] = max(o_maxs[i], c_max[i])

        return o_mins, o_maxs, o_volume

    build = root.find(tag('build'))
    items = build.findall(tag('item')) if build is not None else []

    if not items:
        # Fallback: no <build> section — just use every object resource directly
        items = [{'objectid': oid, 'transform': None} for oid in objects_by_id]
        item_iter = ((objects_by_id.get(i['objectid']), None) for i in items)
    else:
        item_iter = (
            (objects_by_id.get(item.get('objectid')), _parse_transform(item.get('transform')))
            for item in items
        )

    found_any = False
    for obj, transform in item_iter:
        if obj is None:
            continue
        o_min, o_max, o_vol = object_volume_bbox(obj, transform)
        if o_min[0] == float('inf'):
            continue
        found_any = True
        total_volume += o_vol
        for i in range(3):
            mins[i] = min(mins[i], o_min[i])
            maxs[i] = max(maxs[i], o_max[i])

    if not found_any:
        raise MeshParseError('Nessuna mesh trovata nel file 3MF')

    material_count = max(1, len(material_slots))
    return {'min': tuple(mins), 'max': tuple(maxs)}, abs(total_volume), material_count


def _parse_transform(s):
    """3MF 'transform' attribute: 12 floats, row-major 3x4 (linear part + translation)"""
    if not s:
        return None
    try:
        vals = [float(x) for x in s.split()]
    except ValueError:
        return None
    if len(vals) != 12:
        return None
    linear = ((vals[0], vals[1], vals[2]), (vals[3], vals[4], vals[5]), (vals[6], vals[7], vals[8]))
    translation = (vals[9], vals[10], vals[11])
    return (linear, translation)


def _apply_transform(transform, x, y, z):
    if transform is None:
        return x, y, z
    linear, translation = transform
    v = (x, y, z)
    return tuple(
        translation[j] + sum(v[i] * linear[i][j] for i in range(3))
        for j in range(3)
    )


def _compose_transform(first, second):
    """Compose two transforms so that `first` is applied, then `second`"""
    if first is None:
        return second
    if second is None:
        return first
    l1, t1 = first
    l2, t2 = second
    linear = tuple(
        tuple(sum(l1[i][k] * l2[k][j] for k in range(3)) for j in range(3))
        for i in range(3)
    )
    translation = tuple(t2[j] + sum(t1[k] * l2[k][j] for k in range(3)) for j in range(3))
    return (linear, translation)


# ============================================================================
# Shared helpers
# ============================================================================

def _extend_bbox(mins, maxs, points):
    for p in points:
        for i in range(3):
            if p[i] < mins[i]:
                mins[i] = p[i]
            if p[i] > maxs[i]:
                maxs[i] = p[i]


def _signed_tetra_volume(v1, v2, v3):
    # Signed volume of the tetrahedron formed by the origin and triangle v1,v2,v3
    return (
        v1[0] * (v2[1] * v3[2] - v3[1] * v2[2])
        - v1[1] * (v2[0] * v3[2] - v3[0] * v2[2])
        + v1[2] * (v2[0] * v3[1] - v3[0] * v2[1])
    ) / 6.0


def pick_printer(bbox, material_count, technology, printers):
    """
    Among the given PrintPrinter rows, find the smallest (by build volume)
    active one of the right technology that the part fits in — sorting both
    the part's dimensions and each printer's build volume so the part can be
    attributed to any axis (it doesn't have to already be oriented in the
    uploaded file) — and whose max_materials covers the detected material
    count.

    Returns (fits, printer_or_none, reason) where reason is one of
    'ok', 'no_printer_for_technology', 'too_big', 'too_many_materials' —
    used to give the visitor a precise, honest message instead of a bare
    yes/no.
    """
    dims_mm = sorted(
        maxv - minv for minv, maxv in zip(bbox['min'], bbox['max'])
    )

    candidates = [p for p in printers if p.is_active and p.technology == technology]
    if not candidates:
        return False, None, 'no_printer_for_technology'

    def build_volume(p):
        return p.max_build_x_mm * p.max_build_y_mm * p.max_build_z_mm

    candidates.sort(key=build_volume)

    fits_size = None
    for p in candidates:
        build_mm = sorted([p.max_build_x_mm, p.max_build_y_mm, p.max_build_z_mm])
        if all(d <= b for d, b in zip(dims_mm, build_mm)):
            fits_size = p
            break

    if fits_size is None:
        return False, None, 'too_big'

    if (fits_size.max_materials or 1) < material_count:
        # Re-check: maybe a bigger printer than the smallest fitting one also
        # has enough material slots.
        for p in candidates:
            build_mm = sorted([p.max_build_x_mm, p.max_build_y_mm, p.max_build_z_mm])
            fits_dims = all(d <= b for d, b in zip(dims_mm, build_mm))
            if fits_dims and (p.max_materials or 1) >= material_count:
                return True, p, 'ok'
        return False, fits_size, 'too_many_materials'

    return True, fits_size, 'ok'


def compute_quote(bbox, volume_mm3, material_count, material, settings, printers):
    """
    Turn a parsed bbox/volume/material_count into a printability check +
    price estimate.

    - bbox/volume/material_count come from parse_stl() or parse_3mf().
    - material is a PrintMaterial (technology, density_g_cm3, price_per_kg).
    - settings is a PrintSettings row (infill_percent, resin_fill_percent,
      setup_fee, minimum_price, multi_material_fee_per_extra).
    - printers is the list of active PrintPrinter rows to match against.

    FDM uses settings.infill_percent to estimate weight from mesh volume;
    resin uses settings.resin_fill_percent instead (resin prints are close
    to solid, but large ones do get hollowed to save resin). Any extra
    detected material/color beyond the first adds a flat admin-configured
    fee (splitting volume precisely per color isn't reconstructed from the
    file — this is a ballpark, finalized on manual contact).
    """
    fits, printer, fit_reason = pick_printer(bbox, material_count, material.technology, printers)

    volume_cm3 = volume_mm3 / 1000.0
    fill_percent = settings.resin_fill_percent if material.technology == 'resin' else settings.infill_percent
    fill_fraction = max(0.0, min(1.0, (fill_percent or 0) / 100.0))
    effective_volume_cm3 = volume_cm3 * fill_fraction
    weight_g = effective_volume_cm3 * material.density_g_cm3

    material_cost = (weight_g / 1000.0) * material.price_per_kg
    extra_materials = max(0, material_count - 1)
    multi_material_fee = extra_materials * (settings.multi_material_fee_per_extra or 0)
    price = max(
        settings.minimum_price or 0,
        material_cost + (settings.setup_fee or 0) + multi_material_fee
    )

    return {
        'bbox_mm': {
            'x': round(bbox['max'][0] - bbox['min'][0], 1),
            'y': round(bbox['max'][1] - bbox['min'][1], 1),
            'z': round(bbox['max'][2] - bbox['min'][2], 1),
        },
        'volume_cm3': round(volume_cm3, 2),
        'weight_g': round(weight_g, 1),
        'material_count': material_count,
        'price': round(price, 2),
        'fits': fits,
        'printer': printer,
        'fit_reason': fit_reason,
    }
