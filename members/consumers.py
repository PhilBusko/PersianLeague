"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
MEMBERS/CONSUMERS.py    (views file for channels)
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import json
import datetime
import pytz
from collections import OrderedDict

from channels import Group
from channels.auth import http_session_user, channel_session_user, channel_session_user_from_http  

import common.utility as CU
import members.models.tables as MT

import logging
prog_lg = logging.getLogger('progress')
excp_lg = logging.getLogger('exception')


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
CHANNEL VIEWS
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


@channel_session_user_from_http
def ws_add(message):
    # Accept the connection
    message.reply_channel.send({'accept': True})
    
    # notify all users that another user has been added
    # this excludes the new user
    
    utcnow = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    data = {
        'type': 'ADD_USER',
        'userName': message.user.username,
        'createDate': utcnow.strftime(CU.FORMAT_DTSTR),
    }  
    Group('global_chat').send({'text': json.dumps(data)})
    
    # add the new user to the chat group
    
    Group('global_chat').add(message.reply_channel)
    
    try:
        group_m = MT.ChatGroup.objects.get(Type='GLOBAL_CHAT', UserFK=message.user)
        group_m.JoinDate = utcnow
        group_m.save()
    except:
        group_m, crtd = MT.ChatGroup.objects.get_or_create(
            Type='GLOBAL_CHAT', UserFK=message.user, JoinDate=utcnow)
    
    # initialize the new user's chat data
    
    chatText_dict = Channel_Reporter.GetChatText('GLOBAL_CHAT')
    chatGroup_str = Channel_Reporter.GetGroup('GLOBAL_CHAT')
    
    data = {
        'type': 'JOINED_USER',
        'chatText': chatText_dict,
        'chatGroup': chatGroup_str,
    }
    message.reply_channel.send({'text': json.dumps(data)})


@channel_session_user 
def ws_message(message):
    utcnow = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    chattext = message.content['text']
    
    # save to database
    
    chat_m, crtd = MT.ChatText.objects.get_or_create(
        Type='GLOBAL_CHAT', UserFK=message.user,
        CreateDate=utcnow, ChatText=chattext )
    
    chat_mdls = MT.ChatText.objects.filter(Type='GLOBAL_CHAT')
    if chat_mdls.count() > 40:
        MT.ChatText.objects.filter(Type='GLOBAL_CHAT'
                            ).order_by('CreateDate'
                            ).first().delete()
    
    # send message to all users in the group
    
    data = {
        'type': 'NEW_CHAT',
        'userName': message.user.username,
        'chatText': chattext,
        'createDate': utcnow.strftime(CU.FORMAT_DTSTR),
    }    
    Group('global_chat').send({'text': json.dumps(data)})


@channel_session_user 
def ws_drop(message):
    Group('global_chat').discard(message.reply_channel)
    
    MT.ChatGroup.objects.filter(Type='GLOBAL_CHAT', UserFK=message.user).delete()
    
    utcnow = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    data = {
        'type': 'DROP_USER',
        'userName': message.user.username,
        'createDate': utcnow.strftime(CU.FORMAT_DTSTR),
    }
    Group('global_chat').send({'text': json.dumps(data)})


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
LOGIC FUNCTIONS
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


class Channel_Reporter(object):    
    
    
    # get all text of the parameter type as list of dicts
    @staticmethod
    def GetChatText(p_type):
        
        chat_mdls = MT.ChatText.objects.filter(Type=p_type).order_by('CreateDate')
        
        chat_dict = []
        for chat_m in chat_mdls:
            
            newChat = OrderedDict()
            newChat['type'] = 'EXISTING_CHAT'
            newChat['userName'] = chat_m.UserFK.username
            newChat['createDate'] = chat_m.CreateDate.strftime(CU.FORMAT_DTSTR)
            newChat['chatText'] = chat_m.ChatText
            chat_dict.append(newChat)
        
        return chat_dict
    
    
    @staticmethod
    def GetGroup(p_type):
        group_mdls = MT.ChatGroup.objects.filter(Type=p_type).order_by('JoinDate')
        
        group_dict = []
        for group_m in group_mdls:
            
            user = OrderedDict()
            user['userName'] = group_m.UserFK.username
            user['joinDate'] = group_m.JoinDate.strftime(CU.FORMAT_DTSTR)
            group_dict.append(user)
        
        return group_dict





