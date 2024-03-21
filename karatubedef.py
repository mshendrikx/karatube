
import subprocess
import mysql.connector
import requests
import re

from pathlib import Path
from bs4 import BeautifulSoup


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
      if line_data[0] == 'mariadb':
          DB_PASS = line_data[1]  

class SongQueue:
    id = 0
    pos = 0
    roomid = ''
    userid = ''
    firstname = ''
    lastname = ''
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

def db_connect():

    try:    
        conn = mysql.connector.connect(user='root', password=DB_PASS, host=DB_HOST, database='karatube')
        return conn
    except:
        return None
    
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
    
def db_add_song(videoid, name, artist, image):
    
    conn = db_connect()
    if conn == None:
        return False

    cursor = conn.cursor(buffered=True)
    
    sql = 'REPLACE INTO songs (youtubeid, name, artist, image) VALUES (%s,%s,%s,%s)'    
    values = (videoid, name, artist, image)
    
    try:
        cursor.execute(sql, values)
        conn.commit()
        conn.close()
        return True
    except:
        return False
    
def queue_add_song(roomid, userid, youtubeid):
    
    conn = db_connect()
    if conn == None:
        return False    
    cursor = conn.cursor(buffered=True)

    sql = 'INSERT INTO songqueue (roomid, userid, youtubeid, status) VALUES (%s,%s,%s,%s)'    
    values = (roomid, userid, youtubeid, ' ')
    
    try:
        cursor.execute(sql, values)
        conn.commit()
        conn.close()
        return True
    except:
        return False
    
def queue_get(roomid, status):

    index = 1
    reorder_array = []
    counter = {}
        
    conn = db_connect()
    if conn == None:
        return None
    cursor = conn.cursor(buffered=True)
    
    sql = "SELECT * FROM songqueue WHERE roomid = %s AND status = %s ;"    
    values = (roomid, status)
    
    try:
        cursor.execute(sql, values)
    except:
        return None
    
    for row in cursor.fetchall():
        if row[2] in counter:
            counter[row[2]] += 1
        else:
            counter[row[2]] = 1
        reorder_array.append([row, counter[row[2]], row[0]])        

    reorder_array.sort(key=lambda x: (x[1], x[2]))
    
    queue_array = []
    for ordered_line in reorder_array:
        try:
            sql = "SELECT firstname, lastname FROM users WHERE userid = %s ;"  
            values = (ordered_line[0][2],)
            cursor.execute(sql, values)
            for user in cursor.fetchall():
                break
            sql = "SELECT name, artist FROM songs WHERE youtubeid = %s ;"  
            values = (ordered_line[0][3],)
            cursor.execute(sql, values)
            for song in cursor.fetchall():
                break        
            song_queue = SongQueue()
            song_queue.id = ordered_line[0][0]
            song_queue.pos = index
            song_queue.roomid = roomid
            song_queue.userid = ordered_line[0][2]
            song_queue.firstname = user[0]
            song_queue.lastname = user[1]
            song_queue.artist = song[1]
            song_queue.song = song[0]
            queue_array.append(song_queue)
            index += 1           
        except:
            continue        
        
    conn.close()
    
    return queue_array

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
    