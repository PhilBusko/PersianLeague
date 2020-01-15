"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
MEMBERS/MODELS/POSTMAN.py
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import json

import django.contrib.auth.models as AM

import common.utility as CU
import postman.views as PV

import logging
prog_lg = logging.getLogger('progress')
excp_lg = logging.getLogger('exception')


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
POSTMAN INTERFACE
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


class Postman(object):
        
    
    # get inbox data as list of dict
    # DEPRECATE since can't use timezone
    @staticmethod
    def GetInboxDict(p_request):
        try:
            cData = PV.InboxView.as_view()(p_request).context_data
        except:
            CU.excp_lg.error("Error in request object.")
            return []
        
        rawMsgs = cData['pm_messages']
              
        inbox_dict = []
        for msg in rawMsgs:
            newMsg = {}
            newMsg['id'] = msg.id
            newMsg['thread_id'] = msg.thread_id
            newMsg['sender'] = msg.sender.username  + (" (" +  str(msg.count)  + ")" if  msg.count else "");
            newMsg['subject'] = msg.subject
            newMsg['sent_at'] = msg.sent_at.strftime(CU.FORMAT_DTSTR)  if msg.sent_at  else None
            newMsg['read_at'] = msg.read_at.strftime(CU.FORMAT_DTSTR)  if msg.read_at  else None
            newMsg['replied_at'] = msg.replied_at.strftime(CU.FORMAT_DTSTR)  if msg.replied_at  else None
            inbox_dict.append(newMsg)
        
        return inbox_dict
    
    
    # private method, call members.IPostman.GetMessage instead
    @staticmethod
    def GetMessage(p_request, p_msgID, p_timezone):
        
        viewData = PV.MessageView.as_view()(p_request, p_msgID).context_data
        msgData = viewData['pm_messages'][0]
        jMsg = Postman.ConvertMessage(msgData, p_timezone)
        
        return jMsg.__dict__
    
    
    # private method, call members.IPostman.GetConversation instead
    @staticmethod
    def GetConversation(p_request, p_thdID, p_timezone):
        viewData = PV.ConversationView.as_view()(p_request, p_thdID).context_data
        msg_mdls = viewData['pm_messages']
        jMsgs = []
        
        for msg_m in msg_mdls:
            jMsg = Postman.ConvertMessage(msg_m, p_timezone)
            jMsgs.append(jMsg.__dict__)
        
        return jMsgs
    
    
    @staticmethod
    def ConvertMessage(message_m, p_timezone):
        jMsg = MessageData()
        jMsg.id = message_m.id   
        jMsg.thread = message_m.thread_id   
        jMsg.subject = message_m.subject
        jMsg.body = message_m.body
        jMsg.sender = message_m.sender.username
        jMsg.recipient = message_m.recipient.username
        jMsg.sent_at = message_m.sent_at.astimezone(p_timezone).strftime(CU.FORMAT_DTSTR)  if message_m.sent_at  else None
        jMsg.read_at = message_m.read_at.astimezone(p_timezone).strftime(CU.FORMAT_DTSTR)  if message_m.read_at  else None
        jMsg.replied_at = message_m.replied_at.astimezone(p_timezone).strftime(CU.FORMAT_DTSTR)  if message_m.replied_at  else None
        return jMsg
    
    
    
    @staticmethod
    def WriteMessage(p_request):
        v = PV.WriteView.as_view()(p_request)
        
        f = None
        if hasattr(v, 'context_data'):
            f = v.context_data['form'].errors
            #prog_lg.info(v.context_data)
        
        hret = CU.HttpReturn()
        
        if f:
            jf = json.dumps(f)
            hret.results = jf
            hret.status = 401
        else:
            hret.results = "Message Sent."
            hret.status = 201
        return hret
    
    
    @staticmethod
    def ReplyMessage(p_request):
        msgID = int(p_request.POST['message_id'])
        v = PV.ReplyView.as_view()(p_request, msgID)
        
        f = None
        if hasattr(v, 'context_data'):
            f = v.context_data['form'].errors
        
        hret = CU.HttpReturn()
        
        if f:
            jf = json.dumps(f)
            hret.results = jf
            hret.status = 401
        else:
            hret.results = "Message Replied."
            hret.status = 201
        return hret
    
    
    @staticmethod
    def DeleteConversation(p_request):
                
        # pks = p_request.POST.getlist('pks[]')
        # tpks = p_request.POST.getlist('tpks[]')
        # prog_lg.info(p_request.POST)
        # prog_lg.info(pks)
        # prog_lg.info(tpks)
        
        v = DeleteView_Correct.as_view()(p_request)
        f = None
        if hasattr(v, 'context_data'):
            f = v.context_data['form'].errors
        
        hret = CU.HttpReturn()
        
        if f:
            jf = json.dumps(f)
            hret.results = jf
            hret.status = 401
        else:
            hret.results = "Message Deleted."
            hret.status = 201
        return hret
    
    
    # parameter is a MessageData dict
    @staticmethod
    def WriteMessageByData(p_msgDx):
        
        fReq = Postman.GetFakeRequest(p_msgDx['sender'], p_msgDx)
        
        return Postman.WriteMessage(fReq)
    
    
    @staticmethod
    def ReplyMessageByData(p_msgDx, p_messageID):
        
        fReq = Postman.GetFakeRequest(p_msgDx['sender'], p_msgDx)
        fReq.POST['message_id'] = p_messageID
        
        return Postman.ReplyMessage(fReq)
    
    
    # simulate a request so view can be tricked
    @staticmethod
    def GetFakeRequest(p_userName, p_data=None):
        
        from django.test import RequestFactory
        from django.core.urlresolvers import ResolverMatch
        
        factory = RequestFactory()
        
        if not p_data:
            fRequest = factory.get('')
        else:
            fRequest = factory.post('', p_data)
        
        try:
            user_m = AM.User.objects.get(username = p_userName)
        except AM.User.DoesNotExist:
            return None
        
        fRequest.user = user_m
        fRequest._dont_enforce_csrf_checks = True 
        fRequest.resolver_match = ResolverMatch(func='', args=('',),
                                               kwargs={}, url_name=None, app_names=[], namespaces=[])
        
        return fRequest
    
    
    # return a static value signifying a message cannot be replied to
    @staticmethod
    def GetDateNoReply():
        from datetime import datetime
        dateNRP = datetime.strptime('1000 01 01', '%Y %m %d')
        return dateNRP


