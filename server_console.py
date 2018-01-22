
from pathlib import Path
from os import mkdir
from os.path import join, exists
from sys import argv as sys_argv

# from sky_server.utils import menu
# import sky_server.server as serv
# from sky_server.database.database import PostponedMessages

from utils import menu
import server as serv
from database.database import PostponedMessages

CONF_FILE_NAME = 'sky_serv.conf'
CONF_DIR_NAME = 'sky_serv'
CONF_DICT = {
    'hostname': 'localhost',
    'port': '8888',
    'output': 'console'
}
LOG_FILE_NAME = 'logfile.txt'
DB_FILE_NAME = 'server.db'

def make_conf_file():
    conf_dir = join(str(Path.home()), CONF_DIR_NAME)
    if not exists(conf_dir):
        mkdir(conf_dir)
    conf_file = join(conf_dir, CONF_FILE_NAME)
    with open(conf_file, 'w') as f:
        for k,v in CONF_DICT.items():
            f.write('{}={}\n'.format(k,v))

def read_conf():
    conf_file = join(str(Path.home()), CONF_DIR_NAME, CONF_FILE_NAME)
    if not exists(conf_file):
        make_conf_file()
    else:
        with open(conf_file, 'r') as f:
            for line in f:
                kv = line.split('=')
                k = kv[0]
                v = kv[1][:-1]
                CONF_DICT[k] = v

def output_to(msg, output):
    if output == '':
        print(msg)
    else:
        with open(output, 'a') as f:
            f.write(msg)

class ConsoleListener(object):
    def __init__(self, output):
        self.output = output

    def new_message(self, message):
        output_to(message, self.output)

    def new_user_online(self, username):
        output_to('New user online: {}\n'.format(username), self.output)

    def user_offline(self, username):
        output_to('user offline: {}\n'.format(username), self.output)

def main():
    read_conf()
    if len(sys_argv) == 3:
        hostname = sys_argv[1]
        port = int(sys_argv[2])
    else:
        hostname = CONF_DICT['hostname']
        strport = CONF_DICT['port']
        port = int(strport)

    output = ''
    if CONF_DICT['output'] != 'console':
        output = join(str(Path.home()), CONF_DIR_NAME, LOG_FILE_NAME)
    listener = ConsoleListener(output)
    db_file = join(str(Path.home()), CONF_DIR_NAME, DB_FILE_NAME)
    server = serv.Server(hostname, port, listener, db_file)
    server.run()

    while True:
        if CONF_DICT['output'] == 'console':
            menu_item = menu.menu(menu.SERVER_MAIN_MENU)
            if menu_item == 'q':
                server.stop_server()
                print('Good buy!')
                break
            elif menu_item == '1':
                for record in server.log:
                    print(record)
            elif menu_item == '2':
                for record in server.users:
                    print(record)
            elif menu_item == '3':
                for record in server.connected:
                    print(record)
            elif menu_item == '4':
                session = server.db.Session()
                postponed_list = session.query(PostponedMessages).all()
                for record in postponed_list:
                    print(record.user, record.message)
                session.close()
            elif menu_item == '5':
                for record in server.clients:
                    print(record)


if __name__ == '__main__':
    main()