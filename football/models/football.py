"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
FOOTBALL/MODELS/FOOTBALL.py
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import operator
import datetime 
import pytz 
import time
from collections import OrderedDict

from django.db.models import Count, F, Q, Value
from django.db.models.functions import Concat
from django.utils.timezone import localtime

import common.utility as CU
import football.models.tables as FT

import logging
prog_lg = logging.getLogger('progress')
excp_lg = logging.getLogger('exception')


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
GENERAL REPORTS
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


class Reports_General(object):
    
    
    @staticmethod
    def GetSeasons():
        qset = FT.Season.objects.values_list('Season', flat=True
                       ).order_by('-Season')
        if not qset:
            return "Seasons not available."
        return list(qset)
    
    
    @staticmethod
    def GetRounds(p_season, p_filter=""):
        
        if p_filter == 'lastData':
            qset = FT.Game.objects.values_list('Round', flat=True
                ).distinct(
                ).filter(SeasonFK__Season=p_season
                ).exclude(GoalsHome__isnull=True
                ).order_by('-Round')
        
        elif p_filter == 'today':
            today = TimeMachine.GetLastBracket()
            maxRnd = today['round']   if today['round']   else ""
            qset = FT.Game.objects.values_list('Round', flat=True
                ).distinct(
                ).filter(SeasonFK__Season=p_season, Round__lte=maxRnd
                ).order_by('-Round')
        
        else:
            qset = FT.Game.objects.values_list('Round', flat=True
                ).distinct(
                ).filter(SeasonFK__Season=p_season
                ).order_by('-Round')
        
        try:
            if not qset:
                return []
        except Exception:
            return []
        
        return list(qset)
    
    
    @staticmethod
    def GetClubs(p_season):
        
        if p_season:
            qset1 = FT.Game.objects.values_list('ClubHomeFK__Club', flat=True
                ).distinct(
                ).filter(SeasonFK__Season=p_season, Round='01')
            qset2 = FT.Game.objects.values_list('ClubAwayFK__Club', flat=True
                ).distinct(
                ).filter(SeasonFK__Season=p_season, Round='01')
            qset = list(qset1) + list(qset2)
        else:
            qset = FT.Club.objects.values_list('Club', flat=True)
            qset = list(qset)
        
        if not qset:
            return "Clubs not available."
        
        qset.sort()
        return qset
    
    
    @staticmethod
    def GetPlayers(p_club=None, p_position=None):
        
        players = []
        
        if p_club is None and (p_position is None or p_position == 'Any') :
            players = list(FT.Player.objects.annotate(FirstLast=Concat('FirstName', Value(' '), 'LastName')
                                            ).values_list('FirstLast', flat=True) )
        
        elif p_club is not None and (p_position is None or p_position == 'Any') :
            
            pl_insquad = FT.PlayerInClub.objects.annotate(FirstLast=Concat('PlayerFK__FirstName', Value(' '), 'PlayerFK__LastName')
                                                ).values_list('FirstLast', flat=True
                                                ).filter(ClubFK__Club=p_club
                                                ).distinct()
            
            pl_ingames = FT.GameEvent.objects.annotate(FirstLast=Concat('PlayerFK__FirstName', Value(' '), 'PlayerFK__LastName')
                                            ).values_list('FirstLast', flat=True
                                            ).filter(EventClubFK__Club=p_club
                                            ).distinct()
            
            for player in pl_insquad:
                players.append(player)
            for player in pl_ingames:
                if player not in players:
                    players.append(player)
        
        elif p_club is None and p_position is not None:
            
            pl_insquad = FT.PlayerInClub.objects.annotate(FirstLast=Concat('PlayerFK__FirstName', Value(' '), 'PlayerFK__LastName')
                                                ).values_list('FirstLast', flat=True
                                                ).filter(PositionDef=p_position
                                                ).distinct()
            for player in pl_insquad:
                players.append(player)
        
        
        elif p_club is not None and p_position is not None:
            
            pl_insquad = FT.PlayerInClub.objects.annotate(FirstLast=Concat('PlayerFK__FirstName', Value(' '), 'PlayerFK__LastName')
                                                ).values_list('FirstLast', flat=True
                                                ).filter(ClubFK__Club=p_club, PositionDef=p_position
                                                ).distinct()
            
            pl_ingames = FT.GameEvent.objects.annotate(FirstLast=Concat('PlayerFK__FirstName', Value(' '), 'PlayerFK__LastName')
                                            ).values_list('FirstLast', flat=True
                                            ).filter(EventClubFK__Club=p_club, Position=p_position
                                            ).distinct()
            
            for player in pl_insquad:
                players.append(player)
            for player in pl_ingames:
                if player not in players:
                    players.append(player)
        
        players.sort()      # flat list, sorts alphabetically 
        
        return players
    
    
    # this function is necessary to avoid duplicate player references from iplstats data error
    @staticmethod
    def GetPlayersBySeason(p_season):
        
        players = FT.PlayerInClub.objects.annotate(FirstLast=Concat('PlayerFK__FirstName', Value(' '), 'PlayerFK__LastName')
                                        ).values_list('FirstLast', flat=True
                                        ).filter(SeasonFK__Season=p_season)
        players = list(players)
        players.sort()      # flat list, sorts alphabetically 
        
        return players

    
    @staticmethod
    def GetPositions():
        positions = ['Any', 'Goalkeeper', 'Defender', 'Midfield', 'Forward']
        return positions


    @staticmethod
    def GetClubsTransp(p_season):
        
        if p_season:
            qset1 = FT.Game.objects.values_list('ClubHomeFK__Club', flat=True
                ).distinct(
                ).filter(SeasonFK__Season=p_season, Round='01')
            qset2 = FT.Game.objects.values_list('ClubAwayFK__Club', flat=True
                ).distinct(
                ).filter(SeasonFK__Season=p_season, Round='01')
            qset = list(qset1) + list(qset2)
        else:
            qset = FT.Club.objects.values_list('Club', flat=True)
            qset = list(qset)
        
        if not qset:
            return None
        
        qset.sort()
        
        transp = []
        for club in qset:
            fileName = Reports_General.ClubToFileName(club) + " transp.png"
            filePath = "/static/club_images/" + fileName
            transp.append(filePath)
        
        return transp
    
    
    @staticmethod
    def ClubToFileName(p_club):
        fileName = p_club.lower()
        fileName = fileName.rsplit(" ", 1)
        fileName = "_".join(fileName)
        fileName = fileName.replace(" ", "")
        return fileName


    @staticmethod
    def GetLogoPath(p_club):
        fmtName = p_club.lower()
        fmtName = fmtName.rsplit(" ", 1)
        fmtName = "_".join(fmtName)
        fmtName = fmtName.replace(" ", "")
        filePath = "/static/club_images/{} logo.png".format(fmtName)
        return filePath


