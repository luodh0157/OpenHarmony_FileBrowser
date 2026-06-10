# OpenHarmony File Browser

A cross-platform file browser for OpenHarmony/HarmonyOS devices.

## Features

- **Device Management**: Connect to OpenHarmony/HarmonyOS devices via USB or wireless
- **File Browsing**: Navigate device file system with tree and list views
- **File Operations**: Copy, move, delete, rename files and folders
- **File Transfer**: Drag & drop upload/download with progress tracking
- **File Preview**: Preview images and videos
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Requirements

- Python 3.9 or higher
- OpenHarmony/HarmonyOS device with USB debugging enabled
- HDC (HarmonyOS Device Connector) tool

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/OpenHarmony_FileBrowser.git
cd OpenHarmony_FileBrowser

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## HDC Tool Setup

The application requires the HDC (HarmonyOS Device Connector) tool. Place the HDC executable in the appropriate directory:

```
hdc/
├── windows/
│   ├── x86_64/hdc.exe
│   └── x86/hdc.exe
├── linux/
│   ├── x86_64/hdc
│   └── arm64/hdc
└── macos/
    ├── x86_64/hdc
    └── arm64/hdc
```

The application will automatically detect and use the correct version based on your platform and architecture.

## Usage

1. **Connect Device**:
   - USB: Connect your device via USB and enable USB debugging
   - Wireless: Connect via IP address and port

2. **Browse Files**:
   - Navigate directories using the tree view on the left
   - View files in the list view on the right
   - Use the path bar for quick navigation

3. **Transfer Files**:
   - Drag and drop files between your computer and device
   - Use copy/paste or toolbar buttons
   - Monitor progress in the transfer dialog

4. **Preview Files**:
   - Double-click images to preview
   - Click videos to preview thumbnails and play

## Development

### Run Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/
flake8 src/
```

### Build Executable

```bash
python build.py
```

## Project Structure

```
OpenHarmony_FileBrowser/
├── src/                   # Source code
│   ├── gui/              # GUI components
│   ├── core/             # Core logic
│   ├── models/           # Data models
│   ├── utils/            # Utilities
│   └── resources/        # Resources
├── hdc/                  # HDC tool binaries
├── tests/                # Unit tests
├── docs/                 # Documentation
└── logs/                 # Application logs
```

## License

Apache License 2.0

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For bug reports and feature requests, please open an issue on GitHub.