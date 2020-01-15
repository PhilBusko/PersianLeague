"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
PREDICTION/MODELS/UNIVERSAL.py
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import json         # unpack json model fields
import datetime 
import pytz
from collections import OrderedDict
from decimal import Decimal

from django.db import models
from django.db.models import Count, F, Q, Value
from django.db.models.functions import Concat
from django.utils import timezone
import django.contrib.auth.models as AM

import common.utility as CU
import football.models.tables as FT
import football.models.football as FM
import members.models.members as MM

import logging
prog_lg = logging.getLogger('progress')
excp_lg = logging.getLogger('exception')


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
MODEL CLASSES
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


class Univ_Roster(models.Model):
    UserFK = models.ForeignKey(AM.User, on_delete=models.CASCADE)
    SeasonFK = models.ForeignKey(FT.Season, on_delete=models.CASCADE)
    
    Token_LastPop = models.DateTimeField(default=timezone.now() - datetime.timedelta(days=1))   # start with full generator
    Token_Rate = models.DecimalField(max_digits=18,decimal_places=16, default=Decimal('0.0347222222222222'))   # tk/min 
    Token_Total = models.IntegerField(default=0)
    
    # the value is the level of each ability
    Upgrades = models.CharField(max_length=200,
        default='{"goalsG": 0, "scorersG": 0, "doubleDown": 0, "secondChance": 0, "clubFav": 0, "tokenRate": 0}')
    Medals = models.CharField(max_length=200, default='[]')


class Univ_Prediction(models.Model):
    
    UserFK = models.ForeignKey(AM.User, on_delete=models.CASCADE)
    GameFK = models.ForeignKey(FT.Game, on_delete=models.CASCADE)
    
    OpenDate = models.DateTimeField(default=datetime.date.min)
    CloseDate = models.DateTimeField(default=datetime.date.min)
    
    Result = models.IntegerField(null=True)             # 0 Abstain, 1 HomeWin, 2 AwayWin, 3 Tie
    GoalsHome = models.IntegerField(null=True)
    GoalsAway = models.IntegerField(null=True)
    ScorerHomeFK = models.ForeignKey(FT.Player, related_name='pu_home', null=True)
    ScorerAwayFK = models.ForeignKey(FT.Player, related_name='pu_away', null=True)
    AbilitiesUsed = models.CharField(null=True, max_length=500)
    
    PntsResult = models.IntegerField(null=True)
    PntsGoal = models.IntegerField(null=True)
    PntsScorer = models.IntegerField(null=True)
    PntsTotal = models.IntegerField(null=True)


class Univ_Scoring(models.Model):
    
    UserFK = models.ForeignKey(AM.User)
    SeasonFK = models.ForeignKey(FT.Season)   
    Round = models.CharField(max_length=10)
    
    Points_Round = models.IntegerField(default=0)
    Points_AllTime = models.IntegerField(default=0)
    RewardStatus = models.IntegerField(default=0)         # 0: not sent, 1: sent, 2: claimed
    
    Rank_Round = models.IntegerField(null=True)
    Perc_Round = models.DecimalField(null=True, max_digits=8, decimal_places=4)
    Rank_AllTime = models.IntegerField(null=True)
    Perc_AllTime = models.DecimalField(null=True, max_digits=8, decimal_places=4)


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
REPORTER CLASSES
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


class Reporter_Common(object):
    
    
    # returns all games in round as dict
    @staticmethod
    def GetFixtureLocalized(p_season, p_round, p_user_md):
        
        games_dict = FM.Reports_Season.GetFixtureData(p_season, p_round)
        
        if not games_dict:
            return "No games found."
        
        if p_user_md.is_authenticated():
            profile_m = MM.Profile_Reporter.GetProfile_Mdl(p_user_md)
            profTZ = pytz.timezone(profile_m.TimeZone   if profile_m.TimeZone   else 'UTC')
        else:
            profTZ = pytz.utc
        
        gamesFmt = []
        for game_dx in games_dict:
            gameF = OrderedDict()
            gameF['gameid'] = game_dx['id']
            gameF['season'] = game_dx['season']
            gameF['round'] = game_dx['round']
            gameF['playLoc_st'] = game_dx['playDt_utc'].astimezone(profTZ).strftime(CU.FORMAT_DTSTR)    
            gameF['home_club'] = game_dx['home_club']
            gameF['home_goals'] = game_dx['home_goals']  if game_dx['home_goals'] is not None  else "*"
            gameF['home_scorers'] = game_dx['home_scorers']
            gameF['away_club'] = game_dx['away_club']
            gameF['away_goals'] = game_dx['away_goals']  if game_dx['away_goals'] is not None  else "*"
            gameF['away_scorers'] = game_dx['away_scorers']
            gamesFmt.append(gameF)
        
        return gamesFmt
    
    
    @staticmethod
    def GetPredictionWindow(p_playDT):
        open_dm = p_playDT - datetime.timedelta(days=2)
        close_dm = p_playDT - datetime.timedelta(minutes=30)
        
        dates = {
            'open': open_dm,
            'close': close_dm,
        }
        return dates


