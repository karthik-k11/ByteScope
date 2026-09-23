# ByteScope

### Explore what your files are made of.

ByteScope is a lightweight local utility that analyzes binary files and shows their underlying structure.

It reads files as raw bytes and provides information such as:

- File metadata
- File size
- File extension
- Detected file type
- Magic bytes
- Extension/signature mismatch detection
- Hexadecimal preview
- ASCII representation
- MD5 hash
- SHA-256 hash

## Technologies

- Python
- Flask
- HTML
- CSS
- JavaScript
- SQLite — planned
- pytest
- Python Standard Library

## How It Works

```text
File
 ↓
Bytes
 ↓
Magic Bytes
 ↓
File Type Detection
 ↓
Hashing
 ↓
Hex / ASCII Analysis
 ↓
Report