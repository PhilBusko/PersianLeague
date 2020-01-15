"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
MEMBERS/MODELS/TABLES.py
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

from decimal import Decimal

from django.db import models
import django.contrib.auth.models as AM

import common.utility as CU
import football.models.tables as FT

import logging
prog_lg = logging.getLogger('progress')
excp_lg = logging.getLogger('exception')


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
MODEL DECLARATIONS
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


class Profile(models.Model):
    UserFK = models.OneToOneField(AM.User, on_delete=models.CASCADE)
    
    HashID = models.CharField(max_length=16)
    IP = models.CharField(max_length=16, null=True)
    Country = models.CharField(max_length=30, null=True)
    Region = models.CharField(max_length=30, null=True)
    City = models.CharField(max_length=30, null=True)
    TimeZone = models.CharField(max_length=60, null=True)
    
    FavClubFK = models.ForeignKey(FT.Club, null=True)  
    FavClubSet = models.BooleanField(default=False) 
    Slogan = models.CharField(max_length=100, null=True)   
    Icon = models.CharField(max_length=100, null=True)    
    
    Pref_FriendsRealName = models.BooleanField(default=True)
    Pref_FriendsEmail = models.BooleanField(default=True)
    BotAI = models.IntegerField(default=0)
    
    Diamonds = models.IntegerField(default=10)
    LifetimeDiamonds = models.IntegerField(default=10)
    
    def __str__(self):
        return "[Profile] : '{}'".format(self.UserFK.username)


class Relationship(models.Model):
    User1FK = models.ForeignKey(AM.User, related_name="user1", null=True)
    User2FK = models.ForeignKey(AM.User, related_name="user2", null=True)
    RelationValue = models.IntegerField(null=True)


class ChatText(models.Model):
    Type = models.CharField(max_length=20)      # GLOBAL_CHAT
    UserFK = models.ForeignKey(AM.User, on_delete=models.CASCADE)
    CreateDate = models.DateTimeField()
    ChatText = models.CharField(max_length=100, null=True)


class ChatGroup(models.Model):
    Type = models.CharField(max_length=20)      # GLOBAL_CHAT
    UserFK = models.ForeignKey(AM.User, on_delete=models.CASCADE)
    JoinDate = models.DateTimeField()



"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
END OF FILE
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""