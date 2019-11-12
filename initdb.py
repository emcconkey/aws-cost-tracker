#!/usr/bin/env python3
import sqlite3

db = sqlite3.connect('costdata.sqlite')
cursor = db.cursor()
cursor.execute('''
    CREATE TABLE tracking(
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT,
                        account TEXT,
                        product TEXT,
                        cost REAL
                      )
''')
db.commit()

cursor.execute('''
    CREATE TABLE daily_costs(
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT,
                        cost REAL
                      )
''')
db.commit()
