
import subprocess
import requests
import re

from pathlib import Path
from .models import User, Song, Queue
from . import db

APP_PATH = str(Path(__file__).parent.absolute())
YT_BASE_URL = 'https://www.youtube.com/watch?v='
SONGS_DIR = '/static/songs/'
#DB_HOST = 'mariadb'
DB_HOST = '172.18.240.5'

file = APP_PATH + '/passwords.txt'
with open(file, "r") as file:
  for line in file:
      line_data = line.split('=')
      line_data[1] = line_data[1].replace('\n', '')
      if line_data[0] == 'lastfm':
        LASTFM_PASS = line_data[1]
      elif line_data[0] == 'mariadb':
        DB_PASS = line_data[1]  
      elif line_data[0] == 'secretkey':
        SECRET_KEY = line_data[1]          

class SongQueue:
    id = 0
    roomid = ''
    userid = ''
    singer = ''
    youtubeid = ''
    artist = ''
    song = ''
    
class LastFM:
    artist = ''
    song = ''
    
    def get_display_data(self):
        return {
            "artist": self.artist,
            "song": self.song
        }

class YoutubeVideos:
    id = ''
    thumb = ''
    description = ''

    def get_display_data(self):
        image = self.thumb.split('/')[5]
        return {
            "id": self.id,
            "thumb": self.thumb,
            "description": self.description,
            "image": image
        }

def youtube_download(videoid):
    
    filename = APP_PATH + SONGS_DIR + str(videoid) + '.mp4'
    download_url = YT_BASE_URL + str(videoid)
    cmd = ["yt-dlp", "-f", "mp4", "-o", filename, download_url]

    rc = subprocess.call(cmd)
    if rc != 0:
        rc = subprocess.call(cmd)  # retry once. Seems like this can be flaky
    if rc == 0:
        return True
    else:
        return False
    
def video_delete(videoid):
    
    filename = APP_PATH + SONGS_DIR + str(videoid) + '.mp4'
    cmd = ["rm", filename]

    rc = subprocess.call(cmd)
    if rc != 0:
        rc = subprocess.call(cmd)  # retry once. Seems like this can be flaky
    if rc == 0:
        return True
    else:
        return False
    
def queue_get(roomid):

    reorder_array = []
    counter = {}

    queue = Queue.query.filter_by(roomid=roomid)

    for queue_item in queue:
        if queue_item.userid in counter:
            counter[queue_item.userid] += 1
        else:
            counter[queue_item.userid] = 1
        
        reorder_array.append([queue_item, counter[queue_item.userid], queue_item.id])
    
    reorder_array.sort(key=lambda x: (x[1], x[2]))
    
    queue_array = []
    
    for queue_item in reorder_array:
        if queue_item[0].status != '':
            continue
        try:
            user = User.query.filter_by(id=queue_item[0].userid).first()
            song = Song.query.filter_by(youtubeid=queue_item[0].youtubeid).first()
            song_queue = SongQueue()
            song_queue.id = queue_item[0].id
            song_queue.roomid = queue_item[0].roomid
            song_queue.userid = queue_item[0].userid
            song_queue.singer = user.name
            song_queue.youtubeid = queue_item[0].youtubeid
            song_queue.artist = song.artist
            song_queue.song = song.name
            queue_array.append(song_queue)
        except:
            continue

    return queue_array

def next_queue_item(page_load, current_user):
    
    next_song = None
    
    if page_load:
        queue = Queue.query.filter_by(roomid=current_user.roomid, status='P').first()
        try:
            if queue.status == 'P':
                next_song = queue
        except:
            1 == 1

    if next_song == None:
        queue = queue_get(roomid=current_user.roomid)
        try:
            queue = queue[0]    
            Queue.query.filter_by(roomid=current_user.roomid, status='P').delete()
            queue_update = Queue.query.filter_by(id=queue.id).first()
            queue_update.status = 'P'
            db.session.add(queue_update)
            db.session.commit()        

        except:
            next_song = None
    
    if queue:
        next_url = "/static/songs/" + str(queue.youtubeid) + '.mp4'
    else:
        next_url = ''
        
    return next_url

def lastfm_search(search_arg):
  
  url = "https://ws.audioscrobbler.com/2.0/?method=track.search&track=" + search_arg + '&api_key=' + LASTFM_PASS + '&limit=20&format=json'
  try:
    response = requests.get(url)
    data = response.json()  
    tracks = []
    for results in data['results']['trackmatches']['track']:
      last_fm = LastFM()
      last_fm.artist = results['artist']
      last_fm.song = results['name']
      tracks.append(last_fm)
  except:
    return None
  
  return tracks

def youtube_search(search_arg):
    
    search_url = "https://www.youtube.com/results?search_query=karaoke " + search_arg    
    response = requests.get(search_url)
    splited = response.text.split('{"videoRenderer":{"')
    video_list = []
    for video_data in splited:
        try:
            video_id = re.findall(r'videoId":"(.*?)","thumbnail', video_data)[0]
            aux = video_data.replace('{"thumbnails":[{"url":"', 'zz_thumbs')
            aux = aux.replace('?sqp', 'zz_thumbd')
            thumbnail = re.findall(r'zz_thumbs(.*?)zz_thumbd', aux)[0]
            aux = video_data.replace('"title":{"runs":[{"text":"', 'zz_thumbs')
            aux = aux.replace('"}],"accessibility":', 'zz_thumbd')
            description = re.findall(r'zz_thumbs(.*?)zz_thumbd', aux)[0]     
            youtube_video = YoutubeVideos()
            youtube_video.id = video_id
            youtube_video.thumb = thumbnail
            youtube_video.description = description
            video_list.append(youtube_video)
        except:
            continue
        
    return video_list