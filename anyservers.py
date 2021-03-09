import logging
from bottle import ServerAdapter

import socketio  # pip install python-socketio

siows_debug = True
# reme_debug = True

# REME - py4web redis-message system
# ab96343@gmail.com
# version 090321.01

# idea from
# https://stackoverflow.com/questions/15144809/how-can-i-use-tornado-and-redis-asynchronously/15161744
#

anyservers_list = ["tornadoRemeServer"]

import threading
import redis
import json
import pickle

# import tornado.web
import tornado
import datetime
import time


async def start_siows(*args):
    import tornado
    def nil_handler(): pass
    for e in ['WS', ]:
       chan_url = f'http://{args[0][0]}:{args[0][1]}/channel/{e}'
       await tornado.httpclient.AsyncHTTPClient().fetch(chan_url, nil_handler)


class OpenChannel(threading.Thread):
    def __init__(self, channel, host=None, port=None):
        threading.Thread.__init__(self)
        self.daemon = True
        self.lock = threading.Lock()
        self.channel = channel
        self.threading_run = True
        self.redis_pool = redis.ConnectionPool(
            host=host or "localhost", port=port or 6379, db=0
        )
        self.redis = redis.Redis(connection_pool=self.redis_pool)
        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe(channel)
        self.output = []

    def __getitem__(self, item):
        with self.lock:
            return self.output[item]

    def __getslice__(self, start, stop=None, step=None):
        with self.lock:
            return self.output[start:stop:step]

    def __str__(self):
        with self.lock:
            return self.output.__str__()

    # thread loop
    def run(self):
        output_list_limit = 10
        for message in self.pubsub.listen():
            with self.lock:
                if len(self.output) > output_list_limit:
                    self.output.pop(0)
                    print("output_list_limit!!!")
                if self.threading_run == False:
                    break
                self.output.append(message["data"])

    def stop(self):
        self.threading_run = False
        self.pubsub.unsubscribe(self.channel)


# add a method to the application that will return existing channels
# or create non-existing ones and then return them
class ApplicationMixin:  # (object):
    def GetChannel(self, channel, host=None, port=None):
        num_channels_limit = 2  # need Handler for new channels
        if len(self.application.channels) > num_channels_limit:
            print("reme: channels num limitted")
        if channel not in self.application.channels:
            self.application.channels[channel] = OpenChannel(channel, host, port)
            self.application.channels[channel].start()
        return self.application.channels[channel]

    def handle_request(self, response):
        pass

    def sms_example(self, to="myapp", from_="WS"):
        return {
            "sms": "hello",
            "mess_id": time.time(),
            "cmd": "allow",
            "from": from_,
            "user": "user_id",
            "to": to,
            "timestamp": time.time(),
        }

    def get_sms_keys(self,):
        sms = self.sms_example()
        return sms.keys()

    def ToReme(self, key, value, host=None, port=None):
        if self.application.settings.get("REME") == None:
            # self.application.settings['REME'] = redis.Redis(host = 'localhost', port = 6379)
            self.redis_pool = redis.ConnectionPool(
                host=host or "localhost", port=port or 6379, db=0
            )
            self.application.settings["REME"] = redis.Redis(
                connection_pool=self.redis_pool
            )
            self.application.settings["REME"].ping()
            try:
                response = self.application.settings["REME"].client_list()
            except redis.ConnectionError:
                print("redis connection  error")
        self.application.settings["REME"].set(key, value)

    def PubSms(self, wsgi_app, sms={}, fjson=True):
        if len(sms) == 0:
            sms = self.sms_example(wsgi_app)
        body = json.dumps(sms) if fjson else pickle.dumps(sms)
        self.ToReme(wsgi_app, body)

    def WsgiREST(self, app_name="remetest", cmd="GET", data={}):
        # wsgi_rest = f'{self.request.protocol}://{self.request.host}/{app_name}/{ctrl}/{mess}'
        pass

    def WsgiGet(self, app_name="remetest", ctrl="index", mess="empty_mess"):
        wsgi_url = (
            f"{self.request.protocol}://{self.request.host}/{app_name}/{ctrl}/{mess}"
        )
        tornado.httpclient.AsyncHTTPClient().fetch(wsgi_url, self.handle_request)

    def WsgiPost(
        self, app_name="remetest", ctrl="index", mess="in_body_mess", data={"to": "app"}
    ):
        wsgi_url = (
            f"{self.request.protocol}://{self.request.host}/{app_name}/{ctrl}/{mess}"
        )
        body = json.dumps(data)
        request = tornado.httpclient.HTTPRequest(wsgi_url, method="POST", body=body)
        tornado.httpclient.AsyncHTTPClient().fetch(request, self.handle_request)

    def CallWsgi(self, app_name="remetest", ctrl="index", data={}):
        if app_name is None:
            print ('CallWsgi: app_name is None! ', app_name)
            return
        #print( 'app_name   ',app_name  )
        self.PubSms(app_name)
        if len(data) == 0:
            self.WsgiGet(app_name=app_name, ctrl=ctrl, mess="empty_mess")
        elif isinstance(data, str):
            self.WsgiGet(app_name=app_name, ctrl=ctrl, mess=data)
        else:
            self.WsgiPost(app_name, ctrl, mess="mess_in_body", data=data)


