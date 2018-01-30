from os.path import join, exists
from pathlib import Path
from os import mkdir

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

def get_path(filename=''):
    return join(str(Path.home()), CONF_DIR_NAME, filename)