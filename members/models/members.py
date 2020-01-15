"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
MEMBERS/MODELS/MEMBERS.py
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import os
import datetime
import pytz

from django.conf import settings
from django.db.models import Count, F, Q     
import django.contrib.auth.models as AM
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from django.template.loader import render_to_string

import common.utility as CU
import football.models.tables as FT
import football.models.football as FM
import members.models.tables as MT
import members.models.postman as MP
import postman.models as PM

import logging
prog_lg = logging.getLogger('progress')
excp_lg = logging.getLogger('exception')


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
PROFILE REPORTER
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


class Profile_Reporter(object):
    
    
    @staticmethod
    def GetProfile_Mdl(p_user):
        prof_m = MT.Profile.objects.get(UserFK=p_user)
        return prof_m
    
    
    # returns user info as dict
    @staticmethod
    def GetUserData(p_user):    # GetFullUserData
        
        try:
            user_m = AM.User.objects.get(username=p_user)
        except AM.User.DoesNotExist:
            raise ObjectDoesNotExist("User not found.")
        
        try:
            prof_m = MT.Profile.objects.get(UserFK=user_m)
        except MT.Profile.DoesNotExist:
            raise ObjectDoesNotExist("Profile not found.")
        
        if prof_m.TimeZone:
            timezone = pytz.timezone(prof_m.TimeZone).localize(datetime.datetime.now()).strftime('%Z')
            country = prof_m.Country
        else:
            timezone = "Unknown"
            country = "Unknown"
        
        timeOW_dlt = datetime.datetime.utcnow().replace(tzinfo=pytz.utc) - user_m.date_joined    # no GetCustomNow
        if timeOW_dlt.days <= 365:
            timeOW_nm = timeOW_dlt.days / 30.42
            timeOnWebsite = str(round(timeOW_nm, 1)) + " months"
        else:
            timeOW_nm = timeOW_dlt.days / 365
            timeOnWebsite = str(round(timeOW_nm, 2)) + " years"
        
        full = lambda: None
        full.hashID = prof_m.HashID
        full.userName = user_m.username
        full.realName = user_m.get_full_name()
        full.email = user_m.email
        full.dateJoined = user_m.date_joined.strftime(CU.FORMAT_DTSTR_DT)
        full.timeOnWebsite = timeOnWebsite
        full.timezone = timezone 
        full.country = country 
        full.favClub = prof_m.FavClubFK.Club if prof_m.FavClubFK else None
        full.favClubPath = FM.Reports_General.GetLogoPath(prof_m.FavClubFK.Club)  if prof_m.FavClubFK else None
        full.favClubSet = prof_m.FavClubSet
        full.slogan = prof_m.Slogan
        full.icon = '{0}/{1}'.format(prof_m.Icon[0], prof_m.Icon)   if prof_m.Icon   else None
        full.pref_frdRealName = prof_m.Pref_FriendsRealName
        full.pref_frdEmail = prof_m.Pref_FriendsEmail
        full.diamonds = prof_m.Diamonds
        full.lifetimeDiamonds = prof_m.LifetimeDiamonds
        
        return full.__dict__
    
    
    @staticmethod
    def GetUserModel(p_user):
        try:
            user_m = AM.User.objects.get(username=p_user)
        except AM.User.DoesNotExist:
            user_m = None
        return user_m
    
    
    # returns a datetime in the user's timezone
    @staticmethod
    def GetUserNow(p_userMdl):
        
        if p_userMdl.is_authenticated():
            profile_m = Profile_Reporter.GetProfile_Mdl(p_userMdl)
            profTZ = pytz.timezone(profile_m.TimeZone   if profile_m.TimeZone   else 'UTC')
            userNow = FM.TimeMachine.GetCustomNow().astimezone(profTZ).strftime(CU.FORMAT_DTSTR)
        else:   
            userNow = FM.TimeMachine.GetCustomNow().strftime(CU.FORMAT_DTSTR)
        
        return userNow
    
    
    @staticmethod
    def ViewProfileData(p_requester, p_target):
        
        # get user models
        
        try:
            target_m = AM.User.objects.get(username=p_target)
        except AM.User.DoesNotExist:
            raise ObjectDoesNotExist("Target user not found.")
        
        try:
            targetProf_m = MT.Profile.objects.get(UserFK=target_m)
        except MT.Profile.DoesNotExist:
            raise ObjectDoesNotExist("Target user profile not found.")
        
        # get any relation among users
        
        if not p_requester.id:
            relation = "Log in to make friends."
        else:
            relRequester = MT.Relationship.objects.filter(User1FK=p_requester, User2FK=target_m
                ).values_list('RelationValue', flat=True)
            
            relTarget = MT.Relationship.objects.filter(User1FK=target_m, User2FK=p_requester
                ).values_list('RelationValue', flat=True)
            
            if relRequester:
                if relRequester[0] == 1:
                    relation = "Your friend"
                else:
                    relation = "Ignored by you"
                    
            elif relTarget:
                relation = "Ignored by them"
                
            else:
                relation = "None"
        
        # discover target user info for display
        
        if relation == "Your friend" and targetProf_m.Pref_FriendsRealName == True and target_m.get_full_name():
            realName = target_m.get_full_name()
        elif target_m.get_full_name():   # name is set
            realName = "****** ******"
        else:
            realName = ""
        
        if relation == "Your friend" and targetProf_m.Pref_FriendsEmail == True:
            email = target_m.email
        else:
            email = "*********"
        
        if targetProf_m.TimeZone:
            timezone = pytz.timezone(targetProf_m.TimeZone).localize(datetime.datetime.now()).strftime('%Z')
            country = targetProf_m.Country
        else:
            timezone = "Unknown"
            country = "Unknown"
        
        timeOW_dlt = FM.TimeMachine.GetCustomNow() - target_m.date_joined
        if timeOW_dlt.days <= 365:
            timeOW_nm = timeOW_dlt.days / 30.42
            timeOnWebsite = str(round(timeOW_nm, 1)) + " months"
        else:
            timeOW_nm = timeOW_dlt.days / 365
            timeOnWebsite = str(round(timeOW_nm, 2)) + " years"
        
        # create return data structure
        
        full = lambda: None
        
        full.userName = target_m.username
        full.realName = realName
        full.email = email
        full.timezone = timezone 
        full.country = country
        full.icon = '{0}/{1}'.format(targetProf_m.Icon[0], targetProf_m.Icon)   if targetProf_m.Icon   else None
        
        full.relationship = relation
        full.slogan = targetProf_m.Slogan if targetProf_m.Slogan else ""
        full.lifetimeDiamonds = targetProf_m.LifetimeDiamonds
        full.timeOnWebsite = timeOnWebsite        
        full.dateJoined = target_m.date_joined.strftime(CU.FORMAT_DTSTR_DT)
        full.favClub = targetProf_m.FavClubFK.Club if targetProf_m.FavClubFK else None
        
        full.friendList = Relationship_R.GetFriendData(target_m) 
        
        return full.__dict__
    
    
    @staticmethod
    def SearchFriend(p_searcher, p_target):
        hret = CU.HttpReturn()
        
        # first check if there's a user at all
        
        try:
            targetData = Profile_Reporter.GetUserData(p_target)
        except Exception as ex:
            hret.results = "User not found."
            hret.status = 201
            return hret
        
        # check the searcher's friend's list
        
        try:
            targetUser = AM.User.objects.get(username=p_target)
        except AM.User.DoesNotExist:
            targetUser = None
            
        if targetUser:
            try:
                rel_m = MT.Relationship.objects.get(User1FK = p_searcher, User2FK = targetUser)
            except MT.Relationship.DoesNotExist:
                rel_m = None
                        
            if rel_m and rel_m.RelationValue == 1:
                hret.results = "User is in your friend list."
                hret.status = 201
                return hret
            
            if rel_m and rel_m.RelationValue == -1:
                hret.results = "User is in your ignore list."
                hret.status = 201
                return hret
        
        # check the target's ignore list
        
        try:
            relRev_m = MT.Relationship.objects.get(User1FK = targetUser, User2FK = p_searcher)
        except MT.Relationship.DoesNotExist:
            relRev_m = None
        
        if relRev_m and relRev_m.RelationValue == -1:
            hret.results = "User has you in their ignore list."
            hret.status = 201
            return hret
        
        # the target is a potential friend, so return their data to be displayed
        
        hret.results = targetData
        hret.status = 201
        return hret
    
    
    @staticmethod
    def SearchIgnore(p_searcher, p_target):
        
        hret = CU.HttpReturn()
        
        # first check if there's a user at all
        
        try:
            targetData = Profile_Reporter.GetUserData(p_target)
        except Exception as ex:
            hret.results = "User not found."
            hret.status = 201
            return hret
        
        # check for any existing relationship
        
        try:
            targetUser = AM.User.objects.get(username=p_target)
        except AM.User.DoesNotExist:
            targetUser = None
            
        if targetUser:
            try:
                rel_m = MT.Relationship.objects.get(User1FK = p_searcher, User2FK = targetUser)
            except MT.Relationship.DoesNotExist:
                rel_m = None
                
            if rel_m and rel_m.RelationValue == 1:
                hret.results = "User is in your friends list."
                hret.status = 201
                return hret
            
            if rel_m and rel_m.RelationValue == -1:
                hret.results = "User is in your ignore list."
                hret.status = 201
                return hret
        
        # return found user
        
        hret.results = targetData
        hret.status = 201
        return hret



