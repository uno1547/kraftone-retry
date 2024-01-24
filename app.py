from flask import Flask, render_template, jsonify, request
from bson import ObjectId
from flask.json.provider import JSONProvider
import json
import sys
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient('localhost', 27017)
db = client.get_database('retry_db')
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


class CustomJSONProvider(JSONProvider):
    def dumps(self, obj, **kwargs):
        return json.dumps(obj, **kwargs, cls=CustomJSONEncoder)

    def loads(self, s, **kwargs):
        return json.loads(s, **kwargs)
app.json = CustomJSONProvider(app)

@app.route('/')
def home():
  return render_template('index.html')

@app.route('/getdata', methods = ['GET']) 
def get_data():
  sort_mode = request.args.get('sortMode', 'likes') #get 요청의 data 로 넘어온 sortMode : sortMode를 받음, 없다면 기본값 'likes'
  if sort_mode == 'date':
    not_trashed_movies = list(db.movies.find({'trashed' : False}).sort([('open-year', -1), ('open-month', -1), ('opne-month', -1)]))
  else:
    not_trashed_movies = list(db.movies.find({'trashed' : False}).sort({sort_mode : -1}))
  return jsonify({'result' : 'success', 'movies_lists' : not_trashed_movies}) #trashed : False인 리스트를 조건에 맞게 정렬후반환

@app.route('/gettrashdata', methods = ["GET"])
def get_trash_data():
  sort_mode = request.args.get('sortMode', 'likes')
  if sort_mode == 'date':
    trashed_movie = list(db.movies.find({'trashed' : True}).sort([('open-year', -1), ('open-month', -1), ('opne-month', -1)]))
  else:
    trashed_movie = list(db.movies.find({'trashed' : True}).sort({sort_mode : -1}))
  return jsonify({'result' : 'success', 'trashed_lists' : trashed_movie}) #trashed : True인 리스트를 조건에 맞게 정렬후반환

@app.route('/like', methods = ["POST"])
def like_movie():
  like_object_id = ObjectId(request.form['id'])
  like_movie = db.movies.find_one({'_id' : like_object_id}) # button의 post요청으로 넘어온 id값으로 데이터베이스에서 해당영화 조회
  new_likes = like_movie['likes'] + 1 #1추가된 좋아요 개수
  result = db.movies.update_one({'_id' : like_object_id}, {'$set' : {'likes' : new_likes}}) #좋아요 반영 데이터 갱신
  if result.modified_count == 1:
     return jsonify({'result' : 'success'})
  else:
     return jsonify({'result' : 'failure'})

@app.route('/trash', methods = ["POST"])
def trash_movie():
  trash_object_id = ObjectId(request.form['id'])
  db.movies.update_one({'_id' : trash_object_id}, {'$set' : {'trashed' : True}}) #trash를 false에서 true로 변환
  print(db.movies.find_one({'_id' : trash_object_id}))
  return jsonify({'result' : 'success'})

@app.route('/restore', methods = ["POST"])
def restore_movie():
  restore_object_id = ObjectId(request.form['id'])
  db.movies.update_one({'_id' : restore_object_id}, {'$set' : {'trashed' : False}}) #trash를 true에서 false로 변환
  return jsonify({'result' : 'success'})

@app.route('/delete', methods = ["POST"])
def delete_movie():
  delete_object_id = ObjectId(request.form['id'])
  db.movies.delete_one({'_id' : delete_object_id}) #데이터베이스의 컬렉션에서 삭제
  return jsonify({'result' : 'success'})

if __name__ == '__main__':
  app.run(port = 5001, debug = True)