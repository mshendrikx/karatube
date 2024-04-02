from urllib.request import urlretrieve
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_required, current_user
from pathlib import Path
from . import db

from .models import User, Room, Song, Queue
from .karatube import lastfm_search, youtube_search, youtube_download, video_delete, queue_get, get_player_data

main = Blueprint('main', __name__)

@main.route('/')
def index():
    
    return render_template('index.html', user=current_user)

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', current_user=current_user)

@main.route('/profile', methods=['POST'])
@login_required
def profile_post():
    
    password = request.form.get('password')
    repass = request.form.get('repass')
    roomid = request.form.get('roomid')
    roompass = request.form.get('roompass')
    
    if password != repass:
        flash("Password don't match")
        return redirect(url_for('main.profile'))
    
    if roomid != '':
        room = Room.query.filter_by(roomid=roomid).first()
    
        if not room or not check_password_hash(room.password, roompass):
            flash('Wrong room or room password')
            return redirect(url_for('main.profile'))
    
    if password != '':
        current_user.password = generate_password_hash(password, method='pbkdf2:sha256')
    
    if roomid != current_user.roomid:
        current_user.roomid = roomid
        
    db.session.add(current_user)
    db.session.commit()
    
    return render_template('profile.html', current_user=current_user)

@main.route("/library")
@login_required
def library():
    song_list = Song.query.order_by('artist', 'name') 
    user_sel = []
    user_sel.append(current_user)
    user_list = User.query.filter_by(roomid=current_user.roomid)
    for user in user_list:
        if user.id != current_user.id:
            user_sel.append(user)
            
    return render_template("library.html", songs=song_list, user_sel=user_sel, current_user=current_user)

@main.route("/library", methods=['POST'])
@login_required
def library_post():
      
  search_string = request.form.get('search_string')
  lastfm = lastfm_search(search_string)
  
  if lastfm == None:
    flash("No music found in Last FM database")
    flash("alert-warning")
    return redirect(url_for("library"))
  else:
    lastfm_data = [row.get_display_data() for row in lastfm]
    return render_template("musicdb.html", lastfm=lastfm_data)

@main.route("/youtube/<artist>/<song>")
@login_required
def youtube(artist, song):  
  search_arg = artist + ' ' + song
  youtube_videos = youtube_search(search_arg)
  videos = [video.get_display_data() for video in youtube_videos]

  return render_template("youtube.html", videos=videos, artist=artist, song=song)

@main.route("/youtubedl/<artist>/<song>/<id>/<image>/<description>")
@login_required
def youtubedl(artist, song, id, image, description):
  
  result = False
    
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
      image_url = 'https://i.ytimg.com/vi/' + str(id) + '/' + image
      file_name = str(Path(__file__).parent.absolute()) + '/static/thumbs/' + str(id) + '.jpg'
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
        new_queue = Queue(roomid=current_user.roomid, userid=userid, youtubeid=youtubeid, status='')
        db.session.add(new_queue)
        db.session.commit()
        flash("Song added to queue")
        flash("alert-success")
    except:
        flash("Fail to add song to queue")
        flash("alert-danger")
        
    return redirect(url_for("main.library"))

@main.route("/miniplayer/<youtubeid>")
@login_required
def miniplayer(youtubeid):
    video_url = "/static/songs/" + str(youtubeid) + '.mp4'
       
    return render_template("miniplayer.html", video_url=video_url)

@main.route('/queue')
@login_required
def queue():
    
    queue = queue_get(roomid=current_user.roomid)

    return render_template('queue.html', queue=queue)

@main.route("/player")
@login_required
def player():
    
  player_data = get_player_data(True, current_user)
  
  return render_template("player.html", player_data=player_data)

@main.route("/playerdata")
@login_required
def playerdata():

  player_data = get_player_data(False, current_user)
      
  return jsonify({"url": player_data.video_url,
                  "singer": player_data.singer,
                  "next_singer": player_data.next_singer,
                  "song": player_data.song,
                  "next_song": player_data.next_song
                  })