"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
PROFILE EDITOR
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


class Profile_Editor(object):
    
    
    @staticmethod
    def ChangeUserName(user, newName):        
        
        prog_lg.info(newName)
        
        try:
            user_m = AM.User.objects.get(username = user)
        except AM.User.DoesNotExist:
            return "User not found."
        
        user_m.username = newName
        user_m.save()
        
        return "1"
    
    
    @staticmethod
    def SaveRealName(user, first, last):
        hret = CU.HttpReturn()
        try:
            user_m = AM.User.objects.get(username = user)
        except AM.User.DoesNotExist:
            hret.results = "User not found."
            hret.status = 201
            return hret
        
        user_m.first_name = first
        user_m.last_name = last
        user_m.save()
        
        # return succesfull results
        
        hret = CU.HttpReturn()
        hret.results = user_m.get_full_name()
        hret.status = 201
        return hret
    
    
    @staticmethod
    def SaveFavoriteClub(user, newClub):
        
        hret = CU.HttpReturn()
        try:
            user_m = AM.User.objects.get(username = user)
        except AM.User.DoesNotExist:
            hret.results = "User not found."
            hret.status = 201
            return hret
        
        try:
            prof_m = MT.Profile.objects.get(UserFK = user_m)
        except MT.Profile.DoesNotExist:
            hret.results = "Profile not found."
            hret.status = 201
            return hret
        
        try:
            club_m = FT.Club.objects.get(Club = newClub)
        except FT.Club.DoesNotExist:
            hret.results = "Club not found."
            hret.status = 201
            return hret
        
        prof_m.FavClubFK = club_m
        prof_m.FavClubSet = True
        prof_m.save()
        
        # return succesfull results
        
        hret = CU.HttpReturn()
        hret.results = club_m.Club
        hret.status = 201
        return hret
    
    
    @staticmethod
    def SaveSlogan(user, newSlogan):
        hret = CU.HttpReturn()
        try:
            user_m = AM.User.objects.get(username = user)
        except AM.User.DoesNotExist:
            hret.results = "User not found."
            hret.status = 201
            return hret
        
        try:
            prof_m = MT.Profile.objects.get(UserFK = user_m)
        except MT.Profile.DoesNotExist:
            hret.results = "Profile not found."
            hret.status = 201
            return hret
        
        prof_m.Slogan = newSlogan
        prof_m.save()
        
        # return succesfull results
        
        hret = CU.HttpReturn()
        hret.results = newSlogan
        hret.status = 201
        return hret
    
    
    @staticmethod
    def SaveIcon(user, newIcon):
        
        # data gathering
        
        hret = CU.HttpReturn()
        try:
            user_m = AM.User.objects.get(username=user)
        except AM.User.DoesNotExist:
            hret.results = "User not found."
            hret.status = 501
            return hret
        
        try:
            profile_m = MT.Profile.objects.get(UserFK=user_m)
        except AM.User.DoesNotExist:
            hret.results = "Profile not found."
            hret.status = 501
            return hret
        
        # save parameter file from user to the server's file storage
        # new icon type: django.core.files.uploadedfile.InMemoryUploadedFile
        
        # 1. check if it's an image
        
        import magic
        filetype = magic.from_buffer(newIcon.read())
        newIcon.seek(0)     # reset file cursor
        
        if 'image' not in filetype:
            hret.results = "File is not an image."
            hret.status = 422
            return hret
        
        # 2. reduce size of image to at most 500 pixels per side
        
        
        
        
        # 3. save file at server
        
        from django.core.files.storage import FileSystemStorage
        from django.core.files.base import ContentFile
        import socket
        
        folder = profile_m.HashID[0]
        
        host = socket.gethostname()
        if host.startswith('test') or host.startswith('prod'):
            fsLoc = os.path.join(settings.BASE_DIR, 'app_proj/static/user_icons', folder )
        else:
            fsLoc = os.path.join(settings.BASE_DIR, 'members/static/user_icons', folder )
        
        fs = FileSystemStorage(location=fsLoc)      # requires the absolute path
        
        if profile_m.Icon:
            existingFullPath = os.path.join(fsLoc, profile_m.Icon)
            if os.path.isfile(existingFullPath):
                os.remove(existingFullPath)
        
        fileName = profile_m.HashID + '_icon.jpg'
        fs.save(fileName, ContentFile(newIcon.read()))
        
        profile_m.Icon = fileName
        profile_m.save()
        
        # return succesfull results
        
        records = {
            'message': "User icon saved.",
            'iconFileName': fileName,
        }
        
        hret = CU.HttpReturn()
        hret.results = records
        hret.status = 201
        return hret
    
    
    @staticmethod
    def SavePreferences(user, prefs_dct):
        
        hret = CU.HttpReturn()
        try:
            user_m = AM.User.objects.get(username = user)
        except AM.User.DoesNotExist:
            hret.results = "User not found."
            hret.status = 401
            return hret
        
        try:
            prof_m = MT.Profile.objects.get(UserFK = user_m)
        except MT.Profile.DoesNotExist:
            hret.results = "Profile not found."
            hret.status = 401
            return hret
        
        prof_m.Pref_FriendsRealName = prefs_dct['frdRealName']
        prof_m.Pref_FriendsEmail = prefs_dct['frdEmail']
        prof_m.save()
        
        # return succesfull results
        
        hret = CU.HttpReturn()
        hret.results = user_m.get_full_name()
        hret.status = 201
        return hret


    @staticmethod
    def DeleteAccount(user):
        
        hret = CU.HttpReturn()
        try:
            user_m = AM.User.objects.get(username = user)
        except AM.User.DoesNotExist:
            hret.results = "User not found."
            hret.status = 401
            return hret
        
        user_m.is_active = False
        user_m.save()
        
        # return succesfull results
        
        hret = CU.HttpReturn()
        hret.results = "User account inactivated."
        hret.status = 201
        return hret


    @staticmethod
    def DeleteUser(user):
        try:
            user_m = AM.User.objects.get(username=user)
        except:
            return "User not found."
        
        if user_m.is_superuser:
            return "Can't delete an admin."
        
        user_m.delete();
        
        return "User deleted."



