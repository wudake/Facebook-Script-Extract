import socket
import yt_dlp
from pathlib import Path

# 强制使用 IPv4（避免容器环境 IPv6 不可达导致连接失败）
_orig_getaddrinfo = socket.getaddrinfo

def _getaddrinfo_ipv4_only(host, port, family=0, type=0, proto=0, flags=0):
    return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)

socket.getaddrinfo = _getaddrinfo_ipv4_only


class VideoDownloader:
    def __init__(self, temp_dir: str = "./temp"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def download(self, url: str) -> str:
        output_template = str(self.temp_dir / "%(id)s.%(ext)s")
        ydl_opts = {
            'format': 'best[height<=720][ext=mp4]/best[height<=720]/best',
            'merge_output_format': 'mp4',
            'outtmpl': output_template,
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 60,
            'retries': 5,
            'fragment_retries': 5,
            'file_access_retries': 5,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_id = info.get('id', 'unknown')
            # 找到下载的文件
            for f in self.temp_dir.iterdir():
                if f.stem == video_id and f.suffix in ('.mp4', '.webm', '.mkv'):
                    return str(f)
        raise FileNotFoundError("未找到下载的视频文件")