class Reports_Admin(object):    
    
    
    @staticmethod
    def GetCoreCounts():
        
        results = []
        
        newRow = OrderedDict()
        newRow['Table'] = "Season"
        newRow['Count'] = FT.Season.objects.all().count()
        results.append(newRow)
        
        newRow = OrderedDict()
        newRow['Table'] = "Club"
        newRow['Count'] = FT.Club.objects.all().count()
        results.append(newRow)
        
        newRow = OrderedDict()
        newRow['Table'] = "Event"
        newRow['Count'] = FT.Event.objects.all().count()
        results.append(newRow)
        
        return results
    
    
    @staticmethod
    def GetSeasonSummary():
        
        seasons = FT.Season.objects.values_list('Season', flat=True)
        
        player_cnt = dict(
            FT.PlayerInClub.objects.values_list('SeasonFK__Season'
            ).annotate(player_count=Count('PlayerFK', distinct=True)) )
        
        game_cnt = dict(
            FT.Game.objects.values_list('SeasonFK__Season'
            ).annotate(game_count=Count('id')) )
        
        event_cnt = dict(
            FT.GameEvent.objects.values_list('GameFK__SeasonFK__Season'
            ).annotate(event_count=Count('id')) )
                
        summary = []
        for ssn in seasons:
            newRow = OrderedDict()
            newRow['season'] = ssn
            newRow['squad'] = player_cnt.get(ssn) if player_cnt.get(ssn) else 0
            newRow['games'] = game_cnt.get(ssn) if game_cnt.get(ssn) else 0
            newRow['events'] = event_cnt.get(ssn) if event_cnt.get(ssn) else 0
            summary.append(newRow)
        
        colFmt = {
            'season': '',
            'squad': 'format_center',
            'games': 'format_center',
            'events': 'format_center',
        }
        
        plTotal = FT.Player.objects.all().count()
        
        results = {
            'summary': summary, 
            'colFmt': colFmt, 
            'plTotal': plTotal, 
        }
        
        return results
    
    
    @staticmethod
    def GetFullTable(modelTable):
        
        # meta.fields preserves the column order
        
        fields = modelTable._meta.fields
        cols = []
        for field in fields:
            cols.append(field.name)
        
        values = modelTable.objects.values().order_by('id')
        jVals = []
        
        # preserve column order in return structure
        
        for val in values:
            newVal = OrderedDict()
            for key in cols:
                newVal[key] = val[key]
            jVals.append(newVal)
        
        return jVals
    
    
    @staticmethod
    def GetSquadSummary(p_season):
        hret = CU.HttpReturn()
        
        # get the counts for each column
        
        players_dx = dict(FT.PlayerInClub.objects.filter(SeasonFK__Season=p_season
                            ).values_list('ClubFK__Club'
                            ).annotate(player_count=Count('PlayerFK')))
        
        if not players_dx:
            hret.results = "No player data available."
            hret.status = 201
            return hret
        
        gk_dx = dict(FT.PlayerInClub.objects.filter(SeasonFK__Season=p_season, PositionDef='Goalkeeper'
                    ).values_list('ClubFK__Club'
                    ).annotate(player_count=Count('PlayerFK')))
        
        df_dx = dict(FT.PlayerInClub.objects.filter(SeasonFK__Season=p_season, PositionDef='Defender'
                    ).values_list('ClubFK__Club'
                    ).annotate(player_count=Count('PlayerFK')) )
        
        md_dx = dict(FT.PlayerInClub.objects.filter(SeasonFK__Season=p_season, PositionDef='Midfield'
                    ).values_list('ClubFK__Club'
                    ).annotate(player_count=Count('PlayerFK')) )
        
        fw_dx = dict(FT.PlayerInClub.objects.filter(SeasonFK__Season=p_season, PositionDef='Forward'
                    ).values_list('ClubFK__Club'
                    ).annotate(player_count=Count('PlayerFK')) )
        
        # format the data to return
        
        club_dict = []
        for club in players_dx:             # loop over dict keys
            club_dx = OrderedDict()
            club_dx['club'] = club
            club_dx['players'] = players_dx[club]
            club_dx['FW'] = fw_dx[club]   if club in fw_dx   else 0
            club_dx['MD'] = md_dx[club]   if club in md_dx   else 0
            club_dx['DF'] = df_dx[club]   if club in df_dx   else 0
            club_dx['GK'] = gk_dx[club]   if club in gk_dx   else 0   
            club_dict.append(club_dx)
        
        club_dict = sorted(club_dict, key=lambda k: k['club'])
        
        colFormat = OrderedDict()
        colFormat['club'] = ''
        colFormat['players'] = 'format_center'
        colFormat['FW'] = 'format_center'
        colFormat['MD'] = 'format_center'
        colFormat['DF'] = 'format_center'
        colFormat['GK'] = 'format_center'
        
        record = {
           'data': club_dict,
           'colFormat': colFormat,
        }
        
        hret.results = record
        hret.status = 201
        return hret
    
    
    @staticmethod
    def GetRoundSummary(p_season):
        hret = CU.HttpReturn()
        
        rounds_dx = dict(FT.Game.objects.filter(SeasonFK__Season=p_season
                            ).values_list('Round'
                            ).annotate(game_count=Count('Round')))
        
        if not rounds_dx:
            hret.results = "No game data available."
            hret.status = 201
            return hret
        
        event_dx = dict(FT.GameEvent.objects.filter(GameFK__SeasonFK__Season=p_season
                            ).values_list('GameFK__Round'
                            ).annotate(event_count=Count('EventFK')))
        
        rounds_dict = []
        for rnd in rounds_dx:             # loop over dict keys
            rnd_dx = OrderedDict()
            rnd_dx['round'] = rnd
            rnd_dx['games'] = rounds_dx[rnd]
            if rnd in event_dx:
                rnd_dx['events'] = event_dx[rnd]
            else:
                rnd_dx['events'] = 0
            rounds_dict.append(rnd_dx)
        
        rounds_dict = sorted(rounds_dict, key=lambda k: k['round'])
        
        colFormat = OrderedDict()
        colFormat['round'] = 'format_center'
        colFormat['games'] = 'format_center'
        colFormat['events'] = 'format_center'
        
        record = {
           'data': rounds_dict,
           'colFmt': colFormat,
        }
        
        hret.results = record
        hret.status = 201
        return hret
        
    
    @staticmethod
    def GetEventSummary(p_season):
        hret = CU.HttpReturn()
        
        eventCnt_dx = dict(FT.GameEvent.objects.filter(GameFK__SeasonFK__Season=p_season
                                ).values_list('EventFK__Type'
                                ).annotate(event_count=Count('EventFK')))
        
        if not eventCnt_dx:
            hret.results = "Event types not initialized."
            hret.status = 201
            return hret
        
        evHome_dx = dict(
            FT.GameEvent.objects.filter(GameFK__SeasonFK__Season=p_season, GameFK__ClubHomeFK=F('EventClubFK')
                        ).values_list('EventFK__Type'
                        ).annotate(event_count=Count('EventFK')))
        
        evAway_dx = dict(
            FT.GameEvent.objects.filter(GameFK__SeasonFK__Season=p_season, GameFK__ClubAwayFK=F('EventClubFK') 
                        ).values_list('EventFK__Type'
                        ).annotate(event_count=Count('EventFK')) )
        
        types_dict = []
        for evType in eventCnt_dx:             # loop over dict keys
            type_dx = OrderedDict()
            type_dx['type'] = evType
            type_dx['total'] = eventCnt_dx[evType]
            
            if evType in evHome_dx:
                type_dx['HomeClub'] = evHome_dx[evType]
            else:
                type_dx['HomeClub'] = 0
            
            if evType in evAway_dx:
                type_dx['AwayClub'] = evAway_dx[evType]
            else:
                type_dx['AwayClub'] = 0
            
            types_dict.append(type_dx)
        
        types_dict = sorted(types_dict, key=lambda k: k['type'])
        
        colFormat = OrderedDict()
        colFormat['type'] = ''
        colFormat['Total'] = 'format_center'
        colFormat['HomeClub'] = 'format_center'
        colFormat['AwayClub'] = 'format_center'
        
        record = {
           'data': types_dict,
           'colFormat': colFormat,
        }
        
        hret.results = record
        hret.status = 201
        return hret


