"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
FOOTBALL/MODELS/DATA_MANAGER.py
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import csv
import os

from django.conf import settings
from django.db.models import Count, F, Q, Value
from django.db.models.functions import Concat

import common.utility as CU
import football.models.tables as FT
import football.models.football as FM       # does depend on more basic functions 

import logging
prog_lg = logging.getLogger('progress')
excp_lg = logging.getLogger('exception')


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
TABLE MANAGER
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


class Manager(object):    
    
    
    @staticmethod
    def LoadCoreFiles():
        
        path = "football/static/data/Core_Season.csv"
        with open(path) as fhandle:
            reader = csv.reader(fhandle)
            next(reader)  # skip header row
            for row in reader:
                created = FT.Season.objects.get_or_create(
                    Season = row[0],
                    League = row[1],
                    TimeFrame = row[2],
                )
        
        path = "football/static/data/Core_Club.csv"
        with open(path) as fhandle:
            reader = csv.reader(fhandle)
            next(reader)  # skip header row
            for row in reader:
                created = FT.Club.objects.get_or_create(
                    Club = row[0],
                    FullName = row[1],
                    City = row[2],
                    Founded = row[3],
                )
        
        path = "football/static/data/Core_Event.csv"
        with open(path) as fhandle:
            reader = csv.reader(fhandle)
            next(reader)  # skip header row
            for row in reader:
                created = FT.Event.objects.get_or_create(
                    Type = row[0],
                    Event = row[1],
                    Score = row[2],
                    GK = row[3],
                    DF = row[4],
                    MF = row[5],
                    FW = row[6],
                    Description = row[7],
                )
        
        hret = CU.HttpReturn()
        hret.results = "Load core files complete."
        hret.status = 201
        return hret
    
    
    @staticmethod
    def ResetCoreTables():
        Editor.ResetPlayerData()
        FT.Season.objects.all().delete()
        FT.Club.objects.all().delete()
        FT.Event.objects.all().delete()
        
        hret = CU.HttpReturn()
        hret.results = "Database delete complete."
        hret.status = 201
        return hret
    
    
    @staticmethod
    def DeleteEvents(p_season):
        FT.ClubRanking.objects.filter(SeasonFK__Season=p_season).delete()
        FT.GameEvent.objects.filter(GameFK__SeasonFK__Season=p_season).delete()
        
        hret = CU.HttpReturn()
        hret.results = "Delete events complete."
        hret.status = 201
        return hret
    
    
    @staticmethod
    def DeleteGames(p_season):
        FT.ClubRanking.objects.filter(SeasonFK__Season=p_season).delete()
        FT.GameEvent.objects.filter(GameFK__SeasonFK__Season=p_season).delete()
        FT.Game.objects.filter(SeasonFK__Season=p_season).delete()
        
        hret = CU.HttpReturn()
        hret.results = "Delete games complete."
        hret.status = 201
        return hret
    
    
    @staticmethod
    def DeleteAllPlayers():
        FT.ClubRanking.objects.all().delete()
        FT.GameEvent.objects.all().delete()
        FT.Game.objects.all().delete()
        FT.PlayerInClub.objects.all().delete()
        FT.Player.objects.all().delete()
        
        hret = CU.HttpReturn()
        hret.results = "Delete all data complete."
        hret.status = 201
        return hret
    
    
    # adds goals and scorers to game entry row
    @staticmethod
    def CreatePostGameData(p_gameID):
        
        try:
            game_mdl = FT.Game.objects.select_related('ClubHomeFK', 'ClubAwayFK'
                ).get(id = p_gameID) 
        except FT.Game.DoesNotExist:
            return None
        
        prog_lg.info("Round: %s | Game ID: %s" % (game_mdl.Round, str(p_gameID)))
        
        goals = dict(
            FT.GameEvent.objects.values_list('EventClubFK__Club'
                ).filter(GameFK__id = p_gameID,
                    EventFK__Event__in = ["Goal", "Goal, Special Move", "Goal, Own", "Penalty Scored"]
                ).annotate(goal_cnt=Count('id')) )
        
        
        scorer_mdls = FT.GameEvent.objects.annotate(FirstLast=Concat('PlayerFK__FirstName', Value(' '), 'PlayerFK__LastName'))
        
        scorers = list(
            scorer_mdls.values_list(
                'EventClubFK__Club', 'FirstLast'
                ).filter(GameFK__id = p_gameID,
                    EventFK__Event__in = ["Goal", "Goal, Special Move", "Goal, Own", "Penalty Scored"]) )
        
        club_home = game_mdl.ClubHomeFK.Club
        club_away = game_mdl.ClubAwayFK.Club
        goals_home = 0
        goals_away = 0
        scorers_home = ""
        scorers_away = ""
        
        if goals.get(club_home):
            goals_home = goals.get(club_home)
        else:
            goals_home = 0
        
        if goals.get(club_away):
            goals_away = goals.get(club_away)
        else:
            goals_away = 0
        
        for scorer in scorers:
            if scorer[0] == club_home:
                scorers_home += scorer[1] + ", "
            elif scorer[0] == club_away:
                scorers_away += scorer[1] + ", "
        
        game_mdl.GoalsHome = goals_home
        game_mdl.ScorersHome = scorers_home
        game_mdl.GoalsAway = goals_away
        game_mdl.ScorersAway = scorers_away
        game_mdl.save()
    
    
    # add one row per club to ClubRanking model
    @staticmethod
    def CreateClubRanks(p_season, p_round):
        
        ranks = []
        
        # all games exist because this is after IsRoundComplete
        
        game_mdls = FT.Game.objects.select_related('ClubHomeFK', 'ClubAwayFK'
                ).filter(SeasonFK__Season=p_season, Round=p_round) 
        
        if p_round == '01':
            
            for game_m in game_mdls:
                
                if game_m.GoalsHome > game_m.GoalsAway:
                    homePnts = 3
                    awayPnts = 0
                elif game_m.GoalsHome < game_m.GoalsAway:
                    homePnts = 0
                    awayPnts = 3
                else: 
                    homePnts = 1
                    awayPnts = 1
                
                homeCRD = FT.ClubRankData()
                homeCRD.club = game_m.ClubHomeFK.Club
                homeCRD.points = homePnts
                homeCRD.goals_for = game_m.GoalsHome
                homeCRD.goals_vs = game_m.GoalsAway
                
                awayCRD = FT.ClubRankData()
                awayCRD.club = game_m.ClubAwayFK.Club
                awayCRD.points = awayPnts
                awayCRD.goals_for = game_m.GoalsAway
                awayCRD.goals_vs = game_m.GoalsHome
                
                ranks.append(homeCRD)
                ranks.append(awayCRD)
                
        else:
            prevRound = CU.Pad2(int(p_round) -1)
            
            for game_m in game_mdls:
                
                try:
                    prevHome_m = FT.ClubRanking.objects.get(SeasonFK__Season=p_season, Round=prevRound,
                                                            ClubFK__Club=game_m.ClubHomeFK.Club)
                    prevAway_m = FT.ClubRanking.objects.get(SeasonFK__Season=p_season, Round=prevRound,
                                                            ClubFK__Club=game_m.ClubAwayFK.Club)
                except:
                    excp_lg.error("Can't create club ranking for {}. Previous round is missing.".format(p_round))
                    return
                
                if game_m.GoalsHome > game_m.GoalsAway:
                    homePnts = 3
                    awayPnts = 0
                elif game_m.GoalsHome < game_m.GoalsAway:
                    homePnts = 0
                    awayPnts = 3
                else: 
                    homePnts = 1
                    awayPnts = 1
                
                homeCRD = FT.ClubRankData()
                homeCRD.club = game_m.ClubHomeFK.Club
                homeCRD.points = homePnts + prevHome_m.Points
                homeCRD.goals_for = game_m.GoalsHome + prevHome_m.GoalsFor
                homeCRD.goals_vs = game_m.GoalsAway + prevHome_m.GoalsVs
                
                awayCRD = FT.ClubRankData()
                awayCRD.club = game_m.ClubAwayFK.Club
                awayCRD.points = awayPnts + prevAway_m.Points
                awayCRD.goals_for = game_m.GoalsAway + prevAway_m.GoalsFor
                awayCRD.goals_vs = game_m.GoalsHome + prevAway_m.GoalsVs
                
                ranks.append(homeCRD)
                ranks.append(awayCRD)
            
        # sort and assign new ranks
        
        ranks = sorted(ranks, reverse=True)     # uses ClubRankData _gt_ and _lt_ to sort
        
        val = 0
        cpnts = None
        cdiff = None
        cgfor = None
        for rnk in ranks:
            if rnk.points != cpnts:
                cpnts = rnk.points
                cdiff = rnk.goals_for - rnk.goals_vs
                cgfor = rnk.goals_for
                val += 1
            elif rnk.points == cpnts and (rnk.goals_for - rnk.goals_vs) != cdiff:
                cdiff = rnk.goals_for - rnk.goals_vs
                cgfor = rnk.goals_for
                val += 1
            elif rnk.points == cpnts and (rnk.goals_for - rnk.goals_vs) == cdiff and rnk.goals_for != cgfor:
                cgfor = rnk.goals_for
                val += 1
            rnk.rank = val
        
        # insert results into ClubRanking model
        
        for rnk in ranks:
            season_m = FT.Season.objects.get(Season=p_season)
            club_m = FT.Club.objects.get(Club=rnk.club)
            
            newCRank, crtd = FT.ClubRanking.objects.get_or_create(
                SeasonFK=season_m, ClubFK=club_m, Round=p_round, 
                Rank=rnk.rank,
                Points=rnk.points, GoalsFor=rnk.goals_for, GoalsVs=rnk.goals_vs ) 


    @staticmethod
    def DeleteGameEvents(p_gameId):
        deleteCnt, deleteObjs = FT.GameEvent.objects.filter(GameFK__id=p_gameId).delete()
        
        try:
            game_mdl = FT.Game.objects.get(id=p_gameId)
            game_mdl.GoalsHome = None
            game_mdl.ScorersHome = None
            game_mdl.GoalsAway = None
            game_mdl.ScorersAway = None
            game_mdl.save()
        except FT.Game.DoesNotExist:
            ok = True
        
        results = {
            'deleted': deleteCnt,
            'season': game_mdl.SeasonFK.Season,
            'round': game_mdl.Round,
        }
        
        hret = CU.HttpReturn()
        hret.results = results
        hret.status = 201
        return hret



