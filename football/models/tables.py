"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
FOOTBALL/MODELS/TABLES.py
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

from django.db import models

import common.utility as CU

import logging
prog_lg = logging.getLogger('progress')
excp_lg = logging.getLogger('exception')


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
FOOTBALL MODELS
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


class Season(models.Model):
    Season = models.CharField(max_length=30)
    League = models.CharField(max_length=30)
    TimeFrame = models.CharField(max_length=30)
    def __str__(self):              
        return self.Season

class Club(models.Model):
    Club = models.CharField(max_length=30)
    FullName = models.CharField(max_length=50)
    City = models.CharField(max_length=30)
    Founded = models.CharField(max_length=10)
    def __str__(self):              
        return self.Club

class Event(models.Model):
    Type = models.CharField(max_length=30)
    Event = models.CharField(max_length=30)
    Score = models.IntegerField(null=True)
    GK = models.IntegerField(null=True)
    DF = models.IntegerField(null=True)
    MF = models.IntegerField(null=True)
    FW = models.IntegerField(null=True)
    Description = models.CharField(max_length=100, null=True)
    def __str__(self):              
        return self.Event

class Player(models.Model):
    FirstName = models.CharField(max_length=30)
    LastName = models.CharField(max_length=30)
    Nationality = models.CharField(max_length=30)
    DateOfBirth = models.DateField()
    ProfilePhoto = models.CharField(max_length=30, default="_profile.jpg")
    def __str__(self):
        return "PL-> " + self.FirstLast
    def save( self, *args, **kw ):
        self.FirstLast = '{0} {1}'.format( self.FirstName, self.LastName )
        self.LastFirst = '{0} {1}'.format( self.LastName, self.FirstName )
        super( Player, self ).save( *args, **kw )


class PlayerInClub(models.Model):
    SeasonFK = models.ForeignKey(Season)
    ClubFK = models.ForeignKey(Club)
    PlayerFK = models.ForeignKey(Player)
    PositionDef = models.CharField(max_length=10)   # choices=POSITION postgres doesn't map enum field
    ShirtNo = models.CharField(max_length=10)
    def __str__(self):              
        return "%s, %s, %s" % (self.Season, self.Club, self.Player) 

class Game(models.Model):
    # basic data
    SeasonFK = models.ForeignKey(Season)
    Round = models.CharField(max_length=10)
    ClubHomeFK = models.ForeignKey(Club, related_name='club_home', null=True)
    ClubAwayFK = models.ForeignKey(Club, related_name='club_away', null=True)
    PlayDate = models.DateTimeField()
    # post-game data
    GoalsHome = models.IntegerField(null=True)  
    GoalsAway = models.IntegerField(null=True)  
    ScorersHome = models.CharField(max_length=200, null=True)
    ScorersAway = models.CharField(max_length=200, null=True)
    
    def __str__(self):              
        return "R%s : %s vs %s" % (self.Round, self.ClubHomeFK.Club, self.ClubAwayFK.Club)
    def __repr__(self):
        return self.__str__()
    
    class Meta:
        unique_together = ('SeasonFK', 'Round', 'ClubHomeFK')
    
class GameEvent(models.Model):
    GameFK = models.ForeignKey(Game)
    EventFK = models.ForeignKey(Event)
    EventTime = models.TimeField()
    EventClubFK = models.ForeignKey(Club, null=True)
    PlayerFK = models.ForeignKey(Player, null=True)
    Position = models.CharField(max_length=10, null=True)
    def __str__(self):              
        return "GameEvent: G{} {}".format(self.GameFK.id, self.EventFK.Event)
    def __repr__(self):
        return self.__str__()


class ClubRanking(models.Model):
    SeasonFK = models.ForeignKey(Season)
    ClubFK = models.ForeignKey(Club)
    Round = models.CharField(max_length=10)
    
    Rank = models.IntegerField(null=True)
    Points = models.IntegerField(null=True)
    GoalsFor = models.IntegerField(null=True)
    GoalsVs = models.IntegerField(null=True)


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
BASE CLASSES
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


class ClubRankData:
    def __init__(self):
        self.club = None
        self.season = None
        self.round = None
        self.rank = 0
        self.points = 0
        self.goals_for = 0
        self.goals_vs = 0
        self.goals_diff = 0
    def __str__(self):
        return "['{}' P{} G{} D{}]".format(
            self.club, self.points, self.goals_for, self.goals_diff)
    def __repr__(self):
        return self.__str__()
    def __gt__(self, other):
        if self.points > other.points:
            return True
        if self.points == other.points and \
            (self.goals_for - self.goals_vs) > (other.goals_for - other.goals_vs):
            return True
        if self.points == other.points and \
            (self.goals_for - self.goals_vs) == (other.goals_for - other.goals_vs) and \
            self.goals_for > other.goals_for :
            return True
        return False
    def __lt__(self, other):
        if self.points < other.points:
            return True
        if self.points == other.points and \
            (self.goals_for - self.goals_vs) < (other.goals_for - other.goals_vs):
            return True
        if self.points == other.points and \
            (self.goals_for - self.goals_vs) == (other.goals_for - other.goals_vs) and \
            self.goals_for < other.goals_for :
            return True
        return False






"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
END OF FILE
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""