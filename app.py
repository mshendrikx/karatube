from flask import Flask, render_template, jsonify
import time

WAIT_VIDEO = "static/videos/karacool_wait.mp4"

app = Flask(__name__)

# List of video URLs
video_urls = ["static/songs/" + video for video in 
              ["Bon Jovi - Livin` On A Prayer.mp4", 
              "Pearl Jam - State of Love and Trust.mp4",
              "Chrystian e Ralf - Saudade.mp4"]]

@app.route("/")
def index():
    return render_template(
        "home.html",
        site_title='KaraTube',
        title="Home",
        transpose_value='',
        admin=True
    )

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