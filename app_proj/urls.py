"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
PROJECT/URLS.py
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

from django.conf.urls import include, url
from django.contrib import admin
import allauth.account.views as AV

import common.views as BV 
import football.views as FV 
import members.views as MV 
import prediction.views as PV 
import central.views as CV


football_url = [
    url(r'^game_ref/$', FV.fb_game, name='fb_game'),
    url(r'^season_ref/$', FV.fb_season, name='fb_season'),
    url(r'^club_ref/$', FV.fb_club, name='fb_club'),
    url(r'^player_ref/$', FV.fb_player, name='fb_player'),
    url(r'^research_jx/([a-zA-Z0-9_]+)/$', FV.research_jx, name='research_jx'),
    
    url(r'^etl_iplstats/$', FV.etl_iplstats, name='etl_iplstats'),
    url(r'^etl_iplstats_jx/([a-zA-Z0-9_]+)/$', FV.etl_iplstats_jx, name='etl_iplstats_jx'),
    
    url(r'^etl_livescores/$', FV.etl_livescores, name='etl_livescores'),
    url(r'^etl_livescores_jx/([a-zA-Z0-9_]+)/$', FV.etl_livescores_jx, name='etl_livescores_jx'),
    
    url(r'^dataManager_jx/([a-zA-Z0-9_]+)/$', FV.dataManager_jx, name='dataManager_jx'),
]


members_url = [    
    url(r"^accounts/signup/$", AV.signup, name="account_signup"),        # must preserve allauth name field for its internal calls
    url(r"^accounts/login/$", AV.login, name="account_login"),
    url(r"^accounts/logout/$", AV.logout, name="account_logout"),
    
    url(r"^accounts/email/$", MV.email, name="account_email"),
    url(r"^accounts/confirm-email/(?P<key>[-:\w]+)/$", AV.confirm_email, name="account_confirm_email"),
    url(r"^accounts/confirm-email/$", AV.email_verification_sent, name="account_email_verification_sent"),    # used when email still requires confirmation
    url(r"^accounts/password/change/$", AV.password_change, name="account_change_password"),
    url(r"^accounts/password/reset/$", MV.password_reset, name="account_reset_password"),
    url(r"^accounts/password/reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$", MV.password_reset_from_key, name="account_reset_password_from_key"),
    url(r"^accounts/inactive/$", AV.account_inactive, name="account_inactive"),        
    
    url(r'^auth_dialog/', MV.dialog),
    url(r'^messages/', MV.messages, name='messages'),
    url(r'^members_admin/', MV.members_admin, name='members_admin'),
    url(r'^contacts/', MV.contacts, name='contacts'),
    url(r'^profile/', MV.profile, name='profile'),
    
    url(r'^db_edit/([a-zA-Z0-9_]+)/$', MV.db_edit),
    url(r'^db_report/([a-zA-Z0-9_]+)/$', MV.db_report),
]


central_url = [
    url(r'^store/$', CV.store, name='store'),
    url(r'^company/$', CV.company, name='company'),
    url(r'^data_master/$', CV.master, name='master'),
    url(r'^view_profile/([a-zA-Z0-9_]+)', CV.view_profile, name='view_profile'),
    url(r'^central_jx/([a-zA-Z0-9_]+)/$', CV.central_jx, name='central_jx'),
    
    url(r'^admin_messages/', CV.admin_messages, name='admin_messages'),
    url(r'^adminMsg_jx/([a-zA-Z0-9_]+)/$', CV.adminMsg_jx, name='adminMsg_jx'),
    
    url(r'^pu_rewards/', CV.pu_rewards, name='pu_rewards'),
    url(r'^pu_rewards_jx/([a-zA-Z0-9_]+)/$', CV.pu_rewards_jx, name='pu_rewards_jx'),
    url(r'^pu_message_test/', CV.pu_message_test, name='pu_message_test'),
    
    url(r'^bot_users/', CV.botUsers, name='botUsers'),
    url(r'^botUsers_jx/([a-zA-Z0-9_]+)/$', CV.botUsers_jx, name='botUsers_jx'),
]


univpred_url = [
    url(r'^universal/upgrades/$', PV.univ_headq, name='univ_headq'),
    url(r'^universal/predictions/$', PV.univ_preds, name='univ_preds'),
    url(r'^universal/standings/$', PV.univ_ranks, name='univ_ranks'),
    url(r'^universal/the_rules/$', PV.univ_rules, name='univ_rules'),
    url(r'^universal_jx/([a-zA-Z0-9_]+)/$', PV.universal_jx, name="universal_jx"),
]


urlpatterns = [
    url(r'^$', CV.landing, name='landing_page'),   
    url(r'^members/', include(members_url)),     # do not use a namespace, breaks allauth reverse urls 
    url(r'^research/', include(football_url, namespace='football')),
    url(r'^prediction/', include(univpred_url, namespace='prediction')),
    url(r'^messages/', include('postman.urls', namespace='postman', app_name='postman')),
    url(r'^central/', include(central_url, namespace='central', app_name='central')),       # appname?
    
    url(r'^admin/', include(admin.site.urls)),
    url(r'^paypal/', include('paypal.standard.ipn.urls')),
    
    url(r'^', BV.not_found, name='not_found'),
]





