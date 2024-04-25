import urllib.request

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

url = 'https://www.youtube.com.br/results?search_query=' + search_term

url = url.replace(' ', '+')

result = urllib.request.urlopen(url)

result = result.read().decode()

breakpoint