import time
import karatubedef as Kdef
from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user


WAIT_VIDEO = "static/videos/karacool_wait.mp4"

app = Flask(__name__)

app.config['SECRET_KEY'] = '8635aa5d7d90eac37bf2bf58481ed20e5964b88cd1a6d741'

# List of video URLs
video_urls = ["static/songs/" + video for video in 
              ["Bon Jovi - Livin` On A Prayer.mp4", 
              "Pearl Jam - State of Love and Trust.mp4",
              "Chrystian e Ralf - Saudade.mp4"]]


# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User model class
class User(UserMixin):

    def __init__(self, userid, name, roomid, password, admin, lastlogin):
        self.userid = userid
        self.name = name
        self.roomid = roomid
        self.password = password
        self.admin = admin
        self.lastlogin = lastlogin

# Load user from database (replace with your logic)
def load_user(user_id):  
    try:
      conn = Kdef.db_connect()
      cursor = conn.cursor(buffered=True)
      sql = 'SELECT * FROM users WHERE userid = %s;'
      values = (user_id, )
      cursor.execute(sql, values)
      for user_db in cursor.fetchall():
        return User(user_db[0], user_db[1], user_db[2], user_db[3], user_db[4], user_db[5])
    except:
      return None
    
    return None
  
# Used by Flask-Login to load user
@login_manager.user_loader
def load_user_by_id(user_id):
    return load_user(user_id)
  
# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = load_user(username) 
        if user == None or user.password != password:
          return 'Invalid username/password'
        login_user(user)
        return redirect(url_for('home'))
    return render_template('login.html')  

@app.route("/home")
@login_required
def home():
    return render_template("home.html")

@app.route("/library")
@login_required
def library():
    songs_list = Kdef.songs_get()
    song_list = [row.get_display_data() for row in songs_list]
    return render_template("library.html", songs=song_list, alert='', artist='', music='' )
  
@app.route("/queue")
def queue():
    return render_template("queue.html")
  
@app.route("/lastfm")
@login_required
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
@login_required
def musicdb():
  
  if request.args['search_string'] == '':
    alert = 'I'
    return redirect(url_for("library"))
  
  lastfm = Kdef.lastfm_search(request.args['search_string'])
  
  if lastfm == None:
    alert = 'W'
    return redirect(url_for("library"))
  else:
    lastfm_data = [row.get_display_data() for row in lastfm]
    return render_template("musicdb.html", lastfm=lastfm_data)
  
@app.route("/youtube/<artist>/<song>")
@login_required
def youtube(artist, song):
  
  search_arg = artist + ' ' + song
  youtube_videos = Kdef.youtube_search(search_arg)
  videos = [video.get_display_data() for video in youtube_videos]

  return render_template("youtube.html", videos=videos, artist=artist, song=song)

@app.route("/youtubedl/<artist>/<song>/<id>/<image>/<description>")
@login_required
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
@login_required
def player():
  next_url = WAIT_VIDEO
  return render_template("player.html", next_video_url=next_url)

@app.route("/next-video")
@login_required
def get_next_song():
  try:
    next_url = video_urls[0]
    del video_urls[0]
  except:
    next_url = WAIT_VIDEO
  return jsonify({"url": next_url})

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))
  
if __name__ == "__main__":
  app.run(debug=True, port=7001)
  