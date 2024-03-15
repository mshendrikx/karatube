
import subprocess
import mysql.connector
import requests

from pathlib import Path

APP_PATH = str(Path(__file__).parent.absolute())
YT_BASE_URL = 'https://www.youtube.com/watch?v='
SONGS_DIR = '/static/songs/'
DB_PASS = ''
#DB_HOST = 'mariadb'
DB_HOST = '172.18.240.5'
LASTFM_PASS = ''

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
    
def db_add_song(videoid, name, artist, description):
    
    conn = db_connect()
    if conn == None:
        return False

    cursor = conn.cursor(buffered=True)
    
    sql = 'INSERT INTO songs (youtubeid, name, artist, description) VALUES (%s,%s,%s,%s)'    
    values = (videoid, name, artist, description)
    
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