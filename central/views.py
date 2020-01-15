"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
CENTRAL/VIEWS.py
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import json

from django.shortcuts import render
from django.http import JsonResponse
from django.utils.safestring import mark_safe
from django.contrib.auth.decorators import user_passes_test

from django.views.decorators.csrf import csrf_exempt

import common.utility as CU
import football.models.tables as FT
import football.models.football as FM
import football.models.dataManager as FD
import members.models.members as MM
import prediction.models.universal as PU
import central.models.central as CN
import central.models.admin_messages as DM
import central.models.bot_users as BU

import logging
prog_lg = logging.getLogger('progress')
excp_lg = logging.getLogger('exception')


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
CENTRAL PAGES
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


def landing(request):    
    season = FM.TimeMachine.GetLastBracket()['season']
    logos = FM.Reports_General.GetClubsTransp(season)
    topRanks = PU.Reporter_Ranks.GetTopRanks()
    
    context = {
        'topRanks': mark_safe(json.dumps(topRanks)),
        'logos': logos,
    }
    return render(request, 'landing_page.html', context)


def store(request):
    storeConfig = CN.Reporter.GetStoreConfig(request.user)
    
    context = {
        'storeConfig': storeConfig,
    }
    return render(request, 'store.html', context)


def company(request):
    context = {
    }
    return render(request, 'company.html', context)


@user_passes_test(lambda u: u.is_superuser)
def master(request):
    sites = CN.Reporter.GetSites()
    seasons = FM.Reports_General.GetSeasons()
    season = seasons[0]
    
    hretRounds = FM.Reports_Admin.GetRoundSummary(season)
    byRound = mark_safe(json.dumps(hretRounds.results))   if not isinstance(hretRounds.results, str)   else None
    
    simTime = FM.TimeMachine.GetSimTime()
    if simTime:
        simTime = simTime.strftime(CU.FORMAT_DTSTR)
    
    context = {
        'msgAdmin': DM.Reporter.GetMessageAdmin(),
        'sites': CN.Reporter.GetSites(),
        'coreSummary': mark_safe(json.dumps(FM.Reports_Admin.GetCoreCounts())),
        'seasonTable': mark_safe(json.dumps(FM.Reports_Admin.GetFullTable(FT.Season))),
        'clubTable': mark_safe(json.dumps(FM.Reports_Admin.GetFullTable(FT.Club))),
        #'eventTable': FM.Reports_Admin.GetFullTable(FT.Event),
        
        'seasons': seasons,
        'seasonSummary': mark_safe(json.dumps(FM.Reports_Admin.GetSeasonSummary())),
        'byRound': byRound,
        
        'simTime': simTime,
    }
    return render(request, 'data_master.html', context)


def view_profile(request, username):
    season = FM.TimeMachine.GetTodaysBracket()['season']
    user_m = MM.Profile_Reporter.GetUserModel(username)
    
    profileData = MM.Profile_Reporter.ViewProfileData(request.user, username)
    puRoster = PU.Reporter.GetUserRoster(user_m, season)
    puAbilsOwned = PU.Reporter.GetAbilitiesOwned(user_m, season)
    puRecord = PU.Reporter.GetRecord(user_m, season)
    
    context = {
        'profileData': profileData,
        'friendList': mark_safe(json.dumps(profileData['friendList'])),
        'puRoster': puRoster,
        'puAbilsOwned': mark_safe(json.dumps(puAbilsOwned)),
        'puRecordAT': mark_safe(json.dumps(puRecord['recordAT'])),
        'puRecordRD': mark_safe(json.dumps(puRecord['recordRD'])),
        'puThresholds': mark_safe(json.dumps(puRecord['thresholds'])),
    }
    return render(request, 'view_profile.html', context)


def central_jx(request, command):
    
    prog_lg.info("ajax command: " + command)
    
    
    if command == 'update_buyDiamonds':
        itemId = request.POST.get('itemId')
        hret = CN.Editor.PurchaseDiamonds(request.user, itemId) 
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'update_exchangeTokens':
        diamonds = int(request.POST.get('diamonds'))
        hret = CN.Editor.ExchangeTokens(request.user, diamonds) 
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    
    elif command == 'create_msgUser':
        hret = DM.Editor.CreateMessageUser()
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'update_sites':
        CN.Editor.InitializeSites()
        siteOne = CN.Reporter.GetSites()
        
        hret = CU.HttpReturn()
        hret.results = {'domain': siteOne.domain, 'name': siteOne.name}
        hret.status = 200        
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    
    elif command == 'update_claimRewards':
        # this is moved from pu_rewards_jx because the users need access
        messageID = request.POST.get('messageID')
        hret = DM.PU_Editor.ClaimRewards(request.user, messageID)
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    else:
        msg = "command invalid: " + command
        excp_lg.error(msg)
        return JsonResponse(msg, safe=False, status = 404)  


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
ADMIN MESSAGES
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


@user_passes_test(lambda u: u.is_superuser)
def admin_messages(request):
    context = {
        'inbox': mark_safe(json.dumps(DM.Reporter.GetAdminInbox())),
        'messageAdmin': DM.Reporter.GetMessageAdmin(),
        'recTypes': ["To User", "To All Users"],
        'msgReport': mark_safe(json.dumps(DM.Reporter.GetMessageReport())),
    }
    return render(request, 'admin_messages.html', context)


