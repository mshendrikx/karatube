
from urllib.request import urlretrieve
from pathlib import Path

image_url = 'https://i.ytimg.com/vi/GPcc3VziWeM/hqdefault.jpg?sqp=-oaymwEbCKgBEF5IVfKriqkDDggBFQAAiEIYAXABwAEG&rs=AOn4CLCQ3hCAZwSOw3B3HYqFcKCaWDx9yg'
file_name = str(Path(__file__).parent.absolute()) + '/project/static/thumbs/test.jpg'
urlretrieve(image_url, file_name)