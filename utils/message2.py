
from time import time, ctime
import json

MSG_TEMPLATE = {
    "action": "",
    "time": 0,
}

RSP_TEMPLATE = {
    "response": 0,
    "time": 0,
    "alert": "",
}

RESPONSES_DICT = {
    '0': 'unknown code',
    '100': 'general notice',
    '101': ' important notice',
    '200': 'ok',
    '201': 'created',
    '202': 'accepted',
    '300': 'broadcast message',
    '400': 'bad request or bad json',
    '401': 'not authorized',
    '402': 'incorrect username or password',
    '403': 'forbidden : site ban in effect on users ip or similar',
    '404': 'not found : user or room does not exist on the server',
    '409': 'conflict : someone is already connected with a given user name',
    '410': 'gone : user exists but is not available (offline)',
    '500': '500 server error',
}

class GeneralMessage(object):
    def __init__(self):
        self.msg = {}

    def __setattr__(self, key, value):
        if key == 'msg':
            super().__setattr__(key, value)
        else:
            self.msg[key] = value

    def __getitem__(self, item):
        if item in self.msg:
            return self.msg[item]
        else:
            return None

    def __str__(self):
        return '; '.join(['{k}: {v}'.format(k=key, v=value) for key, value in self.msg.items()])

    def length(self, encoding):
        return len((json.dumps(self.msg)).encode(encoding))

    def get_binary_json(self, encoding):
        jsn = json.dumps(self.msg)
        return jsn.encode(encoding)

    def make_from_binary_json(self, data, encoding):
        decoded_data = data.decode(encoding)
        self.msg = json.loads(decoded_data)

class Message(GeneralMessage):
    def __init__(self, action=''):
        self.msg = MSG_TEMPLATE.copy()
        self.msg['action'] = action
        self.msg['time'] = time()

    def __getattr__(self, item):
        if item == 'msg':
            return self.msg
        else:
            if item in self.msg:
                if item == 'time':
                    return ctime(self.msg['time'])
                else:
                    return self.msg[item]
            else:
                return None


class Response(GeneralMessage):
    def __init__(self, response_code=0, alert=''):
        self.msg = RSP_TEMPLATE.copy()
        self.msg['response'] = response_code
        self.msg['time'] = time()
        self.msg['alert'] = alert

    def __getattr__(self, item):
        if item == 'msg':
            return self.msg
        else:
            if item in self.msg:
                if item == 'time':
                    return ctime(self.msg['time'])
                elif (item == 'response') and (str(self.msg['response']) in RESPONSES_DICT):
                    return RESPONSES_DICT[str(self.msg['response'])]
                else:
                    return self.msg[item]
            else:
                return None

class MessageAuthenticate(Message):
    def __init__(self, user, password):
        Message.__init__(self, 'authentificate')
        user_data = {
            'account_name': user,
            'password': password,
        }
        self.user = user_data


class MessageGetContacts(Message):
    def __init__(self, username):
        Message.__init__(self, 'get_contacts')
        self.user = username


class MessageAddContact(Message):
    def __init__(self, username, contact_name):
        Message.__init__(self, 'add_contact')
        self.user = username
        self.contact = contact_name


class MessageDeleteContact(Message):
    def __init__(self, username, contact_name):
        Message.__init__(self, 'delete_contact')
        self.user = username
        self.contact = contact_name


class MessageContactOnline(Message):
    def __init__(self, contact_name):
        Message.__init__(self, 'contact_online')
        self.contact = contact_name


class MessageContactOffline(Message):
    def __init__(self, contact_name):
        Message.__init__(self, 'contact_offline')
        self.contact = contact_name


class MessageContact(Message):
    def __init__(self, contact_login, contact_name, online):
        Message.__init__(self, 'contact_list')
        self.username = contact_login
        self.name = contact_name
        self.online = online


class MessagePersonal(Message):
    def __init__(self, username, dest, text):
        Message.__init__(self, 'personal_message')
        self.user = username
        self.dest = dest
        self.text = text


class MessagePersonalFrom(Message):
    def __init__(self, src_user, text):
        Message.__init__(self, 'personal_message')
        self.src = src_user
        self.text = text


class MessageDeleteLastMessage(Message):
    def __init__(self, username, dest):
        Message.__init__(self, 'delete_last_message')
        self.user = username
        self.dest = dest


class MessageDeleteLastMessageFwd(Message):
    def __init__(self, src):
        Message.__init__(self, 'delete_last_message')
        self.src = src


def main():
    m = MessageAuthenticate('petrov', '12345')
    print(m.__dict__)
    print(m)
    print(m.response)
    print(m.time)


if __name__ == '__main__':
    main()



