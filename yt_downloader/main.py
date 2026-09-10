import yt_dlp

playlist_url = "https://youtube.com/playlist?list=PLD621Q3vNKnhEIcwyMcK7MUvRZxxfU2WJ&si=zDPsnjEzBVTDooh8"


ydl_opts = {
    "format": "bestaudio/best",
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }
    ],
    "outtmpl": "%(playlist_title)s/%(playlist_index)02d - %(title)s.%(ext)s",
    "ignoreerrors": True,  # skip deleted/private videos instead of stopping
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([playlist_url])
