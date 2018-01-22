import logging
import os.path

cwd = os.getcwd()
log_path = os.path.join(os.path.dirname(__file__), 'app.log')
if not os._exists(log_path):
    f = open(log_path, 'a+')
    f.close()

# logging.basicConfig(filename='app.log',
#                     format='%(asctime)s %(levelname)s %(module)s %(funcName)s %(message)s',
#                     level= logging.INFO)

logformat = logging.Formatter('%(levelname)s​​ %(asctime)s​ ​ %(message)s')
logger_handler = logging.FileHandler(log_path, 'w', 'utf-8')
logger_handler.setFormatter(logformat)
logger_handler.setLevel(logging.DEBUG)
logger = logging.getLogger('server')
logger.setLevel(logging.ERROR)
logger.addHandler(logger_handler)