class TimeMachine(object):    
    
    
    # returns season and round for custom now exactly
    @staticmethod
    def GetTodaysBracket():
        
        now_dt = TimeMachine.GetCustomNow().date()
        
        idx = (now_dt.weekday() + 1) % 7    # MON = 0, SUN = 6 -> SUN = 0 .. SAT = 6
        sunday_dt = now_dt - datetime.timedelta(idx)
        nextSunday_dt = sunday_dt + datetime.timedelta(7)
        
        game_mdl = FT.Game.objects.all().order_by('-PlayDate')
        
        # get the current round allowing for anomalous weeks
        
        cSeason = None
        cRound = None
        
        for game_m in game_mdl:
            if game_m.PlayDate.date() >= sunday_dt and game_m.PlayDate.date() < nextSunday_dt:
                cSeason = game_m.SeasonFK.Season
                cRound = game_m.Round
                break
            # assign values for anomalous weeks without games
            if game_m.PlayDate.date() <= now_dt:
                cSeason = game_m.SeasonFK.Season
                cRound = game_m.Round
                break
        
        # correct for anomaly actually being off-season 
        
        if cRound == "30":
            roundGames_mdl = game_mdl.filter(SeasonFK__Season=cSeason, Round="30")
            gameSample_dt = roundGames_mdl[0].PlayDate.date()
            idx = (gameSample_dt.weekday() + 1) % 7    
            sunday_dt = gameSample_dt - datetime.timedelta(idx)
            nextSunday_dt = sunday_dt + datetime.timedelta(7)
            
            if now_dt > nextSunday_dt:
                cSeason = None
                cRound = None
        
        bracket_dx = {
            'season': cSeason,
            'round': cRound,
        }
        return bracket_dx
    
    
    # returns season and round for custom now or closest date
    @staticmethod
    def GetLastBracket():
        
        now_dt = TimeMachine.GetCustomNow().date()
        
        idx = (now_dt.weekday() + 1) % 7    # MON = 0, SUN = 6 -> SUN = 0 .. SAT = 6
        sunday_dt = now_dt - datetime.timedelta(idx)
        nextSunday_dt = sunday_dt + datetime.timedelta(7)
        
        game_mdl = FT.Game.objects.all().order_by('-PlayDate')
        
        # get the current round allowing for anomalous weeks
        
        cSeason = None
        cRound = None
        
        for game_m in game_mdl:
            if game_m.PlayDate.date() >= sunday_dt and game_m.PlayDate.date() < nextSunday_dt:
                cSeason = game_m.SeasonFK.Season
                cRound = game_m.Round
                break
            # assign values for anomalous weeks without games
            if game_m.PlayDate.date() <= now_dt:
                cSeason = game_m.SeasonFK.Season
                cRound = game_m.Round
                break
        
        bracket_dx = {
            'season': cSeason,
            'round': cRound,
        }
        return bracket_dx
    
    
    # returns the number of complete games in parameter round
    @staticmethod
    def GetRoundPeriod(p_season, p_round):
        game_mdls = FT.Game.objects.filter(SeasonFK__Season=p_season, Round=p_round) #.order_by('PlayDate')
        
        finished = 0
        for game_m in game_mdls:
            if game_m.GoalsHome != None:
                finished += 1
        
        return finished
    
    
    # returns the last complete game round for season
    @staticmethod
    def GetLastRound(p_season):        
        rndVal = '01'
        while rndVal:            
            if TimeMachine.GetRoundPeriod(p_season, rndVal) < 8:
                return CU.Pad2( int(rndVal) -1 ) 
            else:
                rndVal = CU.Pad2( int(rndVal) +1 )
    
    
    # returns the play datetime for the first game of parameter round
    @staticmethod
    def GetFirstPlayDate(p_season, p_round):        
        
        game_mdls = FT.Game.objects.filter(SeasonFK__Season=p_season, Round=p_round
                                ).order_by('PlayDate')
        if not game_mdls:
            return None
        
        firstPlay_dt = game_mdls[0].PlayDate
        firstPlay_dt = firstPlay_dt.astimezone(pytz.timezone("Asia/Tehran"))
        
        return firstPlay_dt
    
    
    @staticmethod
    def GetCustomNow():
        simTime = TimeMachine.GetSimTime()
        if simTime:
            return simTime
        
        utcnow = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
        return utcnow
    
    
    @staticmethod
    def GetSimTime():
        try:
            simTime_m = FT.Event.objects.get(Event='SimTime')
        except FT.Event.DoesNotExist:
            simTime_m = None
        
        if simTime_m:
            simTime = CU.TZStringToDT(simTime_m.Description)     # to datetime
        else:
            simTime = None
        
        return simTime
    
    
    @staticmethod
    def SaveSimDate(p_date, p_time):
        
        if not p_date:
            FT.Event.objects.filter(Event='SimTime').delete()
            return "SaveSimDate complete."
        
        # save valid date in string format
        
        dttz = "{0} {1} EST".format(p_date, p_time)        
        sim_tz = CU.TZStringToDT(dttz)
        sim_st = sim_tz.strftime(CU.FORMAT_DTSTR)
        
        FT.Event.objects.filter(Event='SimTime').delete()
        
        simEvt_m, created = FT.Event.objects.get_or_create(
                                Type="NotEvent", Event="SimTime", Description=sim_st)
        
        return "SaveSimDate complete."


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
REFERENCE PAGES
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


