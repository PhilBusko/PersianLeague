"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
PREDICTION/VIEWS.py
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import os
import json
from random import randint

from django.shortcuts import render
from django.http import JsonResponse
from django.utils.safestring import mark_safe
from django.conf import settings

import common.utility as CU
import football.models.football as FM
import members.models.members as MM
import prediction.models.universal as PU

import logging
prog_lg = logging.getLogger('progress')
excp_lg = logging.getLogger('exception')


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
UNIVERSAL
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


def univ_preds(request):
    bk = FM.TimeMachine.GetTodaysBracket()
    prog_lg.debug(bk)
    context = {
        'season': bk['season'],
        'round': bk['round'],
        'now_dt': mark_safe(json.dumps(MM.Profile_Reporter.GetUserNow(request.user))),
        'spectrumOpts': ["Home Win", "Away Win", "Tie", "Abstain"],
        'players': mark_safe(json.dumps(FM.Reports_General.GetPlayersBySeason(bk['season']))),
        'abilsOwned': mark_safe(json.dumps(PU.Reporter.GetAbilitiesOwned(request.user, bk['season']))),
        'abilsUsedRound': mark_safe(json.dumps(PU.Reporter.GetAbilsUsedByRound(request.user, bk['season'], bk['round']))),
        'fixture': mark_safe(json.dumps(PU.Reporter_Common.GetFixtureLocalized(bk['season'], bk['round'], request.user))),
        'predictions': mark_safe(json.dumps(PU.Editor.GetOrCreatePreds(bk['season'], bk['round'], request.user))),
    }
    return render(request, 'pu_predictions.html', context)


def univ_headq(request):
    season = FM.TimeMachine.GetTodaysBracket()['season']
    
    context = {
        'roster': PU.Reporter.GetUserRoster(request.user, season),
        'abilsOwned': PU.Reporter.GetAbilitiesOwned(request.user, season),
        'store': PU.Reporter_Store.GetStoreData(),
        'storeAvailable': PU.Reporter_Store.GetStoreAvailable(request.user, season),
    }
    return render(request, 'pu_headquarters.html', context)


def univ_ranks(request): 
    seasons = FM.Reports_General.GetSeasons()
    #seasons = ['IPL2015']
    season = FM.TimeMachine.GetTodaysBracket()['season']
    roundList = FM.Reports_General.GetRounds(season, "lastData")
    roundv = roundList[0]   if roundList   else None
    
    puRecord = PU.Reporter.GetRecord(request.user, season, roundv)    
    rankData = PU.Reporter_Ranks.RunRankData(season, roundv, "Friends", request.user)
    
    context = {
        'seasons': seasons,
        'roundList': roundList,
        'modes': ["Friends", "Yours", "Top Users"],
        
        # logged user's performance
        
        'status': mark_safe(json.dumps(puRecord['status'])),
        'recordAT': mark_safe(json.dumps(puRecord['recordAT'])),
        'recordRD': mark_safe(json.dumps(puRecord['recordRD'])),
        'thresholds': mark_safe(json.dumps(puRecord['thresholds'])),
        
        # points distribution
        
        'userCntAT': rankData['userCntAT'],
        'binCntAT': rankData['binCntAT'],
        'histAT': mark_safe(json.dumps(rankData['histAT'])),
        'gradeAT': mark_safe(json.dumps(rankData['gradeAT'])),
        'highlightAT': mark_safe(json.dumps(rankData['highlightAT'])),
        
        'userCntRD': rankData['userCntRD'],
        'binCntRD': rankData['binCntRD'],
        'histRD': mark_safe(json.dumps(rankData['histRD'])),
        'gradeRD': mark_safe(json.dumps(rankData['gradeRD'])),
        'highlightRD': mark_safe(json.dumps(rankData['highlightRD'])),
        
        # leaderboards
        
        'ranksAT': mark_safe(json.dumps(rankData['ranksAT'])),
        'ranksRD': mark_safe(json.dumps(rankData['ranksRD'])),
    }
    return render(request, 'pu_standings.html', context)


def univ_rules(request):
    context = {
    }
    return render(request, 'pu_rules.html', context)


def universal_jx(request, command):
    
    prog_lg.info("ajax edit command: " + command)
    
    
    if command == 'get_fixtSummary':
        season = request.GET.get('season')
        hret = PU.Reporter.GetFixturesSummary(season) 
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'delete_events':    
        hret = PU.Editor_Admin.DeleteEvents()
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    
    elif command == 'update_accumulator':    
        hret = PU.Editor.PopTokenAccumulator(request.user)
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'update_buyUpgrade':    
        upgradeType = request.POST.get('upgradeType')
        upgradeLevel = request.POST.get('upgradeLevel')
        hret = PU.Editor.UpgradeBuy(request.user, upgradeType, upgradeLevel)
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    
    elif command == 'update_prediction':    
        pred_st = request.POST.get('pred_st')
        pred_dx = json.loads(pred_st)
        hret = PU.Editor.SavePrediction(request.user, pred_dx)
        
        bk = FM.TimeMachine.GetTodaysBracket()
        hret.results = {
            'saveRes': hret.results,
            'now_dt': MM.Profile_Reporter.GetUserNow(request.user),
            'abilsOwned': PU.Reporter.GetAbilitiesOwned(request.user, bk['season']),
            'abilsUsedRound': PU.Reporter.GetAbilsUsedByRound(request.user, bk['season'], bk['round']),
            'predictions': PU.Editor.GetOrCreatePreds(bk['season'], bk['round'], request.user),
        }
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'get_predictions':    
        season = FM.TimeMachine.GetTodaysBracket()['season']
        roundv = request.GET.get('round')
        
        hret = CU.HttpReturn()
        hret.status = 201
        hret.results = {
            'now_dt': MM.Profile_Reporter.GetUserNow(request.user),
            'abilsOwned': PU.Reporter.GetAbilitiesOwned(request.user, season),
            'abilsUsedRound': PU.Reporter.GetAbilsUsedByRound(request.user, season, roundv),
            'fixture': PU.Reporter_Common.GetFixtureLocalized(season, roundv, request.user),
            'predictions': PU.Editor.GetOrCreatePreds(season, roundv, request.user),
        }
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    
    elif command == 'get_ranksRnd':
        mode = request.GET.get('mode')
        season = request.GET.get('season')
        
        roundList = FM.Reports_General.GetRounds(season, 'lastData')
        if not roundList:
            roundList = ['01']
        lastRound = roundList[0]        # list is sorted descending
        
        results = PU.Reporter_Ranks.RunRankData(season, lastRound, mode, request.user)
        puRecord = PU.Reporter.GetRecord(request.user, season, lastRound)
        
        results = dict(results, **puRecord);
        results['roundList'] = roundList
        
        hret = CU.HttpReturn()
        hret.results = results
        hret.status = 201
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'get_ranks':
        mode = request.GET.get('mode')
        season = request.GET.get('season')
        roundv = request.GET.get('roundv')
        
        results = PU.Reporter_Ranks.RunRankData(season, roundv, mode, request.user)
        puRecord = PU.Reporter.GetRecord(request.user, season, roundv)    
        results = dict(results, **puRecord);
        
        hret = CU.HttpReturn()
        hret.results = results
        hret.status = 201
        return JsonResponse(hret.results, safe=False, status=hret.status)
        
    
    else:
        msg = "command invalid: " + command
        excp_lg.error(msg)
        return JsonResponse(msg, safe=False, status = 404)


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
END OF FILE
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""