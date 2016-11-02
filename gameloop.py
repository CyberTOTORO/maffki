#!/usr/bin/python3
## -*- coding: utf-8 -*-

import database
import time
import json
import connect

CONF_START = 2000000000

class Game:
    def __init__(self, player_ids, username, password):
        self.api = connect.SocialMedia(username, password)
        self.player_ids = player_ids
        self.commands = json.loads(open('data/text.json', encoding='utf-8').read())
        self.roles = open('data/roles.txt', 'r').read().splitlines()
        self.db = database.DataBase()
        self.gameProcess(player_ids)

    def greetingDay(self, player_ids, general_room, mafia_room):
        for elem in player_ids:  # Here send to everybody they are roles
            try:
                id = str(self.db.getVKid(player_ids[elem]['id'])[0])
            except:
                break
            try:
                role = player_ids[elem]['role']
                role += '_text'
                self.api.sendMessage(peer_id=id,  message=self.commands[role])
            except:
                pass

        self.api.sendMessage(peer_id=general_room, message=self.commands['first_day_general'])
        self.api.sendMessage(peer_id=mafia_room, message=self.commands['first_day_mafia'])
        time.sleep(15)

    def gameProcess(self, player_ids):  # TODO: Do not create always chats
        general_room = self.api.createChat(user_ids=','.join(self.getEverybodyList(player_ids)), title=self.commands['general_room'])
        mafia_room = self.api.createChat(user_ids=','.join(self.getMafiaList(player_ids)), title=self.commands['mafia_room'])
        general_room += CONF_START
        mafia_room += CONF_START
        self.greetingDay(player_ids, general_room, mafia_room)
        day = 1
        while self.checkManyRoles(player_ids):
            player_ids = self.gameDay(player_ids, day, general_room, mafia_room)
            if self.checkManyRoles(player_ids):
                player_ids = self.gameNight(player_ids, day, general_room, mafia_room)

        self.callFinishGame(general_room, player_ids)


    def checkManyRoles(self, player_ids):
        others = 0
        mafias = 0
        for elem in range(len(player_ids)):
            if not player_ids[elem]['dead']:
                if player_ids[elem]['role'] == 'mafia':
                    mafias += 1
                else:
                    others += 1
        if mafias and others:
            return True
        else:
            return False


    def getMafiaList(self, player_ids):
        mafia_list = list()
        for elem in player_ids:
            if player_ids[elem]['role'] == 'mafia':
                mafia_list.append(str(self.db.getVKid(int(player_ids[elem]['id']))[0]))
        return mafia_list


    def getEverybodyList(self, player_ids):
        everybody_list = list()
        for elem in player_ids:
            everybody_list.append(str(self.db.getVKid(int(player_ids[elem]['id']))[0]))
        return everybody_list


    def callFinishGame(self, general_room, player_ids):
        for elem in range(len(player_ids)):
            id = str(self.db.getVKid(player_ids[elem]['id'])[0])
            self.api.sendMessage(peer_id=id, message=self.commands['finish'])  # CHECK
            self.db.setActiveGame(player_id=player_ids[elem]['id'], active='FALSE')


    def gameDay(self, player_ids, day, general_room, mafia_room):  # Game loop. Time: DAY
        vote = ""  # Who access for vote
        for elem in player_ids:
            if not player_ids[elem]['dead']:
                player_ids[elem]['votes'] = 0
                player_ids[elem]['voted'] = False
                name_last = self.api.getUser(user_ids=self.db.getVKid(player_ids[elem]['id'])[0])
                vote += '<br>' + str(elem+1) + '.' + name_last[0]['first_name'] + ' ' + name_last[0]['last_name']

        self.api.sendMessage(peer_id=general_room, message=self.commands['day_general'] + vote)

        start = time.time()
        while time.time() - start < 60:
            event = self.api.getLongpoll()
            for i in event:
                if i[0] == 4:  # new message
                    sender = i[3]
                    text = str(i[6])
                    opt = i[7]
                    flags = i[2]

                    if flags & 2:
                        continue

                    if sender == general_room:  # our room event
                        try:
                            id = ''
                            number = ''
                            if text[:8].lower() == 'посадить':
                                number = text.split(' ')
                            for elem in range(len(player_ids)):
                                if str(self.db.getVKid(player_ids[elem]['id'])[0]) == str(opt['from']):
                                    id = elem
                            arrest = int(number[1])-1
                            if not player_ids[id]['dead'] and not player_ids[id]['voted']:
                                if not player_ids[arrest]['dead']:
                                    player_ids[id]['voted'] = True
                                    player_ids[arrest]['votes'] += 1
                                    success_vote = self.commands['success_vote'] + str(arrest+1)
                                    self.api.sendMessage(peer_id=general_room, message=success_vote)
                        except:
                            pass

        max_vote = 0
        loser_num = 0
        loser_id = ""
        count = 0
        for elem in player_ids:
            if player_ids[elem]['votes'] > max_vote:
                loser_num = elem
                loser_id = player_ids[elem]['id']
                max_vote = player_ids[elem]['votes']
                count = 0
            if player_ids[elem]['votes'] == max_vote:
                count += 1

        if count == 1:
            loser_id = self.db.getVKid(loser_id)[0]
            name_last = self.api.getUser(user_ids=loser_id)
            name = name_last[0]['first_name'] + ' ' + name_last[0]['last_name']
            self.api.sendMessage(peer_id=general_room, message=self.commands['success_arrest'] + name)

            player_ids[loser_num]['dead'] = True
            self.api.removeChatUser(chat_id=general_room - CONF_START, user_id=loser_id)
            self.api.removeChatUser(chat_id=mafia_room - CONF_START, user_id=loser_id)
        else:
            self.api.sendMessage(peer_id=general_room, message=self.commands['unsuccess_arrest'])

        return player_ids

    def gameNight(self, player_ids, day, general_room, mafia_room):  # Game loop. Time: DAY
        vote = ""  # Who access for vote
        for elem in player_ids:
            if not player_ids[elem]['dead']:
                player_ids[elem]['votes'] = 0
                player_ids[elem]['voted'] = False
                name_last = self.api.getUser(user_ids=self.db.getVKid(player_ids[elem]['id'])[0])
                vote += '<br>' + str(elem + 1) + '.' + name_last[0]['first_name'] + ' ' + name_last[0]['last_name']

        for elem in player_ids:
            role = player_ids[elem]['role'] + '_night'
            try:
                self.api.sendMessage(peer_id=self.db.getVKid(player_ids[elem]['id'])[0], message=self.commands[role] + vote)
            except:
                pass

        self.api.sendMessage(peer_id=mafia_room, message=self.commands['night_mafia'] + vote)
        commis_check = ''
        commis_id = ''
        start = time.time()
        while time.time() - start < 60: # Game loop
            event = self.api.getLongpoll()
            for i in event:
                if i[0] == 4:  # new message
                    sender = i[3]
                    text = str(i[6])
                    opt = i[7]
                    flags = i[2]

                    if flags & 2:
                        continue

                    if text[:5].lower() == 'убить':
                        if sender == mafia_room:
                            id = ''
                            number = text.split(' ')
                            arrest = int(number[1]) - 1
                            for elem in range(len(player_ids)):
                                if str(self.db.getVKid(player_ids[elem]['id'])[0]) == str(opt['from']):
                                    id = elem
                            try:
                                if not player_ids[id]['dead'] and not player_ids[id]['voted']:
                                    if not player_ids[arrest]['dead'] and not player_ids[arrest]['role'] == 'mafia':
                                        player_ids[id]['voted'] = True
                                        player_ids[arrest]['votes'] += 1
                                        success_vote = self.commands['success_vote'] + str(arrest + 1)
                                        self.api.sendMessage(peer_id=mafia_room, message=success_vote)
                            except:
                                pass


                    if text[:9].lower() == 'проверить':
                        id = self.db.getVKid(sender)[0]
                        for elem in player_ids:
                            if player_ids[elem]['id'] == id and player_ids[elem]['role'] == 'commis':
                                commis_id = self.db.getVKid(id)[0]
                                try:
                                    number = text.split(' ')
                                    if not player_ids[number[1]]['dead']:
                                        commis_check = player_ids[number[1]]['role']
                                except:
                                    pass
        # Finished time

        self.api.sendMessage(peer_id=commis_id, message=self.commands[commis_check]) # Answer to commis


        max_vote = 0
        loser_num = 0
        loser_id = ""
        count = 0
        for elem in player_ids:
            if player_ids[elem]['votes'] > max_vote:
                loser_num = elem
                loser_id = player_ids[elem]['id']
                max_vote = player_ids[elem]['votes']
                count = 0
            if player_ids[elem]['votes'] == max_vote:
                count += 1

        if count == 1:
            loser_id = self.db.getVKid(loser_id)[0]
            name_last = self.api.getUser(user_ids=loser_id)
            name = name_last[0]['first_name'] + ' ' + name_last[0]['last_name']
            self.api.sendMessage(peer_id=general_room, message=self.commands['success_arrest'] + name)
            player_ids[loser_num]['dead'] = True
            self.api.removeChatUser(chat_id=general_room - CONF_START, user_id=loser_id)
            self.api.removeChatUser(chat_id=mafia_room - CONF_START, user_id=loser_id)
        else:
            self.api.sendMessage(peer_id=general_room, message=self.commands['unsuccess_arrest'])

        return player_ids

"""
 if sender == mafia_room:  # our room event
                        try:
                            id = ''
                            number = ''
                            if text[:5].lower() == 'убить':
                                number = text.split(' ')
                            for elem in range(len(player_ids)):
                                if str(self.db.getVKid(player_ids[elem]['id'])[0]) == str(opt['from']):
                                    id = elem
                            arrest = int(number[1]) - 1
                            if not player_ids[id]['dead'] and not player_ids[id]['voted']:
                                if not player_ids[arrest]['dead'] and not player_ids[arrest]['role'] == 'mafia':
                                    player_ids[id]['voted'] = True
                                    player_ids[arrest]['votes'] += 1
                                    success_vote = self.commands['success_vote'] + str(arrest + 1)
                                    self.api.sendMessage(peer_id=mafia_room, message=success_vote)
                        except:
                            pass
"""