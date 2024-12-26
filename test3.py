import musicbrainzngs

musicbrainzngs.set_useragent(
    "python-musicbrainzngs-example",
    "0.1",
    "https://github.com/alastair/python-musicbrainzngs/",
)

class MusicData:
    artist = ""
    song = ""

    def get_display_data(self):
        return {"artist": self.artist, "song": self.song}
    
search_arg = 'paralamas - alagados'

tracks = []
artists = {}

try:
    result = musicbrainzngs.search_recordings(query=search_arg, limit=100)
    for record in result["recording-list"]:
        score = int(record["ext:score"])
        if score < 50:
            break
        artist = record["artist-credit-phrase"].title()
        if not artist in artists:
            artists[artist] = []
        title = record["title"].title()
        if not title in artists[artist]:
            artists[artist].append(title)
    for artist in artists:
        for song in artists[artist]:
            music_data = MusicData()
            music_data.song = song
            music_data.artist = artist
            tracks.append(music_data)
except:
    1 == 1
