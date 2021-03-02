"""
This file defines the database models
"""

from .common import db, Field
from pydal.validators import *

### Define your table below
#
# db.define_table('thing', Field('name'))
#
## always commit your models to avoid problems later
#
# db.commit()
#
if not db(db.auth_user).count():
    u1 = {
        "username": "nil",
        "email": "nil@nil.com",
        "password": str(CRYPT()("xyz12345")[0]),
        "first_name": "MainUser",
        "last_name": "MainUserLast",
    }

    u2 = {
        "username": "anil",
        "email": "anil@nil.com",
        "password": str(CRYPT()("xyz12345")[0]),
        "first_name": "Anil_first",
        "last_name": "Anil_Last",
    }


    for e in [u1, u2]: db.auth_user.insert(**db.auth_user._filter_fields(e) )
    db.commit()

db.define_table(
    'chat_messages',
    Field('user','string', length=1024, ),
    Field('text','string', length=1024, ),
    )
db.commit()

if not db(db.chat_messages).count():
    m1 = {
        "user": "user1",
        "text": "user1-mess",
    }

    m2 = {
        "user": "user2",
        "text": "user2-mess",
    }

    for e in [m1, m2]: db.chat_messages.insert(**db.chat_messages._filter_fields(e) )
    db.commit()