"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
PROFILE SIGNALS
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

# when a user is created, also create their profile

import hashlib
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
@receiver(post_save, sender=AM.User)
def TriggerProfile(sender, instance, created, **kwargs):
    if created:
        emailEnc = instance.email.encode('utf-8')
        hashRaw = hashlib.md5(emailEnc).hexdigest()     # 32 digits
        hashID = ""
        for h in range(0, 9, 1):
            d = hashRaw[h]
            hashID += d.capitalize()
            if h in (2, 5):
                hashID += "-"
        
        prof_m, crtd = MT.Profile.objects.get_or_create(
            UserFK = instance, HashID = hashID)


# override user logged in signal

from django.contrib.auth.signals import user_logged_in
from django.contrib.auth.models import update_last_login
from members.middleware import RequestMiddleware
from django.contrib.gis.geoip2 import GeoIP2
from timezonefinder import TimezoneFinder

user_logged_in.disconnect(update_last_login)

@receiver(user_logged_in)
def user_login_preupdate(sender, user, **kwargs):
    
    # get request data from custom middleware
    
    thread_local = RequestMiddleware.thread_local
    if hasattr(thread_local, 'request'):
        request = thread_local.request
        userIP = request.META['REMOTE_ADDR']
    else:
        excp_lg.error('No http request available for:' + user.username)
        userIP = None
    
    if userIP == "127.0.0.1":
        userIP = "98.204.240.42"    
    
    if userIP:
        try:
            geo = GeoIP2()
            city_dx = geo.city(userIP)
            
            lat = float(city_dx['latitude'])
            lng = float(city_dx['longitude'])
            tf = TimezoneFinder()
            timezone = tf.timezone_at(lng=lng, lat=lat)
            if timezone is None:
                timezone = tf.closest_timezone_at(lng=lng, lat=lat)
            
            if not timezone:
                excp_lg.error("TimeZone not found for " + user.username)
            
            prof_m = MT.Profile.objects.get(UserFK=user)
            
            prof_m.IP = userIP
            prof_m.Country = city_dx['country_name']
            prof_m.Region = city_dx['region']
            prof_m.City = city_dx['city']
            prof_m.TimeZone = timezone
            prof_m.save()
            
        except Exception as ex:
            excp_lg.error(ex)
    
    
    # display welcome message
    
    if not user.last_login:
        first_login = True
    
    # reconnect the built-in signal
    update_last_login(sender, user, **kwargs)


