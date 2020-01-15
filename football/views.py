"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
FOOTBALL/VIEWS.py
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import json
from random import randint

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.utils.safestring import mark_safe
from django.contrib.auth.decorators import user_passes_test

import common.utility as CU
import football.models.tables as FT
import football.models.football as FM
import football.models.dataManager as FD
import football.models.etl_iplstats as FI
import football.models.etl_livescores as FL

import logging
prog_lg = logging.getLogger('progress')
excp_lg = logging.getLogger('exception')


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
REFERENCE PAGES
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


def fb_season(request):
    seasons = FM.Reports_General.GetSeasons()
    bk = FM.TimeMachine.GetLastBracket()
    ranks_ft = FM.Reports_Season.GetClubRanksFT(bk['season'])
    rounds = FM.Reports_General.GetRounds(bk['season'], 'today')
    
    lastRnd = rounds[0]   if len(rounds) > 0   else None
    fixture_ft = FM.Reports_Season.GetFixtureFT(bk['season'], lastRnd)
    
    clubs = FM.Reports_General.GetClubs(bk['season'])
    club1_ft = FM.Reports_Season.GetClubGamesFT(bk['season'], clubs[0])
    club2_ft = FM.Reports_Season.GetClubGamesFT(bk['season'], clubs[1])
    
    context = {
        'seasons': seasons,
        'cSeason': bk['season'],
        'clubRanking': mark_safe(json.dumps(ranks_ft)),
        'rounds': rounds,
        'fixture': mark_safe(json.dumps(fixture_ft)),
        'clubs': clubs,
        'club1': mark_safe(json.dumps(club1_ft)),
        'club2': mark_safe(json.dumps(club2_ft)),
    }
    return render(request, 'fb_season.html', context)


def fb_game(request):
    seasons = FM.Reports_General.GetSeasons()
    bk = FM.TimeMachine.GetLastBracket()
    rounds = FM.Reports_General.GetRounds(bk['season'], 'today')
    lastRnd = rounds[0]   if len(rounds) > 0   else None
    
    game_mdls = FT.Game.objects.filter(SeasonFK__Season=bk['season'], Round=lastRnd).order_by('PlayDate')
    lastGame = None
    prevGame = game_mdls[0]
    for game_m in game_mdls:
        if game_m.GoalsHome == None:
            lastGame = prevGame
            break
        prevGame = game_m
    if not lastGame:
        lastGame = prevGame
    
    lastClub = lastGame.ClubHomeFK.Club   if lastGame   else None
    fixture_ft = FM.Reports_Season.GetFixtureFT(bk['season'], lastRnd)
    props_ref = FM.Reports_Game.RunGameProperties(bk['season'], lastRnd, lastClub)
    
    context = {
        'seasons': seasons,
        'cSeason': bk['season'],
        'rounds': rounds,
        'fixture': mark_safe(json.dumps(fixture_ft)),
        'gameProps': mark_safe(json.dumps(props_ref.results)),
    }
    return render(request, 'fb_game.html', context)


def fb_club(request):
    return render(request, 'fb_club.html')


def fb_player(request):
    return render(request, 'fb_player.html')


