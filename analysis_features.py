import mimetypes
import math
import re
import struct
import zlib
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from signatures import SIGNATURES, identify_header


CHUNK_SIZE = 65536
MAX_SIGNATURE_FINDINGS = 250
MAX_STRINGS = 300
MAX_FORMAT_ITEMS = 200


def _scan_file(path):
    counts = Counter()
    strings = []
    signature_hits = []
    strings_truncated = False
    signatures_truncated = False
    seen_signatures = set()
    current_string = bytearray()
    carry = b""
    overlap = max(map(len, SIGNATURES.values())) + 11
    with path.open("rb") as file:
        while chunk := file.read(CHUNK_SIZE):
            counts.update(chunk)
            scan_data = carry + chunk
            base_offset = file.tell() - len(scan_data)
            for file_type, signature in SIGNATURES.items():
                offset = scan_data.find(signature)
                while offset >= 0:
                    absolute_offset = base_offset + offset
                    detected_type = file_type
                    if file_type == "WAV":
                        detected_type = identify_header(scan_data[offset : offset + 16])
                    key = (file_type, absolute_offset)
                    if absolute_offset > 0 and detected_type != "Unknown" and key not in seen_signatures:
                        if len(signature_hits) < MAX_SIGNATURE_FINDINGS:
                            seen_signatures.add(key)
                            signature_hits.append(
                                {"type": detected_type, "offset": absolute_offset}
                            )
                        else:
                            signatures_truncated = True
                    offset = scan_data.find(signature, offset + 1)
            for byte in chunk:
                if 32 <= byte <= 126 or byte in (9,):
                    if len(current_string) < 4096:
                        current_string.append(byte)
                else:
                    if len(current_string) >= 4 and len(strings) < MAX_STRINGS:
                        strings.append(current_string.decode("ascii", errors="replace"))
                    elif len(current_string) >= 4:
                        strings_truncated = True
                    current_string.clear()
            carry = scan_data[-overlap:] if overlap else b""
    if len(current_string) >= 4 and len(strings) < MAX_STRINGS:
        strings.append(current_string.decode("ascii", errors="replace"))
    elif len(current_string) >= 4:
        strings_truncated = True
    total = sum(counts.values())
    entropy = -sum(
        (count / total) * math.log2(count / total) for count in counts.values()
    ) if total else 0.0
    signature_hits.sort(key=lambda item: item["offset"])
    return entropy, strings, signature_hits, strings_truncated, signatures_truncated


def _inspect_png(path, file_size):
    chunks = []
    issues = []
    if file_size < 8:
        return {"chunks": chunks, "issues": ["Truncated PNG signature or header"]}

    with path.open("rb") as file:
        if file.read(8) != SIGNATURES["PNG"]:
            return {"chunks": chunks, "issues": ["Invalid PNG signature"]}
        ended = False
        while file.tell() + 12 <= file_size and len(chunks) < 10000:
            header = file.read(8)
            if len(header) != 8:
                issues.append("Truncated PNG chunk header")
                break
            length, kind = struct.unpack(">I4s", header)
            chunk_end = file.tell() + length + 4
            if chunk_end > file_size:
                issues.append(f"Chunk {kind.decode('ascii', 'replace')} exceeds file bounds")
                break
            crc = zlib.crc32(kind)
            remaining = length
            while remaining:
                data = file.read(min(CHUNK_SIZE, remaining))
                if not data:
                    issues.append("Truncated PNG chunk data")
                    break
                crc = zlib.crc32(data, crc)
                remaining -= len(data)
            crc_bytes = file.read(4)
            if len(crc_bytes) != 4:
                issues.append("Truncated PNG chunk checksum")
                break
            expected_crc = struct.unpack(">I", crc_bytes)[0]
            name = kind.decode("ascii", errors="replace")
            chunks.append({"type": name, "length": length, "crc_valid": crc == expected_crc})
            if crc != expected_crc:
                issues.append(f"Checksum mismatch in {name} chunk")
            if kind == b"IEND":
                ended = True
                if file.tell() < file_size:
                    issues.append("Data follows PNG IEND chunk")
                break
    if not ended:
        issues.append("PNG IEND chunk is missing")
    return {"chunks": chunks[:MAX_FORMAT_ITEMS], "issues": issues}


def _count_bytes(path, needle):
    count = 0
    carry = b""
    overlap = len(needle) - 1
    with path.open("rb") as file:
        while chunk := file.read(CHUNK_SIZE):
            data = carry + chunk
            count += data.count(needle)
            carry = data[-overlap:] if overlap else b""
    return count


def _count_pdf_pages(path):
    count = 0
    carry = b""
    pattern = re.compile(rb"/Type\s{0,16}/Page\b")
    with path.open("rb") as file:
        while chunk := file.read(CHUNK_SIZE):
            data = carry + chunk
            count += sum(1 for match in pattern.finditer(data) if match.end() > len(carry))
            carry = data[-32:]
    return count


