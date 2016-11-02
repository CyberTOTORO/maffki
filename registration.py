#!/usr/bin/python3
## -*- coding: utf-8 -*-

import time
import random
import json
import threading

import connect
import database
import gameloop

CONF_START = 2000000000
    
class MafiaBot:
    def __init__(self, username, password):
        self.api = connect.SocialMedia(username, password)
        self.username = username
        self.password = password
        self.players_setting = False
        self.commands = json.loads(open('data/text.json', encoding='utf-8').read())
        self.roles = open('data/roles.txt', 'r').read().splitlines()
        self.db = database.DataBase()
        
        #self.urban = tuple('citizen', 'commis', 'bum', 'sergeant', 'putana', 'doctor', 'sheriff')
        #self.mafia = tuple('mafia', 'lawyer', 'killer', 'mafiaboss')
        #self.crazy = tuple('maniac', 'robber')


    def gameCall(self, timer): # Check of the call starter
        event = self.api.getLongpoll()
        for i in event:
            if i[0] == 4:  # new message
                sender = i[3]
                text = str(i[6])
                flags = i[2]

                if flags & 2:  # outcoming message
                    continue

                if sender > CONF_START:
                    continue
                
                if text[:5].lower() == 'старт':
                    if not self.players_setting: # Do a thread
                        self.postRegistration(timer, sender) # First num it's num for sleep
                    elif self.players_setting: # Game already started
                        self.api.sendMessage(peer_id=sender, message=self.commands['reg_already'])
    
    def postRegistration(self, sleep, sender): # Publish the post for registration
        print('The registration post published at ', time.asctime())
        self.players_setting = True
        post_id = self.api.sendWallPost(message=self.commands['wall_txt_start'], attachments=self.commands['wall_att_start'])
        post_id = post_id['post_id']
        self.api.sendMessage(peer_id=sender, message=self.commands['success_start'], attachments='')
        self.api.sendMessage(peer_id=sender, message=self.commands['friend_share']+str(post_id), attachments='')
        time.sleep(sleep)
        reposters = self.api.getPlayers(post_id)
        ready = reposters['count']
        if ready > 1:
            self.checkPlayers(post_id)
        else:
            self.api.delWallPost(post_id=post_id)
            self.players_setting = False
            
    def checkPlayers(self, post_id):
        reposters = self.api.getPlayers(post_id)
        self.api.delWallPost(post_id)
        self.players_setting = False
        ready = 0
        player_ids = dict()
        user_ids = list(map(str, reposters['items']))
        user_ids = ','.join(user_ids)
        users_info = self.api.getUser(user_ids=user_ids, fields='friend_status,can_write_private_message')

        for i in range(len(users_info)): 
            if users_info[i]['friend_status'] < 2:
                if users_info[i]['can_write_private_message'] == 1:
                    self.api.sendMessage(peer_id=users_info[i]['id'], message=self.commands['cant_play'])
            else:
                if users_info[i]['friend_status'] == 2: # Here can be case with 10k friends
                    self.api.addFriend(users_info[i]['id'])
                id = self.db.getPlayerId('vk', users_info[i]['id'])
                id = id[0]
                if not self.db.checkActiveGame(id)[0]:
                    self.db.setActiveGame(id, 'TRUE')
                    player_ids = self.userReg(player_ids, i, id)
                    ready += 1

        if ready > 1:
            self.setRoles(player_ids)
        else:
            self.api.sendWallPost(message=self.commands['unbegun_text'], attachments=self.commands['unbegun_attach'])

    def userReg(self, player_ids, num, id):
        player_ids[num] = dict()
        player_ids[num]['id'] = id
        player_ids[num]['role'] = 'citizen'
        player_ids[num]['dead'] = False
        return player_ids
     
    def setRoles(self, player_ids):
        for elem in range(len(player_ids)):
            numb = random.choice(list(player_ids))
            while not player_ids[numb]['role'] == 'citizen':
                numb = random.choice(list(player_ids))
            player_ids[numb]['role'] = self.roles[elem]
        games = gameloop.Game(player_ids, self.username, self.password)




def main():
    a = MafiaBot('l', 'p')
    while True:
        a.gameCall(70)
    
if __name__ == '__main__':
    main()
