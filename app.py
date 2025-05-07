import project
import logging

#from apscheduler.schedulers.background import BackgroundScheduler
from project.models import Song

app = project.create_app()

# Configure logging
logging.basicConfig(filename='/app/logs/karatube.log', level=logging.WARN, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

app.run(host="0.0.0.0", port=7003)