class Reporter(object):
    
    
    # gat all the user's roster data for season, except for abilities owned
    @staticmethod
    def GetUserRoster(p_user, p_season):
        
        if not p_user.is_authenticated():        
            roster = {
                'tokenAccum': 0,
                'tokenPerc': '{0:.1f}'.format(0),
                'tokenTotal': 0,
                'rateTkDay': 50,
                'lastPop': 0,
                'timeToToken': 0,
                'message': "Log in to use your tokens.",
            }
            return roster
        
        if not p_season:
            roster = {
                'tokenAccum': 0,
                'tokenPerc': '{0:.1f}'.format(0),
                'tokenTotal': 0,
                'rateTkDay': 50,
                'lastPop': 0,
                'timeToToken': 0,
                'message': "Tokens are not available in off-season.",
            }
            return roster
        
        
        season_m = FT.Season.objects.get(Season=p_season)
        rost_m, crtd = Univ_Roster.objects.get_or_create(UserFK=p_user, SeasonFK=season_m)
        
        # get or create roster for each season, runs when home.html asks for extra context from profile
        # why did this code stop working ?
        # rost_m, crtd = Univ_Roster.objects.get_or_create(UserFK=p_user, SeasonFK__Season=p_season)
        
        profile_m = MM.Profile_Reporter.GetProfile_Mdl(p_user)
        
        if profile_m.TimeZone:
            lastPop_tz = rost_m.Token_LastPop.astimezone(pytz.timezone(profile_m.TimeZone))
        else:
            lastPop_tz = rost_m.Token_LastPop       # do everything in UTC
        
        tokenData = Reporter.CalcTokenData(rost_m.Token_LastPop, rost_m.Token_Rate)
        
        roster = {
            'tokenAccum': tokenData.tokens,
            'tokenPerc': '{0:.1f}'.format(tokenData.tokens / tokenData.tokenMax * 100),
            'tokenTotal': rost_m.Token_Total,
            'rateTkDay': tokenData.tokenMax,
            'lastPop': lastPop_tz.strftime(CU.FORMAT_DTSTR_SECS),
            'timeToToken': '{0:.1f}'.format(86440 / tokenData.tokenMax),       # 86440 secs/day
            'message': '',
        }
        
        return roster
    
    
    # get the user's abilities owned from their roster
    @staticmethod
    def GetAbilitiesOwned(p_user, p_season):
        
        try:
            rost_m = Univ_Roster.objects.get(UserFK=p_user, SeasonFK__Season=p_season)
            profile_m = MM.Profile_Reporter.GetProfile_Mdl(p_user)        # for favorite club
        except Exception as ex:
            rost_m = None
            profile_m = None
            
        if rost_m:
            upgrades = json.loads( rost_m.Upgrades )
        else:
            upgrades = {"goalsG": 0, "scorersG": 0, "doubleDown": 0, "secondChance": 0, "clubFav": 0, "tokenRate": 0}
        
        abilsOwned = OrderedDict()
        abilsOwned['goalsG'] = {
            'name': "Goals Guess",
            'level': upgrades['goalsG'],
            'uses': Reporter.GetAbilityOwnedUses("GoalsGuess", upgrades['goalsG']),
            'desc': Reporter.GetAbilityDesc("GoalsGuess", upgrades['goalsG']),
        }
        abilsOwned['scorersG'] = {
            'name': "Scorers Guess",
            'level': upgrades['scorersG'],
            'uses': Reporter.GetAbilityOwnedUses("ScorersGuess", upgrades['scorersG']),
            'desc': Reporter.GetAbilityDesc("ScorersGuess", upgrades['scorersG']),
        }
        abilsOwned['secondChance'] = {
            'name': "Second Chance",
            'level': upgrades['secondChance'],
            'uses': Reporter.GetAbilityOwnedUses("SecondChance", upgrades['secondChance']),
            'desc': Reporter.GetAbilityDesc("SecondChance", upgrades['secondChance']),
        }
        abilsOwned['doubleDown'] = {
            'name': "Double Down",
            'level': upgrades['doubleDown'],
            'uses': Reporter.GetAbilityOwnedUses("DoubleDown", upgrades['doubleDown']),
            'desc': Reporter.GetAbilityDesc("DoubleDown", upgrades['doubleDown']),
        }
        abilsOwned['clubFav'] = {
            'name': "Club Favorite",
            'level': upgrades['clubFav'],
            'uses': Reporter.GetAbilityOwnedUses("ClubFavorite", upgrades['clubFav']),
            'desc': Reporter.GetAbilityDesc("ClubFavorite", upgrades['clubFav']),
            'club': profile_m.FavClubFK.Club   if profile_m and profile_m.FavClubFK   else None,
        }
        abilsOwned['tokenRate'] = {
            'name': "Token Rate",
            'level': upgrades['tokenRate'],
            'uses': Reporter.GetAbilityOwnedUses("TokenRate", upgrades['tokenRate']),
            'desc': Reporter.GetAbilityDesc("TokenRate", upgrades['tokenRate']),
        }
        
        return abilsOwned
    
    
    # helper for GetUserRoster, PopTokenAccumulator
    @staticmethod
    def CalcTokenData(p_lastPop, p_tokenRate):
        
        accumDelta = FM.TimeMachine.GetCustomNow() - p_lastPop        
        accumMins = accumDelta.days * 1440 + accumDelta.seconds / 60 
        accumMins = accumMins  if accumMins <= 1440  else 1440              # 1440 minutes in a day
        
        # int() rounds down, +0.000001 to account for python multiplication errors
        tokenData = lambda: None        
        tokenData.tokens = int(p_tokenRate * Decimal(accumMins) + Decimal('0.000001'))        
        tokenData.tokenMax = int(p_tokenRate * Decimal(1440) + Decimal('0.000001'))
        
        return tokenData
    
    
    # helper for GetAbilitiesOwned
    @staticmethod
    def GetAbilityOwnedUses(abilityType, level):
        
        if abilityType == "GoalsGuess":
            return level
        
        elif abilityType == "ScorersGuess":
            return level
        
        elif abilityType == "SecondChance":
            return level
        
        elif abilityType == "DoubleDown":
            if level == 0:      return 0
            else:               return 1
        
        elif abilityType == "ClubFavorite":
            if level == 0:      return 0
            else:               return 1
        
        elif abilityType == "TokenRate":
            return "passive"
        
        return None
    
    
    # helper for GetAbilitiesOwned
    @staticmethod
    def GetAbilityDesc(abilityType, level):
        
        if abilityType == "GoalsGuess":
            return "Goals Guess x{}".format(level)
        
        elif abilityType == "ScorersGuess":
            return "Scorers Guess x{}".format(level)
        
        elif abilityType == "SecondChance":
            return "Second Choice x{}".format(level)
        
        elif abilityType == "DoubleDown":
            return "Double Down |{}|".format(level)
        
        elif abilityType == "ClubFavorite":
            return "Club Favorite |{}|".format(level)
        
        elif abilityType == "TokenRate":
            if str(level) == '1':      return "Token Rate 55 tks/day"
            elif str(level) == '2':    return "Token Rate 60 tks/day"
            elif str(level) == '3':    return "Token Rate 65 tks/day"
            elif str(level) == '4':    return "Token Rate 70 tks/day"
        
        return None
    
    
    # get all abilities used in the parameter round 
    @staticmethod
    def GetAbilsUsedByRound(p_user, p_season, p_round):
        
        abilityUses = {'goalsG': 0, 'scorersG': 0, 'secondChance': 0, 'doubleDown': 0, 'clubFav': 0}
        
        try:
            abilsUsed_strg = Univ_Prediction.objects.values_list('AbilitiesUsed', flat=True
                                ).filter(UserFK=p_user, GameFK__SeasonFK__Season=p_season, GameFK__Round=p_round)
        except Exception as ex:
            return abilityUses
        
        
        for abilUses in abilsUsed_strg:
            
            if not abilUses:
                continue
            
            abils_ob = json.loads(abilUses) 
            
            if 'goalsG' in abils_ob:
                abilityUses['goalsG'] += 1
            if 'scorersG' in abils_ob:
                abilityUses['scorersG'] += 1
            if 'secondChance' in abils_ob:
                abilityUses['secondChance'] += len(abils_ob['secondChance'])    # += 1 ?
            if 'doubleDown' in abils_ob:
                abilityUses['doubleDown'] += len(abils_ob['doubleDown'])
            if 'clubFav' in abils_ob:
                abilityUses['clubFav'] = 1
        
        return abilityUses 
    
    
    
    # get the user's record in chart format, view-profile doesn't need the status message
    @staticmethod
    def GetRecord(p_user_md, p_season, p_round=None):
        
        # convert user rankings from dict format to chart format
        
        record_dx = Reporter.GetRecord_Dict(p_user_md, p_season)
        recAT_dict = record_dx['alltime']
        recRD_dict = record_dx['rounds']
        
        recAT_plot = []
        for rec in recAT_dict:
            newPnt = [rec['round'], rec['perc%'], rec['points']]
            recAT_plot.append(newPnt)
        
        recRD_plot = []
        for rec in recRD_dict:
            newPnt = [rec['round'], rec['perc%'], rec['points']]
            recRD_plot.append(newPnt)
        
        # get the grade thresholds
        
        thresholds = []
        grade_dict = Reporter_Ranks.GetRewardTableAT()
        
        for grade_dx in grade_dict:
            newLine = [ [1, grade_dx['perc'], grade_dx['grade']],
                        [30, grade_dx['perc']]  ]
            thresholds.append(newLine)
        
        # create the status text
        
        status = {
            'rndPeriod': None,
            'rankAT': None,
            'rankRD': None,
            'percAT': None,
            'percRD': None,
            'rndReward': None,
        }
        
        if p_user_md.is_anonymous():
            status['rndPeriod'] = -1
        
        elif p_round:
            
            rndPeriod = FM.TimeMachine.GetRoundPeriod(p_season, p_round)
            
            if rndPeriod == 0:
                status['rndPeriod'] = rndPeriod
            
            else:
                try:
                    score_md = Univ_Scoring.objects.get(UserFK=p_user_md, SeasonFK__Season=p_season, Round=p_round)
                    status['rndPeriod'] = rndPeriod
                    status['rankAT'] = Reporter_Ranks.GetGrade(score_md.Perc_AllTime)
                    status['rankRD'] = Reporter_Ranks.GetGrade(score_md.Perc_Round)
                    status['percAT'] = '{0:0.1f}'.format(score_md.Perc_AllTime)
                    status['percRD'] = '{0:0.1f}'.format(score_md.Perc_Round)
                    status['rndReward'] = score_md.RewardStatus    
                except:
                    score_md = None
                    status['rndPeriod'] = rndPeriod
        
        # return results
        
        results = {
            'status': status, 
            'recordAT': recAT_plot,
            'recordRD': recRD_plot,
            'thresholds': thresholds,
        } 
        return results
    
    
    @staticmethod
    def GetRecord_Dict(p_user_md, p_season):
        
        score_mdls = []
        if p_user_md.is_authenticated():
            score_mdls = Univ_Scoring.objects.filter(UserFK=p_user_md, SeasonFK__Season=p_season)
        
        alltime = []
        for score_m in score_mdls:
            newRnd = OrderedDict()
            newRnd['round'] = score_m.Round
            newRnd['grade'] = Reporter_Ranks.GetGrade(score_m.Perc_AllTime)
            newRnd['perc%'] = "{0:.2f}".format(score_m.Perc_AllTime)
            newRnd['points'] = score_m.Points_AllTime
            alltime.append(newRnd)
            
        rounds = []
        for score_m in score_mdls:
            newRnd = OrderedDict()
            newRnd['round'] = score_m.Round
            newRnd['grade'] = Reporter_Ranks.GetGrade(score_m.Perc_Round)
            newRnd['perc%'] = "{0:.2f}".format(score_m.Perc_Round)
            newRnd['points'] = score_m.Points_Round
            rounds.append(newRnd)
        
        alltime = sorted(alltime, key=lambda k: k['round'], reverse=True) 
        rounds = sorted(rounds, key=lambda k: k['round'], reverse=True) 
        
        results = {
            'alltime': alltime,
            'rounds': rounds,
        } 
        return results
    
    
    # admin report used by bot users
    @staticmethod
    def GetFixturesSummary(p_season):
                
        gameCnt = FT.Game.objects.values_list('Round'
            ).filter(SeasonFK__Season=p_season
            ).annotate(gameCount=Count('Round')
            ).order_by('Round')
        gameCnt = list(gameCnt)
        
        if gameCnt is None or len(gameCnt) == 0:
            hret = CU.HttpReturn()
            hret.results = "No games available."
            hret.status = 200
            return hret
        
        eventCnt = dict(
            FT.GameEvent.objects.values_list('GameFK__Round'
                                ).filter(GameFK__SeasonFK__Season=p_season
                                ).annotate(eventCount=Count('EventFK')) )
        
        predCnt = dict(
            Univ_Prediction.objects.values_list('GameFK__Round'
                                ).filter(GameFK__SeasonFK__Season=p_season
                                ).annotate(predCount=Count('id')) )
        
        data = []    
        for roundCnt in gameCnt:
            newRow = OrderedDict()
            newRow['round'] = roundCnt[0]
            newRow['games'] = roundCnt[1]
            newRow['events'] = eventCnt[roundCnt[0]]  if roundCnt[0] in eventCnt  else 0
            newRow['preds'] = predCnt[roundCnt[0]]  if roundCnt[0] in predCnt  else 0
            data.append(newRow)
        
        colFormat = {
            'round': 'format_center', 
            'games': 'format_center', 
            'events': 'format_center', 
            'preds': 'format_center', 
        }
        
        result = {
            'data': data,
            'colFormat': colFormat,
        }
        
        # return results
        
        hret = CU.HttpReturn()
        hret.results = result
        hret.status = 200
        return hret


