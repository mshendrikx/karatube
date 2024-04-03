from flask_login import UserMixin
from . import db

class User(UserMixin, db.Model):
    id = db.Column(db.String(100), primary_key=True)
    name = db.Column(db.String(100))
    roomid = db.Column(db.String(100))
    password = db.Column(db.String(1000))
    roomadm = db.Column(db.String(1))
    admin = db.Column(db.String(1))
    
class Song(db.Model):
    youtubeid = db.Column(db.String(100), primary_key=True)
    name = db.Column(db.String(100))
    artist = db.Column(db.String(100))
    
class Room(db.Model):
    roomid = db.Column(db.String(100), primary_key=True)
    password = db.Column(db.String(1000))
    
class Queue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    roomid = db.Column(db.String(100))
    userid = db.Column(db.String(100))
    youtubeid = db.Column(db.String(100))
    status = db.Column(db.String(1))

class Roomadm(db.Model):
    roomid = db.Column(db.String(100), primary_key=True)
    userid = db.Column(db.String(100), primary_key=True)
    
class Config(db.Model):
    id = db.Column(db.String(6), primary_key=True)
    lastfm = db.Column(db.String(100))