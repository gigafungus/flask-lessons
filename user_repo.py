import psycopg
from psycopg.rows import dict_row

class UserRepository:
    def __init__(self, conn):
        self.conn: psycopg.Connection = conn

    def save(self, user):
        if 'id' in user:
            self._update(user)
        else:
            self._create(user)

    def _update(self, user):
        with self.conn.cursor() as cur:
            cur.execute(
                'UPDATE users SET name = %s, nickname = %s, email = %s, password = %s, city = %s WHERE id = %s', 
                (user['name'], user['nickname'], user['email'], user['password'], user['city'], user['id'])
                )
        self.conn.commit()

    def _create(self, user):
        with self.conn.cursor() as cur:
            cur.execute(
                'INSERT INTO users (name, nickname, email, password, city) VALUES (%s, %s, %s, %s, %s)',
                (user['name'], user['nickname'], user['email'], user['password'], user['city'])
            )
        self.conn.commit()

    def list_all(self):
        with self.conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                'SELECT * FROM users'
            )
            return [dict(row) for row in cur]

    def find(self, id):
        with self.conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                'SELECT * FROM users WHERE id = %s',
                (id,)
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def find_by_term(self, term):
        with self.conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                'SELECT * FROM users WHERE nickname ILIKE %s OR name ILIKE %s',
                (f'%{term}%', f'%{term}%')
            )
            return [dict(row) for row in cur]

    def delete(self, id):
        with self.conn.cursor() as cur:
            cur.execute(
                'DELETE FROM users WHERE id = %s',
                (id,)
            )
        self.conn.commit()
        
    