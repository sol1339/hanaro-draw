import secrets
import sqlite3
from datetime import datetime

class DrawStore:
    def __init__(self, path):
        self.db = sqlite3.connect(path, timeout=10)
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS prizes(rank INTEGER PRIMARY KEY, name TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity>=0), used INTEGER NOT NULL DEFAULT 0 CHECK(used>=0 AND used<=quantity));
            CREATE TABLE IF NOT EXISTS history(id INTEGER PRIMARY KEY AUTOINCREMENT, time TEXT, rank INTEGER, name TEXT);
        ''')
        if not self.db.execute('SELECT count(*) FROM prizes').fetchone()[0]:
            quantities = [1, 2, 4] + [0]*7
            with self.db:
                self.db.executemany('INSERT INTO prizes VALUES(?,?,?,0)',
                    [(i, f'{i}등 경품 (수정하세요)', q) for i,q in enumerate(quantities,1)] + [(0,'꽝',19993)])

    def rows(self):
        return self.db.execute('SELECT rank,name,quantity,used FROM prizes ORDER BY rank').fetchall()

    def configure(self, total, entries):
        if type(total) is not int or total <= 0 or len(entries) != 10:
            raise ValueError('총 추첨 수량은 양의 정수, 경품은 1~10등이어야 합니다.')
        for name,q in entries:
            if not name.strip() or len(name.strip()) > 40 or type(q) is not int or q < 0:
                raise ValueError('경품명은 1~40자, 수량은 0 이상의 정수로 입력하세요.')
        blank = total - sum(q for _,q in entries)
        if blank < 0:
            raise ValueError('당첨 경품 합계가 총 추첨 수량보다 많습니다.')
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            values = [('꽝', blank)] + entries
            for rank,(_,_,_,used) in enumerate(self.rows()):
                if values[rank][1] < used:
                    raise ValueError(f'{rank if rank else "꽝"}의 수량은 이미 추첨된 {used}개보다 작을 수 없습니다.')
            self.db.executemany('UPDATE prizes SET name=?,quantity=? WHERE rank=?',
                [(name.strip(),q,i) for i,(name,q) in enumerate(values)])

    def draw(self, chooser=secrets.randbelow):
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            rows = self.rows()
            remaining = sum(q-u for _,_,q,u in rows)
            if remaining <= 0:
                raise ValueError('모든 추첨이 종료되었습니다.')
            ticket = chooser(remaining)
            for rank,name,q,used in rows:
                ticket -= q-used
                if ticket < 0:
                    self.db.execute('UPDATE prizes SET used=used+1 WHERE rank=?',(rank,))
                    cur = self.db.execute('INSERT INTO history(time,rank,name) VALUES(?,?,?)',
                        (datetime.now().astimezone().isoformat(timespec='seconds'),rank,name))
                    result = (cur.lastrowid,rank,name)
                    break
        return result

    def reset(self):
        """Keep prize configuration; atomically clear all draws."""
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            self.db.execute('DELETE FROM history')
            self.db.execute('UPDATE prizes SET used=0')
            self.db.execute("DELETE FROM sqlite_sequence WHERE name='history'")

    def history(self):
        return self.db.execute('SELECT id,time,rank,name FROM history ORDER BY id').fetchall()
