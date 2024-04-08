from urllib.request import urlretrieve
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_required, current_user
from pathlib import Path
from . import db

from .models import User, Room, Song, Queue, Roomadm, Config, Controls
from .karatube import (
    lastfm_search,
    get_lastfm_pass,
    youtube_search,
    youtube_download,
    video_delete,
    queue_get,
    check_video,
    musicbrainz_search
)


class PlayerData:
    singer = ""
    song = ""
    next_singer = ""
    next_song = ""
    video_url = ""
    artist = ""
    queueid = ""


main = Blueprint("main", __name__)


@main.route("/")
def index():

    return render_template("index.html", user=current_user)


@main.route("/profile")
@login_required
def profile():
    return render_template("profile.html", current_user=current_user)


@main.route("/profile", methods=["POST"])
@login_required
def profile_post():

    password = request.form.get("password")
    repass = request.form.get("repass")
    roomid = request.form.get("roomid")
    roompass = request.form.get("roompass")

    if password != repass:
        flash("Password don't match")
        flash("alert-danger")
        return redirect(url_for("main.profile"))

    if roomid != "":

        if roomid == current_user.roomid:
            flash("Already logged at room")
            flash("alert-warning")
            return redirect(url_for("main.profile"))

        room = Room.query.filter_by(roomid=roomid).first()

        if not room or not check_password_hash(room.password, roompass):
            flash("Wrong room or room password")
            flash("alert-danger")
            return redirect(url_for("main.profile"))

    if password != "":
        current_user.password = generate_password_hash(password, method="pbkdf2:sha256")

    if roomid != current_user.roomid:
        current_user.roomid = roomid

    Queue.query.filter_by(userid=current_user.id).delete()
    db.session.add(current_user)
    db.session.commit()

    return render_template("profile.html", current_user=current_user)


@main.route("/library")
@login_required
def library():
    song_list = Song.query.order_by("artist", "name")
    user_sel = []
    user_sel.append(current_user)
    user_list = User.query.filter_by(roomid=current_user.roomid)
    for user in user_list:
        if user.id != current_user.id:
            user_sel.append(user)

    return render_template(
        "library.html", songs=song_list, user_sel=user_sel, current_user=current_user
    )


@main.route("/library", methods=["POST"])
@login_required
def library_post():

    search_string = request.form.get("search_string")
    lastfm_pass = get_lastfm_pass()
    if lastfm_pass != '': 
        musics = lastfm_search(search_string, lastfm_pass=lastfm_pass)
    else:
        musics = musicbrainz_search(search_string)

    if musics == None:
        flash("No music found in database")
        flash("alert-warning")
        return redirect(url_for("main.library"))
    else:
        return render_template("musicdb.html", musics=musics)


@main.route("/youtube/<artist>/<song>")
@login_required
def youtube(artist, song):
    search_arg = artist + " " + song
    youtube_videos = youtube_search(search_arg)
    videos = [video.get_display_data() for video in youtube_videos]

    return render_template("youtube.html", videos=videos, artist=artist, song=song)


@main.route("/youtubedl/<artist>/<song>/<id>/<image>/<description>")
@login_required
def youtubedl(artist, song, id, image, description):

    result = False

    song_exists = Song.query.filter_by(youtubeid=id).first()

    if song_exists:
        flash("Youtube video alredy downloaded")
        flash("alert-warning")
    else:
        if youtube_download(id):
            try:
                new_song = Song(youtubeid=id, name=song, artist=artist)
                db.session.add(new_song)
                db.session.commit()
                result = True
            except:
                video_delete(id)
                result = False

        if result == True:
            image_url = "https://i.ytimg.com/vi/" + str(id) + "/" + image
            file_name = (
                str(Path(__file__).parent.absolute())
                + "/static/thumbs/"
                + str(id)
                + ".jpg"
            )
            urlretrieve(image_url, file_name)
            flash("Youtube video downloaded")
            flash("alert-success")
        else:
            flash("Fail to download Youtube video")
            flash("alert-danger")

    return redirect(url_for("main.library"))


@main.route("/addqueue/<youtubeid>/<userid>")
@login_required
def addqueue(youtubeid, userid):
    try:
        queue_check = Queue.query.filter_by(
            userid=current_user.id, youtubeid=youtubeid, roomid=current_user.roomid
        ).first()
        if queue_check:
            flash("Song alredy in queue")
            flash("alert-warning")
        else:
            if check_video(youtubeid=youtubeid):
                new_queue = Queue(
                    roomid=current_user.roomid,
                    userid=userid,
                    youtubeid=youtubeid,
                    status="",
                )
                db.session.add(new_queue)
                db.session.commit()
                flash("Song added to queue")
                flash("alert-success")
            else:
                Song.query.filter_by(youtubeid=youtubeid).delete()
                db.session.commit()
                flash("There is no video file, download again")
                flash("alert-danger")
    except:
        flash("Fail to add song to queue")
        flash("alert-danger")

    return redirect(url_for("main.library"))


@main.route("/delsong/<youtubeid>")
@login_required
def delsong(youtubeid):

    if current_user.admin == "X":
        if video_delete(youtubeid):
            del_song = Song.query.filter_by(youtubeid=youtubeid).delete()
            db.session.commit()
            if del_song:
                Queue.query.filter_by(youtubeid=youtubeid).delete()
                db.session.commit()
                flash("Song deleted")
                flash("alert-success")
        else:
            flash("Song delete fails")
            flash("alert-danger")
    else:
        flash("Only admin can delete song")
        flash("alert-danger")

    return redirect(url_for("main.library"))


@main.route("/miniplayer/<youtubeid>")
@login_required
def miniplayer(youtubeid):
    video_url = "/static/songs/" + str(youtubeid) + ".mp4"

    return render_template("miniplayer.html", video_url=video_url)


