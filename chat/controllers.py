from py4web import action, request, abort, redirect, URL
from yatl.helpers import A
from .common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash
from .settings import APP_NAME, REME
import json
import pickle
import os

from py4web import Field, action, request, DAL, Field
from py4web.utils.form import Form
import os
from py4web.core import Fixture

import datetime

# https://github.com/selevit/tornado-chat

def get_timestamp():
         ct =  datetime.datetime.now()
         cts = ct.isoformat()
         # ts = ct.timestamp()
         return cts

def sms_example( to='WS', from_= APP_NAME):
         return  {
         "sms": "hello",
         "mess_id": '111', 
         "cmd": "allow",
         "from": from_,
         "user": "user_id",
         "to":  to ,
         'timestamp': get_timestamp()
       }

# REME redis_connection? look to common.py

# --------------------------------- utils ---------------

@action("pub", method=["GET", "POST"])
def pub_sms( reme='WS', cmd ='allow',  ):
    import time

    data = {
        "sms": "hello",
        "mess_id": time.time(),
        "cmd": cmd,
        "from": APP_NAME,
        "user": "user_id",
        "to": reme, 
        'timestamp': time.time() 
    }

    REME.publish(reme, json.dumps(data))
    return 'ok'

def read_body(request):
    if 'wsgi.input' in request:
       post_data = request['wsgi.input'].read()
       if isinstance( post_data, bytes ):
               return  json.loads(post_data)
    return None

#-----------------------------------------------------------

@unauthenticated("index", "index.html")
def index():
    pub_sms()
    mytable = 'chat_messages'
    q= db[mytable].id >0
    return dict(messages= db(q).select() )

def read_reme(key_name):
    global REME
    sms =  REME.get( key_name )  
    try:
       res =  json.loads(sms)
       return  res 
    except:
       print ( 'Not a json format' )
       return sms

# ----------------------------------------------------------------

@action('ws_open/<path:path>', method=["GET", "POST"])
@action.uses(db,)
def ws_open(path=None):
    #print ('got in ws_open: ', path)
    #print ( read_reme(  APP_NAME ) )
    return 'ok'

@action('ws_close/<path:path>', method=["GET", "POST"])
@action.uses(db,)
def ws_close(path=None):
    #print ('got in ws_close: ', path)
    #print ( read_reme(  APP_NAME ) )
    return 'ok'

@action('ws_message/<path:path>', method=["GET", "POST"])
@action.uses(db,)
def ws_message(path=None):
    def my_insert(mytable='chat_messages', data_dict={'user':'x0', 'text':'x1'}):
        row_id = db[mytable].insert(**db[mytable]._filter_fields(data_dict))
        db.commit()
        return row_id
#    print ('got in ws_message: ', path)
#    print ( read_reme(  APP_NAME ) )
    if path == 'mess_in_body':
         user_data = read_body(request)
         if 'user_data' in user_data:
              table_record = json.loads(user_data['user_data'])
              my_insert( data_dict=table_record   )
    return 'ok'