# allow users to change email addresses, but limit to one email per user

from allauth.account.models import EmailAddress
from allauth.account.signals import email_confirmed  
@receiver(email_confirmed)
def update_user_email(sender, request, email_address, **kwargs):
    email_address.set_as_primary()
    stale_addresses = EmailAddress.objects.filter(
        user=email_address.user).exclude(primary=True).delete()


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
RELATIONSHIP LIST
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


class Relationship_R(object):
    
    
    @staticmethod
    def GetFriendData(p_user):
        try:
            rel_mdls = MT.Relationship.objects.filter(User1FK=p_user, RelationValue=1
                ).order_by('User2FK__username')
        except MT.Relationship.DoesNotExist:
            return None
        
        rel_js = []
        for rel_m in rel_mdls:
            rel_c = Relationship_R.GetRelationData(rel_m)
            rel_js.append(rel_c.__dict__)
        
        return rel_js
    
    
    @staticmethod
    def GetIgnoreData(p_user):
        try:
            rel_mdls = MT.Relationship.objects.filter(User1FK__username = p_user, RelationValue = -1
            ).order_by('User2FK__username')
        except MT.Relationship.DoesNotExist:
            return None
        
        rel_js = []
        for rel_m in rel_mdls:
            rel_c = Relationship_R.GetRelationData(rel_m)
            rel_js.append(rel_c.__dict__)
        
        return rel_js
    
    
    @staticmethod
    def GetRelationData(p_rel):
        
        profile_m = MT.Profile.objects.get(UserFK=p_rel.User2FK)
        
        rel = lambda: None
        rel.name = p_rel.User2FK.username
        rel.icon = '{0}/{1}'.format(profile_m.Icon[0], profile_m.Icon)   if profile_m.Icon   else None
        rel.slogan = profile_m.Slogan
        rel.favClub = profile_m.FavClubFK.Club  if profile_m.FavClubFK  else None
        
        return rel


