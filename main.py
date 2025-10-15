from flet import *
import subprocess
import json
import os
import threading
import requests
import platform

# ホームディレクトリ云々
homedir = os.path.abspath(os.path.expanduser("~"))
default_download_dir = os.path.join(homedir,"yt-dlp")

# 開く
def open_folder(path: str):
    path = os.path.abspath(path)
    system = platform.system()

    if system == "Windows":
        subprocess.Popen(["explorer", path])
    elif system == "Darwin":
        subprocess.Popen(["open", path])
    elif system == "Linux":
        subprocess.Popen(["xdg-open", path])
    else:
        pass

# サムネイル
def resolve_thumbnail(vid:str) -> str | None:
    if not vid:
        return None
    urls = [
        f"https://i.ytimg.com/vi/{vid}/maxresdefault.jpg",
        f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
    ]
    for u in urls:
        try:
            r = requests.head(u, timeout=1)
            if r.status_code == 200:
                return u
        except Exception:
            continue
    return None

# 情報取得
def get_video_info(url: str):
    cmd = ["yt-dlp","-J","--flat-playlist","--add-header","Accept-Language: ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",url]
    try:
        if platform.system() == "Windows":
            result = subprocess.run(cmd,capture_output=True,text=True,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

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

def main(page:Page) -> None:
    page.title = "ytdl."
    page.scroll = ScrollMode.ADAPTIVE
    page.theme_mode = ThemeMode.LIGHT
    page.theme = Theme(color_scheme=ColorScheme(primary=Colors.RED))

    # ウィンドウ設定
    page.window.height = 700
    page.window.width = 1200
    page.window.center()
    page.on_close = lambda e: save_current_settings()

    # 諸々の変数
    current_url = ""
    selected_videos = []
    all_videos = []
    download_buttons = []
    settings_path = os.path.abspath("./config.json")

    def load_settings():
        """設定をJSONから読み込む"""
        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print("設定の読み込みに失敗:", e)
                return {}
        return {}
    
    def save_settings(data: dict):
        """設定をJSONに保存する"""
        try:
            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("設定の保存に失敗:", e)
    
    def save_current_settings():
        data = {
            "output_path": output_path_input.value,
            "format": format_dropdown.value,
            "quality": quality_dropdown.value,
            "use_cookies": use_cookies.value,
            "from_cookies": from_cookies.value,
        }
        save_settings(data)

    # ダウンロードボタンのトグル
    def toggle_download_button(state:bool):
        for b in download_buttons:
            b.disabled = state
            b.icon = Icons.HOURGLASS_BOTTOM if state else Icons.DOWNLOAD
            b.text = "ダウンロード中" if state else "ダウンロード"
        download_button.disabled = state
        download_button.icon = Icons.HOURGLASS_BOTTOM if state else Icons.DOWNLOAD
        download_button.text = "ダウンロード中" if state else "ダウンロード"
        page.update()

    # ダウンロード
    def download_video(v: dict):
        url = v.get("url")
        title = v.get("title")
        channel = v.get("channel")
        print("Download : ",title)
        progress_template = "Downloading: %(progress._percent_str)s"
        cmd = ["yt-dlp", "--newline", "--no-warnings","--progress-template",progress_template]
        if use_cookies.value and from_cookies.value != "none":
            cmd.extend(["--cookies-from-browser",from_cookies.value])
        if format_dropdown.value == "mp4" or format_dropdown.value == "mkv":
            if quality_dropdown.value == "auto":
                cmd.extend(["-f","bestvideo[ext=mp4]+bestaudio[ext=m4a]/best","--merge-output-format",format_dropdown.value])
            else:
                cmd.extend(["-f",f"bestvideo[ext=mp4][height>={quality_dropdown.value}]+bestaudio[ext=m4a]/best","--merge-output-format",format_dropdown.value])
        elif format_dropdown.value == "mp3":
            cmd.extend(["-f","bestaudio/best","-x","--audio-format",format_dropdown.value])
            if quality_dropdown.value != "auto":
                cmd.extend(["--audio-quality",quality_dropdown.value])
            else:
                cmd.extend(["--audio-quality","0"])
        else:
            cmd.extend(["-f","bestaudio/best","-x","--audio-format",format_dropdown.value,"--audio-quality","0"])
        
        cmd.extend(["-o",f"{os.path.abspath(output_path_input.value)}/%(title)s.%(ext)s"])
        cmd.append(url)
        try:
            download_progress.value = None
            downloading_title.value = title
            downloading_channel.value = channel
            tabs.selected_index = 2
            log_text.controls.append(Text(f"▶️ ダウンロード開始 : {title}",weight=FontWeight.BOLD,color=Colors.BLUE))
            log_text.scroll_to(-1)
            toggle_download_button(True)
            if platform.system() == 'Windows':
                p = subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1,universal_newlines=True,creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1,universal_newlines=True)
            while True:
                output = p.stdout.readline()
                if output == "" and p.poll() is not None:
                    break
                if output:
                    log_entry = output.strip()
                    if log_entry.startswith("Downloading:") :
                        try:
                            progress = progress = output.split("Downloading: ")[1].strip()
                            download_progress.value = float(progress.strip("%")) / 100
                            download_progress.update()
                        except ValueError:
                            pass
                    else:
                        log_text.controls.append(Text(log_entry))
                        log_text.scroll_to(-1)
                        log_text.update()
            for line in p.stderr:
                output = line.strip()
                if output == "" and p.poll() is not None:
                    break
                if output:
                    error_message = output.strip()
                    log_text.controls.append(Text(f"⚠️ エラー : {error_message}",color=Colors.RED,weight=FontWeight.BOLD))
            p.wait()
            log_text.controls.append(Text(f"✅ ダウンロード完了 : {title}",weight=FontWeight.BOLD,color=Colors.GREEN))
            log_text.scroll_to(-1)
            log_text.update()
        except Exception as e:
            log_text.controls.append(Text(f"[Error] {str(e)}",color=Colors.RED,weight=FontWeight.BOLD))
            log_text.scroll_to(-1)
            log_text.update()
        finally:
            download_progress.value = 1
            downloading_title.value = ""
            downloading_channel.value = ""
            toggle_download_button(False)

    # 情報取得
    def on_fetch(e):
        nonlocal current_url
        videos_list.controls.clear()
        all_videos.clear()
        selected_videos.clear()
        download_buttons.clear()
        fetch_button.icon = Icons.HOURGLASS_BOTTOM
        fetch_button.disabled = True
        tabs.selected_index = 0
        videos_list.controls.append(videos_load)
        page.update()
        if url_input.value:
            current_url = url_input.value
            print("Update CurrentURL : ",current_url)
            videos = get_video_info(url_input.value)
            page.update()
            if not videos:
                page.open(SnackBar(Text("情報の取得中にエラーが発生しました")))
                fetch_button.icon = Icons.SEARCH
                fetch_button.disabled = False
                videos_list.controls.clear()
                videos_list.controls.append(videos_empty)
                page.update()
                return
            videos_list.controls.pop()
            for v in videos:
                all_videos.append(v)
                dl_button = TextButton(
                    text="ダウンロード",
                    icon=Icons.DOWNLOAD,
                    on_click=lambda _e, video=v: download_video(video)
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
                                Text(value=v["channel"],size=12,color=Colors.BLACK54)
                            ],expand=True),
                            dl_button,
                            checkbox
                        ]),padding=10
                    )
                )
                videos_list.controls.append(video_card)
        else:
            page.open(SnackBar(Text("URLを入力してください")))
            fetch_button.icon = Icons.SEARCH
            fetch_button.disabled = False
            videos_list.controls.clear()
            videos_list.controls.append(videos_empty)
            page.update()
            return
        fetch_button.icon = Icons.SEARCH
        fetch_button.disabled = False
        page.update()

    # 選択・全体ダウンロード
    def on_download(e):
        toggle_download_button(True)
        print(current_url)
        if current_url != url_input.value:
            on_fetch(any)
            page.open(SnackBar(Text("情報を取得しました")))
            toggle_download_button(False)
            return
        targets = ([v for v in all_videos if v["url"] in selected_videos] if selected_videos else all_videos)
        if not targets:
            page.open(SnackBar(Text("ダウンロードできる動画がありません")))
            toggle_download_button(False)
            return
        def worker():
            for video in targets:
                download_video(video)
            toggle_download_button(False)
        threading.Thread(target=worker, daemon=True).start()
    
    def on_cookie(e):
        if use_cookies.value:
            from_cookies.disabled = False
            from_cookies.update()
        else:
            from_cookies.disabled = True
            from_cookies.update()
    
    def change_format(e):
        if format_dropdown.value == "mp4" or format_dropdown.value == "mkv":
            quality_dropdown.disabled = False
            quality_dropdown.options = video_quality_list
            quality_dropdown.value = video_quality_list[0].key
            quality_dropdown.update()
        elif format_dropdown.value == "mp3":
            quality_dropdown.disabled = False
            quality_dropdown.options = audio_quality_list
            quality_dropdown.value = audio_quality_list[0].key
            quality_dropdown.update()
        else:
            quality_dropdown.disabled = True
            quality_dropdown.options = []
            quality_dropdown.value = ""
            quality_dropdown.update()
    
    def pick_output_dir(e:FilePickerResultEvent):
        before_path = output_path_input.value
        output_path_input.value = os.path.abspath(e.path) if e.path else before_path
        save_current_settings()
        page.update()
    
    pick_output_dialog = FilePicker(on_result=pick_output_dir)

    page.overlay.append(pick_output_dialog)

    settings = load_settings()

    output_dir = settings.get("output_path", default_download_dir)
    fmt = settings.get("format", "mp4")
    quality = settings.get("quality", "auto")
    use_cookie = settings.get("use_cookies", False)
    from_cookie = settings.get("from_cookies", "none")
    
    # UI要素定義
    url_input = TextField(label="URL", hint_text="URLを入力", expand=True)
    fetch_button = TextButton(text="取得", icon=Icons.SEARCH, on_click=on_fetch)

    videos_empty = Container(
        content=Row(
            [Text("動画がありません\nURLを入力し「取得」を押してください", size=16, text_align=TextAlign.CENTER)],
            alignment=MainAxisAlignment.CENTER
        ),
        padding=padding.all(12)
    )
    videos_load = Container(
        content=Row(
            [
                ProgressRing(width=24, height=24, value=None, stroke_cap=StrokeCap.ROUND),
                Text("読み込み中...", size=16, weight=FontWeight.BOLD)
            ],
            alignment=MainAxisAlignment.CENTER
        ),
        padding=padding.all(12)
    )
    videos_list = Column(
        spacing=10,
        width=float("inf"),
        expand=True,
        scroll=ScrollMode.ADAPTIVE,
        controls=[videos_empty]
    )

    # 保存先
    output_path_input = TextField(
        label="保存先",
        value=output_dir,
        expand=1,
        on_change=lambda e: save_current_settings()
    )
    output_path_button = TextButton(
        text="選択",
        icon=Icons.FOLDER,
        on_click=lambda _: pick_output_dialog.get_directory_path(
            dialog_title="保存先を選択",
            initial_directory=output_path_input.value
        )
    )
    output_path_open = TextButton(
        text="開く",
        icon=Icons.FOLDER_OPEN,
        on_click=lambda _:open_folder(output_path_input.value)
    )

    # cookie
    use_cookies = Switch(
        label="cookieを使用する",
        value=use_cookie,
        on_change=lambda e: [on_cookie(e), save_current_settings()]
    )
    from_cookies = Dropdown(
        label="ブラウザを選択",
        options=[
            DropdownOption(key="none", text="None"),
            DropdownOption(key="chrome", text="Chrome"),
            DropdownOption(key="firefox", text="Firefox"),
            DropdownOption(key="brave", text="Brave")
        ],
        value=from_cookie,
        disabled=not use_cookie,
        expand=1,
        on_change=lambda e: save_current_settings()
    )

    # フォーマット
    format_dropdown = Dropdown(
        label="フォーマット",
        options=[
            DropdownOption(key="mp4", text="mp4"),
            DropdownOption(key="mkv", text="mkv"),
            DropdownOption(key="mp3", text="mp3"),
            DropdownOption(key="wav", text="wav")
        ],
        value=fmt,
        expand=1,
        on_change=lambda e: [change_format(e), save_current_settings()]
    )

    video_quality_list = [
        DropdownOption(key="auto", text="自動"),
        DropdownOption(key="2160", text="4K"),
        DropdownOption(key="1440", text="2K"),
        DropdownOption(key="1080", text="1080p"),
        DropdownOption(key="720", text="720p")
    ]
    audio_quality_list = [
        DropdownOption(key="auto", text="自動"),
        DropdownOption(key="320k", text="320kbps"),
        DropdownOption(key="256k", text="256kbps"),
        DropdownOption(key="192k", text="192kbps"),
        DropdownOption(key="128k", text="128kbps")
    ]

    if fmt in ["mp4", "mkv"]:
        quality_dropdown = Dropdown(
            label="品質",
            options=video_quality_list,
            value=quality,
            expand=1,
            on_change=lambda e: save_current_settings()
        )
    elif fmt == "mp3":
        quality_dropdown = Dropdown(
            label="品質",
            options=audio_quality_list,
            value=quality,
            expand=1,
            on_change=lambda e: save_current_settings()
        )
    else:  # wav
        quality_dropdown = Dropdown(
            label="品質",
            options=[],
            value=None,
            disabled=True,
            expand=1
        )

    # ステータス画面 - 要素
    downloading_title = TextField(label="ダウンロード中の動画", expand=1)
    downloading_channel = TextField(label="チャンネル", expand=1)
    log_text = Column(spacing=0, expand=1, scroll=ScrollMode.ADAPTIVE, width=float("inf"))
    
    download_button = FloatingActionButton(
        text="ダウンロード",
        icon=Icons.DOWNLOAD,
        on_click=on_download,
        bgcolor=Colors.RED_100
    )

    download_progress = ProgressBar(value=0, border_radius=border_radius.all(8))


    # 設定タブ
    setting_tab = Column(
        controls=[
            Row([output_path_input,output_path_button,output_path_open]),
            Row([format_dropdown,quality_dropdown]),
            Row([use_cookies,from_cookies])
        ],
        width=float("inf")
    )

    log_tab = Column(
        controls=[
            Row([downloading_title,downloading_channel]),
            log_text
        ],
        width=float("inf")
    )

    tabs = Tabs(tabs=[
        Tab(text="動画リスト",content=videos_list),
        Tab(text="ダウンロード設定",content=Container(content=setting_tab,padding=padding.all(12))),
        Tab(text="ログ",content=Container(content=log_tab,padding=padding.all(12),expand=1))
    ],height=500,expand=1,selected_index=0,animation_duration=300)

    save_current_settings()
    
    # 最終
    page.floating_action_button = download_button
    page.add(
        Column([
            Row([url_input,fetch_button]),
            tabs
        ]),
        download_progress
    )

if __name__ == '__main__':
    app(target=main)