def research_jx(request, command):
    
    prog_lg.info("ajax command: " + command)
    
    
    if command == 'seasons':
        items = FM.Reports_General.GetSeasons()
        return JsonResponse(items, safe=False)

    elif command == 'clubs':
        season = request.GET.get('season')
        items = FM.Reports_General.GetClubs(season)
        return JsonResponse(items, safe=False)
    
    elif command == 'rounds':
        season = request.GET.get('season')
        filterv = request.GET.get('filter')
        items = FM.Reports_General.GetRounds(season, filterv)
        return JsonResponse(items, safe=False)
    
    elif command == 'players':
        club = request.GET.get('club')
        position = request.GET.get('position')
        items = FM.Reports_General.GetPlayers(club, position)
        return JsonResponse(items, safe=False)
    
    elif command == 'positions':
        items = FM.Reports_General.GetPositions()
        return JsonResponse(items, safe=False)
    
    
    elif command == 'season_data':
        season = request.GET.get('season')  
        ranks_ft = FM.Reports_Season.GetClubRanksFT(season)
        rounds = FM.Reports_General.GetRounds(season, 'lastData')
        roundv = rounds[0]   if rounds   else None
        fixture_ft = FM.Reports_Season.GetFixtureFT(season, roundv)
        clubs = FM.Reports_General.GetClubs(season)
        club1_ft = FM.Reports_Season.GetClubGamesFT(season, clubs[0])
        club2_ft = FM.Reports_Season.GetClubGamesFT(season, clubs[1])
        
        results = {
            'clubRanking': ranks_ft,
            'rounds': rounds,
            'fixture': fixture_ft,
            'clubs': clubs,
            'club1': club1_ft,
            'club2': club2_ft,
        }
        return JsonResponse(results, safe=False)
    
    elif command == 'round_fixture':
        season = request.GET.get('season')
        gameRound = request.GET.get('round')
        ftable = FM.Reports_Season.GetFixtureFT(season, gameRound)
        return JsonResponse(ftable, safe=False)
    
    elif command == 'club_games':
        season = request.GET.get('season')
        club = request.GET.get('club')
        ftable = FM.Reports_Season.GetClubGamesFT(season, club)
        return JsonResponse(ftable, safe=False)
    
    
    elif command == 'season_refresh':
        season = request.GET.get('season')
        rounds = FM.Reports_General.GetRounds(season, 'lastData')
        roundv = rounds[0]   if rounds   else None
        
        fixture_ft = FM.Reports_Season.GetFixtureFT(season, roundv)
        firstClub = fixture_ft['data'][0]['home_club']   if not isinstance(fixture_ft, str)   else None
        props_ref = FM.Reports_Game.RunGameProperties(season, roundv, firstClub)
        
        results = {
            'rounds': rounds,
            'fixture': fixture_ft,
            'home': props_ref.results['home']   if not isinstance(props_ref.results, str)   else None,
            'away': props_ref.results['away']   if not isinstance(props_ref.results, str)   else None,
        }
        return JsonResponse(results, safe=False)
    
    elif command == 'round_game':
        season = request.GET.get('season')
        roundv = request.GET.get('round')
        
        fixture_ft = FM.Reports_Season.GetFixtureFT(season, roundv)
        firstClub = fixture_ft['data'][0]['home_club']   if not isinstance(fixture_ft, str)   else None
        props_ref = FM.Reports_Game.RunGameProperties(season, roundv, firstClub)
        
        results = {
            'fixture': fixture_ft,
            'home': props_ref.results['home'],
            'away': props_ref.results['away'],
        }
        return JsonResponse(results, safe=False)
    
    elif command == 'game_properties':
        season = request.GET.get('season')
        round_ = request.GET.get('round')
        home_club = request.GET.get('home_club')
        hret = FM.Reports_Game.RunGameProperties(season, round_, home_club)
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    
    elif command == 'club_props':
        club = request.GET.get('club')
        hret = FM.Reports_Club.GetClubProperties(club)
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'players_ingame':
        club = request.GET.get('club')
        season = request.GET.get('season')
        position = request.GET.get('position')
        hret = FM.Reports_Club.GetPlayersInGame(club, season, position)
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'player_properties':
        player = request.GET.get('player')
        hret = CU.HttpReturn()
        hret.results = {
            'props': FM.Reports_Player.GetPropertiesDict(player),
            'record': FM.Reports_Player.GetClubRecordDict(player),
        }
        hret.status = 201
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    
    msg = "command invalid: " + command
    return JsonResponse(msg, status = 404)  


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
DATA MANAGEMENT
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


