

from sys import argv as sys_argv

# from sky_server.utils import menu
# import sky_server.server as serv
# from sky_server.database.database import PostponedMessages
# from sky_server.utils.conf import *

from utils import menu
import server as serv
from database.database import PostponedMessages
from utils.conf import *


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
        output_to('New user online: {}'.format(username), self.output)

    def user_offline(self, username):
        output_to('user offline: {}'.format(username), self.output)

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