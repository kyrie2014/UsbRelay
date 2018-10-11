#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Created on 2017-2-28 
@author:  Kyrie Liu  
@description:  MySQL method
"""
import MySQLdb


class DatabaseUtils(object):
    def __init__(self, host, user, passwd, db, port):

        self.conn = MySQLdb.connect(host, user, passwd, db, port, charset='utf8')
        self.cursor = self.conn.cursor()

    def get_rows_count_of_table(self, _table_name, condition):
        """
        get all rows number of the table
        :param _table_name: table name
        :param condition: filter condition, example:'*' - all rows, other 'key="123" and ...'
        :return:
        """
        __rows = 'SELECT COUNT(*) FROM {} WHERE {};'.format(_table_name, condition)
        self.cursor.execute(__rows)
        rows_num = self.cursor.fetchone()
        if rows_num:
            return rows_num[0]
        return 0

    def is_has_row_in_table(self, _table_name, condition):
        """
        whether existed the row in table
        :param _table_name: table name
        :param condition: filter condition, example: 'Key3="567" and ...'
        :return:
        """
        return self.get_rows_count_of_table(_table_name, condition) > 0

    def get_fields_of_table(self, _table_name):
        """
        get all keys of the table
        :param _table_name: table name
        :return: keys iterator
        """
        self.cursor.execute('SELECT * FROM {};'.format(_table_name))
        fields_list = [column[0] for column in self.cursor.description]
        return fields_list

    def is_has_table(self, _table_name):
        """
        whether exists the table
        :param _table_name: table
        :return: true - exist, false - not exist
        """
        is_existed_table = 'SHOW TABLES LIKE "{}"'.format(_table_name)
        self.cursor.execute(is_existed_table)
        __result = self.cursor.fetchall()
        return True if __result else False

    def insert_row_to_table(self, _table_name, _items):
        """
        insert a row value with the length of keys
        :param _table_name: table name
        :param _items: values list, example: ['values1, values2, ...']
        :return: none
        """
        __items_format = []
        for item in _items:
            if str == type(item):
                item = '"' + item.encode('utf8') + '"'
            __items_format.append(str(item))
        __insert = 'INSERT INTO {} VALUES({});'.format(_table_name, ','.join(__items_format))
        # print __insert
        try:
            self.cursor.execute(__insert)
            self.conn.commit()
        except Exception, err:
            print err
            self.conn.rollback()

    def update_value_of_row(self, _table_name, update_items, condition):
        """
        update value of the specific row
        :param _table_name: table name
        :param update_items: 'Key1="123",Key2="234",...'
        :param condition: 'Key3="567" and Key4="789" and ...'
        :return: None
        """
        __update = 'UPDATE {} SET {} WHERE {};'.format(_table_name, update_items, condition)
        try:
            self.cursor.execute(__update)
            self.conn.commit()
        except Exception, err:
            print err
            self.conn.rollback()

    def delete_data_of_table(self, _table_name, condition=None):
        """
        delete data of the specific rows, delete all rows if condition is none
        :param _table_name: table name
        :param condition: 'Key3="xxx" , Key4="xxx" and ...'
        :return:
        """
        __delete = 'DELETE FROM ' + _table_name
        try:
            if condition:
                __delete = '{} WHERE {}'.format(__delete, condition)
            self.cursor.execute(__delete)
            self.conn.commit()
        except Exception, err:
            print err
            self.conn.rollback()

    def drop_table(self, _table_name):
        """
        delete table
        :param _table_name: delete table
        :return: none
        """
        try:
            __drop = 'DROP TABLE ' + _table_name
            self.conn.execute(__drop)
            self.conn.commit()
        except Exception, err:
            print err
            self.conn.rollback()

    def query_data_of_table(self, _table_name, keys, condition=None, order=None):
        """
        query table
        :param order: sorted output by which key
        :param _table_name: table name
        :param keys:  'Key1,key2...'
        :param condition: 'Key1='x' and Key2='y' and ...'
        :return: query result is iterator
        """
        __query = 'SELECT {} FROM {}'.format(keys, _table_name)
        if condition:
            __query += ' WHERE {} '.format(condition)
        if order:
            __query += ' ORDER BY {}'.format(order)

        self.cursor.execute(__query)
        __result = self.cursor.fetchall()
        return list(__result)

    def create_table(self, _table_name, _items):
        """
        create table
        :param _table_name:  table name
        :param _items: Keys list , example: ['Key1', 'Key2', ...]
        :return: None
        """
        if len(_items) < 1:
            print 'Data item too short!'
            return
        __create = 'CREATE TABLE IF NOT EXISTS {} ({})'.format(_table_name, ','.join(_items))
        try:
            self.cursor.execute(__create)
            self.conn.commit()
        except Exception, err:
            print err
            self.conn.rollback()

    def __del__(self):
        self.cursor.close()
        self.conn.close()