from django.db.models.signals import post_save
from django.dispatch import receiver
@receiver(post_save, sender=FT.GameEvent)
def TriggerPostGameData(sender, instance, **kwargs):    
    if instance.EventFK.Event == "Game End":
        gameID = instance.GameFK.id
        Manager.CreatePostGameData(gameID)
        
        season = instance.GameFK.SeasonFK.Season
        gRound = instance.GameFK.Round
        if FM.TimeMachine.GetRoundPeriod(season, gRound) == 8:
            Manager.CreateClubRanks(season, gRound)


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
CSV BACKUPS
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


class Exporter(object):    
    
    
    @staticmethod
    def ExportPlayers(p_season):
        
        expDir = os.path.join(settings.EXPORT_DIR, p_season)
        if not os.path.exists(expDir):
            os.makedirs(expDir)
        
        fileName = "PlayerInClub {0}.csv".format(p_season)
        expPath = os.path.join(expDir, fileName)
        
        player_ls = FT.PlayerInClub.objects.values_list('SeasonFK__Season', 'ClubFK__Club',
                                                          'PlayerFK__FirstName', 'PlayerFK__LastName',
                                                          'PlayerFK__Nationality', 'PlayerFK__DateOfBirth',
                                                          'PositionDef', 'ShirtNo'
                                                        ).filter(SeasonFK__Season=p_season
                                                        ).order_by('ClubFK__Club', 'PlayerFK__FirstName')
        
        with open(expPath, 'wt') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Season", "SquadClub", "FirstName", "LastName",
                             "Nationality", "DateOfBirth", "PositionDef", "ShirtNo"])
            for player_dt in player_ls.iterator():
                writer.writerow(player_dt)
        
        return expPath
    
    
    @staticmethod
    def ExportGames(p_season):
        
        expDir = os.path.join(settings.EXPORT_DIR, p_season)
        if not os.path.exists(expDir):
            os.makedirs(expDir)
        
        fileName = "Game {0}.csv".format(p_season)
        expPath = os.path.join(expDir, fileName)
        
        data_ls = FT.Game.objects.values_list('SeasonFK__Season', 'Round',
                                              'ClubHomeFK__Club', 'ClubAwayFK__Club', 'PlayDate'
                                                ).filter(SeasonFK__Season=p_season
                                                ).order_by('Round').iterator()
        
        with open(expPath, 'wt') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Season", "Round", "ClubHome", "ClubAway", "PlayDate"])
            for data_row in data_ls:
                writer.writerow(data_row)
        
        return expPath
    
    
    @staticmethod
    def ExportEvents(p_season):
        
        expDir = os.path.join(settings.EXPORT_DIR, p_season, "GameEvents")
        if not os.path.exists(expDir):
            os.makedirs(expDir)
        
        game_mdls = FT.Game.objects.filter(SeasonFK__Season=p_season).order_by('Round').iterator()
        
        for game_m in game_mdls:
            
            fileName = "GameEvent {0} {1}.csv".format(game_m.Round, game_m.ClubHomeFK.Club)
            expPath = os.path.join(expDir, fileName)
            
            data_ls = FT.GameEvent.objects.values_list('GameFK__SeasonFK__Season', 'GameFK__Round', 'GameFK__ClubHomeFK__Club',
                                                       'EventFK__Event', 'EventTime', 'EventClubFK__Club',
                                                       'PlayerFK__FirstName', 'PlayerFK__LastName', 'Position'
                                                    ).filter(GameFK=game_m
                                                    ).order_by('EventTime', 'EventFK__Event', 'EventClubFK__Club',
                                                               'Position', 'PlayerFK__FirstName')
            
            with open(expPath, 'wt') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Season", "Round", "ClubHome", "Event", "EventTime", "EventClub",
                                 "FirstName", "LastName", "Position"])
                for data_row in data_ls.iterator():     # don't call iter before this or it has to be reset
                    #excp_lg.warning(data_row)
                    writer.writerow(data_row)
        
        return 


