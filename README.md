# websocket multiuser py4web-chat

1 run the Redis server on a standard port

2 cp wsservers.py to py4web/py4web/utils/

(this file contains the message system (REME) for sending messages between 
the application and the tornado server )

3 cp chat to apps/

4 run server with REME system

./py4web.py run -s tornadoRemeServer apps

firefox localhost:8000/chat

