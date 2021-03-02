# py4web-chat


Howto:

1 run the Redis server on a standard port

2 cp anyservers.py to py4web/py4web/
(this file contains the message system (REME) for sending messages between 
the application and the tornado server )

3 cp chat to apps/

4 run server with REME system
./py4web.py run -s tornadoRemeServer apps

5 firefox localhost:8000/chat