class Reports_Season(object):    
    
    
    # returns all games in round in list of dicts
    @staticmethod
    def GetFixtureData(p_season, p_round):        
        
        game_mdls = FT.Game.objects.filter(SeasonFK__Season=p_season, Round=p_round
                                ).order_by('PlayDate', 'ClubHomeFK__Club')
        if not game_mdls:
            return None
        
        games = []
        for gm in game_mdls:
            newGame = Reports_Game.GameToDict(gm)
            games.append(newGame)
        
        return games
    
    
    # returns parameter ClubRanking model as ClubRankData
    @staticmethod
    def ConvertRank(rank_m):
        rankDt = FT.ClubRankData()
        rankDt.season = rank_m.SeasonFK.Season
        rankDt.round = rank_m.Round
        rankDt.club = rank_m.ClubFK.Club
        rankDt.rank = rank_m.Rank
        rankDt.points =  rank_m.Points
        rankDt.goals_for = rank_m.GoalsFor
        rankDt.goals_vs = rank_m.GoalsVs
        rankDt.goals_diff = rank_m.GoalsFor - rank_m.GoalsVs
        return rankDt
    
    
    # returns last club rankings
    @staticmethod
    def GetLastRanking(p_season):        
        
        # get last round that is complete
        
        lastRnd = TimeMachine.GetLastRound(p_season)
        if not lastRnd:
            return None
        
        # create the ranking data
        
        cRank_mdls = FT.ClubRanking.objects.filter(SeasonFK__Season=p_season, Round=lastRnd)
        ranks = []
        for rnk in cRank_mdls:
            newRank = Reports_Season.ConvertRank(rnk)
            ranks.append(newRank)
        return ranks
    
    
    # returns fixture for season, round in full-table format
    @staticmethod
    def GetFixtureFT(p_season, p_round, p_tz=None):        
        
        games_dict = Reports_Season.GetFixtureData(p_season, p_round)
        
        if not games_dict:
            return "No fixture found."
        
        if not p_tz:
            ctz = "Asia/Tehran"
        else:
            ctz = p_tz
        
        customTZ = pytz.timezone(ctz)
        gamesFmt = []
        for game_dx in games_dict:
            gameF = OrderedDict()
            gameF['id'] = game_dx['id']
            gameF['home_club'] = game_dx['home_club']
            gameF['HG'] = game_dx['home_goals']  if game_dx['home_goals'] is not None  else "*"
            gameF['AG'] = game_dx['away_goals']  if game_dx['away_goals'] is not None  else "*"
            gameF['away_club'] = game_dx['away_club']
            gameF['play_date'] = game_dx['playDt_utc'].astimezone(customTZ).strftime(CU.FORMAT_DTSTR)
            gamesFmt.append(gameF)
        
        colFmt = OrderedDict()
        colFmt['home_club'] = 'format_fixline'
        colFmt['HG'] = 'format_center'
        colFmt['AG'] = 'format_center'
        colFmt['away_club'] = 'format_fixline'
        colFmt['play_date'] = 'format_fixline'
        
        record = {
            'data': gamesFmt,
            'colFmt': colFmt,
        }
        return record
    
    
    # for admin purposes
    @staticmethod
    def GetFixtureDetails(p_season, p_round):        
        
        games_dict = Reports_Season.GetFixtureData(p_season, p_round)
        
        if not games_dict:
            return "No fixture found."
        
        eventCnt = FT.GameEvent.objects.values_list('GameFK__id'
                                    ).filter(GameFK__SeasonFK__Season=p_season, GameFK__Round=p_round
                                    ).annotate(cnt=Count('GameFK__id'))        
        
        gamesFmt = []
        for game_dx in games_dict:
            gameF = OrderedDict()
            gameF['home_club'] = game_dx['home_club']
            gameF['away_club'] = game_dx['away_club']
            gameF['id'] = game_dx['id']
            
            gameOver = game_dx['playDt_utc'] + datetime.timedelta(hours=2)
            gameF['gameOver'] = gameOver.strftime(CU.FORMAT_DTSTR)
            
            hasEvents = False
            for evgm in eventCnt:
                if evgm[0] == game_dx['id']:
                    gameF['events'] = evgm[1]
                    hasEvents = True
                    break
            if not hasEvents:
                gameF['events'] = 0
            
            gamesFmt.append(gameF)
        
        return gamesFmt
    
    
    # returns http-ret for season reference page    
    @staticmethod
    def GetClubRanksFT(p_season):        
        hret = CU.HttpReturn()
        
        rank_dt = Reports_Season.GetLastRanking(p_season)
        rank_dt = sorted(rank_dt, key=operator.attrgetter('rank'))
        
        if not rank_dt:
            return "No rankings found."
        
        ranks_dict = []
        for rnk in rank_dt:
            rank_dx = OrderedDict()
            rank_dx['rank'] = rnk.rank
            rank_dx['club'] = rnk.club
            rank_dx['points'] = rnk.points
            rank_dx['G-Diff'] = rnk.goals_diff
            rank_dx['goals'] = rnk.goals_for
            ranks_dict.append(rank_dx)
        
        colFmt = OrderedDict()
        colFmt['rank'] = 'format_center'
        colFmt['club'] = 'format_fixline'
        colFmt['points'] = 'format_center'
        colFmt['G-Diff'] = 'format_center'
        colFmt['goals'] = 'format_center'
        
        ftable = {
           'data': ranks_dict,
           'colFmt': colFmt,
        }
        return ftable
    
    
    # returns dict for season reference page
    @staticmethod
    def GetClubGamesFT(p_season, p_club):        
        
        # get the game data for each round
        
        games_mdls = FT.Game.objects.filter(SeasonFK__Season=p_season
                                    ).filter( Q(ClubHomeFK__Club=p_club) | Q(ClubAwayFK__Club=p_club)
                                    ).order_by('-PlayDate')
        if not games_mdls:
            return "No games found."
        
        games_dict = []
        for gm in games_mdls:
            newGame = Reports_Game.GameToDict(gm)
            games_dict.append(newGame)
        
        # get the last round that has data
        
        roundLs = Reports_General.GetRounds(p_season, 'lastData')
        if not roundLs:
            roundLs = Reports_General.GetRounds(p_season, 'today')
        currRnd = roundLs[0]        # sorted descending
        
        # create result data by filtering the game data
        
        gamesFmt = []
        for game_dx in games_dict:
            
            if game_dx['round'] > currRnd:
                continue
            
            try:
                rank_m = FT.ClubRanking.objects.get(
                    SeasonFK__Season=p_season, Round=game_dx['round'], ClubFK__Club=p_club)
            except Exception:
                rank_m = None
            
            gameF = OrderedDict()
            gameF['round'] = game_dx['round']
            gameF['rank'] = rank_m.Rank  if rank_m  else '*'
            gameF['home_club'] = game_dx['home_club']
            gameF['HG'] = game_dx['home_goals']  if game_dx['home_goals'] is not None  else "*"
            gameF['AG'] = game_dx['away_goals']  if game_dx['away_goals'] is not None  else "*"
            gameF['away_club'] = game_dx['away_club']
            gamesFmt.append(gameF)
        
        # return in full-table format
        
        colFmt = OrderedDict()
        colFmt['round'] = 'format_center'
        colFmt['rank'] = 'format_center'
        colFmt['home_club'] = 'format_fixline'
        colFmt['HG'] = 'format_center'
        colFmt['AG'] = 'format_center'
        colFmt['away_club'] = 'format_fixline'
        
        ftable = {
           'data': gamesFmt,
           'colFmt': colFmt,
        }
        return ftable


