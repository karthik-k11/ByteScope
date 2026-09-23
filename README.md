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
```

## Current Features

### File Metadata

Displays:

- File name
- Extension
- File size

### Magic Byte Detection

ByteScope checks the beginning of a file against known signatures.

Currently supported signatures:

- PNG
- PDF
- ZIP
- JPEG
- GIF
- WAV
- MP3
- EXE

### Extension Verification

ByteScope compares the file extension with the detected file type.

Example:

```text
Extension: .jpg
Detected Type: PDF
Extension Match: False
```

A mismatch is reported descriptively and is not automatically treated as malware.

### Hex Viewer

Displays:

- Byte offsets
- Hexadecimal bytes
- Printable ASCII characters

Non-printable bytes are represented using `.`.

### File Hashing

Calculates:

- MD5
- SHA-256

Hashes are calculated incrementally so large files do not need to be loaded completely into memory.

## Project Structure

```text
ByteScope/
│
├── app.py
├── file_analyzer.py
├── signatures.py
├── hashing.py
├── hex_viewer.py
│
├── templates/
│   └── index.html
│
├── static/
│   └── style.css
│
├── tests/
│   ├── conftest.py
│   ├── test_analyzer.py
│   ├── test_signatures.py
│   └── test_hashing.py
│
├── requirements.txt
├── .gitignore
└── README.md
```

## Installation

Clone the repository and enter the project directory.

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Running ByteScope

Start the Flask application:

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

Select a file and click **Analyze File**.

## Testing

Run:

```bash
pytest
```

Current test coverage includes:

- File analysis
- Missing file handling
- PNG signature detection
- Unknown file detection
- MD5 hashing
- SHA-256 hashing

## Security Boundary

ByteScope is an inspection tool.

It treats files strictly as data.

It does not:

- Execute uploaded files
- Launch executables
- Run scripts contained in files
- Automatically extract embedded files
- Modify original files
- Delete files
- Upload files to external services