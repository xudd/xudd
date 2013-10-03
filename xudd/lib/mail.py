import logging
import re
import platform

from xudd import PY2
from xudd.actor import Actor
from xudd.lib.tcp import Client



if PY2:
    EOL = '\r\n'
else:
    EOL = b'\r\n'

_log = logging.getLogger(__name__)

class SMTPClient(Actor):
    """SMTP client

    This is where I explain why I wrote this client this way and how to extend
    it! Also, go into depth on the subject of those barking dogs at the
    beginning of the book. (You'd forgotten about those, hadn't you?)
    """
    def __init__(self, hive, id, encoding='utf8'):
        super(SMTPClient, self).__init__(hive, id)

        self.encoding = encoding
        self.incoming = ''
        self.mail_from = None
        self.rcpt_to = None
        self.email = None
        self.rcpt_err = []

        self.connection = hive.create_actor(Client, chunk_handler=self.id)
        self.message_routing.update({
            'handle_chunk': self.noop,
            'connect': self.connect,
            'setup': self.setup,
            'quit': self.quit,
            
        })

    def noop(self, message):
        """NOOP!

        Ze noop, it does nothing!

        Excepts to be called from a xudd.lib.tcp.Client
        """
        self.handle_chunk(message)

    def setup(self, message):
        """Set various variables

        Takes a dict with none or more of the follow keys:
        - *mail_from*: string given to the MAIL FROM command
        - *rcpt_to*: list of strings to be given to successive RCPT TOs
        - *email*: string that is the actually email you want to send

        Send this message as many times as desired

        *email* should already be SMTP safe. So make sure there's no
        <CR><LF>.<CR><LF>s in your message!
        """
        self.mail_from = message.body.get('mail_from', self.mail_from)
        self.rcpt_to = message.body.get('rcpt_to', self.rcpt_to)
        self.email = message.body.get('email', self.email)

    def connect(self, message):
        """Connect to a server

        - *host*: domain name or ip to connect to
        - *port*: port number (default: 25)
        - *helo_name*: name to give the SMTP server on HELO (default: hostname)

        TODO: delayed reply to the actor that sent the message
        """
        self.helo_name = message.body.get('helo_name', platform.node())

        self.message_routing.update({'handle_chunk': self.greeting})
        self.send_message(
            to=self.connection,
            directive='connect',
            body={'host': message.body['host'], 'port': message.body.get('port', 25)}
        )

    def greeting(self, message):
        """Greet the server

        Excepts to be called from a xudd.lib.tcp.Client
        """
        try:
             numeric, msg = self.handle_chunk(message)
        except TypeError:
            # We haven't reached EOL yet
            return

        if numeric != 220:
            _log.error("Didn't get 220 from server on connection")
            self.quit()
            return

        self.message_routing.update({'handle_chunk': self.mail})
        self.send_message(
            to=self.connection,
            directive='send',
            body={'message': "HELO %s%s" % (self.helo_name, EOL)}
        )

    def mail(self, message):
        """Tell the server who we are

        Excepts to be called from a xudd.lib.tcp.Client
        """
        try:
             numeric, msg = self.handle_chunk(message)
        except TypeError:
            # We haven't reached EOL yet
            return

        if numeric != 250:
            _log.error("Aborting before MAIL command")
            self.quit()
            return
        self.message_routing.update({'handle_chunk': self.rcpt})
        self.send_message(
            to=self.connection,
            directive='send',
            body={'message': "MAIL FROM:%s%s" % (self.mail_from, EOL)}
        )

    def rcpt(self, message):
        """Tell the server who the message is for

        Excepts to be called from a xudd.lib.tcp.Client
        """
        try:
             numeric, msg = self.handle_chunk(message)
        except TypeError:
            # We haven't reached EOL yet
            return

        # Is this a reply from a MAIL FROM or a RCPT TO?
        if self.mail_from:
            if numeric != 250:
                _log.error("Aborting before first RCPT command")
                self.quit()
                return
            else:
                self.mail_from = None
        else:
            # Take note of any errors
            if numeric == 250:
                self.rcpt_err.append(None)
            else:
                self.rcpt_err.append([numeric, msg])

        try:
            rcpt = self.rcpt_to.pop()
        except IndexError:
            # We'll send the DATA command here - we wanted to catch RCPT errors first
            _log.debug(str(self.rcpt_err))
            self.message_routing.update({'handle_chunk': self.data})
            self.send_message(
                to=self.connection,
                directive='send',
                body={'message': 'DATA' + EOL}
            )
            return
        
        self.send_message(
            to=self.connection,
            directive='send',
            body={'message': "RCPT TO:%s%s" % (rcpt,EOL)}
        )

    def data(self, message):
        """Send the actual email

        Excepts to be called from a xudd.lib.tcp.Client
        """
        try:
             numeric, msg = self.handle_chunk(message)
        except TypeError:
            # We haven't reached EOL yet
            return

        if numeric != 354:
            _log.error("Aborting after DATA command")
            self.quit()
            return

        data = self.email + EOL + '.' + EOL

        self.message_routing.update({'handle_chunk': self.quit})
        self.send_message(
            to=self.connection,
            directive='send',
            body={'message': data}
        )

    def quit(self, message=None):
        """Disconnect your session

        Can be called as a normal method

        TODO: collect last return code from server, bundle with rcpt_err and
        reply to whatever called connect()
        """

        try:
             numeric, msg = self.handle_chunk(message)
        except TypeError:
            # We haven't reached EOL yet
            if message:
                return
        except AttributeError:
            # message has no body
            pass

        _log.info("Sending QUIT command to server")
        self.message_routing.update({'handle_chunk': self.noop})
        self.send_message(
            to=self.connection,
            directive=u'send',
            body={'message': 'QUIT' + EOL}
        )

    def handle_chunk(self, message):
        """Handle TCP data

        Should be called by methods that expected to be called from
        xudd.lib.tcp.Client"""
        self.incoming += message.body['chunk']

        # find next EOL
        if EOL in self.incoming:
            line, self.incoming = self.incoming.split(EOL, 1)

            # format data into numeric + message
            numeric, msg = line.split(' ', 1)
            numeric = int(numeric)
            return [numeric, msg]

class SMTPServer(Actor):
    """Simple SMTP server.

    Or it will be at least.
    """
    pass