@user_passes_test(lambda u: u.is_superuser)
def adminMsg_jx(request, command):
    
    prog_lg.info("ajax command: " + command)
    
    
    if command == 'get_message':
        msgID = request.GET.get('msgID')
        hret = DM.Reporter.GetAdminMessage(msgID)
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'get_convo':
        thdID = request.GET.get('thdID')
        hret = DM.Reporter.GetAdminConvo(thdID)
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'delete_conv':
        hret = DM.Editor.DeleteConvo(request)
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'insert_newMsg':
        hret = DM.Editor.WriteMessage(request)
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'insert_replyMsg':
        hret = DM.Editor.ReplyMessage(request)    
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'get_inbox':
        inbox = DM.Reporter.GetAdminInbox()   
        hret = CU.HttpReturn()
        hret.results = inbox
        hret.status = 201
        return JsonResponse(hret.results, safe=False, status=hret.status)
        
    elif command == 'delete_messages':
        hret = DM.Editor.DeleteMessages()
        hret.results = DM.Reporter.GetMessageReport()
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    
    else:
        msg = "command invalid: " + command
        excp_lg.error(msg)
        return JsonResponse(msg, safe=False, status = 404)  


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
UNIVERSAL REWARDS
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


@user_passes_test(lambda u: u.is_superuser)
def pu_rewards(request): 
    seasons = FM.Reports_General.GetSeasons()
    #seasons = ['IPL2014']
    roundList = FM.Reports_General.GetRounds(seasons[0], "lastData")
    
    if roundList:
        try:
            rewardsData = PU.Reporter_Ranks.RunRewardsData(seasons[0], roundList[0])
            status = PU.Reporter_Ranks.GetRewardStatus(seasons[0], roundList[0])
        except:
            rewardsData = "no data"
            status = "no status"
            
    else:
        rewardsData = "no data"
        status = "no status"
    
    context = {
        'seasons': seasons,
        'roundList': roundList,
        
        'charts': mark_safe(json.dumps(rewardsData))   if not isinstance(rewardsData, str)   else None,
        'status': mark_safe(json.dumps(status))   if not isinstance(status, str)   else None,
    }
    return render(request, 'pu_rewards.html', context)


@user_passes_test(lambda u: u.is_superuser)
def pu_rewards_jx(request, command):
    
    prog_lg.info("ajax edit command: " + command)
    
    if command == 'get_pointsDist':
        season = request.GET.get('season')
        roundv = request.GET.get('roundv')
        
        results = PU.Reporter_Ranks.RunRewardsData(season, roundv)
        
        hret = CU.HttpReturn()
        hret.results = results
        hret.status = 201
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'get_rewardStatus':
        season = request.GET.get('season')
        #roundv = request.GET.get('roundv')
        roundList = FM.Reports_General.GetRounds(season, "lastData")
        roundv = roundList[0]   if roundList   else ''
        
        charts = PU.Reporter_Ranks.RunRewardsData(season, roundv)
        status = PU.Reporter_Ranks.GetRewardStatus(season, roundv)
        results = {
            'rounds': roundList,
            'charts': charts,
            'status': status   if status['scoreSummary']   else "No score summary available",
        }
        
        hret = CU.HttpReturn()
        hret.results = results
        hret.status = 201
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'update_rankRewards':    
        season = request.POST.get('season')
        roundv = request.POST.get('roundv')
        hret = DM.PU_Editor.RunRewards(season, roundv)
        
        if hret.status < 400:
            roundList = FM.Reports_General.GetRounds(season, "lastData")
            roundLast = roundList[0]   if roundList   else ''
            hret = CU.HttpReturn()
            hret.results = PU.Reporter_Ranks.GetRewardStatus(season, roundLast)
            hret.status = 201
        
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    else:
        msg = "command invalid: " + command
        excp_lg.error(msg)
        return JsonResponse(msg, safe=False, status = 404)


def pu_message_test(request):
    # this is an internal view to facilitate creation of the rewards message
    
    values = PU.Reporter_Ranks.GetRewardValues(35.0, 15.0)
    
    context = {
        'values': values,
        'claimed': False,
    }
    return render(request, 'message_testPage.html', context)


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
BOT USERS
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


@user_passes_test(lambda u: u.is_superuser)
def botUsers(request):
    context = {
        'seasons': FM.Reports_General.GetSeasons(),
    }
    return render(request, 'bot_users.html', context)


@user_passes_test(lambda u: u.is_superuser)
def botUsers_jx(request, command):
    
    prog_lg.info("ajax command: " + command)
    
    
    if command == 'testUsers_count':
        hret = BU.TestUsers_Reports.GetTestUserCount()
        
        prog_lg.debug(hret)
        
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'testUsers_details':
        hret = BU.TestUsers_Reports.GetTestUserDetails()
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    
    elif command == 'create_testUsers':
        userNum = request.POST.get('userNum')
        season = request.POST.get('season')
        BU.TestUsers_Editor.DeleteUsers()
        hret = BU.TestUsers_Editor.CreateUsers(userNum, season)
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'delete_testUsers':
        BU.TestUsers_Editor.DeleteUsers()
        results= "Success"
        return JsonResponse(results, safe=False)
    
    elif command == 'makePreds_testUsers':
        season = request.POST.get('season')
        roundv = request.POST.get('round')
        hret = BU.TestUsers_Editor.MakePredictions(season, roundv)
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    
    else:
        msg = "command invalid: " + command
        excp_lg.error(msg)
        return JsonResponse(msg, safe=False, status = 404)  


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
END OF FILE
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""