"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
MEMBERS/VIEWS.py
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import os
import json

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.generic.base import View, ContextMixin
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
import allauth.account.forms as AF
import allauth.account.views as AV

import common.utility as CU
import members.models.tables as MT
import members.models.members as MM
import members.models.postman as MP
import members.forms as MF             
import members.consumers as MC
import football.models.football as FM

import logging
prog_lg = logging.getLogger('progress')
excp_lg = logging.getLogger('exception')


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
HTML PAGE REQUESTS
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


def messages(request):
    context = {
        'inbox': mark_safe(json.dumps(MM.IPostman.GetInboxDict(request))),
        'adminTypes': ["Technical Support", "Suggestion for Improvement"],
    }
    return render(request, 'messages.html', context)


def members_admin(request):
    context = {
    }
    return render(request, 'members_admin.html', context)


def contacts(request):
    context = {
        'friendList': mark_safe(json.dumps(MM.Relationship_R.GetFriendData(request.user))),
        'ignoreList': mark_safe(json.dumps(MM.Relationship_R.GetIgnoreData(request.user))),
    }
    return render(request, 'contacts.html', context)


def profile(request):
    
    profile_dx = MM.Profile_Reporter.GetUserData(request.user)
    cSeason = FM.TimeMachine.GetTodaysBracket()['season']
    club_names = list(FM.Reports_General.GetClubs(cSeason))
    club_names.insert(0, "None")
    
    context = {
        'changeUser_form': MF.MemberChangeNameForm(),
        'editEmail_form': AF.AddEmailForm(),
        'password_form': MF.MemberPasswordForm(),
        'profile': profile_dx,
        'club_names': mark_safe(json.dumps(club_names)),
    }
    return render(request, 'profile.html', context)


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
AJAX REQUESTS
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


def dialog(request):
    hret = CU.HttpReturn()
    context = {
        'login_form': MF.MemberLoginForm(),
        'signup_form': AF.SignupForm(), # MF.MemberSignupForm(),
        'resetPw_form': AF.ResetPasswordForm(),        
    }
    hret.results = render_to_string("auth_dialog.html", context, request=request)
    
    hret.status = 201
    return JsonResponse(hret.results, safe=False, status=hret.status)


def db_report(request, command):
    
    prog_lg.info("ajax report command: " + command)
    
    if command == 'inbox':
        inbox = MM.IPostman.GetInboxDict(request)   
        hret = CU.HttpReturn()
        hret.results = inbox
        hret.status = 201
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'userData':
        user = request.GET.get('user')
        userData = MM.Profile_Reporter.GetUserData(user)  
        hret = CU.HttpReturn()
        hret.results = userData
        hret.status = 201
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'viewMsg':
        msgID = request.GET.get('msgID')
        message = MM.IPostman.GetMessage(request, msgID)
        unreadCnt = MM.IPostman.GetUnreadCount(request)
        results = {
            'message': message,
            'unreadCnt': unreadCnt,
        }
        return JsonResponse(results, safe=False)
    
    elif command == 'viewConv':
        thdID = request.GET.get('thdID')
        messages = MM.IPostman.GetConversation(request, thdID)        
        unreadCnt = MM.IPostman.GetUnreadCount(request)
        results = {
            'messages': messages,
            'unreadCnt': unreadCnt,
        }
        return JsonResponse(results, safe=False)
    
    
    elif command == 'friendsList':
        hret = CU.HttpReturn()
        hret.results = MM.Relationship_R.GetFriendData(request.user)
        hret.status = 201
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'ignoreList':
        hret = CU.HttpReturn()
        hret.results = MM.Relationship_R.GetIgnoreData(request.user)
        hret.status = 201
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'searchFriend':
        searchUser = request.GET.get('searchUser')
        hret = MM.Profile_Reporter.SearchFriend(request.user, searchUser)
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'searchIgnore':
        searchUser = request.GET.get('searchUser')
        hret = MM.Profile_Reporter.SearchIgnore(request.user, searchUser)
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    else:
        msg = "command invalid: " + command
        excp_lg.error(msg)
        return JsonResponse(msg, safe=False, status = 404)  


