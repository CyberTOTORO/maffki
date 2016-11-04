#!/usr/bin/python3
## -*- coding: utf-8 -*-

import mysql.connector
from mysql.connector import Error

class DataBase:
    def __init__(self):
        try:
            self.conn =  mysql.connector.connect(host='127.0.0.1', database='ivan', user='Ivan', password='72alf@14')
            self.cursor = self.conn.cursor()
        except Error as e:
            print(e)

    def doCommit(self):
        self.conn.commit()

    def getPlayerVals(self, player_id):
        val = (player_id, )
        self.cursor.execute("SELECT `score`,`money` FROM `players` WHERE `playerId` = %s" % val)
        return self.cursor.fetchone()

    def checkActiveGame(self, player_id):
        val = (player_id, )
        self.cursor.execute("SELECT `isPlay` FROM `players` WHERE `playerId` = %s" % val)
        return self.cursor.fetchone()

    def setActiveGame(self, player_id, active):
        val = (active, player_id)
        self.cursor.execute("UPDATE `players` SET `isPlay` = %s WHERE `playerId` = %s" % val)
        self.doCommit()
        return self.cursor.fetchone()

    def setPlayerScore(self, player_id, how):
        val = (how, player_id)
        self.cursor.execute("UPDATE `players` SET `score` = `score` + %s WHERE `playerId` = %s" % val)
        self.doCommit()

    def setPlayerMoney(self, player_id, how):
        val = (how, player_id)
        self.cursor.execute("UPDATE `players` SET `money` = `money` + %s WHERE `playerId` = %s" % val)
        self.doCommit()

    def getPlayerId(self, soc_name, soc_id):
        val = (soc_name, soc_id)
        self.cursor.execute("SELECT `playerId` FROM `players` WHERE %s = '%s'" % val)
        user = self.cursor.fetchone()
        if user == None:
            self.cursor.execute("SELECT `playerId` FROM `players` ORDER BY `playerId` DESC LIMIT 1")
            id = self.cursor.fetchone()
            id = id[0]+1
            val = (id, soc_id)
            query = "INSERT INTO `ivan`.`players` (`playerId`, `score`, `money`," + soc_name + ") VALUES (%s, 0, 0, %s)"
            self.cursor.execute(query, val)
            self.doCommit()
            user = (id, )

        return user

    def getVKid(self, player_id):
        val = (player_id, )
        self.cursor.execute("SELECT `vk` FROM `players` WHERE `playerId` = %s" % val)
        user = self.cursor.fetchone()
        return user