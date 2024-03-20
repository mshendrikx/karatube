import time
import karatubedef as Kdef
from flask import Flask, render_template, jsonify, request

WAIT_VIDEO = "static/videos/karacool_wait.mp4"

app = Flask(__name__)

# List of video URLs
video_urls = ["static/songs/" + video for video in 
              ["Bon Jovi - Livin` On A Prayer.mp4", 
              "Pearl Jam - State of Love and Trust.mp4",
              "Chrystian e Ralf - Saudade.mp4"]]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/browse")
def browse():
    return render_template("browse.html")
  
@app.route("/queue")
def queue():
    return render_template("queue.html")
  
@app.route("/search")
def search():
    return render_template("search.html")
  
@app.route("/lastfm")
def lastfm():
  
  lastfm = Kdef.lastfm_search(request.args['search_string'])

  return render_template("lastfm.html")
  
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