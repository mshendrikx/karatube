import karatubedef as Kdef

file = Kdef.APP_PATH + '/passwords.txt'
with open(file, "r") as file:
  for line in file:
      line_data = line.split('=')
      line_data[1] = line_data[1].replace('\n', '')
      if line_data[0] == 'lastfm':
          Kdef.LASTFM_PASS = line_data[1]
      if line_data[0] == 'mariadb':
          Kdef.DB_PASS = line_data[1]
    
#Kdef.youtube_download('7p2O3JPU5mA')
#conn = Kdef.db_connect()
#result = Kdef.db_add_song('7p2O3JPU5mA', 'Black', 'Pearl Jam', 'CC Karaoke')
#result = Kdef.queue_add_song('regina', 'gabriel', '7p2O3JPU5mA')
#result = Kdef.queue_get('regina', ' ')
result = Kdef.lastfm_search('Forever Young')

breakpoint

