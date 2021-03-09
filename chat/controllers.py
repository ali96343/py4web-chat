from py4web import action, request, abort, redirect, URL
from yatl.helpers import A
from .common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash
import json
import pickle
import os

from py4web import Field, action, request, DAL, Field
from py4web.utils.form import Form
import os

from .remeutils import RemeSms, read_body 

reme = RemeSms()

@unauthenticated("index", "index.html")
@action.uses( reme  )
def index():
    reme.pub_sms (  cmd = 'allow' )
    #user = auth.get_user()
    #message = T("Hello {first_name}".format(**user) if user else "Hello")
    mytable = 'chat_messages'
    q= db[mytable].id >0
    return dict(messages= db(q).select() )

# ----------------------------------------------------------------

@action('ws_open/<path:path>', method=["GET", "POST"])
@action.uses(  reme )
@action.uses(db,)
def ws_open(path=None):
    reme.pub_sms (  cmd = 'allow' )
    #print ('ws_open: ',  path)
    return 'ok'

@action('ws_close/<path:path>', method=["GET", "POST"])
@action.uses(db,)
@action.uses(  reme )
def ws_close(path=None):
    reme.pub_sms (  cmd = 'allow' )
   # print ('ws_close: ',  path)
    return 'ok'

@action('ws_message/<path:path>', method=["GET", "POST"])
@action.uses(db,)
@action.uses(  reme )
def ws_message(path=None):
    reme.pub_sms (  cmd = 'allow' )
    def my_insert(mytable='chat_messages', data_dict={'user':'x0', 'text':'x1'}):
        row_id = db[mytable].insert(**db[mytable]._filter_fields(data_dict))
        db.commit()
        return row_id
    if path == 'mess_in_body':
         user_data = read_body(request)
         #print (user_data)
         if 'user_data' in user_data:
              table_record = json.loads(user_data['user_data'])
              #print ( table_record )
              my_insert( data_dict=table_record   )
    return 'ok'
