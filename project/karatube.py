import musicbrainzngs
import subprocess
import requests
import re
import os

from pathlib import Path
from .models import User, Song, Queue, Config
from . import db

APP_PATH = str(Path(__file__).parent.absolute())
YT_BASE_URL = "https://www.youtube.com/watch?v="
SONGS_DIR = "/static/songs/"
THUMBS_DIR = "/static/thumbs/"

musicbrainzngs.set_useragent(
    "python-musicbrainzngs-example",
    "0.1",
    "https://github.com/alastair/python-musicbrainzngs/",
)


class PlayerData:
    singer = ""
    song = ""
    next_singer = ""
    next_song = ""
    video_url = ""


class SongQueue:
    id = 0
    roomid = ""
    userid = ""
    singer = ""
    youtubeid = ""
    artist = ""
    song = ""
    status = ""


class MusicData:
    artist = ""
    song = ""

    def get_display_data(self):
        return {"artist": self.artist, "song": self.song}


class YoutubeVideos:
    id = ""
    thumb = ""
    description = ""

    def get_display_data(self):
        image = self.thumb.split("/")[5]
        return {
            "id": self.id,
            "thumb": self.thumb,
            "description": self.description,
            "image": image,
        }


def youtube_download(videoid):

    filename = APP_PATH + SONGS_DIR + str(videoid) + ".mp4"
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

    filename = APP_PATH + SONGS_DIR + str(videoid) + ".mp4"
    cmd = ["rm", filename]

    rc = subprocess.call(cmd)
    if rc != 0:
        rc = subprocess.call(cmd)  # retry once. Seems like this can be flaky
    
    filename = APP_PATH + THUMBS_DIR + str(videoid) + ".jpg"
    cmd = ["rm", filename]
    rc = subprocess.call(cmd)
    
    return True

def queue_get(roomid):

    reorder_array = []
    counter = {}

    queue = Queue.query.filter_by(roomid=roomid)

    for queue_item in queue:
        if queue_item.userid in counter:
            counter[queue_item.userid] += 1
        else:
            counter[queue_item.userid] = 1
        if queue_item.status == "P":
            status_int = 0
        else:
            status_int = 1

        reorder_array.append(
            [queue_item, status_int, counter[queue_item.userid], queue_item.id]
        )

    reorder_array.sort(key=lambda x: (x[1], x[2], x[3]))

    queue_array = []

    for queue_item in reorder_array:
        # if queue_item.status_int == 0:
        #    continue
        try:
            user = User.query.filter_by(id=queue_item[0].userid).first()
            song = Song.query.filter_by(youtubeid=queue_item[0].youtubeid).first()
            song_queue = SongQueue()
            song_queue.id = queue_item[0].id
            song_queue.roomid = queue_item[0].roomid
            song_queue.userid = queue_item[0].userid
            song_queue.status = queue_item[0].status
            song_queue.singer = user.name
            song_queue.youtubeid = queue_item[0].youtubeid
            song_queue.artist = song.artist
            song_queue.song = song.name
            queue_array.append(song_queue)
        except:
            continue

    return queue_array


def lastfm_search(search_arg, lastfm_pass):

    url = (
        "https://ws.audioscrobbler.com/2.0/?method=track.search&track="
        + search_arg
        + "&api_key="
        + lastfm_pass
        + "&limit=20&format=json"
    )
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return response.status_code
        data = response.json()
        tracks = []
        for results in data["results"]["trackmatches"]["track"]:
            music_data = MusicData()
            music_data.artist = results["artist"]
            music_data.song = results["name"]
            tracks.append(music_data)
    except:
        return None

    return tracks


def musicbrainz_search(search_arg):

    tracks = []
    try:
        result = musicbrainzngs.search_recordings(query=search_arg)
        for record in result["recording-list"]:
            music_data = MusicData()
            music_data.song = record["title"] 
            music_data.artist = record["artist-credit-phrase"]
            tracks.append(music_data)
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
            aux = video_data.replace('{"thumbnails":[{"url":"', "zz_thumbs")
            aux = aux.replace("?sqp", "zz_thumbd")
            thumbnail = re.findall(r"zz_thumbs(.*?)zz_thumbd", aux)[0]
            aux = video_data.replace('"title":{"runs":[{"text":"', "zz_thumbs")
            aux = aux.replace('"}],"accessibility":', "zz_thumbd")
            description = re.findall(r"zz_thumbs(.*?)zz_thumbd", aux)[0]
            youtube_video = YoutubeVideos()
            youtube_video.id = video_id
            youtube_video.thumb = thumbnail
            youtube_video.description = description
            video_list.append(youtube_video)
        except:
            continue

    return video_list


def get_player_data(page_load, current_user, updatedb):

    count = 0
    player_data = PlayerData()
    queue = queue_get(roomid=current_user.roomid)

    if page_load:
        playing = Queue.query.filter_by(roomid=current_user.roomid, status="P").first()
        try:
            if playing.status == "P":
                user = User.query.filter_by(id=playing.userid).first()
                song = Song.query.filter_by(youtubeid=playing.youtubeid).first()
                player_data.singer = user.name
                player_data.song = song.name
                player_data.video_url = (
                    "/static/songs/" + str(playing.youtubeid) + ".mp4"
                )
                count += 1
        except:
            1 == 1
    else:
        if updatedb:
            Queue.query.filter_by(roomid=current_user.roomid, status="P").delete()
            db.session.commit()

    while count < 2:
        try:
            queue_item = queue[0]
            if count == 0:
                player_data.singer = queue_item.singer
                player_data.song = queue_item.song
                player_data.video_url = (
                    "/static/songs/" + str(queue_item.youtubeid) + ".mp4"
                )
                if updatedb:
                    queue_update = Queue.query.filter_by(id=queue_item.id).first()
                    queue_update.status = "P"
                    db.session.add(queue_update)
                    db.session.commit()
            else:
                player_data.next_singer = queue_item.singer
                player_data.next_song = queue_item.song
        except:
            break

        del queue[0]
        count += 1

    return player_data


def get_lastfm_pass():

    config = Config.query.filter_by(id="CONFIG").first()
    if config:
        return str(config.lastfm)
    else:
        return ""


def check_video(youtubeid):

    video_file = APP_PATH + SONGS_DIR + str(youtubeid) + ".mp4"
    if os.path.exists(video_file):
        return True
    else:
        return False
