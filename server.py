

import select as sel
import socket as sct
import threading as th
import queue as q
#
# import sky_server.database.database as user_db
# import sky_server.log.log_config as lg
# from sky_server.utils import encryption, message2 as msg
# from sky_server.utils.conf import *

import database.database as user_db
import log.log_config as lg
from utils import encryption, message2 as msg
from utils.conf import *


class MessageSender(th.Thread):
    def __init__(self):
        super().__init__()
        self.queue = q.Queue()
        self.daemon = True
        self.stop = False

    def run(self):
        while not self.stop:
            if self.queue.not_empty:
                connection, message = self.queue.get()
                bl = len(message).to_bytes(4, 'big')
                self.send_message(connection, bl + message)

    def send_message(self, connection, bmessage):
        try:
            connection.sendall(bmessage)
        except:
            lg.logger.error('Sender thread; send message error')


class MessageReciever(th.Thread):
    def __init__(self, server):
        super().__init__()
        self.server = server
        self.queue = q.Queue()
        self.daemon = True
        self.stop = False
        self.awaiting_file = {}
        self.continous_recieving = {}
        self.continous_recieving_data = {}

    def run(self):
        while not self.stop:
            try:
                connection, address = self.server.socket.accept()
            except OSError:
                pass
            else:
                connection.send(self.server.public_key.exportKey(format='PEM'))
                self.server.clients.append(connection)
                log_record = 'New connection from client {}'.format(address)
                self.server.listener.new_message(log_record)

                fd = connection.fileno()
                if fd not in self.server.session_key_dict:
                    self.server.session_key_dict[fd] = ''
            finally:
                wait = 0
                sread = []
                swrite = []
                try:
                    sread, swrite, sexc = sel.select(self.server.clients, self.server.clients, [], wait)
                except:
                    pass
                recieved = self.read_requests(sread)
                self.dispatch_recieved_messages(recieved)
        # print('reciever stopped')

    def read_requests(self, r_clients):
        recieved = {}
        for sock in r_clients:
            try:
                if sock.fileno() not in self.continous_recieving:
                    bl = sock.recv(4)
                    l = int.from_bytes(bl, 'big')
                    fd = sock.fileno()
                    if l <= 4096:
                        recieved[sock] = b''
                        leng_to_read = l
                        while leng_to_read != 0:
                            data = sock.recv(leng_to_read)
                            recieved[sock] += data
                            leng_to_read -= len(data)
                    else:
                        data = sock.recv(4096)
                        self.continous_recieving[fd] = l - len(data)
                        self.continous_recieving_data[fd] = data

                else:
                    fd = sock.fileno()
                    to_read = 4096 if self.continous_recieving[fd] > 4096 else self.continous_recieving[fd]
                    data = sock.recv(to_read)
                    self.continous_recieving_data[fd] += data
                    self.continous_recieving[fd] -= len(data)
                    if self.continous_recieving[fd] == 0:
                        recieved[sock] = self.continous_recieving_data[fd]
                        del self.continous_recieving[fd]
                        del self.continous_recieving_data[fd]
            except:
                self.server.socket_unavailable(sock)
        return recieved

    def dispatch_recieved_messages(self, recieved):
        for connection, encrypted_message in recieved.items():
            fd = connection.fileno()
            if self.server.session_key_dict[fd] == '':
                session_key_encrypted = encrypted_message[0:128]
                auth_bmessage_encrypted = encrypted_message[128:]
                session_key = self.server.cipher_rsa_private.decrypt(session_key_encrypted)
                self.server.session_key_dict[fd] = session_key
                auth_bmessage = encryption.decrypt(auth_bmessage_encrypted, session_key)
                auth_message = msg.Message()
                auth_message.make_from_binary_json(auth_bmessage, 'utf-8')
                self.server.authenticate_client(connection, auth_message)
            else:
                session_key = self.server.session_key_dict[fd]
                if fd in self.awaiting_file:
                    file_path = get_path(self.awaiting_file[fd].name)
                    f = encryption.decrypt_file(encrypted_message, session_key, file_path)
                    self.server.forward_file(self.awaiting_file[fd], file_path)
                    del self.awaiting_file[fd]
                    break
                bmessage = encryption.decrypt(encrypted_message, session_key)
                message = msg.Message()
                message.make_from_binary_json(bmessage, 'utf-8')
                if message.action == 'get_contacts':
                    username = message.user
                    self.server.send_contacts(connection, username)
                if message.action == 'add_contact':
                    self.server.add_contact(connection, message.user, message.contact)
                if message.action == 'delete_contact':
                    self.server.delete_contact(connection, message.user, message.contact)
                if message.action == 'personal_message':
                    self.server.forward_personal_message(connection, message)
                if message.action == 'send_file':
                    fdata = msg.File_data(message.name, message.filelength, message.src, message.dest)
                    self.awaiting_file[fd] = fdata


