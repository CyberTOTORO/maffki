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
        self.db = database.DataBase()
        self.urbans = ['citizen', 'commis', 'bum', 'sergeant', 'putana', 'doctor', 'sheriff']
        self.mafias = ['mafia', 'maniac', 'lawyer', 'killer', 'mafiaboss']
        self.gameProcess(player_ids)
        #self.crazies = ('robber', )

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
        mafia_room = self.api.createChat(user_ids=','.join(self.getEverybodyList(player_ids)), title=self.commands['mafia_room'])
        general_room += CONF_START
        mafia_room += CONF_START
        self.greetingDay(player_ids, general_room, mafia_room)
        day = 0
        while self.checkManyRoles(player_ids):
            player_ids = self.gameNight(player_ids, day, general_room, mafia_room)
            if self.checkManyRoles(player_ids):
                player_ids = self.gameDay(player_ids, day, general_room, mafia_room)

        self.callFinishGame(general_room, player_ids)

    def checkManyRoles(self, player_ids):
        others = 0
        mafias = 0
        for elem in player_ids:
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

    def confDel(self, id, conf):
        try:
            self.api.removeChatUser(chat_id=conf, user_id=id)
        except:
            pass

    def gameDay(self, player_ids, day, general_room, mafia_room):  # Game loop. Time: DAY
        vote = ""  # Who access for vote
        for elem in player_ids:
            if not player_ids[elem]['dead']:
                player_ids[elem]['votes'] = 0
                player_ids[elem]['voted'] = False
                player_ids[elem]['who'] = 0
                name_last = self.api.getUser(user_ids=self.db.getVKid(player_ids[elem]['id'])[0])
                vote += '<br>' + str(elem+1) + '.' + name_last[0]['first_name'] + ' ' + name_last[0]['last_name']

        daily_text = 'День ' + str(day) + '-ый' + self.commands['day_general'] + vote
        self.api.sendMessage(peer_id=general_room, message=daily_text)

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
                            for elem in player_ids:
                                if str(self.db.getVKid(player_ids[elem]['id'])[0]) == str(opt['from']):
                                    id = elem
                            arrest = int(number[1])-1
                            if not player_ids[id]['dead'] and not player_ids[id]['voted']:
                                if not player_ids[arrest]['dead']:
                                    player_ids[id]['voted'] = True
                                    player_ids[id]['who'] = arrest
                                    player_ids[arrest]['votes'] += 1
                                    success_vote = self.commands['success_vote'] + str(arrest+1)
                                    self.api.sendMessage(peer_id=general_room, message=success_vote)
                        except:
                            pass

        # Finished time:

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
            name_last = self.api.getUser(user_ids=loser_id, name_case='acc')
            name = name_last[0]['first_name'] + ' ' + name_last[0]['last_name']
            self.api.sendMessage(peer_id=general_room, message=self.commands['success_arrest'] + name)
            player_ids[loser_num]['dead'] = True
            self.confDel(loser_id, general_room - CONF_START)
            self.confDel(loser_id, mafia_room - CONF_START)
        else:
            self.api.sendMessage(peer_id=general_room, message=self.commands['unsuccess_arrest'])

        return player_ids

    def gameNight(self, player_ids, day, general_room, mafia_room):  # Game loop. Time: DAY
        vote = ""  # Who access for vote
        for elem in player_ids:
            if not player_ids[elem]['dead']:
                player_ids[elem]['votes'] = 0
                player_ids[elem]['voted'] = False
                player_ids[elem]['who'] = 0
                name_last = self.api.getUser(user_ids=self.db.getVKid(player_ids[elem]['id'])[0])
                vote += '<br>' + str(elem + 1) + '.' + name_last[0]['first_name'] + ' ' + name_last[0]['last_name']

        for elem in player_ids:
            if not player_ids[elem]['dead']:
                role = player_ids[elem]['role'] + '_night'
                try:
                    self.api.sendMessage(peer_id=self.db.getVKid(player_ids[elem]['id'])[0], message=self.commands[role] + vote)
                except:
                    pass

        self.api.sendMessage(peer_id=mafia_room, message=self.commands['night_mafia'] + vote)
        commis = {'num':-1, 'id':-1, 'victim_num':-1, 'victim_id':-1}
        maniac = {'num':-1, 'id':-1, 'victim_num':-1, 'victim_id':-1}
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

                    if sender == mafia_room: # Mafias vote
                        if text[:5].lower() == 'убить':
                            id = ''
                            number = text.split(' ')
                            arrest = int(number[1]) - 1
                            for elem in player_ids:
                                if str(self.db.getVKid(player_ids[elem]['id'])[0]) == str(opt['from']):
                                    id = elem
                                    if not player_ids[id]['dead'] and not player_ids[id]['voted']:
                                        if not player_ids[arrest]['dead'] and not player_ids[arrest]['role'] == 'mafia':
                                            player_ids[id]['voted'] = True
                                            player_ids[arrest]['votes'] += 1
                                            player_ids[id]['who'] = arrest
                                            success_vote = self.commands['success_vote'] + str(arrest + 1)
                                            self.api.sendMessage(peer_id=mafia_room, message=success_vote)
                                            break

                    if text[:5].lower() == 'убить': # Maniac
                        maniac['id'] = self.db.getPlayerId('vk', sender)[0]
                        print(maniac['id'])
                        for elem in player_ids:
                            if player_ids[elem]['id'] == maniac['id'] and player_ids[elem]['role'] == 'maniac':
                                if not player_ids[elem]['dead'] and not player_ids[elem]['voted']:
                                    maniac['id'] = sender
                                    maniac['num'] = elem
                                    number = text.split(' ')
                                    number[1] = int(number[1]) - 1
                                    if not player_ids[number[1]]['dead']:
                                        player_ids[elem]['voted'] = True
                                        maniac['victim_num'] = number[1]
                                        maniac['victim_id'] = self.db.getVKid(player_ids[number[1]]['id'])[0]
                                        self.api.sendMessage(peer_id=maniac['id'], message=self.commands['success_chose'])

                    if text[:9].lower() == 'проверить': # Commis
                        commis['id'] = self.db.getPlayerId('vk', sender)[0]
                        for elem in player_ids:
                            if player_ids[elem]['id'] == commis['id'] and player_ids[elem]['role'] == 'commis':
                                if not player_ids[elem]['dead'] and not player_ids[elem]['voted']:
                                    commis['id'] = sender
                                    commis['num'] = elem
                                    number = text.split(' ')
                                    number[1] = int(number[1]) - 1
                                    if not player_ids[number[1]]['dead']:
                                        player_ids[elem]['voted'] = True
                                        commis['victim_num'] = number[1]
                                        commis['victim_id'] = self.db.getVKid(player_ids[number[1]]['id'])[0]
                                        self.api.sendMessage(peer_id=commis['id'], message=self.commands['success_check'])

        # Finished time
        if not commis['id'] == -1 and not commis['victim_id'] == -1: # Answer to commis
            name_resp = self.api.getUser(user_ids=commis['victim_id'], fields='sex', name_case='nom')
            name = name_resp[0]['first_name'] + ' ' + name_resp[0]['last_name']
            if player_ids[commis['victim_num']]['role'] in self.urbans:
                text = self.commands['commis_message'] + name + self.commands['commis_urban']
                self.api.sendMessage(peer_id=general_room, message=text)
            elif player_ids[commis['victim_num']]['role'] in self.mafias:
                text = self.commands['commis_message'] + name
                if name_resp[0]['sex'] == 1:
                    text += self.commands['commis_mafia_f']
                else:
                    text += self.commands['commis_mafia_m']
                text += self.commands[player_ids[commis['victim_num']]['role'] + '_ins']
                self.api.sendMessage(peer_id=general_room, message=text)

            try:
                post = name + ' играет за ' + self.commands[player_ids[commis['victim_num']]['role'] + '_acc']
                self.api.sendMessage(peer_id=self.db.getVKid(commis['id'])[0], message=self.commands[post])
            except:
                pass

        if not maniac['id'] == -1 and  not maniac['victim_id'] == -1: # Answer to maniac
            player_ids[maniac['victim_num']]['dead'] = True # Add check to save with items
            maniac['victim_id'] = self.db.getVKid(player_ids[maniac['victim_num']]['id'])[0]
            name_resp = self.api.getUser(user_ids=maniac['victim_id'], fields='sex', name_case='gen')
            name = name_resp[0]['first_name'] + ' ' + name_resp[0]['last_name']
            if name_resp[0]['sex'] == 1:
                text = self.commands['maniac_kill'] + name + '<br>' + 'Она оказалась ' + self.commands[player_ids[maniac['victim_num']]['role'] + '_ins']
                self.api.sendMessage(peer_id=general_room, message=text)
            else:
                text = self.commands['maniac_kill'] + name + '<br>' + 'Он оказался ' + self.commands[player_ids[maniac['victim_num']]['role'] + '_ins']
                self.api.sendMessage(peer_id=general_room, message=text)
        else:
            print('Маньяк не ходил')


        max_vote = 0
        loser_num = -1
        loser_id = ''
        loser_role = ''
        count = 0
        for elem in player_ids:
            if player_ids[elem]['votes'] > max_vote:
                loser_num = elem
                loser_role = player_ids[elem]['role']
                loser_id = player_ids[elem]['id']
                max_vote = player_ids[elem]['votes']
                count = 0
            if player_ids[elem]['votes'] == max_vote:
                count += 1

        if count == 1 and not loser_num == -1:
            if maniac['victim_num'] ==  loser_num:
                self.api.sendMessage(peer_id=general_room, message=self.commands['maniac_mafia'])
            loser_id = self.db.getVKid(loser_id)[0]
            name_resp = self.api.getUser(user_ids=loser_id, fields='sex', name_case='nom')
            name = name_resp[0]['first_name'] + ' ' + name_resp[0]['last_name']
            player_ids[loser_num]['dead'] = True
            if name_resp[0]['sex'] == 1:
                text = self.commands['mafia_kill_f'] + name + '<br>' + 'Она оказалась ' + self.commands[loser_role + '_ins']
                self.api.sendMessage(peer_id=general_room, message=text)
            else:
                text = self.commands['mafia_kill_m'] + name + '<br>' + 'Он оказался ' + self.commands[loser_role + '_ins']
                self.api.sendMessage(peer_id=general_room, message=text)

            self.confDel(loser_id, general_room - CONF_START)
            self.confDel(loser_id, mafia_room - CONF_START)
        else:
            self.api.sendMessage(peer_id=general_room, message=self.commands['unsuccess_kill'])

        self.confDel(maniac['victim_id'], general_room - CONF_START)
        self.confDel(maniac['victim_id'], mafia_room - CONF_START)
        return player_ids

    def useItem(self, player_id):
        social_id = self.db.getPlayerId('vk', player_id)[0]