class Reports_Game(object):    
    
    
    # returns parameter Game model as dict
    @staticmethod
    def GameToDict(game_mdl):
        game_dx = {}
        game_dx['id'] = game_mdl.id
        game_dx['season'] = game_mdl.SeasonFK.Season
        game_dx['round'] = game_mdl.Round
        game_dx['playDt_utc'] = game_mdl.PlayDate         # edit this DateTimeField in cleanup function to serialize
        game_dx['home_club'] = game_mdl.ClubHomeFK.Club
        game_dx['home_goals'] = game_mdl.GoalsHome
        game_dx['home_scorers'] = game_mdl.ScorersHome
        game_dx['away_club'] = game_mdl.ClubAwayFK.Club
        game_dx['away_goals'] = game_mdl.GoalsAway
        game_dx['away_scorers'] = game_mdl.ScorersAway
        
        return game_dx
    
    
    # shortcut that returns a Game dict by ID
    def GameToDictByID(game_id):
        game_m = FT.Game.objects.get(id=game_id)
        game_dx = Reports_Game.GameToDict(game_m)
        return game_dx
    
    
    @staticmethod
    def RunGameProperties(p_season, p_round, p_homeClub):        
        
        try: 
            game_m = FT.Game.objects.get(SeasonFK__Season=p_season, Round=p_round, ClubHomeFK__Club=p_homeClub)
        except FT.Game.DoesNotExist:
            hret = CU.HttpReturn() 
            hret.results = "No game available." 
            hret.status = 201 
            return hret    
        
        # get home line-up
        
        home_lnEvts = FT.GameEvent.objects.annotate(FirstLast=Concat('PlayerFK__FirstName', Value(' '), 'PlayerFK__LastName')
                                        ).values('EventFK__Event', 'FirstLast', 'Position'
                                        ).filter(GameFK=game_m, EventClubFK__Club=p_homeClub
                                        ).filter(EventFK__Event__in=['Player in Line-up'])
        
        home_lineup = OrderedDict([('Goalkeeper', []), ('Defender', []), ('Midfield', []), ('Forward', [])])
        
        for evt in home_lnEvts:
            home_lineup[evt['Position']].append(evt['FirstLast'])
        
        for pos in home_lineup:
            players = sorted(home_lineup[pos])            
            home_lineup[pos] = players
            
        # get away line-up
        
        away_lnEvts = FT.GameEvent.objects.annotate(FirstLast=Concat('PlayerFK__FirstName', Value(' '), 'PlayerFK__LastName')
                                        ).values('EventFK__Event', 'FirstLast', 'Position'
                                        ).filter(GameFK=game_m, EventClubFK__Club=game_m.ClubAwayFK.Club
                                        ).filter(EventFK__Event__in=['Player in Line-up'])
        
        away_lineup = OrderedDict([('Goalkeeper', []), ('Defender', []), ('Midfield', []), ('Forward', [])])
        
        for evt in away_lnEvts:
            away_lineup[evt['Position']].append(evt['FirstLast'])
        
        for pos in away_lineup:
            players = sorted(away_lineup[pos])            
            away_lineup[pos] = players
        
        
        # get home events 
        
        home_mvEvts = FT.GameEvent.objects.annotate(FirstLast=Concat('PlayerFK__FirstName', Value(' '), 'PlayerFK__LastName')
                            ).values('FirstLast', 'EventFK__Event', 'EventTime'
                            ).filter(GameFK=game_m, EventClubFK__Club=game_m.ClubHomeFK.Club
                            ).filter( Q(EventFK__Type='Move') | Q(EventFK__Event__in=['Player Sub-out', 'Player Sub-in']) )
        
        home_moves = []
        for evt in home_mvEvts:
            move = OrderedDict()
            move['player'] = evt['FirstLast']
            move['event'] = evt['EventFK__Event']
            move['game_time'] = evt['EventTime'].strftime("%H:%M")
            home_moves.append(move)
        
        home_moves = sorted(home_moves, key=lambda x: x['event'])
        home_moves = sorted(home_moves, key=lambda x: x['game_time'])
        
        # get away events 
        
        away_mvEvts = FT.GameEvent.objects.annotate(FirstLast=Concat('PlayerFK__FirstName', Value(' '), 'PlayerFK__LastName')
                            ).values('FirstLast', 'EventFK__Event', 'EventTime'
                            ).filter(GameFK=game_m, EventClubFK__Club=game_m.ClubAwayFK.Club
                            ).filter( Q(EventFK__Type='Move') | Q(EventFK__Event__in=['Player Sub-out', 'Player Sub-in']) )
        
        away_moves = []
        for evt in away_mvEvts:
            move = OrderedDict()
            move['player'] = evt['FirstLast']
            move['event'] = evt['EventFK__Event']
            move['game_time'] = evt['EventTime'].strftime("%H:%M")
            away_moves.append(move)
        
        away_moves = sorted(away_moves, key=lambda x: x['event'])
        away_moves = sorted(away_moves, key=lambda x: x['game_time'])
        
        
        # create return structures
        
        home_dt = {
            'name': p_homeClub,
            'goals': game_m.GoalsHome   if game_m.GoalsHome is not None   else '*',
            'lineup': home_lineup,
            'moves': home_moves,
        }
        
        away_dt = {
            'name': game_m.ClubAwayFK.Club,
            'goals': game_m.GoalsAway   if game_m.GoalsAway is not None   else '*',
            'lineup': away_lineup,
            'moves': away_moves,
        }
        
        clubs = {
            'home': home_dt,
            'away': away_dt,
        }
        
        hret = CU.HttpReturn() 
        hret.results = clubs 
        hret.status = 201 
        return hret    