class Importer(object):    
    
    
    @staticmethod
    def ImportPlayers(p_season):
        
        impDir = os.path.join(settings.BASE_DIR, "football/static/data/", p_season)        
        fileName = "PlayerInClub {0}.csv".format(p_season)
        inputPath = os.path.join(impDir, fileName)
        season_m = FT.Season.objects.get(Season=p_season)
        
        if not os.path.isfile(inputPath):
            hret = CU.HttpReturn()
            hret.results = "Player data file not available."
            hret.status = 401
            return hret
        
        with open(inputPath) as fhandle:
            reader = csv.reader(fhandle)
            next(reader)  # skip header row
            
            for row in reader:
                
                season = row[0]
                squadClub = row[1]
                firstName = row[2]
                lastName = row[3]
                nation = row[4]
                dob = row[5]
                posDef = row[6]
                shirt = row[7]
                
                player_m, created = FT.Player.objects.get_or_create(
                    FirstName = firstName, LastName = lastName,
                    Nationality = nation, DateOfBirth = dob,
                )
                
                # insert player squad data 
                
                club_m = FT.Club.objects.get(Club=squadClub)
                plClub_m, created = FT.PlayerInClub.objects.get_or_create(
                    SeasonFK = season_m, ClubFK = club_m,
                    PlayerFK = player_m, PositionDef = posDef, ShirtNo = shirt, 
                )
        
        hret = CU.HttpReturn()
        hret.results = "ImportPlayers complete."
        hret.status = 201
        return hret
    
    
    @staticmethod
    def ImportGames(p_season, p_rndStart=None, p_rndEnd=None):
        
        impDir = os.path.join(settings.BASE_DIR, "football/static/data/", p_season)        
        fileName = "Game {0}.csv".format(p_season)
        inputPath = os.path.join(impDir, fileName)
        season_m = FT.Season.objects.get(Season=p_season)
        
        with open(inputPath) as fhandle:
            reader = csv.reader(fhandle)
            next(reader)  # skip header row
            
            for row in reader:
                
                season = row[0]
                roundv = row[1]
                clubHome = row[2]
                clubAway = row[3]
                playDate = row[4]
                
                if p_rndStart and ( int(roundv) < int(p_rndStart) or int(roundv) > int(p_rndEnd) ):
                    continue
                
                try:
                    clubHome_m = FT.Club.objects.get(Club=clubHome)
                    clubAway_m = FT.Club.objects.get(Club=clubAway)
                    playDate_dt = CU.TZStringToDT(playDate)
                except:
                    msg = "bad data: {}, {}, {}".format(clubHome, clubAway, playDate)
                    CU.excp_lg.error(msg)
                
                game_m, created = FT.Game.objects.get_or_create(
                    SeasonFK=season_m, Round=roundv,
                    ClubHomeFK=clubHome_m, ClubAwayFK=clubAway_m, PlayDate=playDate_dt
                )
        
        hret = CU.HttpReturn()
        hret.results = "ImportGames complete."
        hret.status = 201
        return hret
    
    
    @staticmethod
    def ImportEvents(p_season, p_rndStart=None, p_rndEnd=None):
        
        impDir = os.path.join(settings.BASE_DIR, "football/static/data/", p_season, "GameEvents")
        from os import walk
        fileNames = []
        for (impDir, dirnames, filenames) in walk(impDir):
            fileNames.extend(filenames)
            break
        
        season_m = FT.Season.objects.get(Season=p_season)
        fileNames = sorted(fileNames)
        
        for fName in fileNames:
            inputPath = os.path.join(impDir, fName)
            
            with open(inputPath) as fhandle:
                reader = csv.reader(fhandle)
                next(reader)    # skip header row
                
                for row in reader:
                    
                    season = row[0]
                    roundv = row[1]
                    clubHome = row[2]
                    event = row[3]
                    eventTime = row[4]
                    eventClub = row[5]
                    firstName = row[6]
                    lastName = row[7]
                    pos = row[8]
                    
                    if p_rndStart and ( int(roundv) < int(p_rndStart) or int(roundv) > int(p_rndEnd) ):
                        continue
                    
                    clubHome_m = FT.Club.objects.get(Club=clubHome)
                    game_m = FT.Game.objects.get(SeasonFK=season_m, Round=roundv, ClubHomeFK=clubHome_m)
                    event_m = FT.Event.objects.get(Event=event)
                    eventClub_m = FT.Club.objects.get(Club=eventClub)   if eventClub   else None
                    player_m = FT.Player.objects.get(FirstName=firstName, LastName=lastName)   if firstName   else None
                    
                    event_m, created = FT.GameEvent.objects.get_or_create(
                                                    GameFK=game_m, EventFK=event_m, EventTime=eventTime,
                                                    EventClubFK=eventClub_m, PlayerFK=player_m, Position=pos )
                    
        hret = CU.HttpReturn()
        hret.results = "ImportGames complete."
        hret.status = 201
        return hret
    
    
    @staticmethod
    def ImportSingleEvents(p_gameid):
        game_dx = FM.Reports_Game.GameToDictByID(p_gameid)
        season = game_dx['season']
        fileName = "GameEvent {0} {1}.csv".format(game_dx['round'], game_dx['home_club'])
        season_m = FT.Season.objects.get(Season=season)
        impDir = os.path.join(settings.BASE_DIR, "football/static/data/", season, "GameEvents")
        inputPath = os.path.join(impDir, fileName)
        
        if os.path.isfile(inputPath):
            with open(inputPath) as fhandle:
                reader = csv.reader(fhandle)
                next(reader)    # skip header row
                
                for row in reader:
                    
                    season = row[0]
                    roundv = row[1]
                    clubHome = row[2]
                    event = row[3]
                    eventTime = row[4]
                    eventClub = row[5]
                    firstName = row[6]
                    lastName = row[7]
                    pos = row[8]
                    
                    clubHome_m = FT.Club.objects.get(Club=clubHome)
                    game_m = FT.Game.objects.get(SeasonFK=season_m, Round=roundv, ClubHomeFK=clubHome_m)
                    event_m = FT.Event.objects.get(Event=event)
                    eventClub_m = FT.Club.objects.get(Club=eventClub)   if eventClub   else None
                    player_m = FT.Player.objects.get(FirstName=firstName, LastName=lastName)   if firstName   else None
                    
                    event_m, created = FT.GameEvent.objects.get_or_create(
                                                    GameFK=game_m, EventFK=event_m, EventTime=eventTime,
                                                    EventClubFK=eventClub_m, PlayerFK=player_m, Position=pos )
        
        hret = CU.HttpReturn()
        hret.results = "ImportSingleEvents complete."
        hret.status = 201
        return hret






"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
END OF FILE
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""