class Reporter_Store(object):


    @staticmethod
    def GetStoreData():
        
        store = lambda: None        
        
        store.goalsGuess = []
        for r in range(1, 9, 1):
            store.goalsGuess.append([r,
                                     Reporter_Store.GetUpgradeCost("GoalsGuess", str(r)),
                                     "Goals Guess +1"])
        
        store.scorersGuess = []
        for r in range(1, 9, 1):
            store.scorersGuess.append([r,
                                       Reporter_Store.GetUpgradeCost("ScorersGuess", str(r)),
                                       "Scorers Guess +1"])
        
        store.secondChance = []
        for r in range(1, 5, 1):
            store.secondChance.append([r, Reporter_Store.GetUpgradeCost("SecondChance", str(r)),
                                       "Second Choice +1"])
        
        store.doubleDown = []
        store.doubleDown.append([1,
                                   Reporter_Store.GetUpgradeCost("DoubleDown", str(1)),
                                   "Double Down |1|"])
        store.doubleDown.append([2,
                                   Reporter_Store.GetUpgradeCost("DoubleDown", str(2)),
                                   "Double Down |2|"])
        store.doubleDown.append([3,
                                   Reporter_Store.GetUpgradeCost("DoubleDown", str(3)),
                                   "Double Down |3|"])
        store.doubleDown.append([4,
                                   Reporter_Store.GetUpgradeCost("DoubleDown", str(4)),
                                   "Double Down |4|"])
        
        store.clubFavorite = []
        store.clubFavorite.append([1,
                                   Reporter_Store.GetUpgradeCost("ClubFavorite", str(1)),
                                   "Club Favorite |1|"])
        store.clubFavorite.append([2,
                                   Reporter_Store.GetUpgradeCost("ClubFavorite", str(2)),
                                   "Club Favorite |2|"])
        store.clubFavorite.append([3,
                                   Reporter_Store.GetUpgradeCost("ClubFavorite", str(3)),
                                   "Club Favorite |3|"])
        store.clubFavorite.append([4,
                                   Reporter_Store.GetUpgradeCost("ClubFavorite", str(4)),
                                   "Club Favorite |4|"])
        
        store.tokenRate = []
        store.tokenRate.append([1,
                            Reporter_Store.GetUpgradeCost("TokenRate", str(1)),
                            "Rate 55 tks/day"])
        store.tokenRate.append([2,
                            Reporter_Store.GetUpgradeCost("TokenRate", str(2)),
                            "Rate 60 tks/day"])
        store.tokenRate.append([3,
                            Reporter_Store.GetUpgradeCost("TokenRate", str(3)),
                            "Rate 65 tks/day"])
        store.tokenRate.append([4,
                            Reporter_Store.GetUpgradeCost("TokenRate", str(4)),
                            "Rate 70 tks/day"])
        
        return store.__dict__
    
    
    # helper for GetStoreData()
    @staticmethod
    def GetUpgradeCost(upgradeType, level):
        
        if upgradeType == "GoalsGuess" or upgradeType == 'goalsG':
            if level == '1':      return 350
            elif level == '2':    return 400
            elif level == '3':    return 475
            elif level == '4':    return 575
            elif level == '5':    return 700
            elif level == '6':    return 850
            elif level == '7':    return 1025
            elif level == '8':    return 1225
        
        elif upgradeType == "ScorersGuess" or upgradeType == 'scorersG':
            if level == '1':      return 420
            elif level == '2':    return 470
            elif level == '3':    return 545
            elif level == '4':    return 645
            elif level == '5':    return 770
            elif level == '6':    return 920
            elif level == '7':    return 1095
            elif level == '8':    return 1295
            
        elif upgradeType == "SecondChance" or upgradeType == 'secondChance':
            if level == '1':      return 175
            elif level == '2':    return 255
            elif level == '3':    return 375
            elif level == '4':    return 535
        
        elif upgradeType == "DoubleDown" or upgradeType == 'doubleDown':
            if level == '1':      return 90
            elif level == '2':    return 150
            elif level == '3':    return 240
            elif level == '4':    return 360
        
        elif upgradeType == "ClubFavorite" or upgradeType == 'clubFav':
            if level == '1':      return 160
            elif level == '2':    return 240
            elif level == '3':    return 360
            elif level == '4':    return 520
        
        elif upgradeType == "TokenRate" or upgradeType == 'tokenRate':
            if level == '1':      return 400
            elif level == '2':    return 520
            elif level == '3':    return 700
            elif level == '4':    return 940
        
        return None
    
    
    @staticmethod
    def GetStoreAvailable(p_user, p_season):
        
        avail = {
            'goalsG': False,
            'scorersG': False,
            'doubleDown': False,
            'secondChance': False,
            'clubFav': False,
            'tokenRate': False
        } 
        
        if not p_user.is_authenticated() or not p_season:
            return avail
        
        try:
            rost_m = Univ_Roster.objects.get(UserFK=p_user, SeasonFK__Season=p_season)
        except:
            return avail
        
        cTokens = rost_m.Token_Total
        upgrades = json.loads( rost_m.Upgrades )
        
        for abilType in upgrades:
            nextLvl = upgrades[abilType] +1
            upgCost = Reporter_Store.GetUpgradeCost(abilType, str(nextLvl))
            
            if upgCost:
                if cTokens >= upgCost:
                    avail[abilType] = True
        
        return avail