class Relationship_E(object):
    
    
    @staticmethod
    def SendInvite(p_user, p_target, p_bodyMsg):
        
        # assume the target user exists at this point because the UI requires it
        # assume the target user is not a friend or ignored by the requesting user
        
        # check if there is already an invite
        
        msg_m = PM.Message.objects.filter(sender__username=p_user, recipient__username=p_target,
                                          subject="Friend Invite", recipient_deleted_at=None )
        
        if msg_m:
            hret = CU.HttpReturn()
            hret.results = "Invite already sent."
            hret.status = 201
            return hret
        
        # create invite message and insert it
        # uses dummy body to be replaced later by html
        
        message = MP.MessageData()
        message.sender = p_user
        message.recipients = p_target
        message.subject = "Friend Invite"
        message.body = "Please reload page."
        
        hret = MP.Postman.WriteMessageByData(message.__dict__)        
        
        # get created message data
        
        msg_m = PM.Message.objects.filter(sender__username = p_user, recipient__username = p_target, subject = "Friend Invite"
                                    ).order_by('-sent_at')[0]
        msgID = msg_m.id
        
        # replace body with data for body's accept/reject links
        
        context = {
            'body': p_bodyMsg,
            'messageID': msgID,
            'replied': False,
        }
        tnc = render_to_string("message_invite.html", context)
        
        msg_m.body = tnc
        msg_m.replied_at = MP.Postman.GetDateNoReply()
        msg_m.save()
        
        return hret
    
    
    @staticmethod
    def ReplyInvite(p_accept, p_messageID):
        
        msg_m = PM.Message.objects.get(id = p_messageID)
                
        # create the reply data and send it
        
        message = MP.MessageData()
        message.sender = msg_m.recipient.username
        message.recipients = msg_m.sender.username
        message.subject = "Friend Invite"
        message.body = "The invite was " + ("accepted." if int(p_accept) else "rejected.")
        
        hret = MP.Postman.ReplyMessageByData(message.__dict__, p_messageID)
        
        # make the user friends
        
        if int(p_accept):
            user1_m = AM.User.objects.get(username = msg_m.sender.username)
            user2_m = AM.User.objects.get(username = msg_m.recipient.username)
            rel_m, created = MT.Relationship.objects.get_or_create(
                User1FK = user1_m, User2FK = user2_m, RelationValue = 1)
            rel_m, created = MT.Relationship.objects.get_or_create(
                User1FK = user2_m, User2FK = user1_m, RelationValue = 1)
        
        # disable the links in the invite message
        
        msg_m = PM.Message.objects.get(id = p_messageID)    # refresh message, now with thread_id set
        
        nStart = msg_m.body.find('<span id="body_block">')
        nStart += len('<span id="body_block">')
        nStop = msg_m.body.find('</span id="body_block">')
        bodyMsg = msg_m.body[nStart : nStop]
        
        import html.parser
        html_parser = html.parser.HTMLParser()
        unescaped = html_parser.unescape(bodyMsg)
        
        context = {
            'body': unescaped,
            'messageID': None,
            'replied': True,
        }
        tnc = render_to_string("message_invite.html", context)
        
        msg_m.body = tnc
        msg_m.save()
        
        # mark the reply message as not-replyable
        
        threadID = msg_m.thread_id
        rpl_m = PM.Message.objects.get(parent_id = threadID)   
        
        rpl_m.replied_at = MP.Postman.GetDateNoReply()
        rpl_m.save()
        
        return hret 
    
    
    @staticmethod
    def RemoveFriend(primaryUser, removed):
        removeUser = AM.User.objects.get(username=removed)
        MT.Relationship.objects.get(User1FK = primaryUser, User2FK = removeUser).delete()
        MT.Relationship.objects.get(User1FK = removeUser, User2FK = primaryUser).delete()
        
        hret = CU.HttpReturn()
        hret.results = "Friendship removed."
        hret.status = 201
        return hret
        
    
    @staticmethod
    def IgnoreUser(primaryUser, ignore):
        ignoreUser = AM.User.objects.get(username = ignore)
        rel_m, created = MT.Relationship.objects.get_or_create(
                User1FK = primaryUser, User2FK = ignoreUser, RelationValue = -1)
        
        hret = CU.HttpReturn()
        hret.results = "User ignored."
        hret.status = 201
        return hret
    
    
    @staticmethod
    def RemoveIgnore(primaryUser, ignore):
        ignoreUser = AM.User.objects.get(username = ignore)
        MT.Relationship.objects.get(User1FK = primaryUser, User2FK = ignoreUser).delete()
        
        hret = CU.HttpReturn()
        hret.results = "Ignore relationship removed."
        hret.status = 201
        return hret