# TODO: deprecate this class, use dict instead
class MessageData(object):
    def __init__(self):
        self.id = None 
        self.thread = None
        self.sender = None
        self.recipient = None
        self.subject = None
        self.body = None
        self.sent_at = None
        self.read_at = None
        self.replied_at = None
    def __str__(self):
        return "MsgDT {}: {} -> {} [{}]".format(
            self.id, self.sender, self.recipient, self.subject)
    def __repr__(self):
        return self.__str__()


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
POSTMAN CORRECTIONS
- postman 3.3.1 has a bug in DeleteView, the POST.getlist() call doesn't work
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

from django.views.generic import View
from django.utils.translation import ugettext as _, ugettext_lazy
from django.utils.timezone import now
from django.db.models import Q
from postman.models import Message
from django.contrib import messages
from django.shortcuts import redirect

class UpdateMessageMixin_Correct(PV.UpdateMessageMixin):
    def post(self, request, *args, **kwargs):
        next_url = PV._get_referer(request) or 'postman:inbox'
        pks = request.POST.getlist('pks[]')
        tpks = request.POST.getlist('tpks[]')
        if pks or tpks:
            user = request.user
            filter = Q(pk__in=pks) | Q(thread__in=tpks)
            recipient_rows = Message.objects.as_recipient(user, filter).update(**{'recipient_{0}'.format(self.field_bit): self.field_value})
            sender_rows = Message.objects.as_sender(user, filter).update(**{'sender_{0}'.format(self.field_bit): self.field_value})
            if not (recipient_rows or sender_rows):
                raise Http404  # abnormal enough, like forged ids
            messages.success(request, self.success_msg, fail_silently=True)
            return redirect(request.GET.get('next') or self.success_url or next_url)
        else:
            messages.warning(request, _("Select at least one object."), fail_silently=True)
            return redirect(next_url)

class DeleteView_Correct(UpdateMessageMixin_Correct, View):
    """Mark messages/conversations as deleted."""
    field_bit = 'deleted_at'
    success_msg = ugettext_lazy("Messages or conversations successfully deleted.")
    field_value = now()


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
END OF FILE
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""