class Reporter_Ranks(object):
    
    
    # view callable for admin rewards page
    # move to central ?
    @staticmethod
    def RunRewardsData(p_season, p_round):
        
        scores_mdl = Univ_Scoring.objects.filter(SeasonFK__Season=p_season, Round=p_round)
        
        if not scores_mdl:
            return "Scores data not available."
        
        results = {}
        
        # all time
        
        resHistAT = Reporter_Ranks.GetHistogram(p_season, p_round, scores_mdl, "alltime")
        histAT = resHistAT['hist']
        resTemp = {
            'userCntAT': resHistAT['userCnt'],
            'binCntAT': "{0} to {1}, {2} bins".format(resHistAT['binMax'], resHistAT['binMin'], resHistAT['binCnt'])
        }
        results = dict(results, **resTemp);
        
        aggregAT = Reporter_Ranks.GetHistAggreg(histAT)
        resChartAT = Reporter_Ranks.GetCharts(histAT, aggregAT)
        resTemp = {
            'aggregAT': aggregAT,
            'histAT_plt': resChartAT['hist_plt'],
            'gradeAT_plt': resChartAT['grade_plt'],
        }
        results = dict(results, **resTemp);
        
        # by rounds
        
        resHistRD = Reporter_Ranks.GetHistogram(p_season, p_round, scores_mdl, "rounds")
        histRD = resHistRD['hist']
        resTemp = {
            'userCntRD': resHistRD['userCnt'],
            'binCntRD': "{0} to {1}, {2} bins".format(resHistRD['binMax'], resHistRD['binMin'], resHistRD['binCnt'])
        }
        results = dict(results, **resTemp);
        
        aggregRD = Reporter_Ranks.GetHistAggreg(histRD)
        resChartRD = Reporter_Ranks.GetCharts(histRD, aggregRD)
        resTemp = {
            'aggregRD': aggregRD,
            'histRD_plt': resChartRD['hist_plt'],
            'gradeRD_plt': resChartRD['grade_plt'],
        }
        results = dict(results, **resTemp);
        
        return results
    
    
    @staticmethod
    def GetHistogram(p_season, p_round, p_scores, p_period):
        
        # get scorr models based on period
        
        if p_period == "alltime":
            bins_dict = Univ_Scoring.objects.annotate(Perc=F('Perc_AllTime'), Points=F('Points_AllTime')   # aliasing
                                            ).values('Perc', 'Points').distinct('Perc_AllTime'
                                            ).filter(SeasonFK__Season=p_season, Round=p_round)
        else:
            bins_dict = Univ_Scoring.objects.annotate(Perc=F('Perc_Round'), Points=F('Points_Round')
                                            ).values('Perc', 'Points').distinct('Perc_Round'
                                            ).filter(SeasonFK__Season=p_season, Round=p_round)
        
        # create the histogram structure and add counts
        
        hist = []
        for binDx in bins_dict:            
            newBin = {}
            newBin['perc%'] = binDx['Perc']
            newBin['points'] = binDx['Points']
            newBin['count'] = 0
            hist.append(newBin)
        
        userCnt = 0
        for scr_m in p_scores:
            for hBin in hist:
                if p_period == "alltime" and hBin['perc%'] == scr_m.Perc_AllTime:
                    hBin['count'] += 1
                    userCnt += 1
                    break
                elif p_period == "rounds" and hBin['perc%'] == scr_m.Perc_Round:
                    hBin['count'] += 1
                    userCnt += 1
                    break
        
        binMin = 10000
        binMax = -10000
        for binDx in bins_dict:
            if binDx['Points'] < binMin:
                binMin = binDx['Points']
            if binDx['Points'] > binMax:
                binMax = binDx['Points']
        
        results = {
            'hist': hist,
            'userCnt': userCnt,
            'binCnt': len(hist),
            'binMin': binMin,
            'binMax': binMax,
        }
        return results
    
    
    @staticmethod
    def GetHistAggreg(p_hist):
        
        aggreg = [
            { 'grade': "A", 'percGroup': 99, 'percCnt': 0, 'userCnt': 0, 'pntRange': [10000, -10000], 'details': [] },
            { 'grade': "B", 'percGroup': 96, 'percCnt': 0, 'userCnt': 0, 'pntRange': [10000, -10000], 'details': [] },
            { 'grade': "C", 'percGroup': 91, 'percCnt': 0, 'userCnt': 0, 'pntRange': [10000, -10000], 'details': [] },
            { 'grade': "D", 'percGroup': 84, 'percCnt': 0, 'userCnt': 0, 'pntRange': [10000, -10000], 'details': [] },
            { 'grade': "E", 'percGroup': 75, 'percCnt': 0, 'userCnt': 0, 'pntRange': [10000, -10000], 'details': [] },
            { 'grade': "F", 'percGroup': 64, 'percCnt': 0, 'userCnt': 0, 'pntRange': [10000, -10000], 'details': [] },
            { 'grade': "G", 'percGroup': 51, 'percCnt': 0, 'userCnt': 0, 'pntRange': [10000, -10000], 'details': [] },
            { 'grade': "H", 'percGroup': 36, 'percCnt': 0, 'userCnt': 0, 'pntRange': [10000, -10000], 'details': [] },
            { 'grade': "I", 'percGroup': 19, 'percCnt': 0, 'userCnt': 0, 'pntRange': [10000, -10000], 'details': [] },            
            { 'grade': "J", 'percGroup': 0 , 'percCnt': 0, 'userCnt': 0, 'pntRange': [10000, -10000], 'details': [] },            
        ]
        
        for hBin in p_hist:
            for currGroup in aggreg:
                if hBin['perc%'] > currGroup['percGroup']:
                    currGroup['percCnt'] += 1
                    currGroup['userCnt'] += hBin['count']
                    
                    if hBin['points'] < currGroup['pntRange'][0]:
                        currGroup['pntRange'][0] = hBin['points']
                    
                    if hBin['points'] > currGroup['pntRange'][1]:
                        currGroup['pntRange'][1] = hBin['points']
                    
                    currGroup['details'].append({
                                    'perc%': "{0:.2f}".format(hBin['perc%']),
                                    'points': hBin['points'],
                                    'count': hBin['count'],
                                })
                    break
        
        return aggreg
    
    
    # creates a histogram of percentiles in flot data format
    @staticmethod
    def GetCharts(p_hist, p_aggreg, p_score=None):
        
        # transform histogram data into format for bar series
        # also pull out user's score for highlight
        
        hist_plt = []
        highlight_plt = []
        for b in range(0, len(p_hist)):       # range [min, max)
            currBin = p_hist[b]
            newBin = [currBin['points'], currBin['count']]
            if currBin['points'] != p_score:        
                hist_plt.append(newBin)
            else:
                highlight_plt.append(newBin)
        
        # create ranks for the line series
        
        grade = "A"
        grade_plt = []
        for b in range(0, len(p_aggreg)):
            currGroup = p_aggreg[b]
            
            if currGroup['percCnt'] == 0:
                grade = chr(ord(grade) +1)
                continue
            
            minPnt = currGroup['pntRange'][0] -1   
            maxPnt = currGroup['pntRange'][1]
            
            grade_plt.append([ maxPnt, 0 ])
            grade_plt.append([ maxPnt, currGroup['userCnt'] ])
            grade_plt.append([ (minPnt + maxPnt) /2, currGroup['userCnt'], grade ])
            grade_plt.append([ minPnt, currGroup['userCnt'] ])
            grade_plt.append([ minPnt, 0 ])
            
            grade = chr(ord(grade) +1)
            
        results = {
            'hist_plt': hist_plt,
            'grade_plt': grade_plt,
            'highlight_plt': highlight_plt,
        }
        return results
    
    
    # view callable for standings page
    @staticmethod
    def RunRankData(p_season, p_round, p_mode, p_user_md):
        
        scores_mdl = Univ_Scoring.objects.filter(SeasonFK__Season=p_season, Round=p_round).order_by('UserFK__username')
        results = {}
        
        # all time
        
        resHistAT = Reporter_Ranks.GetHistogram(p_season, p_round, scores_mdl, "alltime")
        histAT = resHistAT['hist']
        if resHistAT['userCnt']:
            binCntAT = "{0} to {1}, {2} bins".format(resHistAT['binMax'], resHistAT['binMin'], resHistAT['binCnt'])
        else:
            binCntAT = "None"
        resTemp = {
            'userCntAT': resHistAT['userCnt'],
            'binCntAT': binCntAT,
        }
        results = dict(results, **resTemp);
        
        aggregAT = Reporter_Ranks.GetHistAggreg(histAT)
        try:
            score = scores_mdl.values_list('Points_AllTime', flat=True).get(UserFK=p_user_md)
        except:
            score = None
        resChartAT = Reporter_Ranks.GetCharts(histAT, aggregAT, score)
        resTemp = {
            'histAT': resChartAT['hist_plt'],
            'gradeAT': resChartAT['grade_plt'],
            'highlightAT': resChartAT['highlight_plt'],
        }
        results = dict(results, **resTemp);
        
        # by rounds
        
        resHistRD = Reporter_Ranks.GetHistogram(p_season, p_round, scores_mdl, "rounds")
        histRD = resHistRD['hist']
        if resHistRD['userCnt']:
            binCntRD = "{0} to {1}, {2} bins".format(resHistRD['binMax'], resHistRD['binMin'], resHistRD['binCnt'])
        else:
            binCntRD = "None"
        resTemp = {
            'userCntRD': resHistRD['userCnt'],
            'binCntRD': binCntRD,
        }
        results = dict(results, **resTemp);
        
        aggregRD = Reporter_Ranks.GetHistAggreg(histRD)
        try:
            score = scores_mdl.values_list('Points_Round', flat=True).get(UserFK=p_user_md)
        except:
            score = None
        resChartRD = Reporter_Ranks.GetCharts(histRD, aggregRD, score)
        resTemp = {
            'histRD': resChartRD['hist_plt'],
            'gradeRD': resChartRD['grade_plt'],
            'highlightRD': resChartRD['highlight_plt'],
        }
        results = dict(results, **resTemp);
        
        # user ranks info
        
        resTemp = Reporter_Ranks.GetRanks(scores_mdl, p_user_md, p_mode)
        results = dict(results, **resTemp);
        
        return results
    
    
    @staticmethod
    def GetRanks(p_scores, p_user_md, p_mode):
        
        # users are already ranked, just format the output for display
        
        ranksAT_dict = []
        ranksRD_dict = []
        for rank_m in p_scores:
            
            newRAT = OrderedDict()
            newRAT['user'] = rank_m.UserFK.username
            newRAT['perc%'] = "{0:.2f}".format(rank_m.Perc_AllTime)
            #newRAT['rank'] = rank_m.Rank_AllTime
            newRAT['points'] = rank_m.Points_AllTime
            ranksAT_dict.append(newRAT)
            
            newRRD = OrderedDict()
            newRRD['user'] = rank_m.UserFK.username
            newRRD['perc%'] = "{0:.2f}".format(rank_m.Perc_Round)
            #newRRD['rank'] = rank_m.Rank_Round
            newRRD['points'] = rank_m.Points_Round
            ranksRD_dict.append(newRRD)
        
        ranksAT_dict = sorted(ranksAT_dict, key=lambda k: k['points']*(-1))
        ranksRD_dict = sorted(ranksRD_dict, key=lambda k: k['points']*(-1)) 
                
        # the filter functions require a sorted array
        
        if p_mode == 'Yours' and p_user_md.is_authenticated():
            ranksAT_dict = Reporter_Ranks.FilterRank_User(ranksAT_dict, p_user_md.username) 
            ranksRD_dict = Reporter_Ranks.FilterRank_User(ranksRD_dict, p_user_md.username)
                    
        elif p_mode == 'Friends' and p_user_md.is_authenticated():
            ranksAT_dict = Reporter_Ranks.FilterRank_Friend(ranksAT_dict, p_user_md) 
            ranksRD_dict = Reporter_Ranks.FilterRank_Friend(ranksRD_dict, p_user_md) 
            #ranksAT_dict = sorted(ranksAT_dict, key=lambda k: k['points']*(-1))
            #ranksRD_dict = sorted(ranksRD_dict, key=lambda k: k['points']*(-1)) 
        
        else:
            ranksAT_dict = Reporter_Ranks.FilterRank_Top(ranksAT_dict) 
            ranksRD_dict = Reporter_Ranks.FilterRank_Top(ranksRD_dict)
        
        
        if not isinstance(ranksAT_dict, str):
            for rank in ranksAT_dict:
                prof_m = MM.Profile_Reporter.GetUserData(rank['user'])
                rank['icon'] = prof_m['icon']
                rank['slogan'] = prof_m['slogan']
                rank['favClub'] = prof_m['favClub']
            
        if not isinstance(ranksRD_dict, str):        
            for rank in ranksRD_dict:
                prof_m = MM.Profile_Reporter.GetUserData(rank['user'])
                rank['icon'] = prof_m['icon']
                rank['slogan'] = prof_m['slogan']
                rank['favClub'] = prof_m['favClub']
        
        
        ranks = {
            'ranksAT': ranksAT_dict,
            'ranksRD': ranksRD_dict,
        }
        return ranks
    
    
    @staticmethod
    def FilterRank_User(ranks_dict, user):
        
        threshold = 10
        
        userIdx = -1
        for idx, rnk in enumerate(ranks_dict):
            if rnk['user'] == user:
                userIdx = idx
                break
        
        if userIdx == -1:
            return "No user scores for the round."
        
        start = userIdx - (threshold -1)
        end = userIdx + threshold +1
        
        if start < 0:
            start = 0
            end -= userIdx - (threshold -1)
            
        if end > len(ranks_dict):
            end = len(ranks_dict)
            start -= userIdx + threshold +1 - len(ranks_dict)
        
        if start < 0:
            start = 0
        
        if end > len(ranks_dict):
            end = len(ranks_dict)
        
        filtered = ranks_dict[start:end]
        
        return filtered
    
    
    @staticmethod
    def FilterRank_Friend(ranks_dx, p_user_md):
        friends = MM.Relationship_R.GetFriendData(p_user_md)
        
        ranks = []
        for rnk in ranks_dx:
            
            if rnk['user'] == p_user_md.username:
                ranks.append(rnk)
                continue
            
            for frd in friends:
                if rnk['user'] == frd['name']:
                    ranks.append(rnk)
                    break
        
        return ranks
    
    
    @staticmethod
    def FilterRank_Top(ranks_dict):
        
        threshold = 10
        userIdx = 0
        
        start = userIdx - (threshold -1)
        end = userIdx + threshold +1
        
        if start < 0:
            start = 0
            end -= userIdx - (threshold -1)
        
        if end > len(ranks_dict):
            end = len(ranks_dict)
            start -= userIdx + threshold +1 - len(ranks_dict)
        
        if start < 0:
            start = 0
        
        if end > len(ranks_dict):
            end = len(ranks_dict)
                
        filtered = ranks_dict[start:end]
        
        return filtered
    
    
    @staticmethod
    def GetGrade(p_perc):
        if (p_perc >= 99):
            return "A"
        elif (p_perc >= 96):
            return "B"
        elif (p_perc >= 91):
            return "C"
        elif (p_perc >= 84):
            return "D"
        elif (p_perc >= 75):
            return "E"
        elif (p_perc >= 64):
            return "F"
        elif (p_perc >= 51):
            return "G"
        elif (p_perc <= 36):
            return "H"
        elif (p_perc <= 19):
            return "I"
        else:
            return "J"
    
    
    @staticmethod
    def GetTopRanks():
        currTime = FM.TimeMachine.GetTodaysBracket()
        season = currTime['season']
        rround = currTime['round']
        period = FM.TimeMachine.GetRoundPeriod(season, rround)
        
        if not rround:
            return []
        
        if period == 0 and rround != '01':
            rround = CU.Pad2(int(rround) -1)  
        
        scores_mdl = Univ_Scoring.objects.filter(SeasonFK__Season=season, Round=rround).order_by('UserFK__username')
        
        # user scores are already ranked, just format the output for display
        
        ranks_dict = []
        for rank_m in scores_mdl:
            newRank = OrderedDict()
            newRank['user'] = rank_m.UserFK.username
            newRank['perc%'] = "{0:.2f}".format(rank_m.Perc_Round)
            newRank['rank'] = rank_m.Rank_Round
            newRank['points'] = rank_m.Points_Round
            ranks_dict.append(newRank)
        
        ranks_dict = sorted(ranks_dict, key=lambda k: k['points']*(-1))
        
        # the filter functions require a sorted array
        
        ranks_dict = ranks_dict[0:4]
        
        cRank = 1
        for rank_dx in ranks_dict:
            rank_dx['rank'] = cRank
            cRank += 1
        
        # add the user's custom info to the rank data
        
        if not isinstance(ranks_dict, str):
            for rank in ranks_dict:
                prof_m = MM.Profile_Reporter.GetUserData(rank['user'])
                rank['icon'] = prof_m['icon']
                rank['slogan'] = prof_m['slogan']
                rank['favClub'] = prof_m['favClub']
        
        return ranks_dict
    
    
    
    # not in use
    @staticmethod
    def GetUserGrade(p_season, p_round, p_user_md):
        
        currScr_md = None
        
        if p_user_md.is_authenticated():
            currScr_mdls = Univ_Scoring.objects.filter(SeasonFK__Season=p_season, Round=p_round, UserFK=p_user_md)
            if len(currScr_mdls) == 1:
                currScr_md = currScr_mdls[0]
        
        lastScr_md = None
        if p_round != "01" and p_user_md.is_authenticated():
            prevRnd = CU.Pad2(int(p_round) -1)
            lastScr_mdls = Univ_Scoring.objects.filter(SeasonFK__Season=p_season, Round=prevRnd, UserFK=p_user_md)
            if len(lastScr_mdls) == 1:
                lastScr_md = lastScr_mdls[0]
        
        
        # all time stats
        
        statsAT_dict = []
        
        newStat = OrderedDict()
        newStat['stat'] = "Grade"
        newStat['current'] = Reporter_Ranks.GetGrade(currScr_md.Perc_AllTime)   if currScr_md   else "None"
        newStat['last'] = Reporter_Ranks.GetGrade(lastScr_md.Perc_AllTime)   if lastScr_md   else "None"
        statsAT_dict.append(newStat)
        
        newStat = OrderedDict()
        newStat['stat'] = "Points"
        newStat['current'] = currScr_md.Points_AllTime   if currScr_md   else "None"
        newStat['last'] = lastScr_md.Points_AllTime   if lastScr_md   else "None"
        statsAT_dict.append(newStat)
        
        newStat = OrderedDict()
        newStat['stat'] = "Perc%"
        newStat['current'] = "{0:.2f}".format(currScr_md.Perc_AllTime)   if currScr_md   else "None"
        newStat['last'] = "{0:.2f}".format(lastScr_md.Perc_AllTime)   if lastScr_md   else "None"
        statsAT_dict.append(newStat)
        
        
        # by round stats
        
        statsRD_dict = []
        
        newStat = OrderedDict()
        newStat['stat'] = "Grade"
        newStat['current'] = Reporter_Ranks.GetGrade(currScr_md.Perc_Round)   if currScr_md   else "None"
        newStat['last'] = Reporter_Ranks.GetGrade(lastScr_md.Perc_Round)   if lastScr_md   else "None"
        statsRD_dict.append(newStat)
        
        newStat = OrderedDict()
        newStat['stat'] = "Points"
        newStat['current'] = currScr_md.Points_Round   if currScr_md   else "None"
        newStat['last'] = lastScr_md.Points_Round   if lastScr_md   else "None"
        statsRD_dict.append(newStat)
        
        newStat = OrderedDict()
        newStat['stat'] = "Perc%"
        newStat['current'] = "{0:.2f}".format(currScr_md.Perc_Round)   if currScr_md   else "None"
        newStat['last'] = "{0:.2f}".format(lastScr_md.Perc_Round)   if lastScr_md   else "None"
        statsRD_dict.append(newStat)
        
        
        colFmt = {
            'stat': 'font_bold',
            'current': 'format_center',
            'last': 'format_center',
        }
        
        
        # get period data
        
        rndFinish = FM.TimeMachine.GetRoundPeriod(p_season, p_round)
        
        if rndFinish == 0:
            rndPeriod = "Round hasn't started."
            
        elif rndFinish == 8:
            rndPeriod = "Rewards to be sent."
            score_mdls = Univ_Scoring.objects.filter(SeasonFK__Season=p_season, Round=p_round)
            rewFin = True
            for score_m in score_mdls:
                if score_m.RewardStatus == 0:
                    rewFin = False
                    break
            if rewFin:
                rndPeriod = "Rewards sent."
        
        else:
            rndPeriod = "{0}/8 games finished.".format(rndFinish)
        
        
        # results structure
        
        results = {
            'statsAT': statsAT_dict,
            'statsRD': statsRD_dict,
            'statsFmt': colFmt,
            'rndPeriod': rndPeriod,
        }
        return results
    
    
    
    @staticmethod
    def GetRewardStatus(p_season, p_rndMax):
        
        # multiple list of dicts for aggregating data from
        # sort by round so matched round datas can be easily found
        
        scoreTotal_dict = Univ_Scoring.objects.values('Round', 
                                                ).filter(SeasonFK__Season=p_season, Round__lte=p_rndMax
                                                ).annotate(UserCnt=Count('Round')
                                                ).order_by('Round')
        
        scoreRew_dict = Univ_Scoring.objects.values('Round', 
                                                ).filter(SeasonFK__Season=p_season, Round__lte=p_rndMax, RewardStatus=1
                                                ).annotate(RewCnt=Count('Round')
                                                ).order_by('Round')
        
        scoreClaim_dict = Univ_Scoring.objects.values('Round', 
                                                ).filter(SeasonFK__Season=p_season, Round__lte=p_rndMax, RewardStatus=2
                                                ).annotate(ClaimCnt=Count('Round')
                                                ).order_by('Round')
        
        games_dict = FT.Game.objects.values('Round'
                                        ).filter(SeasonFK__Season=p_season
                                        ).exclude(GoalsHome__isnull=True
                                        ).annotate(GameCnt=Count('Round')
                                        ).order_by('Round')
        
        rewSummary_dict = []        
        for s in range(0, len(scoreTotal_dict), 1):
            refMain = scoreTotal_dict[s]
            refGames = games_dict[s]
            rewCnt = 0
            claimCnt = 0
            
            for rewItem in scoreRew_dict:
                if rewItem['Round'] == refMain['Round']:
                    rewCnt = rewItem['RewCnt']
            
            for claimItem in scoreClaim_dict:
                if claimItem['Round'] == refMain['Round']:
                    claimCnt = claimItem['ClaimCnt']
            
            newDx = OrderedDict() 
            newDx['round'] = refMain['Round']
            newDx['StartDate'] = FM.TimeMachine.GetFirstPlayDate(p_season, refMain['Round']).strftime(CU.FORMAT_DTSTR_DT)
            newDx['games'] = refGames['GameCnt'] 
            newDx['users'] = refMain['UserCnt'] 
            newDx['Rewards'] = rewCnt 
            newDx['claimed'] = claimCnt 
            rewSummary_dict.append(newDx) 
        
        rewSummary_dict = sorted(rewSummary_dict, key=lambda k: k['round'], reverse=True) 
        
        colFmt = {
            'round': 'format_center',
            'games': 'format_center',
            'users': 'format_center',
            'rewards': 'format_center',
            'claimed': 'format_center',
        }
        
        results = {
            'scoreSummary': rewSummary_dict,
            'colFmt': colFmt,
        }
        return results
    
    
    @staticmethod
    def GetRewardValues(p_percAT, p_percRD):
        
        rewAT = None
        rewTableAT = Reporter_Ranks.GetRewardTableAT()
        for rew in rewTableAT:
            if p_percAT >= rew['perc']:
                rewAT = rew
                break
        
        rewRD = None
        rewTableRD = Reporter_Ranks.GetRewardTableRD()
        for rew in rewTableRD:
            if p_percRD >= rew['perc']:
                rewRD = rew
                break
        
        results = {
            'rewAT': rewAT, 
            'rewRD': rewRD, 
            'rewTotal': { 'diamonds': rewAT['diamonds'] + rewRD['diamonds'] ,
                          'tokens': rewAT['tokens'] + rewRD['tokens'] },            
        }
        return results
    
    
    @staticmethod
    def GetRewardTableAT():
        table = []
        table.append({ 'perc': 99 , 'grade': "A", 'diamonds': 29 , 'tokens': 80 })
        table.append({ 'perc': 96 , 'grade': "B", 'diamonds': 25 , 'tokens': 75 })
        table.append({ 'perc': 91 , 'grade': "C", 'diamonds': 22 , 'tokens': 70 })
        table.append({ 'perc': 84 , 'grade': "D", 'diamonds': 19 , 'tokens': 65 })
        table.append({ 'perc': 75 , 'grade': "E", 'diamonds': 17 , 'tokens': 60 })
        table.append({ 'perc': 64 , 'grade': "F", 'diamonds': 15 , 'tokens': 55 })
        table.append({ 'perc': 51 , 'grade': "G", 'diamonds': 13 , 'tokens': 50 })
        table.append({ 'perc': 36 , 'grade': "H", 'diamonds': 12 , 'tokens': 45 })
        table.append({ 'perc': 19 , 'grade': "I", 'diamonds': 11 , 'tokens': 40 })
        table.append({ 'perc': 0  , 'grade': "J", 'diamonds': 10 , 'tokens': 35 })
        return table
    
    
    @staticmethod
    def GetRewardTableRD():
        table = []
        table.append({ 'perc': 99 , 'grade': "A", 'diamonds': 16 , 'tokens': 130 })
        table.append({ 'perc': 96 , 'grade': "B", 'diamonds': 15 , 'tokens': 120 })
        table.append({ 'perc': 91 , 'grade': "C", 'diamonds': 14 , 'tokens': 112 })
        table.append({ 'perc': 84 , 'grade': "D", 'diamonds': 13 , 'tokens': 104 })
        table.append({ 'perc': 75 , 'grade': "E", 'diamonds': 12 , 'tokens': 97 })
        table.append({ 'perc': 64 , 'grade': "F", 'diamonds': 11 , 'tokens': 90 })
        table.append({ 'perc': 51 , 'grade': "G", 'diamonds': 10 , 'tokens': 83 })
        table.append({ 'perc': 36 , 'grade': "H", 'diamonds': 9 , 'tokens': 77 })
        table.append({ 'perc': 19 , 'grade': "I", 'diamonds': 8 , 'tokens': 71 })
        table.append({ 'perc': 0  , 'grade': "J", 'diamonds': 7 , 'tokens': 65 })
        return table


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
EDITOR CLASSES
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


