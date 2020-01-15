"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
CENTRAL/MODELS/ADMIN_MESSAGES.py
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import pytz
import datetime 
from collections import OrderedDict

import django.contrib.auth.models as AM
from django.template.loader import render_to_string
from django.db.models import Count, F, Q     
import allauth.account.models as LM
import postman.views as PV

import common.utility as CU
import football.models.football as FM
import members.models.tables as MT
import members.models.members as MM
import members.models.postman as MP
import prediction.models.universal as PU

import logging
prog_lg = logging.getLogger('progress')
excp_lg = logging.getLogger('exception')


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
ADMIN MESSAGES
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


class Reporter(object):
    
    
    @staticmethod
    def GetMessageAdmin():
        try:
            user_m = AM.User.objects.get(username=MM.MESSAGE_ADMIN)
        except Exception as ex:
            user_m = None
        return user_m
    
    
    def GetAdminInbox():
        fReq = MP.Postman.GetFakeRequest(MM.MESSAGE_ADMIN)
        cData = PV.InboxView.as_view()(fReq).context_data
        rawMsgs = cData['pm_messages']
        
        messages = []
        for msg in rawMsgs:
            newMsg = MP.MessageData()
            newMsg.id = msg.id
            newMsg.thread_id = msg.thread_id
            newMsg.sender = msg.sender.username  + (" (" +  str(msg.count)  + ")" if  msg.count else "");
            newMsg.subject = msg.subject
            newMsg.sent_at = msg.sent_at.strftime(CU.FORMAT_DTSTR)  if msg.sent_at  else None
            newMsg.replied_at = msg.replied_at.strftime(CU.FORMAT_DTSTR)  if msg.replied_at  else None
            messages.append(newMsg.__dict__)
        
        return messages
    
    
    @staticmethod
    def GetAdminMessage(p_msgID):
        
        user_m = AM.User.objects.get(username=MM.MESSAGE_ADMIN)
        profile_m = MT.Profile.objects.get(UserFK=user_m)
        
        fReq = MP.Postman.GetFakeRequest(MM.MESSAGE_ADMIN)
        
        timezone = pytz.timezone( profile_m.TimeZone   if profile_m.TimeZone   else 'UTC' )
        message_dx = MP.Postman.GetMessage(fReq, p_msgID, timezone)
        
        hret = CU.HttpReturn()
        hret.results = message_dx
        hret.status = 201
        return hret
    
    
    @staticmethod
    def GetAdminConvo(p_msgID):
        
        user_m = AM.User.objects.get(username=MM.MESSAGE_ADMIN)
        profile_m = MT.Profile.objects.get(UserFK=user_m)
        
        fReq = MP.Postman.GetFakeRequest(MM.MESSAGE_ADMIN)
        
        timezone = pytz.timezone( profile_m.TimeZone   if profile_m.TimeZone   else 'UTC' )
        message_dict = MP.Postman.GetConversation(fReq, p_msgID, timezone)
        
        hret = CU.HttpReturn()
        hret.results = message_dict
        hret.status = 201
        return hret
    
    
    @staticmethod
    def GetMessageReport():
        # it's impossible to annotate a model.datetime
        sentDt_date = MP.Message.objects.values_list('sent_at', flat=True).order_by('sent_at')
        
        sentDt_days = []
        for sent_dt in sentDt_date:
            dayF = sent_dt.strftime(CU.FORMAT_DTSTR_DT)
            sentDt_days.append(dayF)
        
        sentDt_dist = sorted(list(set(sentDt_days)), reverse=True)
        
        sent_dict = []
        for sentDate in sentDt_dist:
            new_dx = OrderedDict()
            new_dx['sentdate'] = sentDate
            new_dx['count'] = 0
            sent_dict.append(new_dx)
        
        for sentDay in sentDt_days:
            for dayBin in sent_dict:
                if sentDay == dayBin['sentdate'] :
                    dayBin['count'] += 1
                    break
        
        results = {
            'msgCnt': len(sentDt_days),
            'data': sent_dict,
            'colFmt': {'sentdate':"", "count":"format_center"},
        }
        
        return results


