from flask_restful import Resource
from flask import request
from google.cloud import firestore, pubsub_v1
from utils import get_hashtags
import json

class Chirp:
    def __init__(self, id, message, timestamp, hashtags = []):
        self.id = id
        self.message = message
        self.timestamp = timestamp
        self.hashtags = get_hashtags(message)

class CleanChirps(Resource):
    
    db = firestore.Client()
    
    def post(self):
        for msg in self.db.collection('messages').stream():
            msg.reference.delete()

        for ht in self.db.collection('hashtags').stream():
            ht.reference.delete()


class AddChirp(Resource):
    
    db = firestore.Client()
    publisher = pubsub_v1.PublisherClient()
    
    def validate_body(self, json_body):
        if 'id' not in json_body or \
            'message' not in json_body or \
            'timestamp' not in json_body:
            return False
        
        if type(json_body['id']) is not str:
            return False
        
        if type(json_body['message']) is not str:
            return False
        
        if type(json_body['timestamp']) is not str:
            return False
        
        return True

    def post(self):
    
        json_body = request.get_json()
        if not self.validate_body(json_body):
            return 'Generic error.', 400
        
        chirp = Chirp(
            id = json_body['id'],
            message = json_body['message'],
            timestamp = json_body['timestamp']
        )

        ref = self.db.collection('messages').document(chirp.id)
        try:
            if ref.get().exists:
                return 'Already exists.', 400
        except:
            return 'Generic error.', 400
        
        ref.set({
            'message': chirp.message,
            'hashtags': chirp.hashtags,
            'timestamp': chirp.timestamp
        })

        # add to hashtags
        for ht in chirp.hashtags:
            try:
                ref = self.db.collection('hashtags').document(ht)
                if ref.get().exists:

                    ref.update({
                        'document_id': firestore.ArrayUnion([chirp.id]),
                        'timestamp': firestore.ArrayUnion([chirp.timestamp])
                    })

                else:
 
                    self.db.collection('hashtags').document(ht).set({
                        'document_id': [chirp.id],
                        'timestamp': [chirp.timestamp]
                    })

                    # create topic
                    path = self.publisher.topic_path('flask-test-sac', ht.split('#')[1])
                    self.publisher.create_topic(request={ "name": path })

            except Exception as e:
                print(e)

            try:
                topic_path = self.publisher.topic_path('flask-test-sac', ht.split('#')[1])
                res = self.publisher.publish(topic_path, json.dumps(chirp.__dict__).encode('utf-8'))
                res.result()
            except Exception as e:
                print(e)

        return chirp.__dict__, 200

class GetChirp(Resource):

    db = firestore.Client()
    
    def get(self, id):    
        if not id:
            return 'Not found', 404
        if type(id) is not str:
            return 'Not found', 404

        try:
            ref = self.db.collection('messages').document(id).get()
        except:
            return 'Not found', 404
        if not ref.exists:
            return 'Not found', 404
        
        chirp = Chirp(
            id = id,
            message = ref.get('message'),
            hashtags = ref.get('hashtags'),
            timestamp = ref.get('timestamp')
        )

        return chirp.__dict__, 200