class Editor(object):
    
    
    @staticmethod
    def PopTokenAccumulator(p_user):
        
        hret = CU.HttpReturn()
        
        season = FM.TimeMachine.GetTodaysBracket()['season']
        if not season:
            hret.results = "Off-season"
            hret.status = 201
            return hret
        
        try:
            rost_m = Univ_Roster.objects.get(UserFK=p_user, SeasonFK__Season=season)
        except Univ_Roster.DoesNotExist:
            hret.results = "UP Roster not found for " + season +"."
            hret.status = 501
            return hret
        
        # get accumulated token data to return
        
        tokenData = Reporter.CalcTokenData(rost_m.Token_LastPop, rost_m.Token_Rate)
        tokensFull = lambda: None        
        tokensFull.currAccumToken = tokenData.tokens
        tokensFull.currTokenPerc = '{0:.1f}'.format(tokenData.tokens / tokenData.tokenMax * 100)
        tokensFull.currTokenTotal = rost_m.Token_Total
        tokensFull.nextTokenTotal = rost_m.Token_Total + tokenData.tokens
        
        # only update if there is more than 0 accumulated tokens, otherwise accumulation time is lost
        # some time is always lost since the calculations for current accumulated token round down
        
        if tokenData.tokens > 0:
            profile_m = MM.Profile_Reporter.GetProfile_Mdl(p_user)
            lastPop_tz = FM.TimeMachine.GetCustomNow() 
            tokensFull.lastPop = lastPop_tz.strftime(CU.FORMAT_DTSTR_SECS)
            
            rost_m.Token_LastPop = lastPop_tz       
            rost_m.Token_Total = rost_m.Token_Total + tokenData.tokens
            rost_m.save()
        
        hret.results = tokensFull.__dict__
        hret.status = 201
        return hret
    
    
    @staticmethod
    def UpgradeBuy(user, upgradeType, upgradeLevel):
        
        hret = CU.HttpReturn()
        season = FM.TimeMachine.GetTodaysBracket()['season']
        
        try:
            roster_m = Univ_Roster.objects.get(UserFK=user, SeasonFK__Season=season)
        except Univ_Roster.DoesNotExist:
            hret.results = "Roster not found."
            hret.status = 401
            return hret
        
        # check for errors, in case UI/http gets hacked
        
        levelM = int(upgradeLevel) -1
        upgrades_dx = json.loads(roster_m.Upgrades)
        
        if ( upgradeType == "GoalsGuess" and upgrades_dx['goalsG'] != levelM) or \
            (upgradeType == "ScorersGuess" and upgrades_dx['scorersG'] != levelM) or \
            (upgradeType == "SecondChance" and upgrades_dx['secondChance'] != levelM) or \
            (upgradeType == "DoubleDown" and upgrades_dx['doubleDown'] != levelM) or \
            (upgradeType == "ClubFavorite" and upgrades_dx['clubFav'] != levelM) or \
            (upgradeType == "TokenRate" and upgrades_dx['tokenRate'] != levelM ):
            hret.results = "Level requirement not met."
            hret.status = 201
            return hret
        
        cost = Reporter_Store.GetUpgradeCost(upgradeType, upgradeLevel)
        
        if cost > roster_m.Token_Total:
            hret.results = "Insufficient tokens."
            hret.status = 201
            return hret
        
        # apply upgrade
        
        roster_m.Token_Total = roster_m.Token_Total - cost
        
        if upgradeType == "GoalsGuess":
            upgrades_dx['goalsG'] += 1
        
        elif upgradeType == "ScorersGuess":
            upgrades_dx['scorersG'] += 1
        
        elif upgradeType == "SecondChance":
            upgrades_dx['secondChance'] += 1
            
        elif upgradeType == "DoubleDown":
            upgrades_dx['doubleDown'] += 1
        
        elif upgradeType == "ClubFavorite":
            upgrades_dx['clubFav'] += 1
        
        elif upgradeType == "TokenRate":
            upgrades_dx['tokenRate'] += 1
            
            if upgradeLevel == '1':
                roster_m.Token_Rate = Decimal('0.0381944444444444')
            elif upgradeLevel == '2':
                roster_m.Token_Rate = Decimal('0.0416666666666667')
            elif upgradeLevel == '3':
                roster_m.Token_Rate = Decimal('0.0451388888888889')
            elif upgradeLevel == '4':
                roster_m.Token_Rate = Decimal('0.0486111111111111')
        
        roster_m.Upgrades = json.dumps(upgrades_dx)
        roster_m.save()
        
        hret.results = "Purchase successful."
        hret.status = 201        
        return hret
    
    
    
    # creates predictions for user, season, round when predictions.html is rendered
    @staticmethod
    def GetOrCreatePreds(p_season, p_round, p_user_md):
        
        try:
            season_m = FT.Season.objects.get(Season=p_season)
        except FT.Season.DoesNotExist:
            return "Season not found."
        
        predFmt = []
        game_mdls = FT.Game.objects.filter(SeasonFK=season_m, Round=p_round)
        
        if p_user_md.is_authenticated():
            
            preds_mdls = Univ_Prediction.objects.filter(GameFK__in=game_mdls, UserFK=p_user_md)
            
            if not preds_mdls:            
                for game_m in game_mdls:
                    dates = Reporter_Common.GetPredictionWindow(game_m.PlayDate)
                    
                    pred_m, created = Univ_Prediction.objects.get_or_create(
                        UserFK=p_user_md, GameFK=game_m,
                        OpenDate=dates['open'], CloseDate=dates['close'])
                
                preds_mdls = Univ_Prediction.objects.filter(GameFK__in=game_mdls, UserFK=p_user_md)
            
            profile_m = MM.Profile_Reporter.GetProfile_Mdl(p_user_md)
            profTZ = pytz.timezone(profile_m.TimeZone   if profile_m.TimeZone   else 'UTC')
            
            
            for pred_m in preds_mdls:
                
                if pred_m.ScorerHomeFK:
                    scorerHome = "{} {}".format(pred_m.ScorerHomeFK.FirstName, pred_m.ScorerHomeFK.LastName)
                else:
                    scorerHome = None
                
                if pred_m.ScorerAwayFK:
                    scorerAway = "{} {}".format(pred_m.ScorerAwayFK.FirstName, pred_m.ScorerAwayFK.LastName)
                else:
                    scorerAway = None
                
                predF = OrderedDict()
                predF['gameid'] = pred_m.GameFK.id
                predF['open_date'] = pred_m.OpenDate.astimezone(profTZ).strftime(CU.FORMAT_DTSTR) 
                predF['close_date'] = pred_m.CloseDate.astimezone(profTZ).strftime(CU.FORMAT_DTSTR) 
                predF['result'] = pred_m.Result
                predF['goals_home'] = pred_m.GoalsHome
                predF['goals_away'] = pred_m.GoalsAway
                predF['scorer_home'] = scorerHome
                predF['scorer_away'] = scorerAway
                predF['abilsUsed'] = json.loads(pred_m.AbilitiesUsed)   if pred_m.AbilitiesUsed   else None
                predF['pnts_result'] = pred_m.PntsResult
                predF['pnts_goals'] = pred_m.PntsGoal
                predF['pnts_scorers'] = pred_m.PntsScorer
                predF['pnts_total'] = pred_m.PntsTotal
                predFmt.append(predF)
        
        else:           # user is not authenticated
            
            for game_m in game_mdls:
                dates = Reporter_Common.GetPredictionWindow(game_m.PlayDate)
                
                predF = OrderedDict()
                predF['gameid'] = game_m.id
                predF['open_date'] = dates['open'].strftime(CU.FORMAT_DTSTR) 
                predF['close_date'] = dates['close'].strftime(CU.FORMAT_DTSTR) 
                predF['result'] = None
                predF['goals_home'] = game_m.GoalsHome
                predF['goals_away'] = game_m.GoalsAway
                predF['scorer_home'] = game_m.ScorersHome
                predF['scorer_away'] = game_m.ScorersAway
                predF['abilsUsed'] = None
                predF['pnts_result'] = None
                predF['pnts_goals'] = None
                predF['pnts_scorers'] = None
                predF['pnts_total'] = None
                predFmt.append(predF)
        
        return predFmt
    
    
    @staticmethod
    def SavePrediction(p_user_md, p_predDx):
        hret = CU.HttpReturn()
        
        pred_m = Univ_Prediction.objects.get(UserFK=p_user_md, GameFK__id=p_predDx['gameid']) 
        
        # silly check, just make sure the prediction window still lines up
        
        candOpen_dt = CU.TZStringToDT(p_predDx['open_date'])
        candClose_dt = CU.TZStringToDT(p_predDx['close_date'])
        
        if candOpen_dt != pred_m.OpenDate or candClose_dt != pred_m.CloseDate:
            hret.results = "Prediction window verification failure."
            hret.status = 422        
            return hret
        
        # check that now is inside the prediction window
        
        now_dt = FM.TimeMachine.GetCustomNow()
        
        if now_dt < pred_m.OpenDate or now_dt > pred_m.CloseDate:
            hret.results = "Prediction is outside of window."
            hret.status = 422
            return hret
        
        # check that abilites used don't exceed abilities owned
        
        abilsUsedRound = Editor.GetAbilsUsedSkipGame(p_user_md, p_predDx['gameid'])
        abilsUsed_dx = p_predDx['abilsUsed'] 
        
        if 'goalsG' in abilsUsed_dx:
            abilsUsedRound['goalsG'] += 1
        if 'scorersG' in abilsUsed_dx:
            abilsUsedRound['scorersG'] += 1
        if 'secondChance' in abilsUsed_dx:
            abilsUsedRound['secondChance'] += len(abilsUsed_dx['secondChance'])
        if 'doubleDown' in abilsUsed_dx:
            abilsUsedRound['doubleDown'] += len(abilsUsed_dx['doubleDown'])
        if 'clubFav' in abilsUsed_dx:
            abilsUsedRound['clubFav'] = 1
        
        season = pred_m.GameFK.SeasonFK.Season
        abilsOwned = Reporter.GetAbilitiesOwned(p_user_md, season)
        
        if  abilsUsedRound['goalsG'] > abilsOwned['goalsG']['uses'] or \
            abilsUsedRound['scorersG'] > abilsOwned['scorersG']['uses'] or \
            abilsUsedRound['secondChance'] > abilsOwned['secondChance']['uses'] or \
            abilsUsedRound['doubleDown'] > abilsOwned['doubleDown']['uses'] or \
            abilsUsedRound['clubFav'] > abilsOwned['clubFav']['uses'] :
            hret.results = "Invalid ability use."
            hret.status = 422        
            return hret
        
        # check for user data quality
        
        scorerHm_m = scorerAw_m = scorerHmSC_m = scorerAwSC_m = None
        
        if p_predDx['goals_home'] is not None and p_predDx['goals_away'] is None or \
           p_predDx['goals_home'] is None and p_predDx['goals_away'] is not None: 
            hret.results = "Both goal guesses are required."
            hret.status = 422
            return hret
        
        if 'secondChance' in abilsUsed_dx and 'goals' in abilsUsed_dx['secondChance'] and \
            (abilsUsed_dx['secondChance']['goals']['home'] is not None and abilsUsed_dx['secondChance']['goals']['away'] is None or \
             abilsUsed_dx['secondChance']['goals']['home'] is None and abilsUsed_dx['secondChance']['goals']['away'] is not None ): 
            hret.results = "Both goal guesses are required for second chance."
            hret.status = 422
            return hret
        
        if p_predDx['scorer_home']:
            try:
                scorerHm_m = FT.Player.objects.annotate(FirstLast=Concat('FirstName', Value(' '), 'LastName')
                                            ).get(FirstLast=p_predDx['scorer_home'])
            except FT.Player.DoesNotExist:
                hret.results = "Home scorer not found."
                hret.status = 422
                return hret
        
        if p_predDx['scorer_away']:
            try:
                scorerAw_m = FT.Player.objects.annotate(FirstLast=Concat('FirstName', Value(' '), 'LastName')
                                            ).get(FirstLast=p_predDx['scorer_away'])
            except FT.Player.DoesNotExist:
                hret.results = "Away scorer not found."
                hret.status = 422
                return hret
        
        if 'secondChance' in abilsUsed_dx and 'scorers' in abilsUsed_dx['secondChance'] and 'home' in abilsUsed_dx['secondChance']['scorers']:
            try:
                scorerHmSC_m = FT.Player.objects.annotate(FirstLast=Concat('FirstName', Value(' '), 'LastName')
                                            ).get(FirstLast=abilsUsed_dx['secondChance']['scorers']['home'])
            except FT.Player.DoesNotExist:
                hret.results = "Home scorer not found for second chance."
                hret.status = 422
                return hret
        
        if 'secondChance' in abilsUsed_dx and 'scorers' in abilsUsed_dx['secondChance'] and 'away' in abilsUsed_dx['secondChance']['scorers']:
            try:
                scorerAwSC_m = FT.Player.objects.annotate(FirstLast=Concat('FirstName', Value(' '), 'LastName')
                                            ).get(FirstLast=abilsUsed_dx['secondChance']['scorers']['away'])
            except FT.Player.DoesNotExist:
                hret.results = "Away scorer not found for second chance."
                hret.status = 422
                return hret
        
        # update prediction model
        
        pred_m.Result = p_predDx['result']
        pred_m.GoalsHome = p_predDx['goals_home']
        pred_m.GoalsAway = p_predDx['goals_away']
        pred_m.ScorerHomeFK = scorerHm_m
        pred_m.ScorerAwayFK = scorerAw_m
        pred_m.AbilitiesUsed = json.dumps(abilsUsed_dx)
        pred_m.save()
        
        hret.results = "Save prediction successfull."
        hret.status = 201        
        return hret
    
    
    # helper for SavePrediction
    @staticmethod
    def GetAbilsUsedSkipGame(p_user, p_gameID):
        
        bracket = FT.Game.objects.annotate(Season=F('SeasonFK__Season')     # aliasing!
                                ).values('Season', 'Round'
                                ).get(id=p_gameID)
        
        abilsUsed_strg = Univ_Prediction.objects.values_list('AbilitiesUsed', flat=True
                                ).filter(UserFK=p_user,
                                    GameFK__SeasonFK__Season=bracket['Season'], GameFK__Round=bracket['Round']
                                ).exclude(GameFK__id=p_gameID)
        
        abilityUses = {'goalsG': 0, 'scorersG': 0, 'secondChance': 0, 'doubleDown': 0, 'clubFav': 0}
        
        for abilUses in abilsUsed_strg:
            
            if not abilUses:
                continue
            
            abils_ob = json.loads(abilUses) 
            
            if 'goalsG' in abils_ob:
                abilityUses['goalsG'] += 1
            if 'scorersG' in abils_ob:
                abilityUses['scorersG'] += 1
            if 'secondChance' in abils_ob:
                abilityUses['secondChance'] += len(abils_ob['secondChance'])
            if 'doubleDown' in abils_ob:
                abilityUses['doubleDown'] += len(abils_ob['doubleDown'])
            if 'clubFav' in abils_ob:
                abilityUses['clubFav'] = 1
        
        return abilityUses
    
    
    
    # score all users' predictions for a game
    @staticmethod
    def RunScoreAndRank(p_gameID):
        
        # score the game for all users' predictions
        
        game_dx = FM.Reports_Game.GameToDictByID(p_gameID)
        
        gameRes = 0
        if game_dx['home_goals'] > game_dx['away_goals']:       gameRes = 1
        elif game_dx['home_goals'] < game_dx['away_goals']:     gameRes = 2
        else:                                                   gameRes = 3
        
        Editor.CreateScoring(game_dx, gameRes)
        
        # add ranks
        
        Editor.CreateRanking(game_dx['season'], game_dx['round'], 'round')
        Editor.CreateRanking(game_dx['season'], game_dx['round'], 'alltime')
    
    
    # subroutine for RunScoreAndRank()
    @staticmethod
    def CreateScoring(p_game_dx, p_gameRes):
        
        # get the predictions for each user
        # must use model so it can be updated with points
        
        try:
            pred_mdls = Univ_Prediction.objects.select_related('ScorerHomeFK', 'ScorerAwayFK'
                                              ).filter(GameFK__id=p_game_dx['id']) 
        except Univ_Prediction.DoesNotExist:
            return None
        
        
        # loop over all users' predictions for this game
        
        for pred_m in pred_mdls:
            
            abilsUsed = json.loads(pred_m.AbilitiesUsed)   if pred_m.AbilitiesUsed   else {}
            roster_m = Univ_Roster.objects.get(UserFK__username=pred_m.UserFK, SeasonFK__Season=p_game_dx['season'])
            abilsOwned = json.loads(roster_m.Upgrades)
            
            
            # get result points
            
            resultPnts = 0
            if pred_m.Result:
                if pred_m.Result == p_gameRes:  resultPnts = 2
                else:                           resultPnts = -1
            
            if 'secondChance' in abilsUsed and 'result' in abilsUsed['secondChance']:
                if abilsUsed['secondChance']['result'] == 0:            resultSCPnts = 0
                elif abilsUsed['secondChance']['result'] == p_gameRes:  resultSCPnts = 2
                else:                                                   resultSCPnts = -1
                if resultSCPnts > resultPnts:
                    resultPnts = resultSCPnts
            
            if 'doubleDown' in abilsUsed and 'result' in abilsUsed['doubleDown']:
                if resultPnts > 0:      resultPnts += abilsOwned['doubleDown']
                elif resultPnts < 0:    resultPnts -= abilsOwned['doubleDown'] 
            
            if 'clubFav' in abilsUsed:
                if resultPnts > 0:      resultPnts += abilsOwned['clubFav'] 
                elif resultPnts < 0:    resultPnts -= abilsOwned['clubFav'] 
            
            
            # get goals guess points
            
            goalsPnts = 0
            if pred_m.GoalsHome is not None:
                if pred_m.GoalsHome == p_game_dx['home_goals'] and pred_m.GoalsAway == p_game_dx['away_goals']:
                    goalsPnts = 5
                elif (p_game_dx['home_goals'] - p_game_dx['away_goals']) == (pred_m.GoalsHome - pred_m.GoalsAway):
                    goalsPnts = 3
                elif pred_m.GoalsHome != p_game_dx['home_goals'] and pred_m.GoalsAway != p_game_dx['away_goals']:
                    goalsPnts = -2
            
            if 'secondChance' in abilsUsed and 'goals' in abilsUsed['secondChance']:
                abilGoalsHm = abilsUsed['secondChance']['goals']['home']
                abilGoalsAw = abilsUsed['secondChance']['goals']['away']
                goalSCPnts = 0
                if abilGoalsHm == p_game_dx['home_goals'] and abilGoalsAw == p_game_dx['away_goals']:
                    goalSCPnts = 5
                elif (p_game_dx['home_goals'] - p_game_dx['away_goals']) == (abilGoalsHm - abilGoalsAw):
                    goalSCPnts = 3
                elif abilGoalsHm != p_game_dx['home_goals'] and abilGoalsAw != p_game_dx['away_goals']:
                    goalSCPnts = -2
                if goalSCPnts > goalsPnts:
                    goalsPnts = goalSCPnts
            
            if 'doubleDown' in abilsUsed and 'goals' in abilsUsed['doubleDown']:
                if goalsPnts > 0:      goalsPnts += abilsOwned['doubleDown']
                elif goalsPnts < 0:    goalsPnts -= abilsOwned['doubleDown']
            
            if 'clubFav' in abilsUsed:
                if goalsPnts > 0:      goalsPnts += abilsOwned['clubFav'] 
                elif goalsPnts < 0:    goalsPnts -= abilsOwned['clubFav'] 
            
            
            # get scorers points
            
            scorersPnts = 0
            if pred_m.ScorerHomeFK and pred_m.ScorerAwayFK:
                if pred_m.ScorerHomeFK.FirstLast in p_game_dx['home_scorers'] and \
                   pred_m.ScorerAwayFK.FirstLast in p_game_dx['away_scorers']:
                    scorersPnts = 8
                elif pred_m.ScorerHomeFK.FirstLast in p_game_dx['home_scorers'] or \
                     pred_m.ScorerAwayFK.FirstLast in p_game_dx['away_scorers']:
                    scorersPnts = 3
                else:
                    scorersPnts = -3
            elif pred_m.ScorerHomeFK:
                if pred_m.ScorerHomeFK.FirstLast in p_game_dx['home_scorers']:
                    scorersPnts = 4
                else:
                    scorersPnts = -2
            elif pred_m.ScorerAwayFK:
                if pred_m.ScorerAwayFK.FirstLast in p_game_dx['away_scorers']:
                    scorersPnts = 4
                else:
                    scorersPnts = -2
            
            if 'secondChance' in abilsUsed and 'scorers' in abilsUsed['secondChance']:
                abilScorersHm = abilsUsed['secondChance']['scorers']['home']
                abilScorersAw = abilsUsed['secondChance']['scorers']['away']
                scorersSCPnts = 0
                if abilScorersHm and abilScorersAw:
                    if abilScorersHm in p_game_dx['home_scorers'] and \
                       abilScorersAw in p_game_dx['away_scorers']:
                        scorersSCPnts = 8
                    elif abilScorersHm in p_game_dx['home_scorers'] or \
                         abilScorersAw in p_game_dx['away_scorers']:
                        scorersSCPnts = 3
                    else:
                        scorersSCPnts = -3
                elif abilScorersHm:
                    if abilScorersHm in p_game_dx['home_scorers']:
                        scorersSCPnts = 4
                    else:
                        scorersSCPnts = -2
                elif abilScorersAw:
                    if pred_m.ScorerAwayFK.FirstLast in p_game_dx['away_scorers']:
                        scorersSCPnts = 4
                    else:
                        scorersSCPnts = -2
                if scorersSCPnts > scorersPnts:
                    scorersPnts = scorersSCPnts
            
            if 'doubleDown' in abilsUsed and 'scorers' in abilsUsed['doubleDown']:
                if scorersPnts > 0:      scorersPnts += abilsOwned['doubleDown']
                elif scorersPnts < 0:    scorersPnts -= abilsOwned['doubleDown']
            
            if 'clubFav' in abilsUsed:
                if scorersPnts > 0:      scorersPnts += abilsOwned['clubFav'] 
                elif scorersPnts < 0:    scorersPnts -= abilsOwned['clubFav']
            
            
            # set points for this prediction
            
            pred_m.PntsResult = resultPnts
            pred_m.PntsGoal = goalsPnts
            pred_m.PntsScorer = scorersPnts
            pred_m.PntsTotal = resultPnts + goalsPnts + scorersPnts
            
            pred_m.save()
            
            # update overall scoring for round
            # only create a score entry if a prediction was made
            
            # if resultPnts == 0 and goalsPnts == 0 and scorersPnts == 0:
            #     return
            
            season_m = FT.Season.objects.get(Season=p_game_dx['season'])
            score_m, crtd = Univ_Scoring.objects.get_or_create(
                            UserFK=pred_m.UserFK, SeasonFK=season_m, Round=p_game_dx['round'])
            
            if crtd and p_game_dx['round'] != '01':
                prevRound = CU.Pad2( int(p_game_dx['round']) -1 )
                try:
                    prevScore_m = Univ_Scoring.objects.get(
                                UserFK=pred_m.UserFK, SeasonFK__Season=p_game_dx['season'], Round=prevRound)
                    score_m.Points_AllTime = prevScore_m.Points_AllTime
                except Univ_Scoring.DoesNotExist:
                    skip = True
            
            score_m.Points_Round += pred_m.PntsTotal
            score_m.Points_AllTime += pred_m.PntsTotal
            
            score_m.save()
    
    
    # subroutine for RunScoreAndRank()
    @staticmethod
    def CreateRanking(p_season, p_round, p_mode):
        
        score_mdls = Univ_Scoring.objects.filter(SeasonFK__Season=p_season, Round=p_round)
        
        # initialize ranks for sorting later
        
        ranks = []
        for score_m in score_mdls:
            createRank = UserRank()
            createRank.user = score_m.UserFK.username
            if p_mode == 'round':   createRank.points = score_m.Points_Round
            else:                   createRank.points = score_m.Points_AllTime
            ranks.append(createRank)
        
        # add rank data
        
        ranks = sorted(ranks, reverse=True)         # uses class's _gt_ and _lt_ to sort
        
        val = 0
        cpnts = None
        for rnk in ranks:
            if rnk.points != cpnts:
                cpnts = rnk.points
                val += 1
            rnk.rank = val
        
        # calculate percentile
        # using formula p = (b + 0.5 * e) / n * 100
        # b = number of entries before current rank
        # e = number of entries of current rank
        # n = total number of entries
        # formula dict contains {rank : [b, e]}
        
        formula = {}
        currRankV = 100000000
        for r in range(len(ranks) -1, -1, -1):
            currRank_c = ranks[r]
            if currRank_c.rank < currRankV:
                currRankV = currRank_c.rank
                formula[currRankV] = [(len(ranks)-1 -r), 1]
            else:
                formula[currRankV][1] += 1
        
        for rnk in ranks:
            percentile = (formula[rnk.rank][0] + 0.5 * formula[rnk.rank][1]) / float(len(ranks)) * 100
            rnk.percentile =  "{0:.4f}".format(percentile)         
        
        # copy data into Univ_Scoring model
        
        for score_m in score_mdls:
            for rnk in ranks:
                if score_m.UserFK.username == rnk.user:
                    if p_mode == 'round':
                        score_m.Rank_Round = rnk.rank
                        score_m.Perc_Round = rnk.percentile                        
                    else:
                        score_m.Rank_AllTime = rnk.rank
                        score_m.Perc_AllTime = rnk.percentile                        
                    score_m.save()