"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
POSTMAN INTERFACE
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import postman.views as PV

# can't import central files to this file
# so define the message admin here 
MESSAGE_ADMIN = "LigeMa"


class IPostman(object):
    
    
    # define inbox dict here so message times can get user's timezone
    @staticmethod
    def GetInboxDict(p_request):
        try:
            cData = PV.InboxView.as_view()(p_request).context_data
        except:
            CU.excp_lg.error("Error in request object.")
            return []
        
        rawMsgs = cData['pm_messages']
        profile_m = MT.Profile.objects.get(UserFK=p_request.user)
        timezone = pytz.timezone( profile_m.TimeZone   if profile_m.TimeZone   else 'UTC' )
        
        inbox_dict = []
        for msg in rawMsgs:
            newMsg = {}
            newMsg['id'] = msg.id
            newMsg['thread_id'] = msg.thread_id
            newMsg['sender'] = msg.sender.username  + (" (" +  str(msg.count)  + ")" if  msg.count else "");
            newMsg['subject'] = msg.subject
            newMsg['sent_at'] = msg.sent_at.astimezone(timezone).strftime(CU.FORMAT_DTSTR)  if msg.sent_at  else None
            newMsg['read_at'] = msg.read_at.astimezone(timezone).strftime(CU.FORMAT_DTSTR)  if msg.read_at  else None
            newMsg['replied_at'] = msg.replied_at.astimezone(timezone).strftime(CU.FORMAT_DTSTR)  if msg.replied_at  else None
            inbox_dict.append(newMsg)
        
        return inbox_dict

    
    @staticmethod
    def GetMessage(p_request, p_msgID):
        profile_m = MT.Profile.objects.get(UserFK=p_request.user)
        timezone = pytz.timezone( profile_m.TimeZone   if profile_m.TimeZone   else 'UTC' )
        message_dx = MP.Postman.GetMessage(p_request, p_msgID, timezone)
        return message_dx
    
    
    @staticmethod
    def GetConversation(p_request, p_msgID):
        profile_m = MT.Profile.objects.get(UserFK=p_request.user)
        timezone = pytz.timezone( profile_m.TimeZone   if profile_m.TimeZone   else 'UTC' )
        message_dict = MP.Postman.GetConversation(p_request, p_msgID, timezone)
        return message_dict
    
    
    @staticmethod
    def WriteUserMessage(p_request):
        
        sender = p_request.user.username
        recipient = p_request.POST.get('recipients')
        
        # prog_lg.debug(sender)
        # prog_lg.debug(recipient)
        
        # exceptions
        
        if "admin " in recipient:
            return IPostman.WriteAdminMessage(p_request)
        
        if sender == recipient:
            return MP.Postman.WriteMessage(p_request)
        
        # check for relationship status
        
        relValue = MT.Relationship.objects.values_list('RelationValue', flat=True
            ).filter(User1FK__username = recipient, User2FK__username = sender)
        if relValue:
            relValue = relValue[0]
        else:
            relValue = 0
        
        hret = CU.HttpReturn()
        
        if relValue == 0:
            hret.results = "Message NOT sent: user is not in your friends list."
            hret.status = 201
            return hret
        elif relValue == -1:
            hret.results = "Message NOT sent: user has you in their ignore list."
            hret.status = 201
            return hret
        
        # send message if friends
        
        return MP.Postman.WriteMessage(p_request)
    
    
    @staticmethod
    def WriteAdminMessage(p_request):
        
        sender = p_request.user.username
        recipient = p_request.POST.get('recipients')
        subject = p_request.POST.get('subject')
        body = p_request.POST.get('body')
        
        if "Technical" in recipient:
            subject = "[TS] " + subject
        elif "Suggestion" in recipient:
            subject = "[SI] " + subject
        
        message = MP.MessageData()
        message.sender = sender
        message.recipients = MESSAGE_ADMIN     
        message.subject = subject
        message.body = body
        
        fReq = MP.Postman.GetFakeRequest(sender, message.__dict__)
        
        return MP.Postman.WriteMessage(fReq)
    
    
    @staticmethod
    def GetUnreadCount(p_request):
        inbox_dict = MP.Postman.GetInboxDict(p_request)
        
        unreadCnt = 0
        for msg in inbox_dict:
            if not msg['read_at']:
                unreadCnt += 1
        
        return unreadCnt



"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
END OF FILE
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""