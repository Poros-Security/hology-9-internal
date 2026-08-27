#!/usr/bin/env python3
"""Shared CLI-metadata helpers for the ILusion packer and solver.

Two things live here:

  * `method_il()`   - pull a MethodDef body out of a .NET PE exactly the way
                      `MethodBase.GetMethodBody().GetILAsByteArray()` does,
                      i.e. the code bytes only, with the method header
                      stripped off. This is the step every "why is my key
                      wrong" bug comes from.
  * `rva_arrays()`  - recover the static array blobs that Roslyn parks in
                      .sdata and loads with RuntimeHelpers.InitializeArray.
"""
import struct

# ELEMENT_TYPE_*
ET_VALUETYPE = 0x11
ET_CLASS = 0x12

# method header kinds
CORILMETHOD_TINYFORMAT = 0x02
CORILMETHOD_FATFORMAT = 0x03


def _s(item):
    """dnfile hands back heap items; unwrap to a plain str/bytes."""
    return item.value if hasattr(item, "value") else item


def find_methoddef(pe, name, type_name=None):
    """Return the MethodDef row named `name`, optionally scoped to a type."""
    hits = []
    for td in pe.net.mdtables.TypeDef.rows:
        ns, tn = _s(td.TypeNamespace), _s(td.TypeName)
        full = "{}.{}".format(ns, tn) if ns else tn
        if type_name is not None and full != type_name:
            continue
        for ref in td.MethodList:
            if ref.row is not None and _s(ref.row.Name) == name:
                hits.append(ref.row)

    if len(hits) != 1:
        raise LookupError("expected exactly one {}{}, found {}".format(
            (type_name + ".") if type_name else "", name, len(hits)))
    return hits[0]


def method_il(pe, name, type_name=None):
    """The IL body of `name`, header stripped - what GetILAsByteArray returns."""
    md = find_methoddef(pe, name, type_name)
    if not md.Rva:
        raise ValueError("method {!r} has no body".format(name))

    off = pe.get_offset_from_rva(md.Rva)
    data = pe.__data__
    first = data[off]

    if first & 0x03 == CORILMETHOD_TINYFORMAT:
        size = first >> 2
        body = off + 1
    elif first & 0x03 == CORILMETHOD_FATFORMAT:
        size = struct.unpack_from("<I", data, off + 4)[0]
        body = off + 12
    else:
        raise ValueError("unrecognised method header 0x{:02X}".format(first))

    return bytes(data[body:body + size])


def _decompress_uint(buf, pos):
    b = buf[pos]
    if b & 0x80 == 0:
        return b, pos + 1
    if b & 0x40 == 0:
        return ((b & 0x3F) << 8) | buf[pos + 1], pos + 2
    return (((b & 0x1F) << 24) | (buf[pos + 1] << 16)
            | (buf[pos + 2] << 8) | buf[pos + 3]), pos + 4


def _static_array_sizes(pe):
    """1-based TypeDef row -> byte size, for __StaticArrayInitTypeSize=N."""
    marker = "__StaticArrayInitTypeSize="
    sizes = {}
    for i, td in enumerate(pe.net.mdtables.TypeDef.rows):
        tn = _s(td.TypeName) or ""
        if tn.startswith(marker):
            try:
                sizes[i + 1] = int(tn[len(marker):])
            except ValueError:
                pass
    return sizes


def rva_arrays(pe):
    """Every RVA-mapped static array blob in the module, as a list of bytes.

    Roslyn compiles `new byte[] { ... }` with more than a couple of constant
    elements into a field whose data lives in .sdata and whose type is a
    synthetic struct literally named `__StaticArrayInitTypeSize=<n>` - so the
    blob length is recoverable from metadata alone, without decoding the
    static constructor.
    """
    sizes = _static_array_sizes(pe)
    out = []

    for row in pe.net.mdtables.FieldRva.rows:
        field = row.Field.row
        if field is None:
            continue
        sig = bytes(_s(field.Signature))
        if len(sig) < 3 or sig[0] != 0x06:            # FIELD calling convention
            continue

        pos = 1
        while sig[pos] in (0x1F, 0x20):               # cmod_reqd / cmod_opt
            pos += 1
            _, pos = _decompress_uint(sig, pos)
        if sig[pos] not in (ET_VALUETYPE, ET_CLASS):
            continue
        pos += 1

        coded, _ = _decompress_uint(sig, pos)
        if coded & 0x03 != 0:                         # TypeDefOrRef -> TypeDef
            continue
        size = sizes.get(coded >> 2)
        if not size:
            continue

        out.append(bytes(pe.get_data(row.Rva, size)))

    return out
