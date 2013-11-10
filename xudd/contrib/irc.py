###############################################################################
# Code below from http://susam.in/files/code/others/hmmbot.py and released
# under the GPL
###############################################################################

import re
import logging

_log = logging.getLogger(__name__)

class ParsedMessage(object):
    """This class represents a received message in IRC protocol.

    An example of a received IRC message is:

    :spal!n=spal@unaffiliated/spal PRIVMSG #python :hello, world

    The above message is parsed as:

    prefix = 'spal!n=spal@unaffiliated/spal'
    command = 'PRIVMSG'
    params = '#python :hello, world'

    Some messages may not have a prefix. The prefix of such messages is
    set to None. An example of such message is:

    PING :simmons.freenode.net
    """
    def __init__(self, message):
        """Parse the received IRC message."""

        self.message = message
        self.prefix = None
        self.command = None
        self.params = None

        # RFC 1459 - 2.3.1
        # <message> ::= [':' <prefix> <SPACE> ] <command> <params> <crlf>
        #
        # The prefix is extracted into self.prefix and rest of the
        # message is left intact in message.
        if message.startswith(':'):
            self.prefix, message = message[1:].split(None, 1)

        # RFC 1459 - 2.3.1
        # <command> ::= <letter> { <letter> } | <number> <number> <number>
        #
        # The command and params are separated into separate variables.
        message = message.split(None, 1)
        if len(message) < 2:
            _log.critical('Bad message found')
            return
        else:
            self.command, self.params = message

class ParsedPrefix(object):
    """This class represents a prefix present in a received IRC message.

    An example of a prefix is:

    spal!n=spal@unaffiliated/spal

    The above prefix is parsed as: nick = 'spal', user = 'spal' and
    host = 'unaffiliated/spal'.

    If any part of the prefix is missing, then that part is set to None.
    """

    def __init__(self, prefix):
        """Parse the specified prefix."""

        if not prefix:
            self.prefix = self.nick = self.user = self.host = None
            return

        self.prefix = prefix

        # RFC 1459 - 2.3.1
        # <prefix> ::= <servername> | <nick> [ '!' <user> ] [ '@' <host> ]
        nick_regex = re.compile(r'^([^!@]+)')
        user_regex = re.compile(r'!([^!@]+)')
        host_regex = re.compile(r'@([^!@]+)')

        match = nick_regex.search(prefix)
        if match:
            self.nick = match.group(1)
        else:
            self.nick = None

        match = user_regex.search(prefix)
        if match:
            self.user = match.group(1)
        else:
            self.user = None

        match = host_regex.search(prefix)
        if match:
            self.host = match.group(1)
        else:
            self.host = None

class ParsedParams(object):
    """This class represents the params of a command in IRC message.

    An example of params is:

    #python :hello, world

    It is parsed as: middle = '#python', trailing = ':hello, world'.
    """

    def __init__(self, params):
        """Parse the specified params."""

        if not params:
            self.params = self.middle = self.trailing = None
            return

        self.params = params
        self.middle = None

        # RFC 1459 - 2.3.1
        # <params> ::= <SPACE> [ ':' <trailing> | <middle> <params> ]
        if ':' in self.params:
            self.middle, self.trailing = self.params.split(':', 1)
            self.middle = self.middle.strip()
        else:
            self.middle = params
            self.trailing = None

        if not self.middle:
            self.middle = None

        if not self.trailing:
            self.trailing = None