@user_passes_test(lambda u: u.is_superuser)
def dataManager_jx(request, command):
    
    prog_lg.info("ajax command: " + command)
    
    
    if command == 'load_core':
        hret = FD.Manager.LoadCoreFiles()
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'reset':
        hret = FD.Manager.ResetCoreTables()
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'exp_season':
        season = request.GET.get('season')
        FD.Exporter.ExportPlayers(season)
        FD.Exporter.ExportGames(season)
        FD.Exporter.ExportEvents(season)
        
        hret = CU.HttpReturn()
        hret.results = "Export successfull."
        hret.status = 200                
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'imp_season':
        season = request.POST.get('season')
        FD.Importer.ImportPlayers(season)
        FD.Importer.ImportGames(season)
        FD.Importer.ImportEvents(season)
        
        hretRounds = FM.Reports_Admin.GetRoundSummary(season)
        results = {
            'seasonSummary': FM.Reports_Admin.GetSeasonSummary(),
            'byRound': hretRounds.results,
        }
        
        hret = CU.HttpReturn()
        hret.results = results
        hret.status = 200                
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'imp_players':
        season = request.POST.get('season')
        hret = FD.Importer.ImportPlayers(season)
        
        if hret.status >= 400:
            return JsonResponse(hret.results, safe=False, status=hret.status)
        
        hretRounds = FM.Reports_Admin.GetRoundSummary(season)
        results = {
            'seasonSummary': FM.Reports_Admin.GetSeasonSummary(),
            'byRound': hretRounds.results,
        }
        
        hret = CU.HttpReturn()
        hret.results = results
        hret.status = 200                
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'imp_games':
        season = request.POST.get('season')
        rndStart = request.POST.get('rndStart')
        rndEnd = request.POST.get('rndEnd')
        FD.Importer.ImportGames(season, rndStart, rndEnd)
        
        hretRounds = FM.Reports_Admin.GetRoundSummary(season)
        results = {
            'seasonSummary': FM.Reports_Admin.GetSeasonSummary(),
            'byRound': hretRounds.results,
        }
        
        hret = CU.HttpReturn()
        hret.results = results
        hret.status = 200                
        return JsonResponse(hret.results, safe=False, status=hret.status)

    elif command == 'imp_events':
        season = request.POST.get('season')
        rndStart = request.POST.get('rndStart')
        rndEnd = request.POST.get('rndEnd')
        FD.Importer.ImportEvents(season, rndStart, rndEnd)
        
        hretRounds = FM.Reports_Admin.GetRoundSummary(season)
        results = {
            'seasonSummary': FM.Reports_Admin.GetSeasonSummary(),
            'byRound': hretRounds.results,
        }
        
        hret = CU.HttpReturn()
        hret.results = results
        hret.status = 200                
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'load_game':
        gameid = request.POST.get('gameid')
        FD.Importer.ImportSingleEvents(gameid)
        
        game_m = FT.Game.objects.get(id=gameid)
        ftable = FM.Reports_Season.GetFixtureFT(game_m.SeasonFK.Season, game_m.Round, 'America/New_York')
        return JsonResponse(ftable, safe=False)
    
    elif command == 'get_fixture':
        season = request.GET.get('season')
        roundv = CU.Pad2(request.GET.get('rndStart'))
        
        ftable = FM.Reports_Season.GetFixtureFT(season, roundv, 'America/New_York')          
        return JsonResponse(ftable, safe=False)
    
    elif command == 'delete_events':
        season = request.POST.get('season')
        FD.Manager.DeleteEvents(season)
        
        hretRounds = FM.Reports_Admin.GetRoundSummary(season)
        results = {
            'seasonSummary': FM.Reports_Admin.GetSeasonSummary(),
            'byRound': hretRounds.results,
        }
        
        hret = CU.HttpReturn()
        hret.results = results
        hret.status = 200                
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'delete_games':
        season = request.POST.get('season')
        FD.Manager.DeleteGames(season)
        
        hretRounds = FM.Reports_Admin.GetRoundSummary(season)
        results = {
            'seasonSummary': FM.Reports_Admin.GetSeasonSummary(),
            'byRound': hretRounds.results,
        }
        
        hret = CU.HttpReturn()
        hret.results = results
        hret.status = 200                
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'delete_allPlayers':
        FD.Manager.DeleteAllPlayers()
        
        hretRounds = FM.Reports_Admin.GetRoundSummary(None)
        results = {
            'seasonSummary': FM.Reports_Admin.GetSeasonSummary(),
            'byRound': hretRounds.results,
        }
        
        hret = CU.HttpReturn()
        hret.results = results
        hret.status = 200                
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'get_tableReport':
        season = request.GET.get('season')
        hretRounds = FM.Reports_Admin.GetRoundSummary(season)
        results = {
            'seasonSummary': FM.Reports_Admin.GetSeasonSummary(),
            'byRound': hretRounds.results,
        }
        
        hret = CU.HttpReturn()
        hret.results = results
        hret.status = 200                
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'update_simDate':
        simDate = request.POST.get('simDate')
        simTime = request.POST.get('simTime')
        
        FM.TimeMachine.SaveSimDate(simDate, simTime)
        results = FM.TimeMachine.GetSimTime()
        if results:
            results = results.strftime(CU.FORMAT_DTSTR)
        
        hret = CU.HttpReturn()
        hret.results = results
        hret.status = 200                
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    
    msg = "command invalid: " + command
    return JsonResponse(msg, safe=False, status = 404)  


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
ETL PAGES
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