def db_edit(request, command):
    
    prog_lg.info("ajax edit command: " + command)
    
    
    if command == 'changeUser':
        
        form = MF.MemberChangeNameForm(request.user, request.POST)
        
        if form.is_valid():
            # is_valid creates form.cleaned_data
            newName = form.cleaned_data.get('username')           
            result = MM.Profile_Editor.ChangeUserName(request.user, newName)
            hret = CU.HttpReturn()
            
            if result == "1":
                hret.results = newName
                hret.status = 201
                return JsonResponse(hret.results, safe=False, status=hret.status)
            else:
                hret.results = result
                hret.status = 404
                return JsonResponse(hret.results, safe=False, status=hret.status)
        
        hret = CU.HttpReturn()
        hret.results = form.errors
        hret.status = 422
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'realName':
        first = request.POST.get('first')
        last = request.POST.get('last')
        hret = MM.Profile_Editor.SaveRealName(request.user, first, last)
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'favClub':
        newClub = request.POST.get('newClub')
        hret = MM.Profile_Editor.SaveFavoriteClub(request.user, newClub)
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'slogan':
        newSlogan = request.POST.get('newSlogan')
        hret = MM.Profile_Editor.SaveSlogan(request.user, newSlogan)
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'icon':
        newIcon = request.FILES['iconFile']        
        hret = MM.Profile_Editor.SaveIcon(request.user, newIcon)
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'savePrefs':
        
        # the code to get an object from request.body does not work as stated on stackoverflow
        # this procedure is the closest thing that actually works for this version of django
        # it's only good for 1 object in request.body
        
        import urllib
        prefsDec = request.body.decode("utf-8")                  # stackoverflow part
        prefsConv = urllib.parse.unquote(prefsDec)               # had to puzzle this out
        equalIndex = prefsConv.index("=")   
        prefs_txt = prefsConv[equalIndex+1 : len(prefsConv)]     # isolate serialized object
        prefs_dct = json.loads(prefs_txt)                        # convert to python dict
        
        hret = MM.Profile_Editor.SavePreferences(request.user, prefs_dct)
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'deleteAcc':
        hret = MM.Profile_Editor.DeleteAccount(request.user)
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'delete_user':
        userName = request.POST.get('userName')
        results = MM.Profile_Editor.DeleteUser(userName)
        return JsonResponse(results, safe=False)
    
    
    elif command == 'sendMsg':
        hret = MM.IPostman.WriteUserMessage(request)
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'replyMsg':
        hret = MP.Postman.ReplyMessage(request)
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'deleteConv':
        hret = MP.Postman.DeleteConversation(request)
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'msg_friendInvite':
        user = request.user.username
        targetUser = request.POST['inviteUser']
        bodyMsg = request.POST['inviteBody']
        hret = MM.Relationship_E.SendInvite(user, targetUser, bodyMsg)
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'msg_friendReply':
        accept = request.POST['accept']
        messageID = request.POST['messageID']
        hret = MM.Relationship_E.ReplyInvite(accept, messageID)
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'msg_friendRemove':
        primary = request.user
        removeFriend = request.POST['removeFriend']
        hret = MM.Relationship_E.RemoveFriend(primary, removeFriend)
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'ignoreUser':
        primary = request.user
        ignoreUser = request.POST['ignoreUser']
        hret = MM.Relationship_E.IgnoreUser(primary, ignoreUser)
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    elif command == 'ignoreRemove':
        primary = request.user
        removeIgnore = request.POST['removeIgnore']
        hret = MM.Relationship_E.RemoveIgnore(primary, removeIgnore)
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
    
    elif command == 'emailInvite':
        email_address = request.POST.get('email')
        
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string
        from email.mime.image import MIMEImage
        
        context = {
            'inviter': request.user.username,
        }
        text_content = render_to_string('messages/email_inviteUser.txt', context)
        html_content = render_to_string('messages/email_inviteUser.html', context)
        
        subject = "Invite to Play at lige-ma.com"
        eFrom = "Lige Ma LLC <no_reply@mg.lige-ma.com>"
        email_m = EmailMultiAlternatives(subject, text_content, eFrom)
        email_m.attach_alternative(html_content, "text/html")
        email_m.to = [email_address]
        
        results = email_m.send()
        return JsonResponse(results, safe=False)
    
    
    else:
        msg = "command invalid: " + command
        excp_lg.error(msg)
        return JsonResponse(msg, safe=False, status = 404)  



"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
ALLAUTH VIEWS OVERRIDE
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
- the password reset with key view serves the html page used for that
    - it must be overwritten so that the form can have the uidb36 variable
    - this is necessary so when rendering the ajax-enabled template, the correct url can be called
- the password reset doesn't strictly need to be overridden
    - it's nice to make it return the standard http-response object
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


class MemberPasswordResetView(AV.PasswordResetView):
    def __init__(self, *args, **kwargs):
        super(MemberPasswordResetView, self).__init__(*args, **kwargs)
        self.success_url = ""
    
    def dispatch(self, request, *args, **kwargs):
        #prog_lg.info("dispatch")
        return super(MemberPasswordResetView, self).dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.save(self.request)     # sends the email with link to reset
        hret = CU.HttpReturn()
        hret.results = "E-mail with link sent."
        hret.status = 201
        return JsonResponse(hret.results, safe=False, status=hret.status)
    
password_reset = MemberPasswordResetView.as_view()


class MemberPasswordResetFromKeyView(AV.PasswordResetFromKeyView):
    form_class = MF.MemberResetPasswordKeyForm
    
    def __init__(self, *args, **kwargs):
        super(MemberPasswordResetFromKeyView, self).__init__(*args, **kwargs)
    
    def form_valid(self, form):
        #junk = super(MemberPasswordResetFromKeyView, self).form_valid(form)
        # doesn't work, must remove all calls to HttpResponse
        
        from allauth.account.adapter import get_adapter
        from allauth.account import signals
        from django.contrib import messages
        
        form.save()
        get_adapter().add_message(self.request,
                                  messages.SUCCESS,
                                  'account/messages/password_changed.txt')
        signals.password_reset.send(sender=self.reset_user.__class__,
                                    request=self.request,
                                    user=self.reset_user)
        
        hret = CU.HttpReturn()
        hret.results = "Password is reset. You may now log in."
        hret.status = 201
        return JsonResponse(hret.results, safe=False, status=hret.status)     
        
password_reset_from_key = MemberPasswordResetFromKeyView.as_view()


class MemberEmailView(AV.EmailView):
    form_class = MF.MemberAddEmailForm
    
email = MemberEmailView.as_view()



def test_email(request):
    
    emailAdr = request.POST.get('email')
    prog_lg.info(emailAdr)
    
    from django.core.mail import EmailMessage
    email = EmailMessage('test subject', 'test email body', to=[emailAdr])
    sendRes = email.send(fail_silently=False)
    
    prog_lg.info(sendRes)
    
    hret = CU.HttpReturn()
    hret.results = "Email sent."
    hret.status = 201
    return JsonResponse(hret.results, safe=False, status=hret.status)
    


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
END OF FILE
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""