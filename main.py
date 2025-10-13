from flet import *
import subprocess
import json
import os
import threading
import requests

homedir = os.path.abspath(os.path.expanduser("~"))
default_download_dir = os.path.join(homedir,"yt-dlp")

def resolve_thumbnail(vid:str) -> str | None:
    if not vid:
        return None
    urls = [
        f"https://i.ytimg.com/vi/{vid}/maxresdefault.jpg",
        f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
    ]
    for u in urls:
        try:
            r = requests.head(u, timeout=3)
            if r.status_code == 200:
                return u
        except Exception:
            continue
    return None

def get_video_info(url: str):
    cmd = ["yt-dlp","-J","--flat-playlist",url]
    try:
        result = subprocess.run(cmd,capture_output=True,text=True,check=True)
        data = json.loads(result.stdout)

        if "entries" in data:
            entries = data["entries"]
        else:
            entries = [data]
        
        videos = []
        for v in entries:
            vid = v.get("id")
            url = v.get("url") or v.get("webpage_url")
            title = v.get("title") or v.get("fulltitle") or "None"
            channel = v.get("uploader") or v.get("channel") or "None"
            videos.append({
                "id": vid,
                "url": url,
                "title": title,
                "channel": channel
            })
        return videos
    except subprocess.CalledProcessError as e:
        print("ERROR: ",e)
        return []

def download_video(url: str, output_dir: str):
    print("Download : ",url)
    cmd = [
        "yt-dlp",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best",
        "--merge-output-format", "mp4",
        "-o", f"{output_dir}/%(title)s.%(ext)s",
        "--no-playlist",
        url
    ]
    try:
        subprocess.run(cmd,check=True)
    except subprocess.CalledProcessError:
        pass

def main(page:Page):
    page.title = "ytdl."

    def on_fetch(e):
        videos_list.controls.clear()
        if url_input.value:
            videos = get_video_info(url_input.value)
            if not videos:
                return
            for v in videos:
                handler = (lambda _e, u=v["url"]: download_video(u, default_download_dir))
                video_card = Card(
                    content=Container(
                        content=Row([
                            Image(src=resolve_thumbnail(v["id"]),width=182,border_radius=border_radius.all(8)),
                            Column([
                                Text(value=v["title"],weight=FontWeight.BOLD,size=16),
                                Text(value=f"{v["url"]}",size=12,color=Colors.BLACK54)
                            ],expand=True),
                            TextButton(text=f"Download({v["id"]})",icon=Icons.DOWNLOAD,on_click=handler)
                        ]),padding=10
                    )
                )
                videos_list.controls.append(video_card)
                page.update()

    
    url_input = TextField(label="URL", hint_text="URLを入力", expand=True)
    fetch_button = TextButton(text="取得",icon=Icons.SEARCH,on_click=on_fetch)
    videos_list = Column(spacing=10,height=500,width=float("inf"),scroll=ScrollMode.ADAPTIVE)

    page.add(
        Row([url_input,fetch_button]),
        videos_list
    )

app(target=main)