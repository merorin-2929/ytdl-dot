# ytdl-.(dot)

## Sorry!!!
Sorry! This software only supports Japanese!

## About
シンプルなyt-dlp GUIソフトウェアです。

## 機能(β)
![](2025-10-13-14-42-08.png)

- **プレイリスト分割**  
    プレイリストを分割し一本ずつダウンロードできるようになっています

- **設定の保存**  
    設定を保存して起動時に読み込めます。

- **フォーマット・品質の選択**  
    mp4,mkv,mp3,wavから選択できます。  
    mp4,mkvの場合は自動または4K〜720p,mp3の場合は自動または320kbps〜128kbpsを選択できます。

## 実装予定

- **Music Mode**  
    Music向けに最適化されたメタデータパースをするモードの実装

## 動作環境及び必須パッケージ

| OS | バージョン | python | pyinstaller |
| --- | --- | --- | --- |
| Windows 11 | 24H2 | OK | OK(配布中) |
| macOS | Sonoma | OK | NG |
| Ubuntu | 24.04 LTS | OK | OK |

開発環境は主にWindowsです。  
動作検証はWindows及びmacOSで都度行っています。  
Linuxに関してはWSL上のUbuntuで動作検証を行っています。

### Windowsの必須パッケージ

- yt-dlp(このアプリには含まれていません)
- ffmpeg(動画の処理)

### macOSの必須パッケージ

- yt-dlp(このアプリには含まれていません)
- ffmpeg(動画の処理)

### Linuxの必須パッケージ

- yt-dlp(このアプリには含まれていません)
- ffmpeg(動画の処理)
- libmpvもしくはmpv(GUIの動作に必要)