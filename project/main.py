from urllib.request import urlretrieve
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_required, current_user
from pathlib import Path
from . import db

from .models import User, Room, Song, Queue, Roomadm
from .karatube import lastfm_search, youtube_search, youtube_download, video_delete, queue_get, get_player_data

class PlayerData:
    singer = ''
    song = ''
    next_singer = ''
    next_song = ''
    video_url = ''    
    
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
        flash("alert-danger")
        return redirect(url_for('main.profile'))
    
    if roomid != '':

        if roomid == current_user.roomid:
            flash("Already logged at room")
            flash("alert-warning")
            return redirect(url_for('main.profile'))

        room = Room.query.filter_by(roomid=roomid).first()
    
        if not room or not check_password_hash(room.password, roompass):
            flash('Wrong room or room password')
            flash("alert-danger")
            return redirect(url_for('main.profile'))
    
    if password != '':
        current_user.password = generate_password_hash(password, method='pbkdf2:sha256')
    
    if roomid != current_user.roomid:
        current_user.roomid = roomid
        
    Queue.query.filter_by(userid=current_user.id).delete()
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
        queue_check = Queue.query.filter_by(userid=current_user.id, youtubeid=youtubeid, roomid=current_user.roomid).first()
        if queue_check:
            flash("Song alredy in queue")
            flash("alert-warning")            
        else:
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

  return render_template("player.html")

@main.route("/screenupdate")
@login_required
def screenupdate():

  player_data = PlayerData()
  queue_play = Queue.query.filter_by(roomid=current_user.roomid, status='P').first()
  queue = queue_get(roomid=current_user.roomid)
 
  try:
    if queue_play.status == 'P':
        user = User.query.filter_by(id=queue_play.userid).first()
        song = Song.query.filter_by(youtubeid=queue_play.youtubeid).first()
        player_data.singer = user.name
        player_data.song = song.name
        player_data.video_url = '/static/songs/' + str(queue_play.youtubeid) + '.mp4'
        
        for queue_next in queue:
            player_data.next_singer = queue_next.singer
            player_data.next_song = queue_next.song
            break
        
  except:
      player_data = PlayerData()
      for queue_next in queue:
          queue_update = Queue.query.filter_by(id=queue_next.id).first()
          if queue_update:
            queue_update.status = 'P'
            db.session.add(queue_update)
            db.session.commit()    
      
  return jsonify({"video_url": player_data.video_url,
                  "singer": player_data.singer,
                  "next_singer": player_data.next_singer,
                  "song": player_data.song,
                  "next_song": player_data.next_song
                  })

@main.route("/queueupdate")
@login_required
def queueupdate():
    
  Queue.query.filter_by(roomid=current_user.roomid, status='P').delete()
  db.session.commit() 
  
  queue = queue_get(roomid=current_user.roomid)
  try: 
    if queue[0]:
        queue_next = Queue.query.filter_by(id=queue[0].id).first()
        queue_next.status = 'P'
        db.session.add(queue_next)
        db.session.commit()  
  except:
      1 == 1
      
  return jsonify({})

@main.route('/createroom')
@login_required
def createroom():
    return render_template('create_room.html', current_user=current_user)

@main.route('/createroom', methods=['POST'])
@login_required
def createroom_post():
    
    # login code goes here
    userid = request.form.get('userid')
    roomid = request.form.get('roomid')
    roompass = request.form.get('roompass')

    user = User.query.filter_by(id=userid).first()
    # check if the user actually exists
    # take the user-supplied password, hash it, and compare it to the hashed password in the database
    if not user:
        flash('No user in DB.')
        flash("alert-danger")
        return redirect(url_for('main.createroom')) # if the user doesn't exist or password is wrong, reload the page

    room = Room.query.filter_by(roomid=roomid).first()
    # check if the room actually exists
    # take the room-supplied password, hash it, and compare it to the hashed password in the database
    if room:
        flash('Room alredy exists.')
        flash("alert-danger")
        return redirect(url_for('main.createroom')) # if the room doesn't exist or password is wrong, reload the page
    
    try:
        new_room = Room(roomid=roomid, password=generate_password_hash(roompass, method='pbkdf2:sha256'))
        db.session.add(new_room)
        new_roomadm = Roomadm(roomid=roomid, userid=userid)
        db.session.add(new_roomadm)
        db.session.commit()
        flash('Room created.')
        flash("alert-success")
    except:
        flash('Fail to create Room.')
        flash("alert-danger")
        
    return redirect(url_for('main.createroom'))