@main.route("/queue")
@login_required
def queue():

    queue = queue_get(roomid=current_user.roomid)

    return render_template("queue.html", queue=queue, current_user=current_user)


@main.route("/delqueue/<queueid>")
@login_required
def delqueue(queueid):

    if current_user.roomadm == "X":
        del_queue = Queue.query.filter_by(id=queueid).delete()
        db.session.commit()

        if del_queue:
            flash("Queue deleted")
            flash("alert-success")
        else:
            flash("Fail to delete queue")
            flash("alert-danger")

    else:
        flash("Only room admin can delete queue")
        flash("alert-danger")

    return redirect(url_for("main.queue"))


@main.route("/player")
@login_required
def player():

    config = Config.query.filter_by(id="CONFIG").first()
    return render_template("player.html", player_config=config)


@main.route("/screenupdate")
@login_required
def screenupdate():

    try:
        first = True
        player_data = PlayerData()
        queue = queue_get(roomid=current_user.roomid)
        for queue_item in queue:
            if first:
                player_data.singer = queue_item.singer
                player_data.song = queue_item.song
                player_data.artist = queue_item.artist
                player_data.video_url = (
                    "/static/songs/" + str(queue_item.youtubeid) + ".mp4"
                )
                player_data.queueid = str(queue_item.id)
                if queue_item.status == "":
                    Queue.query.filter_by(id=queue_item.id).update({"status": "P"})
                    db.session.commit()
                first = False
            else:
                player_data.next_singer = queue_item.singer
                player_data.next_song = queue_item.song
                break

    except:
        1 == 1

    control = Controls.query.filter_by(roomid=current_user.roomid).first()
    if control:
        command = control.command
        Controls.query.filter_by(id=control.id).delete()
        db.session.commit()
    else:
        command = ""

    return jsonify(
        {
            "video_url": player_data.video_url,
            "singer": player_data.singer,
            "next_singer": player_data.next_singer,
            "song": player_data.song,
            "next_song": player_data.next_song,
            "artist": player_data.artist,
            "queueid": player_data.queueid,
            "command": command,
        }
    )


@main.route("/queueupdate")
@login_required
def queueupdate():

    Queue.query.filter_by(roomid=current_user.roomid, status="P").delete()
    db.session.commit()

    queue = queue_get(roomid=current_user.roomid)
    try:
        if queue[0]:
            queue_next = Queue.query.filter_by(id=queue[0].id).first()
            queue_next.status = "P"
            db.session.add(queue_next)
            db.session.commit()
    except:
        1 == 1

    return jsonify({})


@main.route("/createroom")
@login_required
def createroom():

    if current_user.admin == "":
        flash("Must be administrator.")
        flash("alert-danger")
        return redirect(url_for("main.index"))

    return render_template("create_room.html", current_user=current_user)


@main.route("/createroom", methods=["POST"])
@login_required
def createroom_post():

    if current_user.admin == "":
        flash("Must be administrator.")
        flash("alert-danger")
        return redirect(url_for("main.index"))

    # login code goes here
    userid = request.form.get("userid")
    roomid = request.form.get("roomid")
    roompass = request.form.get("roompass")

    user = User.query.filter_by(id=userid).first()
    # check if the user actually exists
    # take the user-supplied password, hash it, and compare it to the hashed password in the database
    if not user:
        flash("No user in DB.")
        flash("alert-danger")
        return redirect(
            url_for("main.createroom")
        )  # if the user doesn't exist or password is wrong, reload the page

    room = Room.query.filter_by(roomid=roomid).first()
    # check if the room actually exists
    # take the room-supplied password, hash it, and compare it to the hashed password in the database
    if room:
        flash("Room alredy exists.")
        flash("alert-danger")
        return redirect(
            url_for("main.createroom")
        )  # if the room doesn't exist or password is wrong, reload the page

    try:
        new_room = Room(
            roomid=roomid,
            password=generate_password_hash(roompass, method="pbkdf2:sha256"),
        )
        db.session.add(new_room)
        new_roomadm = Roomadm(roomid=roomid, userid=userid)
        db.session.add(new_roomadm)
        db.session.commit()
        flash("Room created.")
        flash("alert-success")
    except:
        flash("Fail to create Room.")
        flash("alert-danger")

    return redirect(url_for("main.createroom"))


@main.route("/configuration")
@login_required
def configuration():

    if current_user.admin == "":
        flash("Must be administrator.")
        flash("alert-danger")
        return redirect(url_for("main.index"))

    config = Config.query.filter_by(id="CONFIG").first()

    return render_template(
        "configuration.html", current_user=current_user, config=config
    )


@main.route("/configuration", methods=["POST"])
@login_required
def configuration_post():

    if current_user.admin == "":
        flash("Must be administrator.")
        flash("alert-danger")
        return redirect(url_for("main.index"))

    lastfm = request.form.get("lastfm")
    updateratio = request.form.get("updateratio")
    songint = request.form.get("songint")
    config = Config.query.filter_by(id="CONFIG").first()
    config.lastfm = lastfm
    config.updateratio = int(updateratio)
    if config.updateratio == 0:
        config.updateratio = 1
    config.songint = int(songint)
    if config.songint == 0:
        config.songint = 10
    db.session.add(config)
    db.session.commit()

    flash("Configuration updated.")
    flash("alert-success")

    return render_template(
        "configuration.html", current_user=current_user, config=config
    )


@main.route("/setcommand/<command>")
@login_required
def setcommand(command):

    if current_user.roomadm == "X":
        control = Controls(roomid=current_user.roomid, command=command)
        db.session.add(control)
        db.session.commit()

    return redirect(url_for("main.index"))
