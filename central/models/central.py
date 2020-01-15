"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
COMMON/CENTRAL.py
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import pytz
import json
import datetime

from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from paypal.standard.forms import PayPalPaymentsForm
import django.contrib.auth.models as AM

import common.utility as CU
import members.models.members as MM
import football.models.football as FM
import prediction.models.universal as PU

import logging
prog_lg = logging.getLogger('progress')
excp_lg = logging.getLogger('exception')


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
CENTRAL CLASSES
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


class Reporter(object):
    
    
    @staticmethod
    def GetStoreConfig(p_userMdl):
        store_dict = []
        store_dict.append( {'id': 1, 'dollars': 5, 'diamonds': 50, 'caption': "(100% Value)",
                            'form': Reporter.GetPaypalForm(5, 50, p_userMdl)} )
        store_dict.append( {'id': 2, 'dollars': 10, 'diamonds': 110, 'caption': "(110% Value)",
                            'form': Reporter.GetPaypalForm(10, 110, p_userMdl)} )
        store_dict.append( {'id': 3, 'dollars': 20, 'diamonds': 230, 'caption': "(115% Value)",
                            'form': Reporter.GetPaypalForm(20, 230, p_userMdl)} )
        store_dict.append( {'id': 4, 'dollars': 50, 'diamonds': 600, 'caption': "(120% Value)",
                            'form': Reporter.GetPaypalForm(50, 600, p_userMdl)} )
        store_dict.append( {'id': 5, 'dollars': 100, 'diamonds': 1300, 'caption': "(130% Value!)",
                            'form': Reporter.GetPaypalForm(100, 1300, p_userMdl)} )
        return store_dict
    
    
    @staticmethod
    def GetPaypalForm(p_dollars, p_diamonds, p_userMdl):
        
        # business: must be seller's email or get paypal error
        # item name: displayed in paypal invoice
        # invoice: must be unique for each transaction
        # return/cancel url: must be csrf_exempt views
        # custom message: string variable that is hidden from buyer
        #               use it to identify user and mini-game that has been paid for ?
        
        import socket
        import ipgetter
        
        if socket.gethostname().startswith('prod'):
            hostIP = "lige-ma.com"
        elif socket.gethostname().startswith('test'): 
            hostIP = socket.gethostname()[0:4] + ".lige-ma.com"
        else:
            hostIP = 'http://0bcfe77c.ngrok.io'     # ngrok for dev
        
        paypal_dict = {
            'business': 'lig3ma@gmail.com', 
            'amount': p_dollars,
            'item_name': 'Diamonds x{0}'.format(p_diamonds),
            'invoice': Reporter.GetUniqueInvoice(p_userMdl),
            'notify_url': hostIP + reverse('paypal-ipn'),       # os.join
            'return_url': hostIP + reverse('central:store'),
            'cancel_return': hostIP + reverse('central:store'),
            'custom': json.dumps({'user': p_userMdl.username, 'diamonds': p_diamonds}),
        }
        
        form = PayPalPaymentsForm(initial=paypal_dict)
        return form
    
    
    @staticmethod
    def GetUniqueInvoice(p_userMdl):
        import hashlib
        rawEnc = (p_userMdl.username + datetime.datetime.utcnow().strftime(CU.FORMAT_DTSTR_SECS)).encode('utf-8')
        hashRaw = hashlib.md5(rawEnc).hexdigest()     # 32 digits
        return hashRaw
    
    
    @staticmethod
    def GetSites():
        siteOne = Site.objects.get_current()
        return siteOne


