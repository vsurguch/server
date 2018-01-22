
import sqlalchemy as sql
import sqlalchemy.orm as orm

# import sky_server.utils.singleton as single
import utils.singleton as single

import os.path


class User(object):
    def __init__(self, name, login, password):
        self.name = name
        self.login = login
        self.password = password

    def __repr__(self):
        return '<User: (id=), (name={}), (login={})>'.format(self.id, self.name, self.login)


class ConnectedUser(object):
    def __init__(self, fd):
        self.fd = fd

    def __repr__(self):
        return '<Connected user: (fd={}), (user_id={})'.format(self.fd, self.user_id)


class RelatedUsers(object):
    def __init__(self, user_id, related_id):
        self.user_id = user_id
        self.related_id = related_id

    def __repr__(self):
        return '<Related: (user_id={}) (related_id={})'.format(self.user_id, self.related_id)

class PostponedMessages(object):
    def __init__(self, user_id, message):
        self.user_id = user_id
        self.message = message


class Database(single.SingletonVerifier):
    def __init__(self, db_file):

        db_exists = os.path.exists(db_file)

        self.engine = sql.create_engine('sqlite:///{}'.format(db_file))
        self.metadata = sql.MetaData()
        self.metadata.bind = self.engine

        if db_exists:
            users_table = sql.Table('users', self.metadata, autoload=True  )
            connected_users_table = sql.Table('connected_users', self.metadata, autoload=True)
            related_users = sql.Table('related_users',self.metadata, autoload=True)
            postponed = sql.Table('postponed', self.metadata, autoload=True)
        else:
            users_table = sql.Table('users', self.metadata,
                                     sql.Column('id', sql.Integer, primary_key=True),
                                     sql.Column('name', sql.String),
                                     sql.Column('login', sql.String),
                                    sql.Column('password', sql.String))

            connected_users_table = sql.Table('connected_users', self.metadata,
                                              sql.Column('id', sql.Integer, primary_key=True),
                                              sql.Column('fd', sql.Integer),
                                              sql.Column('user_id', sql.Integer, sql.ForeignKey('users.id')))

            related_users = sql.Table('related_users', self.metadata,
                                      sql.Column('user_id', sql.Integer, sql.ForeignKey('users.id')),
                                      sql.Column('related_id', sql.Integer, sql.ForeignKey('users.id')),
                            sql.PrimaryKeyConstraint('user_id', 'related_id'))

            postponed = sql.Table('postponed', self.metadata,
                                  sql.Column('id', sql.Integer, primary_key=True),
                                  sql.Column('user_id', sql.Integer, sql.ForeignKey('users.id')),
                                  sql.Column('message', sql.Binary))

            self.metadata.create_all(self.engine)

        orm.mapper(ConnectedUser, connected_users_table,
                   properties={'user': orm.relationship(User, backref='connected_user')})

        orm.mapper(RelatedUsers, related_users)

        orm.mapper(User, users_table, properties={'related':
                                                      orm.relationship(User, secondary=related_users,
                                                                       primaryjoin=(users_table.c.id==related_users.c.user_id),
                                                                       secondaryjoin=(users_table.c.id==related_users.c.related_id),
                                                                       backref=orm.backref('users'))})

        orm.mapper(PostponedMessages, postponed, properties={'user': orm.relationship(User, backref='postponed')})

        self.Session = orm.sessionmaker(bind=self.engine)

        self.delete_all_connected()

    def close_connection(self):
        self.engine.dispose()

    # user operations
    def add_user_by_fields(self, session, name, login, password):
        user_exists = session.query(User).filter_by(login=login).first()
        result = None
        if user_exists is None:
            user = User( name, login, password)
            session.add(user)
            session.commit()
            result = user
        return result

    def delete_user(self, session, user):
        session.delete(user)
        session.commit()

    def delete_user_by_username(self, username):
        session = self.Session()
        user = session.query(User).filter_by(login = username).first()
        session.delete(user)
        session.commit()

    def get_all(self, session):
        users = session.query(User).all()
        return users

    def get_user_by_username(self, session, username):
        user = session.query(User).filter_by(login=username).first()
        return user

# connected user operations
    def add_connected_user(self, session, fd, user):
        connected_user = ConnectedUser(fd)
        connected_user.user = user
        session.add(connected_user)
        session.commit()

    def delete_connected_user(self, session, fd):
        connected = session.query(ConnectedUser).filter_by(fd=fd).first()
        session.delete(connected)
        session.commit()

    def delete_all_connected(self):
        session = self.Session()
        n = session.query(ConnectedUser).delete()
        session.commit()
        session.close()
        return n

    def get_connected_user_by_fd(self, session, fd):
        c_user = session.query(ConnectedUser).filter_by(fd=fd).first()
        return c_user

    def get_all_connected(self, session):
        c_users = session.query(ConnectedUser).all()
        return c_users

# related user operations
    def add_related(self, session, user, related_user):
        if user != related_user and related_user not in user.related:
            user.related.append(related_user)
            session.commit()

    def delete_related(self, session, user, related_user):
        if related_user in user.related:
            user.related.remove(related_user)
            session.commit()

#postponed operations
    def delete_postponed_by_id(self, session, id):
        record = session.query(PostponedMessages).filter_by(id=id).first()
        session.delete(record)
        session.commit()