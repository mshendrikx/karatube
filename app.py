import project
import os
import subprocess
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from project.models import Song

YT_BASE_URL = "https://www.youtube.com/watch?v="

app = project.create_app()

# Configure logging
logging.basicConfig(filename='/app/logs/karatube.log', level=logging.WARN, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def youtube_download():

    with app.app_context():
        songs = Song.query.filter_by(downloaded=0)
        
        for song in  songs:
            video_file = str(song.youtubeid) + ".mp4"
            filename = '/app/project/static/songs/' + video_file            
            if not os.path.exists(filename):
                download_url = YT_BASE_URL + str(song.youtubeid)
                try:
                    command = "yt-dlp -f mp4 " + download_url + " --cookies /app/cookies.txt -o " + filename
                    process = subprocess.run(command, capture_output=True, text=True, check=True, shell=True)
                except Exception as e:
                    app.logger.error(e.stderr)
                    print(e.stderr)
                    continue
    
scheduler = BackgroundScheduler()
scheduler.add_job(func=youtube_download, trigger="interval", minutes=1)
scheduler.start()

app.run(host="0.0.0.0", port=7003)
