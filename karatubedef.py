
import subprocess
import mysql.connector

from pathlib import Path

YT_BASE_URL = 'https://www.youtube.com/watch?v='
SONGS_DIR = '/static/songs/'
DB_PASS = '1mT17H75YD34'
#DB_HOST = 'mariadb'
DB_HOST = '172.18.240.5'

def db_connect():

    try:    
        conn = mysql.connector.connect(user='root', password=DB_PASS, host=DB_HOST, database='karatube')
        return conn
    except:
        return None
    
def youtube_download(videoid):
    
    current_path = str(Path(__file__).parent.absolute())
    filename = current_path + SONGS_DIR + str(videoid) + '.mp4'
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
    
def queue_get(roomid):
    
    conn = db_connect()
    if conn == None:
        return None
    
    queue = []
    
    
    
    