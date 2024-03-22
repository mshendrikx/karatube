import time
import karatubedef as Kdef
from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_login import LoginManager
from app import views  # Import views

WAIT_VIDEO = "static/videos/karacool_wait.mp4"

app = Flask(__name__)

app.config['SECRET_KEY'] = '35ab4b6fd905da243ba2b43d1830797ff7fbad883254a75e'  # Replace with a strong secret key

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect to login on unauthorized access

@login_manager.user_loader
def load_user(user_id):
  return Kdef.User.get_by_userid(user_id)  # Use User.get_by_email to fetch user

# List of video URLs
video_urls = ["static/songs/" + video for video in 
              ["Bon Jovi - Livin` On A Prayer.mp4", 
              "Pearl Jam - State of Love and Trust.mp4",
              "Chrystian e Ralf - Saudade.mp4"]]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/library")
def library():
    songs_list = Kdef.songs_get()
    song_list = [row.get_display_data() for row in songs_list]
    return render_template("library.html", songs=song_list, alert='', artist='', music='' )
  
@app.route("/queue")
def queue():
    return render_template("queue.html")
  
@app.route("/lastfm")
def lastfm():
  
  if request.args['search_string'] == '':
    alert = 'I'
    return redirect(url_for("library"))
    #return render_template("library.html", alert=alert)
  
  lastfm = Kdef.lastfm_search(request.args['search_string'])
  
  if lastfm == None:
    alert = 'W'
    return redirect(url_for("library"))
  else:
    lastfm_data = [row.get_display_data() for row in lastfm]
    return render_template("lastfm.html", lastfm=lastfm_data)

@app.route("/musicdb")
def musicdb():
  
  if request.args['search_string'] == '':
    alert = 'I'
    return redirect(url_for("library"))
    #return render_template("library.html", alert=alert)
  
  lastfm = Kdef.lastfm_search(request.args['search_string'])
  
  if lastfm == None:
    alert = 'W'
    return redirect(url_for("library"))
  else:
    lastfm_data = [row.get_display_data() for row in lastfm]
    return render_template("musicdb.html", lastfm=lastfm_data)
  
@app.route("/youtube/<artist>/<song>")
def youtube(artist, song):
  
  search_arg = artist + ' ' + song
  youtube_videos = Kdef.youtube_search(search_arg)
  videos = [video.get_display_data() for video in youtube_videos]

  return render_template("youtube.html", videos=videos, artist=artist, song=song)

@app.route("/youtubedl/<artist>/<song>/<id>/<image>/<description>")
def youtubedl(artist, song, id, image, description):
  
  result = False
    
  if Kdef.youtube_download(id):
    if Kdef.db_add_song(id, song, artist, image):
      result = True
    else:
      Kdef.video_delete(id)
  
  if result == True:
    alert = 'S'
  else:
    alert = 'W'
  
  return redirect(url_for("library"))
  
@app.route("/player")
def player():
  next_url = WAIT_VIDEO
  return render_template("player.html", next_video_url=next_url)

@app.route("/next-video")
def get_next_song():
  try:
    next_url = video_urls[0]
    del video_urls[0]
  except:
    next_url = WAIT_VIDEO
  return jsonify({"url": next_url})

if __name__ == "__main__":
  app.run(debug=True, port=7001)
  