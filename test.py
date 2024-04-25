from youtubesearchpython import VideosSearch

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
        
def is_karaoke(title):
    
    return ('karaoke' in title.lower() or 'backtracking' in title.lower() or 'instrumental' in title.lower())

        
search_arg = search_arg = 'Iggy Pop & Kate Pierson Candy'

search_term = search_arg.replace('&', ' ')
search_term = search_term.replace('/', ' ')
search_term = search_term.replace('.', ' ')
search_term = search_term + ' karaoke'
videos_search = VideosSearch(search_term, region='BR', language='pt-BR')
video_list = []
count = 0
while count < 20:
    for video in videos_search.resultComponents: 
        try:   
            if video['type'] != 'video':
                continue
            if not is_karaoke(video['title']):
                continue
            youtube_video = YoutubeVideos()
            youtube_video.id = video['id']
            youtube_video.thumb = video['thumbnails'][0]['url'].split("?")[0]
            youtube_video.description = video['title']
            video_list.append(youtube_video)
        except:
            continue
    videos_search.next()
    count += 1
    
breakpoint
