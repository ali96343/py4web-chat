from py4web.core import Fixture
import threading
import redis
import time
import json
from .settings import APP_NAME

class RemeSms(Fixture):
    reconnect_on_request = True
    def __init__( self, wsgi_name=APP_NAME, host = None, port =None):
        self.wsgi_name = wsgi_name
        self.local = threading.local()
        self.local.r = redis.Redis(host=host or 'localhost', port = port or '6379' )
        self.local.changed = False
        self.local.data = {} 
        self.local.data['sms']= {} 
        try:
            self.local.r.ping()
            test_data = {   f'{wsgi_name}': 'started' } 
            test_data = json.dumps( test_data  )
            self.local.r.set(wsgi_name,  test_data )
        except:
            print ('run redis, pls!')

    def pub_sms(self, reme='WS', cmd ='allow', uname = 'user_id'  ):
    
        data = {
            "sms": "hello",
            "mess_id": time.time(),
            "cmd": cmd,
            "from": self.wsgi_name,
            "user": uname,
            "to": reme,
            'timestamp': time.time()
        }
        self.local.r.publish(reme, json.dumps(data))

    def get_sms(self, ):
        sms = self.local.r.get( self.wsgi_name )
        try:
           self.local.data['sms'] = json.loads(sms)
        except:
           print ( 'Not a json format' )
    
    def get_data(self):
        return getattr(self.local, "data", {})

    def get(self, key, default=None):
        return self.get_data().get(key, default)

    def __getitem__(self, key):
        return self.get_data()[key]

    def __delitem__(self, key):
        if key in self.get_data():
            self.local.changed = True
            del self.local.data[key]

    def __setitem__(self, key, value):
        self.local.changed = True
        self.local.data[key] = value

    def keys(self):
        return self.get_data().keys()

    def __iter__(self):
        for item in self.get_data().items():
            yield item

    def on_request(self):
        try:
            self.local.data['sms'] = json.loads(  self.local.r.get( self.wsgi_name ) )
        except:
            print ('bad data format in sms!')

def read_body(request):
    if 'wsgi.input' in request:
       post_data = request['wsgi.input'].read()
       if isinstance( post_data, bytes ):
               return  json.loads(post_data)
    return None