class Editor(object):
    
    
    @staticmethod
    def PurchaseDiamonds(p_user, p_itemId):
        
        # get data for item purchased
        
        store_data = Reporter.MoneyStoreData()
        item_dt = {}
        
        for item in store_data:
            if str(item['id']) == p_itemId:
                item_dt = item
        
        profile_m = MM.Profile_Reporter.GetProfile_Mdl(p_user)
        
        prog_lg.debug(item_dt)
        
        # process payment
        
        cost = item_dt['dollars']
        profile_m.LifetimeMoney += cost
        
        # award diamonds
        
        results = {
            'diamond_old': profile_m.Diamonds,
            'diamond_new': profile_m.Diamonds + item_dt['diamonds'],
        }
        
        profile_m.Diamonds += item_dt['diamonds']
        profile_m.LifetimeDiamonds += item_dt['diamonds']
        profile_m.save()
        
        hret = CU.HttpReturn()
        hret.results = results
        hret.status = 200
        return hret
    
    
    @staticmethod
    def ExchangeTokens(p_user, p_diamonds):
        hret = CU.HttpReturn()
        
        profile_m = MM.Profile_Reporter.GetProfile_Mdl(p_user)
        roster_m = PU.Univ_Roster.objects.get(UserFK=p_user)
        
        if p_diamonds > profile_m.Diamonds:
            hret.results = "Insufficient diamonds for exchange."
            hret.status = 401
            return hret
        
        numTokens = p_diamonds * 35 / 11
        
        results = {
            'diamond_old': profile_m.Diamonds,
            'diamond_new': profile_m.Diamonds - p_diamonds,
            'token_old': roster_m.Token_Total,
            'token_new': roster_m.Token_Total + numTokens,            
        }
        
        profile_m.Diamonds -= p_diamonds
        profile_m.save()
        roster_m.Token_Total += numTokens
        roster_m.save()
        
        hret.results = results
        hret.status = 200
        return hret
    
    
    @staticmethod
    def InitializeSites():
        siteOne = Site.objects.get_current()
        siteOne.domain = "www.lige-ma.com"
        siteOne.name = "Lige Ma LLC"
        siteOne.save()



"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
OTHERS
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


# handler for paypal payment received signal
from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.signals import valid_ipn_received

def PaypalHandler(sender, **kwargs):
    ipn_obj = sender
    if ipn_obj.payment_status == ST_PP_COMPLETED:
        
        # seller id may be hacked
        if ipn_obj.receiver_email != 'lig3ma@gmail.com':
            excp_lg.error("paypal seller tampered with")
            excp_lg.error(ipn_obj.__dict__)
        
        # the seller is correct
        else:
            custom_dict = json.loads(ipn_obj.custom)
            user = custom_dict['user']
            diamonds = custom_dict['diamonds']
            money = ipn_obj.mc_gross #- ipn_obj.mc_fee
            
            user_m = AM.User.objects.get(username=user)
            profile_m = MM.Profile_Reporter.GetProfile_Mdl(user_m)
            profile_m.Diamonds += diamonds
            profile_m.LifetimeDiamonds += diamonds
            profile_m.save()
        
    else:
        excp_lg.warning("not STPP status")
        excp_lg.warning(ipn_obj.__dict__)

valid_ipn_received.connect(PaypalHandler)


# add the logged user's data to all template contexts
# requires an entry in settings.template_context_processors
def context_profile(request):
    
    if not request.user.is_anonymous():
        season = FM.TimeMachine.GetTodaysBracket()['season']
        profile_dt = MM.Profile_Reporter.GetUserData(request.user)
        puRoster_dx = PU.Reporter.GetUserRoster(request.user, season)
        unreadCnt = MM.IPostman.GetUnreadCount(request)
    else:
        profile_dt = None
        puRoster_dx = None
        unreadCnt = 0
    
    # the template context now has these variables by default
    
    xcontext = {
        'profile': profile_dt,
        'puRoster': puRoster_dx,
        'unreadCnt': unreadCnt,
    }
    return xcontext


def context_background(request):
    path = request.path
    
    if path == "/":                                         fileName = "bkgd_landing.png"
    elif path == "/prediction/universal/predictions/":      fileName = "bkgd_pu_preds.png"
    elif path == "/prediction/universal/upgrades/":         fileName = "bkgd_pu_upgrades.png"
    elif path == "/prediction/universal/standings/":        fileName = "bkgd_pu_standings.png"
    elif path.startswith("/research/"):                     fileName = "bkgd_football.png"
    elif path == "/central/store/":                         fileName = "bkgd_store.png"
    elif path.startswith("/members/"):                      fileName = "bkgd_account.png"
    else:                                                   fileName = "bkgd_default.png"
    
    bkgdPath = "/static/graphics/{}".format(fileName)    
    xcontext = {
        'bkgdPath': bkgdPath,
    }
    return xcontext


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
END OF FILE
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""