class Reports_Club(object):    
    
    
    @staticmethod
    def GetClubProperties(p_club):        
        club_m = FT.Club.objects.get(Club=p_club)
        club_dx = OrderedDict()
        club_dx['club'] = club_m.Club
        club_dx['full_name'] = club_m.FullName
        club_dx['city'] = club_m.City
        club_dx['founded'] = club_m.Founded
        
        hret = CU.HttpReturn()
        hret.results = club_dx
        hret.status = 201
        return hret
    
    
    @staticmethod
    def GetPlayersInGame(p_club, p_season, p_pos):
        # players can be from event list for game, from squad or other club squad
        # players can be from squad with no games played
        
        events = FT.GameEvent.objects.annotate(FirstLast=Concat('PlayerFK__FirstName', Value(' '), 'PlayerFK__LastName')
                    ).values_list('FirstLast'
                    ).filter(GameFK__SeasonFK__Season=p_season, EventClubFK__Club=p_club, Position=p_pos
                    ).filter(EventFK__Event__in=['Player in Line-up', 'Player Sub-in']
                    ).annotate(cnt=Count('id'))
        events_dx = dict(events)
        
        squads = FT.PlayerInClub.objects.annotate(FirstLast=Concat('PlayerFK__FirstName', Value(' '), 'PlayerFK__LastName')
                                        ).values_list('FirstLast', flat=True
                                        ).filter(SeasonFK__Season=p_season, ClubFK__Club=p_club, PositionDef=p_pos)
        
        # create list of dicts with all data
        
        players_dict = []
        
        for evt in events_dx:
            squad = FT.PlayerInClub.objects.annotate(FirstLast=Concat('PlayerFK__FirstName', Value(' '), 'PlayerFK__LastName')
                                            ).values_list('ClubFK__Club'
                                            ).filter(SeasonFK__Season=p_season, FirstLast=evt).first()
            newPlr = OrderedDict()
            newPlr['name'] = evt
            newPlr['squad'] = squad
            newPlr['games'] = events_dx[evt]
            players_dict.append(newPlr)
        
        for sqd in squads:            
            if sqd not in events_dx:
                newPlr = OrderedDict()
                newPlr['name'] = sqd
                newPlr['squad'] = p_club
                newPlr['games'] = 0
                players_dict.append(newPlr)
        
        players_dict = sorted(players_dict, key=lambda k: k['name'])
        players_dict = sorted(players_dict, key=lambda k: k['games'], reverse=True)
        
        # return results
        
        colFormat = OrderedDict()
        colFormat['name'] = ''
        colFormat['squad'] = ''
        colFormat['games'] = 'format_center'
        
        record = {
            'data': players_dict,
            'colFormat': colFormat,
        }
        
        hret = CU.HttpReturn()
        hret.results = record  if players_dict  else "No players available."
        hret.status = 201
        return hret


