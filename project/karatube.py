import musicbrainzngs
import subprocess
import requests
import os
import smtplib

# import socks
# import socket
# import re

# from fp.fp import FreeProxy
from pytubefix import YouTube, helpers

# from requests.adapters import HTTPAdapter
# from pytube import cipher
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from youtubesearchpython import VideosSearch
from pathlib import Path
from .models import User, Song, Queue, Config
from . import db

APP_PATH = str(Path(__file__).parent.absolute())
YT_BASE_URL = "https://www.youtube.com/watch?v="
SONGS_DIR = "/static/songs/"
THUMBS_DIR = "/static/thumbs/"
TOKEN_DIR = "/token/"

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
    try:
        # proxy_handler = {
        #    "socks5": "89.117.74.15:9050"
        # }
        # helpers.install_proxy(proxy_handler)
        YouTube(download_url).streams.first().download(filename=filename)
        # YouTube(download_url, allow_oauth_cache=True ,use_po_token=True, token_file=token_file).streams.first().download(filename=filename)
        return True
    except Exception as error:
        print(error)
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


def queue_add(roomid, userid, youtubeid, status):

    try:
        new_queue = Queue(
            roomid=roomid,
            userid=userid,
            youtubeid=youtubeid,
            status=status,
            order=999999,
        )
        db.session.add(new_queue)
        db.session.commit()
    except:
        return False

    reorder_array = []
    counter = {}

    queue = Queue.query.filter_by(roomid=roomid).order_by(Queue.order)

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
            [queue_item, status_int, counter[queue_item.userid], queue_item.order]
        )

    reorder_array.sort(key=lambda x: (x[1], x[2], x[3]))

    counter = 1
    for reorder_item in reorder_array:
        queue_item = reorder_item[0]
        queue_item.order = counter
        counter += 1

    db.session.commit()

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
        elif queue_item.status == "D":
            if check_video(youtubeid=queue_item.youtubeid):
                queue_item.status = ""
                song = Song.query.filter_by(youtubeid=queue_item.youtubeid).first()
                song.downloaded = 1
                db.session.commit() 
                status_int = 1
            else:
                status_int = 2
        else:
            status_int = 1

        reorder_array.append(
            [queue_item, status_int, counter[queue_item.userid], queue_item.order]
        )

    reorder_array.sort(key=lambda x: (x[1], x[2], x[3]))

    queue_array = []

    for queue_item in reorder_array:
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


def is_karaoke(title):

    return (
        "karaok" in title.lower()
        or "videok" in title.lower()
        or "backtracking" in title.lower()
        or "instrumental" in title.lower()
    )


def youtube_search(search_arg):

    replaces = ["&", "/", ".", ";", ",", ":", "?"]

    for replace in replaces:
        search_term = search_arg.replace(replace, " ")
    search_term = search_term + " karaoke"
    videos_search = VideosSearch(search_term, region="BR", language="pt")
    video_list = []

    count = 0
    while count < 5:
        for video in videos_search.resultComponents:
            try:
                if video["type"] != "video":
                    continue
                if not is_karaoke(video["title"]):
                    continue
                youtube_video = YoutubeVideos()
                youtube_video.id = video["id"]
                youtube_video.thumb = video["thumbnails"][0]["url"].split("?")[0]
                youtube_video.description = video["title"]
                video_list.append(youtube_video)
            except:
                continue
        videos_search.next()
        count += 1

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


def create_message(
    sender_name, sender_email, recipient, subject, text_content, html_content=None
):
    message = MIMEMultipart("alternative")
    message["From"] = (
        sender_name + " <" + sender_email + ">"
    )  # Set sender name and email
    message["To"] = recipient
    message["Subject"] = subject

    # Add plain text part
    part1 = MIMEText(text_content, "plain")
    message.attach(part1)

    # Add HTML part (optional)
    if html_content:
        part2 = MIMEText(html_content, "html")
        message.attach(part2)

    return message


def send_email(
    sender_name,
    sender_email,
    recipient,
    subject,
    text_content,
    html_content=None,
    smtp_server="localhost",
    smtp_port=25,
):
    message = create_message(
        sender_name, sender_email, recipient, subject, text_content, html_content
    )

    try:
        # Connect to the SMTP server (modify server/port as needed)
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            # Start TLS encryption if required by Postfix configuration
            if server.has_extn("STARTTLS"):
                server.starttls()

            # Authenticate if required (check Postfix configuration)
            if server.has_extn("AUTH"):
                # Replace with your credentials
                server.login("your_username", "your_password")

            server.sendmail(sender_email, recipient, message.as_string())

            return True
    except:
        return False


def recover_email(user, password):

    # Example usage with a custom sender name
    sender_name = "KaraTube"
    sender_email = os.environ["KARATUBE_EMAIL"]
    recipient_email = user.email
    subject = "KaraTube Login"
    text_content = "User: " + str(user.id) + "\n" + "Password: " + str(password)

    return send_email(
        sender_name=sender_name,
        sender_email=sender_email,
        recipient=recipient_email,
        subject=subject,
        text_content=text_content,
        smtp_server=os.environ["SMTP_SERVER"],
        smtp_port=os.environ["SMTP_PORT"],
    )


def update_yt_dlp():
    try:
        subprocess.run(["pip3", "install", "--upgrade", "yt-dlp"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        return False
