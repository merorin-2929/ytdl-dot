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

def download_video(v: dict, output_dir: str, progressbar: ProgressBar):
    url = v.get("url")
    title = v.get("title")
    print("Download : ",title)
    cmd = [
        "yt-dlp",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best",
        "--merge-output-format", "mp4",
        "-o", f"{output_dir}/%(title)s.%(ext)s",
        "--no-playlist",
        url
    ]
    try:
        progressbar.value = None
        progressbar.update()
        subprocess.run(cmd,check=True)
        progressbar.value = 1
        progressbar.update()
    except subprocess.CalledProcessError:
        pass

def main(page:Page):
    page.title = "ytdl."
    page.scroll = ScrollMode.ADAPTIVE

    selected_videos = []
    all_videos = []
    download_buttons = []

    def toggle_download_button(state:bool):
        for b in download_buttons:
            b.disabled = state
            b.icon = Icons.HOURGLASS_BOTTOM if state else Icons.DOWNLOAD
            b.text = "ダウンロード中" if state else "ダウンロード"
        download_button.disabled = state
        download_button.icon = Icons.HOURGLASS_BOTTOM if state else Icons.DOWNLOAD
        download_button.text = "ダウンロード中" if state else "ダウンロード"
        page.update()

    def on_fetch(e):
        videos_list.controls.clear()
        all_videos.clear()
        selected_videos.clear()
        download_buttons.clear()
        fetch_button.icon = Icons.HOURGLASS_BOTTOM
        fetch_button.disabled = True
        fetch_button.update()
        if url_input.value:
            videos = get_video_info(url_input.value)
            if not videos:
                return
            for v in videos:
                all_videos.append(v)
                dl_button = TextButton(
                    text="ダウンロード",
                    icon=Icons.DOWNLOAD,
                    on_click=lambda _e, video=v: download_video(video,output_path_input.value,download_progress)
                )
                download_buttons.append(dl_button)
                checkbox = Checkbox(value=False)
                def on_check(_e,v=v, cb=checkbox):
                    if cb.value:
                        selected_videos.append(v["url"])
                    else:
                        try:
                            selected_videos.remove(v["url"])
                        except ValueError:
                            pass
                checkbox.on_change = on_check

                video_card = Card(
                    content=Container(
                        content=Row([
                            Image(src=resolve_thumbnail(v["id"]),width=182,border_radius=border_radius.all(8)),
                            Column([
                                Text(value=v["title"],weight=FontWeight.BOLD,size=16,max_lines=2),
                                Text(value=v["url"],size=12,color=Colors.BLACK54)
                            ],expand=True),
                            dl_button,
                            checkbox
                        ]),padding=10
                    )
                )
                videos_list.controls.append(video_card)
                page.update()
        fetch_button.icon = Icons.SEARCH
        fetch_button.disabled = False
        fetch_button.update()

    def on_download(e):
        toggle_download_button(True)
        targets = ([v for v in all_videos if v["url"] in selected_videos] if selected_videos else all_videos)
        if not targets:
            page.open(SnackBar(Text("ダウンロードできる動画がありません")))
            toggle_download_button(False)
            return
        def worker():
            for video in targets:
                download_video(video,output_path_input.value,download_progress)
            msg = f"{len(targets)}件のダウンロードを完了しました"
            page.open(SnackBar(Text(msg)))
            toggle_download_button(False)
        threading.Thread(target=worker, daemon=True).start()
    
    url_input = TextField(label="URL", hint_text="URLを入力", expand=True)
    fetch_button = TextButton(text="取得",icon=Icons.SEARCH,on_click=on_fetch)
    videos_list = Column(spacing=10,width=float("inf"),expand=True,scroll=ScrollMode.ADAPTIVE)
    output_path_input = TextField(label="保存先",value=default_download_dir)
    output_path_button = TextButton(text="選択",icon=Icons.FOLDER)
    download_button = FloatingActionButton(text="ダウンロード",icon=Icons.DOWNLOAD,on_click=on_download)
    download_progress = ProgressBar(value=0,border_radius=border_radius.all(8))
    page.floating_action_button = download_button
    tabs = Tabs(tabs=[
        Tab(text="動画リスト",icon=Icons.LIST,content=videos_list),
        Tab(text="ダウンロード設定",icon=Icons.SETTINGS,content=[])
    ],height=500,expand=1,selected_index=0,animation_duration=300)

    page.add(
        Column([
            Row([url_input,fetch_button]),
            tabs
        ]),
        download_progress
    )

app(target=main)