class Server(object):
    def __init__(self, hostname, port, listener, db):
        #socket
        self.server_address = (hostname, port)
        self.socket = sct.socket(sct.AF_INET, sct.SOCK_STREAM)
        self.socket.bind(self.server_address)
        self.socket.listen(5)
        self.socket.settimeout(0.2)
        self.stop = False

        #encription
        self.key, self.public_key = encryption.generate_key_public_key()
        self.cipher_rsa_private = encryption.generate_cipher_rsa_private(self.key)
        self.session_key_dict = {}
        self.sending_file = {}
        self.sending_file_data = {}

        #clients
        self.clients = []
        self.users = []
        self.connected = []
        self.postponed = []

        #listenter
        self.listener = listener

        #logging
        self.log = []
        log_record = '!!! Server socket created on {h} at port {p}'.format(h=self.server_address[0],
                                                                             p=self.server_address[1])
        # lg.logger.info(log_record)
        self.listener.new_message(log_record)
        self.log.append(log_record)

        #db
        self.db_file = db

    def run(self):
        self.sender = MessageSender()
        self.sender.start()

        self.reciever = MessageReciever(self)
        self.reciever.start()

        self.db = user_db.Database(self.db_file)
        self.form_users_list()


    def socket_unavailable(self, socket):
        # удаляем из базы данных
        session = self.db.Session()
        fd = socket.fileno()
        connected_user = self.db.get_connected_user_by_fd(session, fd)
        if connected_user is not None:
            self.user_offline(session, connected_user.user.login)
            session.delete(connected_user)
            session.commit()
        session.close()

        #удаляем session_key
        if fd in self.session_key_dict:
            del self.session_key_dict[fd]

        # записываем уведовмление в лог
        # address = socket.getpeername()
        log_record = 'Client {} () disconnected.'.format(connected_user)
        self.listener.new_message(log_record)
        self.log.append(log_record)

        # удаляем сокет из списка подключенных клиентов
        self.clients.remove(socket)

    def form_users_list(self):
        session = self.db.Session()
        all_users = self.db.get_all(session)
        self.users = all_users[:]
        session.close()

    def send_session_key_ok(self, connection):
        message_session_key_ok = msg.Response(200, 'session_key_ok')
        self.send_encrypted_message(connection, message_session_key_ok, binary=False)

    def authenticate_client(self, client_connection, message):
        #читаем сообщение от указанного клинета
        user_data = message.user
        username = user_data['account_name']
        password = user_data['password']
        # fd = str(client_connection.fileno())
        self.listener.new_message('Client {} asked for authentification'.format(username))

        session = self.db.Session()
        user = self.db.get_user_by_username(session, username)
        #если такого пользователя нет
        if user == None:
            # если пользователь не существует, добавить нового пользователя
            newuser = self.db.add_user_by_fields(session, username, username, password)
            self.users.append(newuser)
            # уведомляем пользователя о добавлении в базу данных
            resp_message = msg.Response(200, 'user does not exist, new user created with username %s' % username)
            self.send_encrypted_message(client_connection, resp_message, binary=False)

            # добавляем в базу данных
            self.db.add_connected_user(session, client_connection.fileno(), newuser)
            self.new_user_online(session, username)

            # добавляем запись в лог и сообщаяем всем о новом клиенте в сети
            log_record = 'Client \'{}\'({}) registered and authenticated'.format(username, client_connection.getpeername())
            self.listener.new_message(log_record)
            self.log.append(log_record)

        # если пароль неверный
        elif password != user.password:
            # отправить сообщение
            resp_message = msg.Response(402, 'Password incorrect')
            self.send_encrypted_message(client_connection, resp_message, binary=False)
            #не подключаем клиента
            self.clients.remove(client_connection)
            self.listener.new_message('Client {}: incorrect password'.format(username))
        #если все верно
        else:
            # добавляем в базу данных
            self.db.add_connected_user(session, client_connection.fileno(), user)

            # сообщяем клиенту об успешной аутентификацц
            resp_message = msg.Response(200, 'Successfully authenticated')
            self.send_encrypted_message(client_connection, resp_message, binary=False)

            # добавляем запись в лог и сообщаяем всем о новом клиенте в сети
            address = client_connection.getpeername()
            log_record = 'Client \'{}\' ({}) authenticated.'.format(username, address)
            self.listener.new_message(log_record)
            self.log.append(log_record)
            self.new_user_online(session, username)
        session.close()

    #поиск контактов для пользователя username
    def find_related_users_online(self, session, username):
        related_online = []
        user = self.db.get_user_by_username(session, username)
        related_users = user.related
        for r_user in related_users:
            if len(r_user.connected_user)>0 is not None:
                fd = r_user.connected_user[0].fd
                for sock in self.clients:
                    if sock.fileno() == fd:
                        related_online.append(sock)
        return related_online

    #действия при входе пользователя username
    def new_user_online(self, session, username):
        # session = self.db.Session()
        related_online = self.find_related_users_online(session, username)
        message = msg.MessageContactOnline(username)
        for r_user in related_online:
            self.send_encrypted_message(r_user, message, binary=False)
        self.connected.append(username)
        self.listener.new_user_online(username)
        # session.close()

    #действия при выходе пользователя username
    def user_offline(self, session,  username):
        # session = self.db.Session()
        related_online = self.find_related_users_online(session, username)
        message = msg.MessageContactOffline(username)
        for r_user in related_online:
            self.send_encrypted_message(r_user, message, binary=False)
        self.connected.remove(username)
        self.listener.user_offline(username)
        # session.close()

    def send_postponed(self, connection, username):
        # send postponed messages
        session = self.db.Session()
        user = self.db.get_user_by_username(session, username)
        postponed = user.postponed
        for record in postponed:
            record_id = record.id
            bmessage = record.message
            self.send_encrypted_message(connection, bmessage, binary=True)
            self.db.delete_postponed_by_id(session, record_id)
        session.close()

    #отправка контакта по запросу
    def send_contact(self, connection, contact):
        if len(contact.connected_user) > 0:
            online_status = True
        else:
            online_status = False
        contact_message = msg.MessageContact(contact.login, contact.name, online_status)
        self.send_encrypted_message(connection, contact_message, binary=False)

    #отправка списка контактов по запросу
    def send_contacts(self, connection, username):
        session = self.db.Session()
        user = self.db.get_user_by_username(session, username)
        contact_list= user.related
        response_message = msg.Response(202, str(len(contact_list)))
        self.send_encrypted_message(connection, response_message, binary=False)
        for contact in contact_list:
            self.send_contact(connection, contact)
        session.close()
        self.listener.new_message('Client {} asked for contacts'.format(username))
        self.send_postponed(connection, username)

    #отправка сообщения другому пользователю
    def forward_personal_message(self, connection, message):
        username = message.user
        dest = message.dest
        message_text = message.text
        log_record = 'new personal pmesssage: from:{}; to: {};'.format(username, dest)
        self.listener.new_message(log_record)
        self.log.append(log_record)

        # создаем сообщение для отправки
        forward_message = msg.MessagePersonalFrom(username, message_text)
        # находим в списке connected users и выявняем его сокет
        session = self.db.Session()
        user = self.db.get_user_by_username(session, dest)
        if user is not None:
            if len(user.connected_user) > 0:
                c_user = user.connected_user[0]
                fd = c_user.fd
                user_sock = None
                for sock in self.clients:
                    if sock.fileno() == fd:
                        user_sock = sock
                        break
                log_record = 'forwarding message to {}'.format(str(user_sock))
                self.log.append(log_record)
                self.send_encrypted_message(user_sock, forward_message, binary=False)
            else:
                postponed_message = user_db.PostponedMessages(user.id, forward_message.get_binary_json('utf-8'))
                user.postponed.append(postponed_message)
                session.commit()
                response = msg.Response(404, 'user is not connected, message saved to postponed')
                self.send_encrypted_message(connection, response, binary=False)
        session.close()

    # пересылка файла
    def forward_file(self, fdata, filename):
        dest = fdata.dest
        session = self.db.Session()
        user = self.db.get_user_by_username(session, dest)
        if user is not None:
            if len(user.connected_user) > 0:
                c_user = user.connected_user[0]
                fd = c_user.fd
                user_sock = None
                for sock in self.clients:
                    if sock.fileno() == fd:
                        user_sock = sock
                        break
                message = msg.MessageSendFile(fdata.name, fdata.filelength, fdata.src, fdata.dest)
                self.send_encrypted_message(user_sock, message, False)
                self.send_encrypted_file(user_sock, filename)

    #Добавление контакта
    def add_contact(self, connection, username, contact_name):
        session = self.db.Session()
        try:
            user = self.db.get_user_by_username(session, username)
            contact = self.db.get_user_by_username(session, contact_name)
            self.db.add_related(session, user, contact)
            response = msg.Response(205, 'contact_add_ok')
            self.send_encrypted_message(connection, response, binary=False)
            self.send_contact(connection, contact)
            self.listener.new_message('Client {} added contact: {}'.format(username, contact_name))
        except:
            response = msg.Response(405, 'contact_add_error')
            self.send_encrypted_message(connection, response, binary=False)
            log_record = "problem adding contact"
            self.listener.new_message(log_record)
            lg.logger.error('Main thread; add contact:{} - {}; add contact error'.format(username, contact_name))
        finally:
            session.close()

    #Удаление контакта
    def delete_contact(self, connection, username, contact_name):
        session = self.db.Session()
        try:
            user = self.db.get_user_by_username(session, username)
            contact = self.db.get_user_by_username(session, contact_name)
            self.db.delete_related(session, user, contact)
            response = msg.Response(206, contact_name)
            # response.add_key_value('contact', contact_name)
            self.send_encrypted_message(connection, response, binary=False)
            self.listener.new_message('Client {} deleted contact: {}'.format(username, contact_name))
        except:
            response = msg.Response(406, 'contact_delete_error')
            self.send_encrypted_message(connection, response, binary=False)
            log_record = "problem deleting contact"
            self.listener.new_message(log_record)
            lg.logger.error('Main thread; delete contact:{} - {}; delete contact error'.format(username, contact_name))
        finally:
            session.close()

    # def send_message(self, connection, message):
    #     print(message)
    #     bmessage = message.get_binary_json('utf-8')
    #     connection.send(bmessage)

    def send_encrypted_message(self, connection, message, binary):
        fd = connection.fileno()
        if not binary:
            bmessage = message.get_binary_json('utf-8')
        else:
            bmessage = message
        if fd in self.session_key_dict:
            enctypted_message = encryption.encrypt(bmessage, self.session_key_dict[fd])
            self.sender.queue.put((connection, enctypted_message))

    def send_encrypted_file(self, connection, file):
        fd = connection.fileno()
        if fd in self.session_key_dict:
            encrypted_file = encryption.encrypt_file(file, self.session_key_dict[fd])
            print(len(encrypted_file))
            self.sender.queue.put((connection, encrypted_file))

    def broadcast(self, text_message, omit=None):
        self.listener.new_message('Broadcast message: {}'.format(text_message))
        for sock in self.clients:
            if sock != omit:
                try:
                    log_record = 'broadcast message: %s' % text_message
                    self.log.append(log_record)
                    broadcast_message = msg.Response(300)
                    broadcast_message.alert = text_message
                    self.send_encrypted_message(sock, broadcast_message, binary=False)
                except:
                    self.socket_unavailable(sock)

    def stop_server(self):
        self.broadcast('Server is going to shut down.')
        self.sender.stop = True
        self.reciever.stop = True
        self.db.close_connection()
        self.sender.join(timeout=0.5)
        self.reciever.join(timeout=0.5)
        self.stop = True
        self.socket.close()
        log_record = 'Server stoped. Server socket closed.'
        self.listener.new_message(log_record)





