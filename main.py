import sys
import os
import yt_dlp
import customtkinter as tk
import threading
import time
import tempfile
import shutil
import subprocess
from tkinter import filedialog, messagebox
import json
from datetime import datetime
import re
from urllib.parse import urlparse, parse_qs
import tkinter as tkinter_root

current_quality = "192"
current_format = "mp3"
current_download_folder = os.path.expanduser("~/Downloads")
preserve_metadata = True
download_history = []
download_stats = {"total_downloads": 0, "total_size_mb": 0, "total_time_saved": 0}
is_playlist_mode = False

batch_mode = False
clipboard_monitoring = False
download_queue = []
current_download_index = 0

def get_ffmpeg_path():
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, "ffmpeg.exe")

def get_app_data_dir():
    if os.name == 'nt':
        app_data = os.path.join(os.path.expanduser("~"), "AppData", "Local", "ytxtract")
    else:
        app_data = os.path.join(os.path.expanduser("~"), ".ytxtract")
    
    os.makedirs(app_data, exist_ok=True)
    return app_data

def save_settings_to_file():
    try:
        app_data_dir = get_app_data_dir()
        settings_file = os.path.join(app_data_dir, "settings.json")
        settings = {
            'quality': current_quality,
            'format': current_format,
            'download_folder': current_download_folder,
            'preserve_metadata': preserve_metadata,
            'is_playlist_mode': is_playlist_mode,
            'batch_mode': batch_mode,
            'clipboard_monitoring': clipboard_monitoring
        }
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
        print("Settings saved to file")
    except Exception as e:
        print(f"Error saving settings: {e}")

def load_settings_from_file():
    global current_quality, current_format, current_download_folder, preserve_metadata, is_playlist_mode
    global batch_mode, clipboard_monitoring
    try:
        app_data_dir = get_app_data_dir()
        settings_file = os.path.join(app_data_dir, "settings.json")
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                settings = json.load(f)
            
            current_quality = settings.get('quality', "192")
            current_format = settings.get('format', "mp3")
            current_download_folder = settings.get('download_folder', os.path.expanduser("~/Downloads"))
            preserve_metadata = settings.get('preserve_metadata', True)
            is_playlist_mode = settings.get('is_playlist_mode', False)
            batch_mode = settings.get('batch_mode', False)
            clipboard_monitoring = settings.get('clipboard_monitoring', False)
            print("Settings loaded from file")
    except Exception as e:
        print(f"Error loading settings: {e}")

def hide_console_window():
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        return startupinfo
    return None

clipboard_monitor_thread = None
clipboard_monitor_running = False
last_clipboard_content = ""

def start_clipboard_monitoring():
    global clipboard_monitor_thread, clipboard_monitor_running
    if not clipboard_monitor_running:
        clipboard_monitor_running = True
        clipboard_monitor_thread = threading.Thread(target=clipboard_monitor_worker, daemon=True)
        clipboard_monitor_thread.start()
        print("Clipboard monitoring started")

def stop_clipboard_monitoring():
    global clipboard_monitor_running
    clipboard_monitor_running = False
    print("Clipboard monitoring stopped")

def clipboard_monitor_worker():
    global last_clipboard_content
    while clipboard_monitor_running:
        try:
            current_clipboard = app.clipboard_get()
            if (current_clipboard != last_clipboard_content and 
                current_clipboard and 
                ('youtube.com' in current_clipboard or 'youtu.be' in current_clipboard)):
                
                last_clipboard_content = current_clipboard
                app.after(0, lambda: auto_paste_url(current_clipboard))
        except Exception:
            pass
        time.sleep(1)

def auto_paste_url(url):
    current_text = textbox.get("0.0", "end-1c").strip()
    placeholder_text = "Paste YouTube URL here..." if not batch_mode else "Paste YouTube URLs here (one per line)..."
    
    if current_text == placeholder_text:
        textbox.delete("0.0", "end")
        textbox.insert("0.0", url)
        textbox.configure(border_color=("#238636", "#238636"))
        status_label.configure(text="✅ YouTube URL auto-detected!")

def parse_batch_urls(text):
    urls = []
    lines = text.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line and ('youtube.com' in line or 'youtu.be' in line):
            urls.append(line)
    return urls

def process_batch_downloads(urls):
    global download_queue, current_download_index
    download_queue = urls
    current_download_index = 0
    
    if download_queue:
        app.after(0, lambda: status_label.configure(text=f"📦 Batch mode: {len(download_queue)} URLs queued"))
        app.after(0, lambda: progress_bar.pack(pady=(10, 0)))
        
        download_next_in_queue()

def download_next_in_queue():
    global current_download_index
    
    if current_download_index < len(download_queue):
        current_url = download_queue[current_download_index]
        app.after(0, lambda: status_label.configure(text=f"⬇️ Downloading {current_download_index + 1}/{len(download_queue)}..."))
        app.after(0, lambda: progress_bar.set((current_download_index + 1) / len(download_queue)))
        
        download_thread_obj = threading.Thread(target=batch_download_worker, args=(current_url,))
        download_thread_obj.daemon = True
        download_thread_obj.start()
    else:
        app.after(0, lambda: status_label.configure(text="✅ Batch download completed!"))
        app.after(0, lambda: progress_bar.pack_forget())
        app.after(0, lambda: button.configure(state="normal", text=f"📥 Download {current_format.upper()}", fg_color=("#238636", "#238636")))
        download_queue.clear()
        current_download_index = 0

def batch_download_worker(url):
    global current_download_index
    try:
        ffmpeg_path = get_ffmpeg_path()
        download_single_video(url, ffmpeg_path)
        
        current_download_index += 1
        app.after(0, download_next_in_queue)
        
    except Exception as e:
        print(f"Batch download error for {url}: {e}")
        current_download_index += 1
        app.after(0, download_next_in_queue)

