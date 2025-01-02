import project
import os

from project.models import Song
from apscheduler.schedulers.background import BackgroundScheduler
from pytubefix import YouTube

YT_BASE_URL = "https://www.youtube.com/watch?v="

app = project.create_app()

def youtube_download():
    
    print("Scheduler funcionou.")
    with app.app_context():
       
        songs = Song.query.filter_by(downloaded=0)
        
        for song in  songs:
            video_file = str(song.youtubeid) + ".mp4"
            filename = '/app/project/static/songs/' + video_file
            file_path = '/app/project/static/songs'
            if not os.path.exists(filename):
                download_url = YT_BASE_URL + str(song.youtubeid)
                try:
                    YouTube(download_url).streams.first().download(output_path=file_path, filename=video_file)
                except Exception as e:
                    1 == 1
                    continue
    
scheduler = BackgroundScheduler()
scheduler.add_job(func=youtube_download, trigger="interval", minutes=1)
scheduler.start()

app.run(host="0.0.0.0", port=7003)