class ReadChannel(tornado.web.RequestHandler, ApplicationMixin):
    async def get(self, channel):
        # get the channel
        channel = self.GetChannel(channel)
        # write out its entire contents as a list
        # self.write('{}'.format(channel[:]))
        self.write("{}".format(len(channel[:])))


class FaviconHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("its my ico and robots")


def tornadoRemeServer():
    class WsHandler(tornado.websocket.WebSocketHandler, ApplicationMixin):
        def initialize(self,):
            if not "WS" in self.application.channels:
                self.GetChannel("WS")
                print ('up WS')
            self.app_name = None

        def simple_init(self):
            self.stop = False
            if not "WS" in self.application.channels:
                print("error:  where WS?!")
                self.stop = True
                return
            for message in self.application.channels["WS"].output[::-1]:
                if isinstance(message, bytes):
                    self.data = json.loads(message)
                    if all([k in self.data for k in self.get_sms_keys()]):
                        self.app_name = self.data["from"]
                        #print("++++   ", self.app_name)
                        if self.data["cmd"] != "allow":
                            print(self.data["cmd"])
                            self.close()
                    else:
                        print("bad sms format!")
                        self.stop = True
                    break
            if self.app_name is None:
                self.stop = True
            #print("!!! ", self.app_name)

        def open(self):
            self.simple_init()
            self.application.WsPool.add(self)
            self.CallWsgi( app_name = self.app_name, ctrl = 'ws_open', )

        def on_message(self, message):
            # if any( [self.stop is True, not self in self.application.WsPool , not message, len(message) > 1000 ]):
            #   return
            if self.app_name is None:
                print("self.app_name is None")
                return
            for value in self.application.WsPool:
                if value != self:
                    value.ws_connection.write_message(message)

            self.CallWsgi(
                app_name=self.app_name, ctrl="ws_message", data={"user_data": message}
            )

        def on_close(self):
            self.application.WsPool.discard(self)
            self.stop = True
            self.CallWsgi( app_name = self.app_name, ctrl = 'ws_close', )

        #crossdomain connections allowed
        def check_origin(self, origin):
             return True


    # ---------------------------------------------------------------------------------------------------
    sio = socketio.AsyncServer(
        async_mode="tornado"
    )  # logger=True, engineio_logger=True)

    class SioHandler(socketio.AsyncNamespace):
        def on_connect(self, sid, environ):
            print(self.__dict__)
            siows_debug and print("sio: connect ", sid)
            print("connect!")
            pass

        def on_disconnect(self, sid):
            print("disconnect!")
            pass

        async def on_to_py4web(self, sid, data):
            print("sio: from client: ", data)
            siows_debug and print("sio: from client: ", data)
            await sio.emit("py4web_echo", data)

    # ---------------------------------------------------------------------------------------------------
    class TornadoRemeServer(ServerAdapter):
        def run(self, handler):  # pragma: no cover
            # if siows_debug: self.quiet = True
            self.quit = False
            if not self.quiet:
                log = logging.getLogger("tornadoReme")
                log.setLevel(logging.ERROR)
                log.addHandler(logging.StreamHandler())

            import tornado.wsgi, tornado.httpserver, tornado.web, tornado.ioloop

            tornado.ioloop.IOLoop.configure("tornado.platform.asyncio.AsyncIOLoop")
            container = tornado.wsgi.WSGIContainer(handler)

            sio.register_namespace(SioHandler(namespace="/"))
            app = tornado.web.Application(
                [
                    (r"/favicon.ico|/robots.txt", FaviconHandler),
                    (r"/channel/(?P<channel>\S+)", ReadChannel),
                    (r"/websocket/?", WsHandler),
                    (r"/socket.io/", socketio.get_tornado_handler(sio)),
                    (r".*", tornado.web.FallbackHandler, dict(fallback=container)),
                ],
                REME=None,
                debug=True,
                autoreload=False,
            )
            app.channels = {}
            app.WsPool = set()
            app.SioPool = set()  # []
            server = tornado.httpserver.HTTPServer(app)
            server.listen(port=self.port, address=self.host)
            loop = tornado.ioloop.IOLoop.current()

            loop.add_timeout(datetime.timedelta(seconds=2), start_siows,  [ self.host, self.port  ])

            try:
                loop.start()
            finally:
                for channel in app.channels:
                    app.channels[channel].stop()
                    app.channels[channel].join()

    return TornadoRemeServer


# https://stackoverflow.com/questions/4043129/giving-my-python-application-a-web-interface-to-monitor-it-using-tornado

# import threading
# t = threading.Thread(target = tornado.ioloop.IOLoop.instance().start)
# t.start()

# https://code-live.ru/post/chat-with-tornado-backbone-and-websockets/
