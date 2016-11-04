#!/usr/bin/python3
## -*- coding: utf-8 -*-

import vkapi
#import captcha

import random

class SocialMedia:
    def __init__(self, username, password):
        self.api = vkapi.VkApi(username, password, token_file='token.txt') #captcha_handler=captcha.CaptchaHandler())
        self.api.initLongpoll()
        
    def getRandomID(self):
        return random.randint(0, 10000000)
    
    def getLongpoll(self):
        return self.api.getLongpoll()
    
    def sendMessage(self, peer_id, message, attachments = ''):
        return self.api.messages.send(peer_id=peer_id, random_id=self.getRandomID(), message=message, attachments=attachments)
        
    def sendWallPost(self, message, attachments):
        return self.api.wall.post(message=message, attachments=attachments)
    
    def delWallPost(self, post_id):
        return self.api.wall.delete(post_id=post_id)
    
    def createChat(self, user_ids, title):
        return self.api.messages.createChat(user_ids=user_ids, title=title)
        
    def addFriend(self, user_id):
        return self.api.friends.add(user_id=user_id)
        
    def getUser(self, user_ids, fields='', name_case=''):
        return self.api.users.get(user_ids=user_ids, fields=fields, name_case=name_case)

    def removeChatUser(self, chat_id, user_id):
        return self.api.messages.removeChatUser(chat_id=chat_id, user_id=user_id)

    def getPlayers(self, post_id): # Сделать тут случай, если больше 1к репостов
        players_ids = list()
        return self.api.likes.getList(type='post', item_id=post_id, count=1000)
        #return self.api.wall.getReposts(item_id=post_id, count=1000)
        #return players_ids