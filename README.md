# 🎵 ytxtract - YouTube Audio/Video Downloader

A comprehensive, modern YouTube downloader with an elegant dark-themed GUI built with CustomTkinter. Features real-time quality detection, smart playlist handling, batch processing, and intelligent fallback mechanisms for reliable downloads.

![Python](https://img.shields.io/badge/python-v3.7+-blue.svg)
![Platform](https://img.shields.io/badge/platform-windows-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Downloads](https://img.shields.io/badge/downloads-yt--dlp-orange.svg)

## ✨ Features

### 🎵 Audio Downloads
- **Multiple Formats**: MP3, FLAC, WAV, M4A with high-quality encoding
- **Real-time Quality Detection**: Automatically detects and displays actual available audio bitrates
- **Smart Quality Selection**: Interactive popup showing real bitrates (128k, 192k, 256k, 320k+)
- **Audio Fallback System**: 3-tier fallback strategy for problematic videos
- **Metadata Preservation**: Automatic title, artist, album art, and date preservation

### 🎬 Video Downloads
- **Video Formats**: MP4, MKV with optimal codec selection
- **Dynamic Resolution Detection**: Real-time detection of available video qualities
- **Resolution Selection**: Interactive popup with resolution, fps, and file size estimates
- **Smart Format Merging**: Combines best video and audio streams automatically
- **Quality Filtering**: Minimum 240p filter with duplicate resolution removal

### 📋 Advanced Features
- **Intelligent Playlist Handling**: One-time quality selection for entire playlists
- **Batch Processing**: Multi-URL processing with sequential download queue
- **Automatic Clipboard Monitoring**: Real-time YouTube URL detection from clipboard
- **Download History & Statistics**: Persistent tracking with file size and duration metrics
- **Interactive Quality Popups**: Modal dialogs for precise quality control
- **Smart URL Parsing**: Handles various YouTube URL formats and playlist extraction

### 🔧 User Experience
- **Modern Dark Theme**: Professional GitHub-inspired dark UI with CustomTkinter
- **Real-time Progress Tracking**: Visual progress bars with status updates
- **Context-aware Interface**: Right-click menus, keyboard shortcuts, and tooltips
- **Error Recovery**: Comprehensive error handling with fallback mechanisms
- **Persistent Settings**: Auto-saved preferences in system AppData directory

### 🚀 Performance & Reliability
- **Multi-threaded Downloads**: Non-blocking UI with background processing
- **Smart Error Handling**: Age-restricted, geo-blocked, and private video detection
- **Automatic Retry Logic**: Multiple download strategies for maximum success rate
- **Memory Optimization**: Temporary file management with automatic cleanup
- **Network Resilience**: Timeout handling and connection retry mechanisms

## 📦 Installation

### Prerequisites
- Python 3.7 or higher
- Windows OS (primary support)
- Internet connection for yt-dlp updates

### Quick Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/ytxtract.git
   cd ytxtract
   ```

2. **Install dependencies**:
   ```bash
   pip install yt-dlp customtkinter
   ```

3. **Download FFmpeg**:
   - Download `ffmpeg.exe` from [FFmpeg.org](https://ffmpeg.org/download.html)
   - Place `ffmpeg.exe` in the same directory as `main.py`

4. **Launch application**:
   ```bash
   python main.py
   ```

### Alternative Installation
```bash
# Install with pip (if available)
pip install -r requirements.txt

# Or install dependencies manually
pip install yt-dlp>=2023.7.6 customtkinter>=5.2.0
```

## 🚀 Usage Guide

### Basic Operation
1. **Paste URL**: Copy any YouTube URL and paste into the input field
2. **Configure Settings**: Click ⚙️ to access format, quality, and folder settings
3. **Start Download**: Click download button or press Enter
4. **Monitor Progress**: Watch real-time progress and status updates

### Advanced Features

#### 📋 Smart Playlist Downloads
1. Enable "Playlist Downloads" in settings (⚙️)
2. Paste playlist URL (handles various playlist formats)
3. **One-time Quality Selection**: Choose quality once for entire playlist
4. **Batch Processing**: All videos download with consistent quality
5. **Progress Tracking**: Individual video progress with overall completion

#### 📦 Batch URL Processing
1. Enable "Batch Downloads" in settings
2. Paste multiple YouTube URLs (one per line in text field)
3. **Sequential Processing**: Downloads queue automatically
4. **Error Isolation**: Failed downloads don't stop the batch

#### 🎵 Audio Quality Selection System
1. Enable "Show audio quality selection popup for audio" in settings
2. **Real-time Detection**: See actual available bitrates from yt-dlp
3. **Format Details**: View bitrate, file size estimates, and codec info
4. **Fallback Options**: If no real formats detected, shows standard quality options
   ```
   🎵 320 kbps (~8.5 MB)
   🎵 256 kbps (~6.8 MB) 
   🎵 192 kbps (~5.1 MB)
   🎵 128 kbps (~4.2 MB)
   ```

#### 🎬 Video Resolution Selection System
1. Enable "Show resolution selection popup for videos" in settings
2. **Dynamic Resolution List**: Real resolutions available for the specific video
3. **Detailed Format Info**: Resolution, fps, file size, and codec details
4. **Smart Filtering**: Removes duplicates, shows best quality for each resolution
   ```
   📺 1920x1080 60fps (~45.2 MB)
   📺 1280x720 30fps (~23.1 MB)
   📺 854x480 30fps (~15.8 MB)
   ```

#### 🔄 Automatic Clipboard Monitoring
1. Enable "Clipboard Monitoring" in settings
2. **Auto-detection**: Automatically detects YouTube URLs copied to clipboard
3. **Smart Filtering**: Only triggers on valid YouTube URLs
4. **Non-intrusive**: Runs in background without affecting system performance

### Settings Configuration

Access comprehensive settings via ⚙️ button:

**Output Configuration**:
- **Format Selection**: MP3, WAV, FLAC, M4A, MP4, MKV
- **Download Directory**: Custom folder selection with folder browser
- **Audio Quality**: Default bitrate setting (when popup disabled)

**Advanced Options**:
- **Metadata Preservation**: Title, artist, album art, upload date
- **Playlist Mode**: Enable/disable playlist download capability
- **Batch Processing**: Multi-URL download mode
- **Quality Popups**: Interactive resolution/audio quality selection

**User Experience**:
- **Clipboard Monitoring**: Auto-paste YouTube URLs
- **Download History**: Persistent download tracking
- **Statistics**: File size and duration metrics

## 📁 Project Structure

```
ytxtract/
├── main.py                    # Main application (2083 lines)
├── ffmpeg.exe                 # FFmpeg executable (required)
├── README.md                  # Documentation
└── AppData/                   # Auto-created on first run
    ├── settings.json          # User preferences
    ├── download_history.json  # Download history
    └── download_stats.json    # Usage statistics
```

### Key Components in main.py

**Core Functions**:
- `download_single_video()` - Main download logic with preset format support
- `show_audio_quality_selection_popup()` - Real-time audio quality detection
- `show_resolution_selection_popup()` - Dynamic video resolution selection
- `get_available_audio_formats()` / `get_available_video_formats()` - yt-dlp format detection

**UI Management**:
- Modern CustomTkinter interface with GitHub dark theme
- Real-time progress tracking and status updates
- Context menus and keyboard shortcut support

**Data Persistence**:
- Settings auto-save in Windows AppData directory
- Download history with file paths and metadata
- Usage statistics tracking

## ⚙️ Technical Implementation

### Architecture Overview
- **GUI Framework**: CustomTkinter for modern, native-feeling interface
- **Download Engine**: yt-dlp with custom format selection logic
- **Media Processing**: FFmpeg for audio/video conversion and metadata handling
- **Threading Model**: Background downloads with main thread UI updates
- **Data Storage**: JSON-based settings and history in system directories


### Error Handling & Fallback System
1. **Primary Download**: Standard yt-dlp with selected quality
2. **Audio Fallback**: 3-tier strategy for problematic videos
3. **Format Fallback**: Alternative format selection if primary fails
4. **Network Recovery**: Automatic retry with different parameters

### Playlist Processing Logic
- **URL Analysis**: Detects playlist vs individual video URLs
- **One-time Selection**: Quality popup appears once for entire playlist
- **Format Persistence**: Selected quality applied to all playlist items
- **Progress Tracking**: Individual video progress within playlist context

## 🔧 Troubleshooting

### Common Issues & Solutions

**FFmpeg Not Found**
```
Error: FFmpeg executable not found
Solution: Place ffmpeg.exe in same directory as main.py
Download: https://ffmpeg.org/download.html
```

**Video Unavailable**
```
Error: Video unavailable, private, or deleted
Solution: Audio fallback automatically triggered for music content
Alternative: Try different URL format or check video accessibility
```

**Quality Popup Not Showing**
```
Issue: Expected quality selection popup doesn't appear
Cause: Video may not have multiple qualities available
Solution: Check settings → Enable quality popups, or video has limited formats
```

**Network/Connection Errors**
```
Error: Network timeout or connection issues
Solution: Check internet connection, try again, or use VPN if geo-blocked
Note: Some regions may restrict YouTube access
```

**Playlist Download Issues**
```
Issue: Playlist not downloading completely
Solution: Enable "Playlist Downloads" in settings
Check: URL is valid playlist format, not private playlist
```

### Performance Optimization

**Large Playlists (100+ videos)**:
- Download in smaller batches to avoid memory issues
- Use MP3 format for faster processing and smaller files
- Monitor disk space during large downloads

**System Resources**:
- Close other applications during large downloads
- Ensure sufficient disk space (2x video file size recommended)
- Use SSD for faster temporary file processing

## 🎯 Keyboard Shortcuts & Navigation

- **Ctrl+V**: Paste URL from clipboard (works anywhere in app)
- **Enter**: Start download (when URL field focused)
- **Escape**: Close current popup or application
- **Right-click**: Context menu in URL field (paste/clear/select all)
- **Tab**: Navigate between interface elements

## 📊 Feature Comparison

| Feature | Basic Mode | Advanced Mode | Benefits |
|---------|------------|---------------|----------|
| Audio Download | ✅ Standard quality | ✅ Real-time quality selection | Optimal file size vs quality |
| Video Download | ✅ Best available | ✅ Resolution picker with details | HD preservation with size control |
| Playlist Support | ❌ Single video only | ✅ Bulk download with one-time selection | Massive time savings |
| Batch Processing | ❌ One URL at a time | ✅ Multi-URL queue system | Efficient bulk operations |
| Quality Control | ⚙️ Settings-based | 🔍 Real-time detection & selection | Precise quality control |
| Error Recovery | ⚠️ Basic retry | 🔄 Multi-tier fallback system | Maximum success rate |
| User Experience | 📱 Simple interface | 📊 Rich UI with progress tracking | Professional workflow |

## 🤝 Contributing

### Development Guidelines
- **Code Style**: Follow PEP 8 Python standards
- **GUI Components**: Use CustomTkinter for consistency
- **Download Logic**: Extend yt-dlp functionality carefully
- **Error Handling**: Always provide user-friendly error messages
- **Testing**: Test with various YouTube content types

### Architecture Notes
- Main UI thread handles interface updates
- Background threads manage downloads and processing
- Settings persistence uses JSON in system AppData
- FFmpeg integration for media processing

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Legal Disclaimer

**Important**: This tool is intended for personal use only. Users must:
- Respect YouTube's Terms of Service
- Comply with copyright laws and fair use policies
- Only download content they have permission to download
- Use responsibly and ethically

The developers are not responsible for misuse of this software.

## 🙏 Acknowledgments

**Core Technologies**:
- **[yt-dlp](https://github.com/yt-dlp/yt-dlp)**: Powerful YouTube downloader library
- **[FFmpeg](https://ffmpeg.org/)**: Multimedia processing toolkit
- **[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)**: Modern tkinter UI framework

**Created by**: iWishkem  
**Inspired by**: Community need for reliable YouTube content downloading

---

**🎵 Enjoy seamless YouTube content downloading with ytxtract! 🚀**