class Editor(object):
    
    
    @staticmethod
    def CreateMessageUser():
        
        hret = CU.HttpReturn()
        
        try:
            exist_m = AM.User.objects.get(username=MESSAGE_ADMIN)
        except Exception as ex:
            exist_m = None
        
        if exist_m:
            hret.results = "Message-Admin already exists."
            hret.status = 401       # client error
            return hret
        
        # create user, profile and verify email
        
        email = "lig3ma@gmail.com"
        newUser = AM.User.objects.create_user(MM.MESSAGE_ADMIN, email, '9f8g7h6i5j')
        
        newUser.is_superuser = True
        newUser.is_staff = True
        newUser.save()
        
        prof_m = MT.Profile.objects.get(UserFK=newUser)
        prof_m.Country = "United States"
        prof_m.TimeZone = "America/New_York"
        prof_m.save()
        
        emdd_m, crtd = LM.EmailAddress.objects.get_or_create(
            user=newUser, email=email, verified=True, primary=True)
        
        # return success
        
        hret.results = Reporter.GetMessageAdmin().username
        hret.status = 200
        return hret
    
    
    @staticmethod
    def DeleteConvo(p_request):
        fReq = MP.Postman.GetFakeRequest(MM.MESSAGE_ADMIN, p_request.POST)
        hret = MP.Postman.DeleteConversation(fReq)
        return hret
    
    
    @staticmethod
    def WriteMessage(p_request):
        recipient = p_request.POST['recipients']
        
        if recipient == "ALL USERS":
            hret = Editor.WriteAllUsers(p_request)
            
        else:
            fReq = MP.Postman.GetFakeRequest(MM.MESSAGE_ADMIN, p_request.POST)
            hret = MP.Postman.WriteMessage(fReq)
        
        return hret
    
    
    @staticmethod
    def ReplyMessage(p_request):
        fReq = MP.Postman.GetFakeRequest(MM.MESSAGE_ADMIN, p_request.POST)
        hret = MP.Postman.ReplyMessage(fReq)
        return hret
    
    
    @staticmethod
    def WriteAllUsers(p_request):
        user_mdls = AM.User.objects.all()
        msgAdmin_m = Reporter.GetMessageAdmin()
        
        for user_m in user_mdls:
            currReqPost = p_request.POST.copy()
            currReqPost['recipients'] = user_m.username
            
            fReq = MP.Postman.GetFakeRequest(MM.MESSAGE_ADMIN, currReqPost)
            hret = MP.Postman.WriteMessage(fReq)
            
            if hret.status >= 400:
                excp_lg.error(hret.results)
            
            msg_m = MP.Message.objects.filter(sender=msgAdmin_m, recipient=user_m,
                                ).order_by('-sent_at').first()
            msg_m.replied_at = MP.Postman.GetDateNoReply()          # message can't be replyed in contacts.html
            msg_m.save()
        
        hret = CU.HttpReturn()
        hret.results = "All messages sent."
        hret.status = 200
        return hret
    
    
    @staticmethod
    def DeleteMessages():
        # requirement: all messages on the day that is 2 weeks ago are deleted
        # function meant to be run every day around 11:30pm 
        
        twoWeeks = datetime.datetime.utcnow().replace(tzinfo=pytz.utc) - datetime.timedelta(days=14)
        twoWeeks = twoWeeks.replace(hour=23, minute=59, second=59)
        
        delete_mdls = MP.Message.objects.filter(sent_at__lt=twoWeeks)
        delete_mdls.delete()        
        
        hret = CU.HttpReturn()
        hret.results = "Delete messages complete."
        hret.status = 201
        return hret


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
UNIVERSAL REWARDS
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


class PU_Reporter(object):
    
    
    @staticmethod
    def nMessage(p_request):
        
        return 
    