@user_passes_test(lambda u: u.is_superuser)
def etl_iplstats(request):
    context = {
        'seasons': FM.Reports_General.GetSeasons(),
    }
    return render(request, 'etl_iplstats.html', context)


@user_passes_test(lambda u: u.is_superuser)
def etl_iplstats_jx(request, command):    
    
    prog_lg.info("ajax edit command: " + command)
    
    
    if command == 'load_players':
        season = request.POST.get('season')
        hret = FI.IPLS_Squad.RunPlayerSquadData(season)
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'load_game':
        season = request.POST.get('season')
        rndStart = request.POST.get('rndStart')
        hret = FI.IPLS_GameEvents.RunGameData(season, rndStart)
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'game_fixtures':
        season = request.POST.get('season')
        rndStart = request.POST.get('rndStart')
        rndEnd = request.POST.get('rndEnd')
        hret = FI.IPLS_GVPartial.RunFixturesOnly(season, rndStart, rndEnd)
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'game_oneround':
        season = request.POST.get('season')
        roundv = request.POST.get('round')
        hret = FI.IPLS_GVPartial.RunGameOneRound(season, roundv)
        return JsonResponse(hret.results, safe=False, status=hret.status)
        
        
    elif command == 'import_fixture':
        url = request.POST.get('url')
        hret = FL.Editor.RunImportFixture(url)
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    
    elif command == 'get_players':
        season = request.GET.get('season')
        hret = FM.Reports_Admin.GetSquadSummary(season)
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'game_byround':
        season = request.GET.get('season')
        hret = FM.Reports_Admin.GetRoundSummary(season)
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'game_byevent':
        season = request.GET.get('season')
        hret = FM.Reports_Admin.GetEventSummary(season)
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'game_byfixtures':
        season = request.GET.get('season')
        results = FM.Reports_Admin.GetFixturesSummary(season)
        return JsonResponse(results)
    
    elif command == 'load_singleGame':
        gameUrl = request.POST.get('gameUrl')
        hret = FI.IPLS_GVPartial.RunSingleGame(gameUrl)
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    
    msg = "command invalid: " + command
    return JsonResponse(msg, status = 404)  



@user_passes_test(lambda u: u.is_superuser)
def etl_livescores(request):
    bracket = FM.TimeMachine.GetTodaysBracket()
        
    rounds = FM.Reports_General.GetRounds(bracket['season'], '')
    fixtureDeets = FM.Reports_Season.GetFixtureDetails(bracket['season'], bracket['round'])
    players = FM.Reports_General.GetPlayersBySeason(bracket['season'])
    
    context = {
        'seasons': FM.Reports_General.GetSeasons(),
        'rounds': rounds,
        'currRnd': bracket['round'],
        'fixture': mark_safe(json.dumps(fixtureDeets)),
        'players': mark_safe(json.dumps(players)),
    }
    return render(request, 'etl_livescores.html', context)


@user_passes_test(lambda u: u.is_superuser)
def etl_livescores_jx(request, command):    
    
    prog_lg.info("ajax command: " + command)
    
    
    if command == 'preImport_liveGame':
        gameId = request.GET.get('gameId')
        url = request.GET.get('url')
        transf_dx = FL.Editor.TransformGameEvents(gameId, url)
        return JsonResponse(transf_dx, safe=False)
    
    elif command == 'load_liveGame':
        gameData = request.POST.get('gameData')
        gameData = json.loads(gameData)     # json data must be encoded as string
        results = FL.Editor.LoadGameData(gameData)               
        return JsonResponse(results, safe=False)
    
    elif command == 'delete_gameEvents':
        gameId = request.POST.get('gameId')
        delRes = FD.Manager.DeleteGameEvents(gameId)
        results = delRes.results
        fixtDetails = FM.Reports_Season.GetFixtureDetails(results['season'], results['round'])
        return JsonResponse(fixtDetails, safe=False)
    
    elif command == 'refresh_round':
        roundv = request.GET.get('round')
        bracket = FM.TimeMachine.GetTodaysBracket()
        
        fixtDetails = FM.Reports_Season.GetFixtureDetails(bracket['season'], roundv)

        return JsonResponse(fixtDetails, safe=False)
    
    
    msg = "command invalid: " + command
    return JsonResponse(msg, status = 404)  


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
END OF FILE
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""