def open_settings():
    settings_menu = tk.CTkToplevel(app)
    settings_menu.title("⚙️ Settings")
    settings_menu.geometry("500x750")
    settings_menu.resizable(False, False)
    settings_menu.configure(fg_color=("#0d1117", "#0d1117"))
    settings_menu.transient(app)
    settings_menu.grab_set()
    
    settings_menu.grid_columnconfigure(0, weight=1)
    
    header = tk.CTkLabel(
        settings_menu,
        text="⚙️ Settings",
        font=tk.CTkFont(size=28, weight="bold"),
        text_color=("#58a6ff", "#58a6ff")
    )
    header.grid(row=0, column=0, pady=(30, 40))
    
    scrollable_frame = tk.CTkScrollableFrame(
        settings_menu,
        width=450,
        height=500,
        corner_radius=20,
        border_width=1,
        border_color=("#21262d", "#21262d"),
        fg_color=("#161b22", "#161b22")
    )
    scrollable_frame.grid(row=1, column=0, padx=30, pady=(0, 20), sticky="ew")
    
    row_counter = 0
    
    quality_label = tk.CTkLabel(
        scrollable_frame,
        text="🎵 Audio Quality:",
        font=tk.CTkFont(size=16, weight="bold"),
        text_color=("#f0f6fc", "#f0f6fc")
    )
    quality_label.grid(row=row_counter, column=0, padx=30, pady=(30, 10), sticky="w")
    row_counter += 1
    
    quality_var = tk.StringVar(value=current_quality)
    
    def on_quality_change(selected_quality):
        global current_quality
        current_quality = selected_quality
        save_settings_to_file()
    
    quality_menu = tk.CTkOptionMenu(
        scrollable_frame,
        values=["128", "192", "256", "320"],
        variable=quality_var,
        command=on_quality_change,
        height=40,
        font=tk.CTkFont(size=14),
        fg_color=("#21262d", "#21262d"),
        button_color=("#30363d", "#30363d"),
        button_hover_color=("#58a6ff", "#58a6ff")
    )
    quality_menu.grid(row=row_counter, column=0, padx=30, pady=(0, 25), sticky="ew")
    row_counter += 1
    
    format_label = tk.CTkLabel(
        scrollable_frame,
        text="📁 Output Format:",
        font=tk.CTkFont(size=16, weight="bold"),
        text_color=("#f0f6fc", "#f0f6fc")
    )
    format_label.grid(row=row_counter, column=0, padx=30, pady=(0, 10), sticky="w")
    row_counter += 1
    
    format_var = tk.StringVar(value=current_format)
    
    def on_format_change(selected_format):
        global current_format
        current_format = selected_format
        save_settings_to_file()
        try:
            format_display = current_format.upper()
            if 'button' in globals():
                button.configure(text=f"📥 Download {format_display}")
        except Exception:
            pass
    
    format_menu = tk.CTkOptionMenu(
        scrollable_frame,
        values=["mp3", "mkv", "wav", "flac", "m4a", "mp4"],
        variable=format_var,
        command=on_format_change,
        height=40,
        font=tk.CTkFont(size=14),
        fg_color=("#21262d", "#21262d"),
        button_color=("#30363d", "#30363d"),
        button_hover_color=("#58a6ff", "#58a6ff")
    )
    format_menu.grid(row=row_counter, column=0, padx=30, pady=(0, 25), sticky="ew")
    row_counter += 1
    
    folder_label = tk.CTkLabel(
        scrollable_frame,
        text="📁 Download Folder:",
        font=tk.CTkFont(size=16, weight="bold"),
        text_color=("#f0f6fc", "#f0f6fc")
    )
    folder_label.grid(row=row_counter, column=0, padx=30, pady=(0, 10), sticky="w")
    row_counter += 1
    
    folder_frame = tk.CTkFrame(scrollable_frame, fg_color="transparent")
    folder_frame.grid(row=row_counter, column=0, padx=30, pady=(0, 25), sticky="ew")
    folder_frame.grid_columnconfigure(0, weight=1)
    row_counter += 1
    
    folder_entry = tk.CTkEntry(
        folder_frame,
        height=40,
        font=tk.CTkFont(size=12),
        fg_color=("#21262d", "#21262d"),
        border_color=("#30363d", "#30363d"),
        text_color=("#f0f6fc", "#f0f6fc")
    )
    folder_entry.insert(0, current_download_folder)
    folder_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
    
    browse_button = tk.CTkButton(
        folder_frame,
        text="📂 Browse",
        width=80,
        height=40,
        font=tk.CTkFont(size=12),
        fg_color=("#30363d", "#30363d"),
        hover_color=("#58a6ff", "#58a6ff"),
        command=lambda: browse_folder(folder_entry)
    )
    browse_button.grid(row=0, column=1)
    
    metadata_var = tk.BooleanVar(value=preserve_metadata)
    
    def on_metadata_change():
        global preserve_metadata
        preserve_metadata = metadata_var.get()
        save_settings_to_file()
    
    metadata_checkbox = tk.CTkCheckBox(
        scrollable_frame,
        text="🎯 Preserve Metadata & Album Art",
        variable=metadata_var,
        command=on_metadata_change,
        font=tk.CTkFont(size=14),
        text_color=("#f0f6fc", "#f0f6fc"),
        fg_color=("#238636", "#238636"),
        hover_color=("#2ea043", "#2ea043")
    )
    metadata_checkbox.grid(row=row_counter, column=0, padx=30, pady=(0, 20), sticky="w")
    row_counter += 1
    
    playlist_var = tk.BooleanVar(value=is_playlist_mode)
    
    def on_playlist_mode_change():
        global is_playlist_mode
        is_playlist_mode = playlist_var.get()
        save_settings_to_file()
    
    playlist_checkbox = tk.CTkCheckBox(
        scrollable_frame,
        text="📋 Enable Playlist Downloads",
        variable=playlist_var,
        command=on_playlist_mode_change,
        font=tk.CTkFont(size=14),
        text_color=("#f0f6fc", "#f0f6fc"),
        fg_color=("#238636", "#238636"),
        hover_color=("#2ea043", "#2ea043")
    )
    playlist_checkbox.grid(row=row_counter, column=0, padx=30, pady=(0, 20), sticky="w")
    row_counter += 1
    
    batch_var = tk.BooleanVar(value=batch_mode)
    
    def on_batch_mode_change():
        global batch_mode
        batch_mode = batch_var.get()
        save_settings_to_file()
        if batch_mode:
            url_label.configure(text="🔗 Paste YouTube URLs (one per line for batch)")
        else:
            url_label.configure(text="🔗 Paste YouTube URL")
    
    batch_checkbox = tk.CTkCheckBox(
        scrollable_frame,
        text="📦 Enable Batch Downloads",
        variable=batch_var,
        command=on_batch_mode_change,
        font=tk.CTkFont(size=14),
        text_color=("#f0f6fc", "#f0f6fc"),
        fg_color=("#238636", "#238636"),
        hover_color=("#2ea043", "#2ea043")
    )
    batch_checkbox.grid(row=row_counter, column=0, padx=30, pady=(0, 20), sticky="w")
    row_counter += 1
    
    clipboard_var = tk.BooleanVar(value=clipboard_monitoring)
    
    def on_clipboard_monitoring_change():
        global clipboard_monitoring
        clipboard_monitoring = clipboard_var.get()
        save_settings_to_file()
        if clipboard_monitoring:
            start_clipboard_monitoring()
        else:
            stop_clipboard_monitoring()
    
    clipboard_checkbox = tk.CTkCheckBox(
        scrollable_frame,
        text="📋 Auto-detect YouTube URLs in clipboard",
        variable=clipboard_var,
        command=on_clipboard_monitoring_change,
        font=tk.CTkFont(size=14),
        text_color=("#f0f6fc", "#f0f6fc"),
        fg_color=("#238636", "#238636"),
        hover_color=("#2ea043", "#2ea043")
    )
    clipboard_checkbox.grid(row=row_counter, column=0, padx=30, pady=(0, 20), sticky="w")
    row_counter += 1
    
    credits_label = tk.CTkLabel(
        scrollable_frame,
        text="ℹ️ Credits:",
        font=tk.CTkFont(size=16, weight="bold"),
        text_color=("#f0f6fc", "#f0f6fc")
    )
    credits_label.grid(row=row_counter, column=0, padx=30, pady=(10, 5), sticky="w")
    row_counter += 1
    
    credits_text = tk.CTkLabel(
        scrollable_frame,
        text="• Made by iWishkem\n• yt-dlp - YouTube video downloader\n• FFmpeg - Media processing toolkit\n• CustomTkinter - Modern UI framework\n",
        font=tk.CTkFont(size=12),
        text_color=("#8b949e", "#8b949e"),
        justify="left"
    )
    credits_text.grid(row=row_counter, column=0, padx=30, pady=(0, 25), sticky="w")
    
    button_frame = tk.CTkFrame(settings_menu, fg_color="transparent")
    button_frame.grid(row=2, column=0, padx=30, pady=(0, 30), sticky="ew")
    button_frame.grid_columnconfigure((0, 1), weight=1)
    
    cancel_button = tk.CTkButton(
        button_frame,
        text="❌ Cancel",
        command=settings_menu.destroy,
        height=45,
        font=tk.CTkFont(size=14, weight="bold"),
        fg_color=("#21262d", "#21262d"),
        hover_color=("#30363d", "#30363d"),
        text_color=("#8b949e", "#8b949e")
    )
    cancel_button.grid(row=0, column=0, padx=(0, 15), sticky="ew")
    
    save_button = tk.CTkButton(
        button_frame,
        text="💾 Save Settings",
        command=lambda: save_settings(
            quality_var.get(), 
            format_var.get(), 
            folder_entry.get(), 
            metadata_var.get(),
            playlist_var.get(),
            batch_var.get(),
            clipboard_var.get(),
            settings_menu
        ),
        height=45,
        font=tk.CTkFont(size=14, weight="bold"),
        fg_color=("#238636", "#238636"),
        hover_color=("#2ea043", "#2ea043")
    )
    save_button.grid(row=0, column=1, padx=(15, 0), sticky="ew")

