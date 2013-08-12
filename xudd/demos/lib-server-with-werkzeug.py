from xudd.lib.server import Server
from xudd.lib.http import HTTP
from xudd.lib.wsgi import WSGI
from xudd.hive import Hive

from werkzeug.wrappers import Request, Response

import logging

def wsgi_app(environ, start_response):
    request = Request(environ)
    response = Response('Hello {0}'.format(request.args.get('name', 'World!')))
    return response(environ, start_response)

def serve():
    logging.basicConfig(level=logging.DEBUG)

    logging.getLogger('xudd.hive').setLevel(logging.INFO)
    logging.getLogger('xudd.actor').setLevel(logging.INFO)


    hive = Hive()

    wsgi_id = hive.create_actor(WSGI, app=wsgi_app)
    http_id = hive.create_actor(HTTP, request_handler=wsgi_id)
    server_id = hive.create_actor(Server, request_handler=http_id)

    hive.send_message(
        to=server_id,
        directive='listen')

    hive.run()


if __name__ == '__main__':
    serve()
