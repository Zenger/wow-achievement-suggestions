# SPDX-License-Identifier: MIT
import json
import sqlite3


# noinspection SqlNoDataSourceInspection
class DataHandler:
    def __init__(self):
        self.init_database()

    def init_database(self):
        self.connection = sqlite3.connect('data.db', check_same_thread=False)
        self.cursor = self.connection.cursor()

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                achievement_id INTEGER,
                name TEXT,
                description TEXT,
                is_account_wide INTEGER
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS criteria (
                criteria_id INTEGER,
                description TEXT
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievements_criteria (
                achievement_id INTEGER,
                parent_achievement_id INTEGER,
                criteria_id INTEGER
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS character_achievements ( 
                realm TEXT,
                name TEXT,
                achievement_data_blob TEXT
            )
        ''')


        self.connection.commit()

    def store_achievement_data(self, achievement_data):
        is_account_wide = achievement_data.is_account_wide or False

        if not self.achievement_exist(achievement_data.id):
            self.cursor.execute('''
                INSERT INTO achievements (achievement_id, name, description, is_account_wide)
                VALUES (?, ?, ?, ?)
            ''', (achievement_data.id, achievement_data.name, achievement_data.description, is_account_wide))
            self.connection.commit()

        if achievement_data.criteria and achievement_data.criteria.child_criteria:
            for criteria in achievement_data.criteria.child_criteria:
                achievement_id = criteria.achievement.id if criteria.achievement else 0
                parent_achievement_id = achievement_data.id
                if not self.criteria_exist(criteria.id):
                    self.cursor.execute('''
                        INSERT INTO criteria (criteria_id, description)
                        VALUES (?, ?)
                    ''', (criteria.id, criteria.description))
                if not self.criteria_has_child_criteria(criteria.id):
                    self.cursor.execute(
                        '''INSERT INTO achievements_criteria (achievement_id, parent_achievement_id, criteria_id) VALUES (?, ?, ?)''',
                        (achievement_id, parent_achievement_id, criteria.id))

        self.connection.commit()


    def store_character_achievement(self, realm, name, data_blob):
        self.cursor.execute('''INSERT INTO character_achievements (realm, name, achievement_data_blob) VALUES (?, ?, ?)''', (realm, name, data_blob))
        self.connection.commit()
        return self.cursor.lastrowid

    def achievement_exist(self, achievement_id):
        self.cursor.execute('SELECT * FROM achievements WHERE achievement_id = ?', (achievement_id,))
        return self.cursor.fetchone() is not None

    def criteria_exist(self, criteria_id):
        self.cursor.execute('SELECT * FROM criteria WHERE criteria_id = ?', (criteria_id,))
        return self.cursor.fetchone() is not None

    def criteria_has_child_criteria(self, criteria_id):
        self.cursor.execute('SELECT * FROM achievements_criteria WHERE criteria_id = ?', (criteria_id,))
        return self.cursor.fetchone() is not None

    def get_character_achievements(self, realm, name):
        self.cursor.execute('SELECT * FROM character_achievements WHERE realm = ? AND name = ?', (realm, name))
        data = self.cursor.fetchone()
        if data:
            try:
                return json.loads(data[2])
            except:
                return None