def browse_folder(entry_widget):
    folder_path = filedialog.askdirectory(
        title="Select Download Folder",
        initialdir=current_download_folder
    )
    if folder_path:
        entry_widget.delete(0, "end")
        entry_widget.insert(0, folder_path)

def save_settings(quality, format_type, download_folder, metadata, playlist_mode, batch_mode_setting, clipboard_monitoring_setting, window):
    global current_quality, current_format, current_download_folder, preserve_metadata, is_playlist_mode
    global batch_mode, clipboard_monitoring
    
    current_quality = quality
    current_format = format_type
    current_download_folder = download_folder
    preserve_metadata = metadata
    is_playlist_mode = playlist_mode
    batch_mode = batch_mode_setting
    clipboard_monitoring = clipboard_monitoring_setting
    
    save_settings_to_file()
    
    if clipboard_monitoring:
        start_clipboard_monitoring()
    else:
        stop_clipboard_monitoring()
    
    format_display = current_format.upper()
    button.configure(text=f"📥 Download {format_display}")
    placeholder_text = "🔗 Paste YouTube URL" if not batch_mode else "🔗 Paste YouTube URLs (one per line for batch)"
    url_label.configure(text=placeholder_text)
    
    window.destroy()

def add_to_history(title, format_type, file_path):
    global download_history
    download_history.insert(0, {
        'title': title,
        'format': format_type,
        'path': file_path,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    if len(download_history) > 10:
        download_history = download_history[:10]
    save_download_history()

def save_download_history():
    try:
        app_data_dir = get_app_data_dir()
        history_file = os.path.join(app_data_dir, "download_history.json")
        with open(history_file, 'w') as f:
            json.dump(download_history, f)
    except Exception as e:
        print(f"Error saving history: {e}")

def load_download_history():
    global download_history
    try:
        app_data_dir = get_app_data_dir()
        history_file = os.path.join(app_data_dir, "download_history.json")
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                download_history = json.load(f)
    except Exception as e:
        print(f"Error loading history: {e}")

def cleanup_old_data_files():
    try:
        old_stats_file = os.path.join(current_download_folder, "download_stats.json")
        old_history_file = os.path.join(current_download_folder, "download_history.json")
        
        if os.path.exists(old_stats_file):
            os.remove(old_stats_file)
            print("Removed old stats file from downloads folder")
        
        if os.path.exists(old_history_file):
            os.remove(old_history_file)
            print("Removed old history file from downloads folder")
            
    except Exception as e:
        print(f"Error cleaning up old files: {e}")

def animate_progress_bar():
    for i in range(101):
        progress_bar.set(i / 100)
        time.sleep(0.01)

def pulse_button():
    if button.cget("state") == "normal":
        original_color = button.cget("fg_color")
        button.configure(fg_color=("#1f538d", "#14375e"))
        app.after(150, lambda: button.configure(fg_color=original_color) if button.cget("state") == "normal" else None)

def clear_placeholder(event):
    current_text = textbox.get("0.0", "end-1c").strip()
    placeholder_text = "Paste YouTube URL here..." if not batch_mode else "Paste YouTube URLs here (one per line)..."
    if current_text == placeholder_text:
        textbox.delete("0.0", "end")
        textbox.configure(border_color=("#58a6ff", "#58a6ff"))
        return "break"

def download_as_audio_fallback(url, ffmpeg_path, temp_dir):
    try:
        app.after(0, lambda: status_label.configure(text="🎵 Attempting audio-only download..."))
        
        safe_title = f"audio_{int(time.time())}"
        uploader = 'Unknown'
        duration = 0
        
        strategies = [
            {
                'name': 'Audio-only with cookies',
                'opts': {
                    'format': 'bestaudio/best',
                    'outtmpl': os.path.join(temp_dir, f"{safe_title}_1.%(ext)s"),
                    'quiet': True,
                    'no_warnings': True,
                    'ignoreerrors': True,
                    'extract_flat': False,
                }
            },
            {
                'name': 'Best available format',
                'opts': {
                    'format': 'best/worst',
                    'outtmpl': os.path.join(temp_dir, f"{safe_title}_2.%(ext)s"),
                    'quiet': True,
                    'no_warnings': True,
                    'ignoreerrors': True,
                    'extract_flat': False,
                }
            },
            {
                'name': 'Any audio format',
                'opts': {
                    'format': 'bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio',
                    'outtmpl': os.path.join(temp_dir, f"{safe_title}_3.%(ext)s"),
                    'quiet': True,
                    'no_warnings': True,
                    'ignoreerrors': True,
                    'extract_flat': False,
                }
            }
        ]
        
        downloaded_file = None
        
        for i, strategy in enumerate(strategies):
            try:
                app.after(0, lambda: status_label.configure(text=f"🔄 Trying strategy {i+1}/3..."))
                print(f"Trying {strategy['name']}")
                
                with yt_dlp.YoutubeDL(strategy['opts']) as ydl:
                    ydl.download([url])
                
                temp_files = [f for f in os.listdir(temp_dir) 
                             if not f.endswith('.part') and not f.endswith('.tmp')]
                
                if temp_files:
                    downloaded_file = os.path.join(temp_dir, temp_files[0])
                    print(f"Success with {strategy['name']}: {downloaded_file}")
                    break
                    
            except Exception as strategy_error:
                print(f"Strategy {i+1} failed: {strategy_error}")
                continue
        
        if not downloaded_file or not os.path.exists(downloaded_file):
            try:
                with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if info:
                        app.after(0, lambda: status_label.configure(text="❌ Content found but download blocked"))
                    else:
                        app.after(0, lambda: status_label.configure(text="❌ Content not accessible"))
            except:
                app.after(0, lambda: status_label.configure(text="❌ Video completely unavailable"))
            
            raise Exception("All download strategies failed - content may be geo-blocked, deleted, or private")
        
        file_size = os.path.getsize(downloaded_file)
        total_size_mb = file_size / (1024 * 1024)
        
        file_ext = os.path.splitext(downloaded_file)[1] or '.mp3'
        if file_ext.lower() not in ['.mp3', '.m4a', '.wav', '.flac']:
            file_ext = '.mp3'
        
        final_filename = f"{safe_title}{file_ext}"
        final_path = os.path.join(current_download_folder, final_filename)
        
        counter = 1
        while os.path.exists(final_path):
            name_part = f"{safe_title}_{counter}"
            final_filename = f"{name_part}{file_ext}"
            final_path = os.path.join(current_download_folder, final_filename)
            counter += 1
        
        if file_ext.lower() != '.mp3' and ffmpeg_path and os.path.exists(ffmpeg_path):
            try:
                app.after(0, lambda: status_label.configure(text="🔄 Converting to MP3..."))
                mp3_path = final_path.replace(file_ext, '.mp3')
                
                cmd = [ffmpeg_path, '-i', downloaded_file, '-acodec', 'libmp3lame', 
                       '-ab', f'{current_quality}k', mp3_path]
                startupinfo = hide_console_window()
                if startupinfo:
                    subprocess.run(cmd, check=True, capture_output=True, startupinfo=startupinfo)
                else:
                    subprocess.run(cmd, check=True, capture_output=True)
                
                final_path = mp3_path
                final_filename = os.path.basename(mp3_path)
            except Exception as convert_error:
                print(f"FFmpeg conversion failed: {convert_error}")
        else:
            shutil.move(downloaded_file, final_path)
        
        app.after(0, lambda: status_label.configure(text="✅ Audio download completed!"))
        
        format_name = file_ext.upper().replace('.', '') + " (Audio Fallback)"
        add_to_history(safe_title, format_name, final_path)
        
        return total_size_mb
        
    except Exception as e:
        error_msg = f"❌ Audio fallback failed: {str(e)}"
        app.after(0, lambda: status_label.configure(text=error_msg))
        print(f"Audio fallback error: {e}")
        return 0

def download_thread(url):
    start_time = time.time()
    total_size_mb = 0
    
    try:
        ffmpeg_path = get_ffmpeg_path()
        
        if is_playlist_mode and is_playlist_url(url):
            playlist_info = get_playlist_info(url)
            if playlist_info:
                app.after(0, lambda: status_label.configure(text=f"📋 Found playlist: {playlist_info['count']} videos"))
                
                for i, entry in enumerate(playlist_info['entries']):
                    if entry:
                        try:
                            if 'url' in entry:
                                video_url = entry['url']
                            elif 'id' in entry:
                                entry_id = entry['id']
                                if (len(entry_id) == 11 and 
                                    entry_id.replace('-', '').replace('_', '').isalnum() and
                                    not entry_id.startswith(('PL', 'UC', 'UU'))):
                                    video_url = f"https://www.youtube.com/watch?v={entry_id}"
                                else:
                                    print(f"Skipping invalid video ID in playlist: {entry_id}")
                                    continue
                            else:
                                print(f"Skipping entry with no valid URL/ID: {entry}")
                                continue
                            
                            app.after(0, lambda i=i: status_label.configure(text=f"⬇️ Downloading {i+1}/{playlist_info['count']}..."))
                            app.after(0, lambda i=i: progress_bar.set((i+1) / playlist_info['count']))
                            
                            file_size = download_single_video(video_url, ffmpeg_path)
                            total_size_mb += file_size
                        except Exception as video_error:
                            print(f"Failed to download video {i+1}: {video_error}")
                            app.after(0, lambda i=i: status_label.configure(text=f"⚠️ Skipped video {i+1} (error)"))
                            continue
                
                app.after(0, lambda: status_label.configure(text="✅ Playlist download completed!"))
            else:
                app.after(0, lambda: status_label.configure(text="⚠️ Playlist info failed, downloading single video..."))
                file_size = download_single_video(url, ffmpeg_path)
                total_size_mb += file_size
        else:
            file_size = download_single_video(url, ffmpeg_path)
            total_size_mb += file_size
        
        end_time = time.time()
        duration_seconds = end_time - start_time
        
        format_display = current_format.upper()
        app.after(0, lambda: progress_bar.pack_forget())
        app.after(0, lambda: status_label.configure(text="✅ Download completed successfully!"))
        app.after(0, lambda: button.configure(state="normal", text=f"📥 Download {format_display}", fg_color=("#238636", "#238636")))
        app.after(0, lambda: pulse_button())
        
    except Exception as e:
        handle_download_error(e)

def download_single_video(url, ffmpeg_path):
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_output = os.path.join(temp_dir, "temp_file.%(ext)s")
            
            video_title = None
            safe_title = None
            uploader = 'Unknown'
            duration = 0
            upload_date = ''
            info_extraction_failed = False
            
            try:
                with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                    info = ydl.extract_info(url, download=False)
                    video_title = info.get('title', 'video')
                    safe_title = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    
                    uploader = info.get('uploader', 'Unknown')
                    duration = info.get('duration', 0)
                    upload_date = info.get('upload_date', '')
            except Exception as info_error:
                print(f"Failed to get video info: {info_error}")
                info_extraction_failed = True
                error_msg = str(info_error).lower()
                audio_fallback_triggers = [
                    "video unavailable", "not available", "private video", 
                    "deleted", "removed", "blocked", "age restricted",
                    "sign in to confirm", "music", "audio only", "no video"
                ]
                
                if any(trigger in error_msg for trigger in audio_fallback_triggers):
                    app.after(0, lambda: status_label.configure(text="⚠️ Video issue detected, trying audio download..."))
                    return download_as_audio_fallback(url, ffmpeg_path, temp_dir)
                
                safe_title = f"video_{int(time.time())}"
            
            if current_format in ["mkv", "mp4"]:
                ydl_opts = {
                    'format': 'best',
                    'outtmpl': temp_output,
                    'ffmpeg_location': ffmpeg_path,
                    'noplaylist': True,
                    'ignoreerrors': True,
                    'no_warnings': True
                }
                
                app.after(0, lambda: status_label.configure(text="⬇️ Downloading video..."))
                
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                except Exception as download_error:
                    error_msg = str(download_error).lower()
                    if "not available" in error_msg or "unavailable" in error_msg or "private" in error_msg:
                        app.after(0, lambda: status_label.configure(text="⚠️ Video download failed, trying audio..."))
                        return download_as_audio_fallback(url, ffmpeg_path, temp_dir)
                    else:
                        raise download_error
                
                temp_files = [f for f in os.listdir(temp_dir) if f.startswith("temp_file")]
                if temp_files:
                    temp_file = os.path.join(temp_dir, temp_files[0])
                    final_output = os.path.join(current_download_folder, f"{safe_title}.{current_format}")
                    
                    if current_format == "mkv":
                        app.after(0, lambda: status_label.configure(text="🔄 Converting to MKV..."))
                        
                        cmd = [ffmpeg_path, '-i', temp_file, '-c', 'copy']
                        if preserve_metadata:
                            cmd.extend(['-metadata', f'title={safe_title}', '-metadata', f'artist={uploader}'])
                        cmd.append(final_output)
                        
                        startupinfo = hide_console_window()
                        if startupinfo:
                            subprocess.run(cmd, check=True, capture_output=True, startupinfo=startupinfo)
                        else:
                            subprocess.run(cmd, check=True, capture_output=True)
                    else:
                        app.after(0, lambda: status_label.configure(text="🔄 Processing MP4..."))
                        if preserve_metadata:
                            cmd = [ffmpeg_path, '-i', temp_file, '-c', 'copy', 
                                   '-metadata', f'title={safe_title}', '-metadata', f'artist={uploader}', final_output]
                            startupinfo = hide_console_window()
                            if startupinfo:
                                subprocess.run(cmd, check=True, capture_output=True, startupinfo=startupinfo)
                            else:
                                subprocess.run(cmd, check=True, capture_output=True)
                        else:
                            shutil.copy2(temp_file, final_output)
                    
                    file_size_mb = os.path.getsize(final_output) / (1024 * 1024)
                    
                    add_to_history(safe_title, current_format.upper(), final_output)
                    update_download_stats(file_size_mb, duration)
                    
                    app.after(0, lambda: status_label.configure(text="✅ Video download completed!"))
                    return file_size_mb
                    
            else:
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': temp_output,
                    'ffmpeg_location': ffmpeg_path,
                    'noplaylist': True,
                    'ignoreerrors': True,
                    'no_warnings': True
                }
                
                app.after(0, lambda: status_label.configure(text="🎵 Downloading audio..."))
                
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                except Exception as download_error:
                    app.after(0, lambda: status_label.configure(text="⚠️ Standard audio download failed, trying fallback..."))
                    return download_as_audio_fallback(url, ffmpeg_path, temp_dir)
                
                temp_files = [f for f in os.listdir(temp_dir) if f.startswith("temp_file")]
                if temp_files:
                    temp_file = os.path.join(temp_dir, temp_files[0])
                    final_output = os.path.join(current_download_folder, f"{safe_title}.{current_format}")
                    
                    app.after(0, lambda: status_label.configure(text=f"🔄 Converting to {current_format.upper()}..."))
                    
                    codec_map = {
                        'mp3': 'libmp3lame',
                        'wav': 'pcm_s16le',
                        'flac': 'flac',
                        'm4a': 'aac'
                    }
                    
                    codec = codec_map.get(current_format, 'libmp3lame')
                    cmd = [ffmpeg_path, '-i', temp_file, '-acodec', codec]
                    
                    if current_format in ['mp3', 'm4a']:
                        cmd.extend(['-ab', f'{current_quality}k'])
                    
                    if preserve_metadata:
                        cmd.extend(['-metadata', f'title={safe_title}', '-metadata', f'artist={uploader}'])
                        if upload_date:
                            cmd.extend(['-metadata', f'date={upload_date[:4]}'])
                    
                    cmd.append(final_output)
                    startupinfo = hide_console_window()
                    if startupinfo:
                        subprocess.run(cmd, check=True, capture_output=True, startupinfo=startupinfo)
                    else:
                        subprocess.run(cmd, check=True, capture_output=True)
                    
                    file_size_mb = os.path.getsize(final_output) / (1024 * 1024)
                    
                    add_to_history(safe_title, current_format.upper(), final_output)
                    update_download_stats(file_size_mb, duration)
                    
                    app.after(0, lambda: status_label.configure(text="✅ Audio download completed!"))
                    return file_size_mb
                    
    except Exception as e:
        print(f"Error in download_single_video: {e}")
        raise e
    
    return 0

def handle_download_error(e):
    error_msg = str(e).lower()
    if "not a valid url" in error_msg or "invalid url" in error_msg:
        user_friendly_error = "Invalid YouTube URL! Please enter a valid link."
    elif "video unavailable" in error_msg or "private video" in error_msg:
        user_friendly_error = "Video unavailable or private! This content cannot be accessed."
    elif "age-restricted" in error_msg:
        user_friendly_error = "Age-restricted video! This content requires sign-in."
    elif "network" in error_msg or "connection" in error_msg:
        user_friendly_error = "Network error! Check your connection."
    elif "playlist" in error_msg:
        user_friendly_error = "Playlist error! Trying single video download..."
    elif "extraction" in error_msg:
        user_friendly_error = "Failed to extract video info! Try again."
    elif "ffmpeg" in error_msg:
        user_friendly_error = "FFmpeg error! Check if ffmpeg.exe is present."
    elif "geo-blocked" in error_msg or "blocked" in error_msg:
        user_friendly_error = "Content blocked in your region!"
    elif "all download strategies failed" in error_msg:
        user_friendly_error = "Content not accessible! May be deleted, private, or geo-blocked."
    else:
        user_friendly_error = "Download failed! Please try again."
    
    app.after(0, lambda: progress_bar.pack_forget())
    app.after(0, lambda: status_label.configure(text=f"❌ {user_friendly_error}"))
    format_display = current_format.upper()
    app.after(0, lambda: button.configure(state="normal", text=f"📥 Download {format_display}", fg_color=("#238636", "#238636")))
    print(f"Error: {e}")

def indir_sadece_ses(url):
    input_text = url.strip()
    
    if not input_text or input_text == "Paste YouTube URL here...":
        status_label.configure(text="❌ Please enter a valid YouTube URL!")
        progress_bar.pack_forget()
        textbox.configure(border_color=("#f85149", "#f85149"))
        app.after(2000, lambda: textbox.configure(border_color=("#30363d", "#30363d")))
        return
    
    if button.cget("state") == "disabled":
        return
    
    if batch_mode and '\n' in input_text:
        urls = parse_batch_urls(input_text)
        if len(urls) > 1:
            button.configure(state="disabled", text="📦 Processing Batch...", fg_color=("#6f42c1", "#6f42c1"))
            process_batch_downloads(urls)
            return
        elif len(urls) == 1:
            url = urls[0]  # Single URL from batch input
        else:
            status_label.configure(text="❌ No valid YouTube URLs found!")
            textbox.configure(border_color=("#f85149", "#f85149"))
            app.after(2000, lambda: textbox.configure(border_color=("#30363d", "#30363d")))
            return
    else:
        url = input_text
    
    if is_playlist_url(url) and not is_playlist_mode:
            response = messagebox.askyesno(
                "Playlist Detected", 
                "This appears to be a playlist URL. Do you want to download just the specific video?\n\n"
                "Enable 'Playlist Downloads' in settings to download entire playlists.",
                icon="question"
            )
            if not response:
                return
            
            video_id_match = re.search(r'[?&]v=([a-zA-Z0-9_-]{11})', url)
            if video_id_match:
                video_id = video_id_match.group(1)
                url = f"https://www.youtube.com/watch?v={video_id}"
                print(f"Extracted video ID from playlist URL: {video_id}")
            else:
                print("Could not extract video ID from playlist URL, using original URL")
    
    button.configure(state="disabled", text="⬇️ Downloading...", fg_color=("#6f42c1", "#6f42c1"))
    
    progress_bar.pack(pady=(10, 0))
    status_label.configure(text="🚀 Starting download...")
    progress_bar.set(0.1)
    
    download_thread_obj = threading.Thread(target=download_thread, args=(url,))
    download_thread_obj.daemon = True
    download_thread_obj.start()

def is_playlist_url(url):
    playlist_patterns = [
        r'[?&]list=([a-zA-Z0-9_-]+)',
        r'/playlist\?list=([a-zA-Z0-9_-]+)',
        r'youtube\.com/.*[?&]list=([a-zA-Z0-9_-]+)',
        r'youtu\.be/.*[?&]list=([a-zA-Z0-9_-]+)'
    ]
    
    for pattern in playlist_patterns:
        match = re.search(pattern, url)
        if match:
            list_id = match.group(1)
            if list_id not in ['WL', 'LL'] and not list_id.startswith('UU'):
                return True
    
    return False

def get_playlist_info(url):
    try:
        ydl_opts = {
            'quiet': True, 
            'extract_flat': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'playlistend': 50
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if info and 'entries' in info:
                valid_entries = []
                for entry in info['entries']:
                    if entry is not None:
                        if 'url' in entry:
                            valid_entries.append({'url': entry['url']})
                        elif 'id' in entry:
                            entry_id = entry['id']
                            if (len(entry_id) == 11 and 
                                entry_id.replace('-', '').replace('_', '').isalnum() and
                                not entry_id.startswith('PL') and  
                                not entry_id.startswith('UC') and  
                                not entry_id.startswith('UU')):   
                                valid_entries.append({'id': entry_id})
                            else:
                                print(f"Skipping invalid video ID: {entry_id}")
                        elif 'webpage_url' in entry:
                            valid_entries.append({'url': entry['webpage_url']})
                        elif 'ie_key' in entry and entry.get('ie_key') == 'Youtube':
                            if 'title' in entry:
                                print(f"Skipping entry with no URL/ID: {entry.get('title', 'Unknown')}")
                
                if valid_entries:
                    return {
                        'title': info.get('title', 'Unknown Playlist'),
                        'count': len(valid_entries),
                        'entries': valid_entries
                    }
                else:
                    print("No valid entries with extract_flat, trying full extraction...")
                    return get_playlist_info_full(url)
            
            if info and info.get('id'):
                video_id = info.get('id')
                if len(video_id) == 11 and not video_id.startswith(('PL', 'UC', 'UU')):
                    return {
                        'title': info.get('title', 'Single Video'),
                        'count': 1,
                        'entries': [{'id': video_id}]
                    }
                
    except Exception as e:
        print(f"Error getting playlist info: {e}")
        try:
            video_id_match = re.search(r'(?:v=|/)([a-zA-Z0-9_-]{11})', url)
            if video_id_match:
                video_id = video_id_match.group(1)
                if not video_id.startswith(('PL', 'UC', 'UU')):
                    return {
                        'title': 'Extracted Video',
                        'count': 1,
                        'entries': [{'id': video_id}]
                    }                    
        except Exception:
            pass
    
    return None

def get_playlist_info_full(url):
    try:
        ydl_opts = {
            'quiet': True, 
            'extract_flat': False,
            'no_warnings': True,
            'ignoreerrors': True,
            'playlistend': 20
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if info and 'entries' in info:
                valid_entries = []
                for entry in info['entries']:
                    if entry is not None and 'id' in entry:
                        entry_id = entry['id']
                        if len(entry_id) == 11 and not entry_id.startswith(('PL', 'UC', 'UU')):
                            valid_entries.append({'id': entry_id})
                
                if valid_entries:
                    return {
                        'title': info.get('title', 'Unknown Playlist'),
                        'count': len(valid_entries),
                        'entries': valid_entries
                    }
    except Exception as e:
        print(f"Full extraction fallback failed: {e}")
    
    return None

def save_download_stats():
    try:
        app_data_dir = get_app_data_dir()
        stats_file = os.path.join(app_data_dir, "download_stats.json")
        with open(stats_file, 'w') as f:
            json.dump(download_stats, f)
    except Exception as e:
        print(f"Error saving stats: {e}")

def load_download_stats():
    global download_stats
    try:
        app_data_dir = get_app_data_dir()
        stats_file = os.path.join(app_data_dir, "download_stats.json")
        if os.path.exists(stats_file):
            with open(stats_file, 'r') as f:
                download_stats = json.load(f)
    except Exception as e:
        print(f"Error loading stats: {e}")

def update_download_stats(file_size_mb, duration_seconds):
    global download_stats
    download_stats["total_downloads"] += 1
    download_stats["total_size_mb"] += file_size_mb
    download_stats["total_time_saved"] += duration_seconds
    save_download_stats()

def open_history_window():
    history_window = tk.CTkToplevel(app)
    history_window.title("📜 Download History")
    history_window.geometry("700x500")
    history_window.configure(fg_color=("#0d1117", "#0d1117"))
    history_window.transient(app)
    history_window.grab_set()
    
    header = tk.CTkLabel(
        history_window,
        text="📜 Download History",
        font=tk.CTkFont(size=24, weight="bold"),
        text_color=("#58a6ff", "#58a6ff")
    )
    header.pack(pady=(20, 30))
    
    if not download_history:
        no_history_label = tk.CTkLabel(
            history_window,
            text="No downloads yet! 🎵",
            font=tk.CTkFont(size=16),
            text_color=("#8b949e", "#8b949e")
        )
        no_history_label.pack(pady=50)
    else:
        scrollable_frame = tk.CTkScrollableFrame(
            history_window,
            width=650,
            height=350,
            corner_radius=15,
            fg_color=("#161b22", "#161b22")
        )
        scrollable_frame.pack(padx=20, pady=(0, 20), fill="both", expand=True)
        
        for i, item in enumerate(download_history):
            item_frame = tk.CTkFrame(
                scrollable_frame,
                corner_radius=10,
                fg_color=("#21262d", "#21262d")
            )
            item_frame.pack(fill="x", padx=10, pady=5)
            
            title_label = tk.CTkLabel(
                item_frame,
                text=f"🎵 {item['title']}",
                font=tk.CTkFont(size=14, weight="bold"),
                text_color=("#f0f6fc", "#f0f6fc"),
                anchor="w"
            )
            title_label.pack(fill="x", padx=15, pady=(10, 5))
            
            details_label = tk.CTkLabel(
                item_frame,
                text=f"Format: {item['format']} | Downloaded: {item['timestamp']}",
                font=tk.CTkFont(size=12),
                text_color=("#8b949e", "#8b949e"),
                anchor="w"
            )
            details_label.pack(fill="x", padx=15, pady=(0, 10))

def open_stats_window():
    stats_window = tk.CTkToplevel(app)
    stats_window.title("📊 Download Statistics")
    stats_window.geometry("500x400")
    stats_window.configure(fg_color=("#0d1117", "#0d1117"))
    stats_window.transient(app)
    stats_window.grab_set()
    
    header = tk.CTkLabel(
        stats_window,
        text="📊 Download Statistics",
        font=tk.CTkFont(size=24, weight="bold"),
        text_color=("#58a6ff", "#58a6ff")
    )
    header.pack(pady=(20, 30))
    
    stats_frame = tk.CTkFrame(
        stats_window,
        corner_radius=15,
        fg_color=("#161b22", "#161b22")
    )
    stats_frame.pack(padx=30, pady=20, fill="both", expand=True)
    
    downloads_label = tk.CTkLabel(
        stats_frame,
        text=f"🎵 Total Downloads: {download_stats['total_downloads']}",
        font=tk.CTkFont(size=18, weight="bold"),
        text_color=("#f0f6fc", "#f0f6fc")
    )
    downloads_label.pack(pady=(30, 15))
    
    size_gb = download_stats['total_size_mb'] / 1024
    size_label = tk.CTkLabel(
        stats_frame,
        text=f"💾 Total Size: {size_gb:.2f} GB",
        font=tk.CTkFont(size=16),
        text_color=("#f0f6fc", "#f0f6fc")
    )
    size_label.pack(pady=10)
    
    hours = download_stats['total_time_saved'] / 3600
    time_label = tk.CTkLabel(
        stats_frame,
        text=f"⏰ Content Downloaded: {hours:.1f} hours",
        font=tk.CTkFont(size=16),
        text_color=("#f0f6fc", "#f0f6fc")
    )
    time_label.pack(pady=10)

def create_context_menu():
    def paste_url():
        try:
            clipboard_data = app.clipboard_get()
            if clipboard_data:
                textbox.delete("0.0", "end")
                textbox.insert("0.0", clipboard_data)
                if 'youtube.com' in clipboard_data or 'youtu.be' in clipboard_data:
                    textbox.configure(border_color=("#238636", "#238636"))
                    status_label.configure(text="✅ URL pasted!")
                else:
                    textbox.configure(border_color=("#f85149", "#f85149"))
                    status_label.configure(text="❌ Not a YouTube URL")
        except Exception:
            pass
    
    def clear_text():
        textbox.delete("0.0", "end")
        placeholder_text = "Paste YouTube URL here..." if not batch_mode else "Paste YouTube URLs here (one per line)..."
        textbox.insert("0.0", placeholder_text)
        textbox.configure(border_color=("#30363d", "#30363d"))
        status_label.configure(text="✅ Ready to download")
    
    def show_context_menu(event):
        try:
            context_menu = tk.CTkFrame(app, fg_color=("#21262d", "#21262d"), corner_radius=8)
            
            paste_btn = tk.CTkButton(
                context_menu,
                text="📋 Paste URL",
                command=paste_url,
                width=120,
                height=30,
                font=tk.CTkFont(size=12),
                fg_color=("#30363d", "#30363d"),
                hover_color=("#58a6ff", "#58a6ff")
            )
            paste_btn.pack(padx=5, pady=2)
            
            clear_btn = tk.CTkButton(
                context_menu,
                text="🗑️ Clear",
                command=clear_text,
                width=120,
                height=30,
                font=tk.CTkFont(size=12),
                fg_color=("#30363d", "#30363d"),
                hover_color=("#f85149", "#f85149")
            )
            clear_btn.pack(padx=5, pady=2)
            
            x, y = event.x_root, event.y_root
            context_menu.place(x=x-app.winfo_rootx(), y=y-app.winfo_rooty())
            
            def remove_menu():
                try:
                    context_menu.destroy()
                except Exception:
                    pass
            
            app.after(3000, remove_menu)
            app.bind("<Button-1>", lambda e: remove_menu())
            
        except Exception as e:
            print(f"Context menu error: {e}")
    
    textbox.bind("<Button-3>", show_context_menu)

if __name__ == "__main__":
    tk.set_appearance_mode("dark")
    tk.set_default_color_theme("blue")
    
    load_settings_from_file()
    
    load_download_stats()
    load_download_history()
    
    cleanup_old_data_files()
    
    app = tk.CTk()
    app.title("🎵 YouTube MP3 Converter")
    app.geometry("600x550")
    app.resizable(False, False)
    app.configure(fg_color=("#0d1117", "#0d1117"))
    
    app.grid_columnconfigure(0, weight=1)
    app.grid_rowconfigure(1, weight=1)
    
    header_frame = tk.CTkFrame(app, fg_color="transparent")
    header_frame.grid(row=0, column=0, padx=30, pady=(30, 20), sticky="ew")
    header_frame.grid_columnconfigure(1, weight=1)
    
    history_button = tk.CTkButton(
        header_frame,
        text="📜",
        command=open_history_window,
        width=40,
        height=40,
        font=tk.CTkFont(size=16),
        corner_radius=20,
        fg_color=("#21262d", "#21262d"),
        hover_color=("#30363d", "#30363d"),
        text_color=("#8b949e", "#8b949e")
    )
    history_button.grid(row=0, column=0, sticky="nw")
    
    title_container = tk.CTkFrame(header_frame, fg_color="transparent")
    title_container.grid(row=0, column=1, sticky="")
    
    title_label = tk.CTkLabel(
        title_container, 
        text="🎵 YouTube MP3", 
        font=tk.CTkFont(size=32, weight="bold"),
        text_color=("#58a6ff", "#58a6ff")
    )
    title_label.pack()
    
    subtitle_label = tk.CTkLabel(
        title_container, 
        text="Convert YouTube videos to high-quality audio/video files",
        font=tk.CTkFont(size=14),
        text_color=("#8b949e", "#8b949e")
    )
    subtitle_label.pack(pady=(5, 0))
    
    right_buttons_frame = tk.CTkFrame(header_frame, fg_color="transparent")
    right_buttons_frame.grid(row=0, column=2, sticky="ne")
    
    stats_button = tk.CTkButton(
        right_buttons_frame,
        text="📊",
        command=open_stats_window,
        width=40,
        height=40,
        font=tk.CTkFont(size=16),
        corner_radius=20,
        fg_color=("#21262d", "#21262d"),
        hover_color=("#30363d", "#30363d"),
        text_color=("#8b949e", "#8b949e")
    )
    stats_button.pack(side="left", padx=(0, 10))
    
    settings_button = tk.CTkButton(
        right_buttons_frame,
        text="⚙️",
        command=open_settings,
        width=40,
        height=40,
        font=tk.CTkFont(size=16),
        corner_radius=20,
        fg_color=("#21262d", "#21262d"),
        hover_color=("#30363d", "#30363d"),
        text_color=("#8b949e", "#8b949e")
    )
    settings_button.pack(side="left")
    
    content_frame = tk.CTkFrame(
        app, 
        corner_radius=25, 
        border_width=1, 
        border_color=("#21262d", "#21262d"),
        fg_color=("#161b22", "#161b22")
    )
    content_frame.grid(row=1, column=0, padx=30, pady=(0, 20), sticky="nsew")
    content_frame.grid_columnconfigure(0, weight=1)
    
    input_frame = tk.CTkFrame(content_frame, fg_color="transparent")
    input_frame.grid(row=0, column=0, padx=30, pady=(30, 0), sticky="ew")
    input_frame.grid_columnconfigure(0, weight=1)
    
    url_label = tk.CTkLabel(
        input_frame, 
        text="🔗 Paste YouTube URL" if not batch_mode else "🔗 Paste YouTube URLs (one per line for batch)",
        font=tk.CTkFont(size=16, weight="bold"),
        text_color=("#f0f6fc", "#f0f6fc")
    )
    url_label.grid(row=0, column=0, sticky="w", pady=(0, 10))
    
    textbox = tk.CTkTextbox(
        input_frame, 
        height=100,
        corner_radius=15,
        border_width=2,
        font=tk.CTkFont(size=14),
        border_color=("#30363d", "#30363d"),
        fg_color=("#0d1117", "#0d1117"),
        text_color=("#f0f6fc", "#f0f6fc")
    )
    textbox.grid(row=1, column=0, sticky="ew", pady=(0, 20))
    placeholder_text = "Paste YouTube URL here..." if not batch_mode else "Paste YouTube URLs here (one per line)..."
    textbox.insert("0.0", placeholder_text)
    textbox.bind("<Button-1>", clear_placeholder)
    textbox.bind("<Key>", clear_placeholder)
    
    create_context_menu()
    
    def paste_from_clipboard(event=None):
        try:
            clipboard_data = app.clipboard_get()
            if clipboard_data:
                current_text = textbox.get("0.0", "end-1c").strip()
                textbox.delete("0.0", "end")
                textbox.insert("0.0", clipboard_data.strip())
                
                if 'youtube.com' in clipboard_data or 'youtu.be' in clipboard_data:
                    textbox.configure(border_color=("#238636", "#238636"))
                    status_label.configure(text="✅ URL pasted from clipboard!")
                else:
                    textbox.configure(border_color=("#f85149", "#f85149"))
                    status_label.configure(text="❌ Not a YouTube URL")
                
                return "break"
        except Exception as e:
            print(f"Paste error: {e}")
    
    app.bind('<Control-v>', paste_from_clipboard)
    textbox.bind('<Control-v>', paste_from_clipboard)
    
    button = tk.CTkButton(
        input_frame, 
        text=f"📥 Download {current_format.upper()}",
        command=lambda: indir_sadece_ses(textbox.get("0.0", "end-1c").strip()),
        height=55,
        font=tk.CTkFont(size=18, weight="bold"),
        corner_radius=15,
        fg_color=("#238636", "#238636"),
        hover_color=("#2ea043", "#2ea043"),
        text_color=("#ffffff", "#ffffff")
    )
    button.grid(row=2, column=0, sticky="ew", pady=(0, 30))
    
    status_frame = tk.CTkFrame(app, fg_color="transparent")
    status_frame.grid(row=2, column=0, padx=30, pady=(0, 30), sticky="ew")
    
    status_label = tk.CTkLabel(
        status_frame,
        text="✅ Ready to download",
        font=tk.CTkFont(size=14),
        text_color=("#8b949e", "#8b949e")
    )
    status_label.pack(pady=(0, 15))
    
    progress_bar = tk.CTkProgressBar(
        status_frame,
        width=400,
        height=8,
        corner_radius=10,
        progress_color=("#238636", "#238636"),
        fg_color=("#21262d", "#21262d")
    )
    progress_bar.set(0)
    
    app.bind('<Control-v>', lambda e: textbox.focus())
    app.bind('<Return>', lambda e: indir_sadece_ses(textbox.get("0.0", "end-1c").strip()))
    app.bind('<Escape>', lambda e: app.quit())
    
    if clipboard_monitoring:
        start_clipboard_monitoring()
        
    app.mainloop()