def _inspect_pdf(path, file_size):
    with path.open("rb") as file:
        header = file.read(8)
        file.seek(max(0, file_size - 2048))
        tail = file.read(2048)
    issues = []
    if not header.startswith(b"%PDF-"):
        issues.append("PDF version header is missing")
    if b"%%EOF" not in tail:
        issues.append("PDF EOF marker is missing")
    return {
        "version": header[5:8].decode("ascii", errors="replace").strip("\x00")
        if header.startswith(b"%PDF-")
        else "Unknown",
        "objects": _count_bytes(path, b" obj"),
        "pages": _count_pdf_pages(path),
        "issues": issues,
    }


def _inspect_zip(path):
    entries = []
    issues = []
    file_size = path.stat().st_size
    with path.open("rb") as file:
        file.seek(max(0, file_size - 65557))
        tail = file.read(65557)
        eocd_index = tail.rfind(b"PK\x05\x06")
        if eocd_index < 0 or len(tail) - eocd_index < 22:
            return {"entries": entries, "issues": ["ZIP end-of-central-directory record is missing"]}

        (
            _signature,
            disk_number,
            central_disk,
            disk_entries,
            total_entries,
            central_size,
            central_offset,
            _comment_length,
        ) = struct.unpack_from("<4s4H2LH", tail, eocd_index)
        if disk_number != 0 or central_disk != 0 or disk_entries != total_entries:
            issues.append("Multi-disk ZIP archives are not inspected")
            return {"entries": entries, "issues": issues}
        if (
            disk_entries == 0xFFFF
            or total_entries == 0xFFFF
            or central_size == 0xFFFFFFFF
            or central_offset == 0xFFFFFFFF
        ):
            issues.append("ZIP64 directory metadata is not inspected")
            return {"entries": entries, "issues": issues}

        central_end = central_offset + central_size
        if central_end > file_size or central_end > file_size - len(tail) + eocd_index:
            issues.append("ZIP central directory exceeds file bounds")
            return {"entries": entries, "issues": issues}

        file.seek(central_offset)
        for index in range(min(total_entries, MAX_FORMAT_ITEMS)):
            fixed = file.read(46)
            if len(fixed) != 46:
                issues.append("Truncated ZIP central directory")
                break
            fields = struct.unpack("<4s6H3L5H2L", fixed)
            if fields[0] != b"PK\x01\x02":
                issues.append(f"Invalid ZIP central directory record at entry {index + 1}")
                break
            name_length, extra_length, comment_length = fields[10:13]
            record_end = file.tell() + name_length + extra_length + comment_length
            if record_end > central_end:
                issues.append(f"ZIP entry {index + 1} exceeds central directory bounds")
                break
            raw_name = file.read(min(name_length, 512))
            if len(raw_name) != min(name_length, 512):
                issues.append(f"Truncated filename in ZIP entry {index + 1}")
                break
            file.seek(record_end)
            encoding = "utf-8" if fields[3] & 0x800 else "cp437"
            entries.append(
                {
                    "name": raw_name.decode(encoding, errors="replace"),
                    "size": fields[9],
                    "compressed_size": fields[8],
                    "encrypted": bool(fields[3] & 1),
                }
            )
        if total_entries > MAX_FORMAT_ITEMS:
            issues.append(f"Only the first {MAX_FORMAT_ITEMS} entries are shown")
    return {"entries": entries, "issues": issues}


def analyze_details(file_path):
    path = Path(file_path)
    stat = path.stat()
    with path.open("rb") as file:
        header = file.read(32)
    detected_type = identify_header(header)
    (
        entropy,
        strings,
        signatures,
        strings_truncated,
        signatures_truncated,
    ) = _scan_file(path)
    for index, finding in enumerate(signatures):
        finding["estimated_end"] = (
            signatures[index + 1]["offset"] if index + 1 < len(signatures) else stat.st_size
        )
        finding["estimated_size"] = finding["estimated_end"] - finding["offset"]

    structures = {}
    corruption = []
    if detected_type == "PNG":
        structures["PNG"] = _inspect_png(path, stat.st_size)
        corruption.extend(structures["PNG"]["issues"])
    elif detected_type == "PDF":
        structures["PDF"] = _inspect_pdf(path, stat.st_size)
        corruption.extend(structures["PDF"]["issues"])
    elif detected_type == "ZIP":
        structures["ZIP"] = _inspect_zip(path)
        corruption.extend(structures["ZIP"]["issues"])

    return {
        "metadata": {
            "mime_type": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
            "modified_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
            "magic_bytes": header[:16].hex(" ").upper(),
        },
        "entropy": round(entropy, 4),
        "strings": strings,
        "strings_truncated": strings_truncated,
        "embedded_signatures": signatures,
        "embedded_signatures_truncated": signatures_truncated,
        "carving_candidates": signatures,
        "structures": structures,
        "corruption_indicators": corruption,
    }