class Editor_Admin(object):
    
    
    @staticmethod
    def DeleteEvents():
        Univ_Prediction.objects.all().delete()        
        Univ_Scoring.objects.all().delete()
        
        FT.ClubRanking.objects.all().delete()        
        FT.GameEvent.objects.all().delete()
        
        game_mdls = FT.Game.objects.all()
        
        for game_m in game_mdls:
            game_m.GoalsHome = None 
            game_m.GoalsAway = None 
            game_m.home_scorers = None 
            game_m.ScorersAway = None
            game_m.save()
        
        hret = CU.HttpReturn()
        hret.results = "DeleteEvents() Complete"
        hret.status = 201
        return hret


# when a game gets scored, also score the predictions
from django.db.models.signals import post_save
from django.dispatch import receiver
@receiver(post_save, sender=FT.Game)
def Univ_TriggerScoring(sender, instance, **kwargs):
    # game has been post-processed
    if instance.GoalsHome is not None:      
        gameID = instance.id
        Editor.RunScoreAndRank(gameID)


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
SUB-CLASSES
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


class UserRank:
    def __init__(self):
        self.user = None
        self.season = None
        self.round = None
        self.points = None
        self.rank = None
        self.percentile = None
        
        self.preds = None
        self.avgPnts = None
    def __str__(self):
         return "Rank: {} | {} | {}".format(
            self.rank, self.user, self.points)  
    def __repr__(self):
        return self.__str__()
    def __gt__(self, other):
        return self.points > other.points or (self.points == other.points and self.user < other.user)
    def __lt__(self, other):
        return self.points < other.points or (self.points == other.points and self.user > other.user)


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
END OF FILE
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""