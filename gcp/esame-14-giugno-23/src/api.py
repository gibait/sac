from flask_restful import Resource
from flask import request
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
import ipaddress
import json

collections = ['rules'] # List of collections to be created

def validate_id(id):
    if not id:
            return None, 404
    try:
        id = int(id)
    except:
        return None, 400
    
    if id < 0:
        return None, 400
    
    return True

class Generic(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def validate_nm_ip(self):
        try:
            ipaddress.ip_address(self.ip)
            ipaddress.ip_network(f'{self.ip}/{self.netmaskCIDR}')
            ipaddress.ip_address(self.gw)
        except:
            return False
        return True

    def validate_body(self, json_body):
        for k, v in self.__dict__.items():
            if k not in json_body:
                return False
            if k == 'ip' and type(v) is not str:
                return False
            if k == 'netmaskCIDR' and type(v) is not int:
                return False
            if k == 'gw' and type(v) is not str:
                return False
            if k == 'device' and type(v) is not str:
                return False
        
        return self.validate_nm_ip()

class CleanGeneric(Resource):
    
    db = firestore.Client()
    
    def post(self):
        for coll in collections:
            for doc in self.db.collection(coll).stream():
                doc.reference.delete()

        return None, 200

class HandleRules(Resource):
    
    db = firestore.Client()
    
    def post(self, id: int):
    
        if (res := validate_id(id)) is not True:
            return res

        json_body = request.get_json()
        obj = Generic(**json_body)

        if not obj.validate_body(json_body):
            return None, 400

        ref = self.db.collection('rules').document(id)
        try:
            if ref.get().exists:
                return None, 409
        except:
            return None, 400
        
        ref.set(obj.__dict__)
        return obj.__dict__, 201
    
    def get(self, id: int):

        if (res := validate_id(id)) is not True:
            return res

        try:
            ref = self.db.collection('rules').document(id).get()
        except:
            return None, 404
        if not ref.exists:
            return None, 404

        obj = Generic(**ref.to_dict())
        return obj.__dict__, 200 

    def put(self, id: int):

        if (res := validate_id(id)) is not True:
            return res

        try:
            ref = self.db.collection('rules').document(id).get()
        except:
            return None, 400
        if not ref.exists:
            return None, 404

        obj = Generic(**ref.to_dict())
        update = dict(request.get_json())
        for k, v in update.items():
            if hasattr(obj, k):
                setattr(obj, k, v)

        if not obj.validate_nm_ip():
            return None, 400

        self.db.collection('rules').document(id).update(obj.__dict__)
        return obj.__dict__, 200   
    
    def delete(self, id: int):

        if (res := validate_id(id)) is not True:
            return res

        try:
            ref = self.db.collection('rules').document(id).get()
        except:
            return 'Not found', 404
        if not ref.exists:
            return 'Not found', 404

        self.db.collection('rules').document(id).delete()
        return 'Deleted', 204

class ListRules(Resource):

    db = firestore.Client()

    def get(self):
        rules = []
        for doc in self.db.collection('rules').order_by('netmaskCIDR', direction=firestore.Query.DESCENDING).stream():
            rules.append(doc.id)
        return rules, 200
    
    def post(self):
        rules = []

        ip = request.get_json().strip('"')
        
        if not ipaddress.ip_address(ip):
            return None, 400

        # scansione lineare 🤮
        ref = self.db.collection('rules').order_by('netmaskCIDR', direction=firestore.Query.DESCENDING).stream()
        for doc in ref:
            obj = Generic(**doc.to_dict())
            if ipaddress.ip_address(ip) in ipaddress.ip_network(f'{obj.ip}/{obj.netmaskCIDR}'):
                return json.dumps(doc.id), 200