class Reports_Player(object):    
    
    
    @staticmethod
    def GetPropertiesDict(p_player):        
        player_m = FT.Player.objects.annotate(FirstLast=Concat('FirstName', Value(' '), 'LastName')
                                    ).get(FirstLast=p_player)
        
        player_dx = OrderedDict()
        player_dx['player'] = player_m.FirstLast
        player_dx['nationality'] = player_m.Nationality
        player_dx['date_of_birth'] = player_m.DateOfBirth.strftime("%Y-%m-%d")
        player_dx['profile'] = player_m.ProfilePhoto
        
        return player_dx
    
    
    @staticmethod
    def GetClubRecordDict(p_player):
        
        events = FT.GameEvent.objects.annotate(FirstLast=Concat('PlayerFK__FirstName', Value(' '), 'PlayerFK__LastName')
                    ).values('GameFK__SeasonFK__Season', 'EventClubFK__Club', 'Position'
                    ).filter(FirstLast=p_player
                    ).filter(EventFK__Event__in=['Player in Line-up', 'Player Sub-in']
                    ).annotate(EvtCnt=Count('GameFK__id', distinct = True))
        
        squads = FT.PlayerInClub.objects.annotate(FirstLast=Concat('PlayerFK__FirstName', Value(' '), 'PlayerFK__LastName')
                                        ).values('SeasonFK__Season', 'ClubFK__Club', 'PositionDef'
                                        ).filter(FirstLast=p_player)
        
        # create list of dicts with all data
        
        squads_dict = []
        
        for evt in events:
            newSqd = OrderedDict()
            newSqd['season'] = evt['GameFK__SeasonFK__Season']
            newSqd['club'] = evt['EventClubFK__Club']
            newSqd['position'] = evt['Position']
            newSqd['games'] = evt['EvtCnt']
            squads_dict.append(newSqd)
        
        for sqd in squads:
            currSeason = sqd['SeasonFK__Season']
            currClub = sqd['ClubFK__Club']
            hasEntry = False
            
            for item in squads_dict:
                if item['season'] == currSeason and item['club'] == currClub:
                    hasEntry = True
            
            if not hasEntry:
                newSqd = OrderedDict()
                newSqd['season'] = currSeason
                newSqd['club'] = currClub
                newSqd['position'] = sqd['PositionDef']
                newSqd['games'] = 0
                squads_dict.append(newSqd)
        
        # return results
        
        squads_dict = sorted(squads_dict, key=lambda k: k['season'], reverse=True)
        results = squads_dict  if squads_dict  else "No squad data available."
        return results



"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
END OF FILE
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""