class PU_Editor(object):
    
    
    @staticmethod
    def RunRewards(p_season, p_round):
        
        roundStatus = FM.TimeMachine.GetRoundPeriod(p_season, p_round)
        
        if roundStatus != 8:
            hret = CU.HttpReturn()
            hret.results = "Round is not finished!"
            hret.status = 401
            return hret
        
        # loop over scores whose rewards have not been sent
        
        scores_mdl = PU.Univ_Scoring.objects.filter(SeasonFK__Season=p_season, Round=p_round, RewardStatus=0)
        
        for score_m in scores_mdl:
            values = PU.Reporter_Ranks.GetRewardValues(score_m.Perc_AllTime, score_m.Perc_Round)
            
            PU_Editor.SendRewardMsg(score_m.UserFK, p_season, p_round, values)
            
            score_m.RewardStatus = 1
            score_m.save()
            
            #prog_lg.debug(score_m.UserFK.username)
            #break   # dev only
        
        hret = CU.HttpReturn()
        hret.results = "RunRewards() Complete"
        hret.status = 201
        return hret
    
    
    @staticmethod
    def SendRewardMsg(p_userMdl, p_season, p_round, p_values):
        
        msgAdmin_m = Reporter.GetMessageAdmin()
        userGrade = PU.Reporter_Ranks.GetUserGrade(p_season, p_round, p_userMdl)
        
        # try:
        #     admin_m = AM.User.objects.get(username="admin")
        # except Exception as ex:
        #     admin_m = None
        
        # create message model with dummy body to be replaced later 
        
        message = MP.MessageData()
        message.sender = msgAdmin_m
        message.recipients = p_userMdl
        message.subject = "Pishbini Ranking R{0}".format(p_round)
        message.body = "Not initialized."
        
        hret = MP.Postman.WriteMessageByData(message.__dict__)        
        
        # get created message model and replace body with js-enabled html
        
        msg_m = MP.Message.objects.filter(sender=msgAdmin_m, recipient=p_userMdl,
                                        subject__contains="Pishbini Ranking"
                                        ).order_by('-sent_at').first()
        
        context = {
            'values': p_values,
            'userGrade': userGrade,
            'messageID': msg_m.id,
            'claimed': False,
        }
        tnc = render_to_string("message_puRankRewards.html", context)
        
        msg_m.body = tnc
        msg_m.replied_at = MP.Postman.GetDateNoReply()      # message can't be replyed in contacts.html
        msg_m.save()
        
        return hret
    
    
    @staticmethod
    def ClaimRewards(p_userMdl, p_msgID):
        hret = CU.HttpReturn()
        
        # get the score model
        
        msg_m = MP.Message.objects.filter(id=p_msgID)[0]
        subject = msg_m.subject
        season = FM.TimeMachine.GetTodaysBracket()['season']
        
        import re
        xStr = '([0-9]+)'
        m = re.search(xStr, subject)
        roundv = m.group(1)
        
        score_m = PU.Univ_Scoring.objects.filter(UserFK=p_userMdl, SeasonFK__Season=season, Round=roundv)[0]
        
        if not score_m:
            hret.results = "No score available for user in round."
            hret.status = 401
            return hret
        
        # use the score data to allocate rewards 
        
        if score_m.RewardStatus == 2:
            hret.results = "Reward for round already claimed."
            hret.status = 401
            return hret
        
        values = PU.Reporter_Ranks.GetRewardValues(score_m.Perc_AllTime, score_m.Perc_Round)
        profile_m = MM.Profile_Reporter.GetProfile_Mdl(p_userMdl)
        roster_m = PU.Univ_Roster.objects.get(UserFK=p_userMdl, SeasonFK__Season=season)
        
        results = {
            'diamond_old': profile_m.Diamonds,
            'diamond_new': profile_m.Diamonds + values['rewTotal']['diamonds'],
            'token_old': roster_m.Token_Total,
            'token_new': roster_m.Token_Total + values['rewTotal']['tokens'],            
        }
        
        score_m.RewardStatus = 2
        score_m.save()
        
        roster_m.Token_Total +=  values['rewTotal']['tokens']
        roster_m.save()
        
        profile_m.Diamonds += values['rewTotal']['diamonds']
        profile_m.save()
        
        # update the reward message so it can't be claimed again
        
        msg_m.body = msg_m.body.replace('<div id="claim_group" class="inner_margin2"',
                                        '<div id="claim_group" class="inner_margin2 format_disable"')
        msg_m.save()
        
        hret.results = results
        hret.status = 200
        return hret


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
END OF FILE
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""