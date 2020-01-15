"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
FOOTBALL/MODELS/ETL_LIVESCORES.py
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import requests
import lxml
import datetime 
import time
import pytz
import re

from django.db.models import Count, F, Q, Value
from django.db.models.functions import Concat

import common.utility as CU
import football.models.tables as FT

import logging
prog_lg = logging.getLogger('progress')
excp_lg = logging.getLogger('exception')


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
LIVE SCORES
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


class Editor(object):
    
    
    # extract from web and transform some of the data
    @staticmethod
    def TransformGameEvents(p_id, p_url):
        page_flat = Editor.GetFixtureFlatPage(p_url)
        trans_dx = Editor.GetLiveData(page_flat, p_id)
        return trans_dx
    
    
    # helper for TransformGameEvents
    @staticmethod
    def GetFixtureFlatPage(p_url):
        
        page = requests.get(p_url)
        page_flat = page.text
        
        nStart = page_flat.find('<head>')
        nStart += len('<head>')
        nStop = page_flat.find('</head>')
        page_flat = page_flat[0 : nStart] + page_flat[nStop : len(page_flat)]
        
        nStart = page_flat.find('<script>')
        nStart += len('<script>')
        nStop = page_flat.find('</script>')
        page_flat = page_flat[0 : nStart] + page_flat[nStop : len(page_flat)]
        
        nStart = page_flat.find('<iframe')
        nStart += len('<iframe')
        nStop = page_flat.find('</iframe>')
        page_flat = page_flat[0 : nStart] + "> " + page_flat[nStop : len(page_flat)]
                
        #excp_lg.warning(page_flat)
        
        return page_flat
    
    
    # helper for TransformGameEvents
    @staticmethod
    def GetLiveData(p_htmlflat, p_id):
        
        # prepare to get live score data
        
        html = lxml.etree.HTML(p_htmlflat)
        body = html.find('.//body')
        gameTable_elem = body.getchildren()
        
        trans_dx = {
            'id': p_id,
            'home': "",
            'away': "",
            'events': [],
        }
        
        # get live data as list of events
        
        for row_el in gameTable_elem:
            
            try:
                classes = row_el.items()[0][1]      # assumes there's only 1 item, 'class'
            except Exception:
                continue
            
            cells_elem = row_el.getchildren()
            
            if "row-tall" in classes:
                homeLive = cells_elem[1].xpath('string()').strip()
                awayLive = cells_elem[3].xpath('string()').strip()
                
                homeIPLS = Editor.TransformClub(homeLive)
                awayIPLS = Editor.TransformClub(awayLive)
                
                trans_dx['home'] = homeIPLS
                trans_dx['away'] = awayIPLS
            
            elif "row-gray" in classes:                
                evtime = cells_elem[0].xpath('string()').strip() 
                left_tx = cells_elem[1].xpath('string()').strip()
                right_tx = ""
                if len(cells_elem) > 3:
                    right_tx = cells_elem[3].xpath('string()').strip()
                
                if not evtime:
                    continue
                
                if left_tx:
                    isGoal = cells_elem[1].xpath('.//span[contains(@class,"goal")]')
                    isRedcard = cells_elem[1].xpath('.//span[contains(@class,"redcard")]')
                    isRedcard = isRedcard or cells_elem[1].xpath('.//span[contains(@class,"redyellowcard")]')
                    eventType = "Goal" if isGoal else ""
                    eventType += "Card: Red" if isRedcard else ""
                    
                    live_player = left_tx.replace("(pen.)", "").replace("(o.g.)", "").strip()
                    
                    ipls_player = FT.Player.objects.annotate(FirstLast=Concat('FirstName', Value(' '), 'LastName')
                                                    ).values('FirstLast'
                                                    ).filter(FirstLast=live_player)
                    if ipls_player:
                        ipls_player = ipls_player[0]['FirstLast']
                    else:
                        ipls_player = None
                    
                    newEvent = {
                        'club': homeIPLS,
                        'live_player': live_player,
                        'ipls_player': ipls_player,
                        'time': int(evtime[:-1]),
                        'event': eventType
                    }
                    trans_dx['events'].append(newEvent)
                
                if right_tx or cells_elem[3].xpath('.//span[contains(@class,"goal")]'):
                    isGoal = cells_elem[3].xpath('.//span[contains(@class,"goal")]')
                    isRedcard = cells_elem[3].xpath('.//span[contains(@class,"redcard")]')
                    isRedcard = isRedcard or cells_elem[3].xpath('.//span[contains(@class,"redyellowcard")]')
                    eventType = "Goal" if isGoal else ""
                    eventType += "Card: Red" if isRedcard else ""
                    
                    live_player = right_tx.replace("(pen.)", "").replace("(o.g.)", "").strip()
                    
                    ipls_player = FT.Player.objects.annotate(FirstLast=Concat('FirstName', Value(' '), 'LastName')
                                                    ).values('FirstLast'
                                                    ).filter(FirstLast=live_player)
                    if ipls_player:
                        ipls_player = ipls_player[0]['FirstLast']
                    else:
                        ipls_player = None
                    
                    if isGoal and not live_player:
                        live_player = "not listed"
                    
                    newEvent = {
                        'club': awayIPLS,
                        'live_player': live_player,
                        'ipls_player': ipls_player,
                        'time': int(evtime[:-1]),
                        'event': eventType
                    }
                    trans_dx['events'].append(newEvent)
        
        # add ligema required events
        
        trans_dx['events'].append({'club': None, 'live_player': None, 'time': 0,  'event': "Game Half1 Start"})
        trans_dx['events'].append({'club': None, 'live_player': None, 'time': 46, 'event': "Game Half1 Stop"})
        trans_dx['events'].append({'club': None, 'live_player': None, 'time': 47, 'event': "Game Half2 Start"})
        trans_dx['events'].append({'club': None, 'live_player': None, 'time': 99, 'event': "Game Half2 Stop"})
        trans_dx['events'].append({'club': None, 'live_player': None, 'time': 100, 'event': "Game End"})   # this must be the last event
        
        return trans_dx
    
    
    # helper for TransformGameEvents
    @staticmethod
    def TransformClub(p_club):
        if p_club == "": return "Damash GLN"
        if p_club == "": return "Esteghlal AHV"
        if p_club == "Esteghlal Khuzestan": return "Esteghlal KHU"
        if p_club == "Esteghlal": return "Esteghlal TEH"
        if p_club == "": return "Fajr Sepasi SHZ"
        if p_club == "FC Mashhad": return "SiahJamegan MSH"
        if p_club == "Foolad Khuzestan": return "Foolad KHU"
        if p_club == "Gostaresh Foolad FC": return "Gostaresh TBZ"
        if p_club == "": return "Malavan ANZ"
        if p_club == "Machine Sazi FC": return "Mashin Sazi TBZ"
        if p_club == "": return "Mes KRM"
        if p_club == "": return "Naft MJS"
        if p_club == "Naft Tehran": return "Naft TEH"
        if p_club == "Padideh FC": return "Padideh MSH"
        if p_club == "Pars Jonoubi Jam Bushehr": return "Pars Jonobi JAM"
        if p_club == "Paykan": return "Paykan TEH"
        if p_club == "Persepolis": return "Perspolis TEH"
        if p_club == "": return "Rahahan RAY"
        if p_club == "": return "Rahahan TEH"
        if p_club == "Saba Qom": return "Saba QOM"
        if p_club == "Saipa": return "Saipa ALB"
        if p_club == "Sanat Naft Abadan": return "Sanat Naft ABD"
        if p_club == "Sepahan": return "Sepahan ESF"
        if p_club == "Sepidrood Rasht": return "SepidRood RST"
        if p_club == "": return "SiahJamegan MSH"
        if p_club == "Tractor Sazi Tabriz": return "Teraktor TBZ"
        if p_club == "Zob Ahan": return "Zobahan ESF"
        return "No iplstats club matched."
    
    
    # load game data into database
    @staticmethod
    def LoadGameData(game_dx):
        game_m = FT.Game.objects.get(id=game_dx['id'])
        homeClub_m = FT.Club.objects.get(Club=game_dx['home'])
        awayClub_m = FT.Club.objects.get(Club=game_dx['away'])
        
        for eventRaw in game_dx['events']:
            event_m = FT.Event.objects.get(Event=eventRaw['event'])
            evClub_m = FT.Club.objects.get(Club=eventRaw['club'])   if eventRaw['club']   else None
            player_m = FT.Player.objects.annotate(FirstLast=Concat('FirstName', Value(' '), 'LastName')
                                        ).get(FirstLast=eventRaw['ipls_player'])   if eventRaw['live_player']   else None
            ev_time = (datetime.datetime(100,1,1,0,0,0) + datetime.timedelta(minutes=int(eventRaw['time']))).time()
            
            try:
                newEvent, created = FT.GameEvent.objects.get_or_create(
                    GameFK = game_m,
                    EventFK = event_m,
                    EventTime = ev_time,
                    EventClubFK = evClub_m,
                    PlayerFK = player_m,
                    Position = None,
                )
            except Exception as ex:
                # allow any errors to stop the processing so game-end event is not inserted
                message = "Type: {0}\nArguments:{1!r}".format(type(ex).__name__, ex.args)
                excp_lg.error(message)
                raise ex
        
        return "Game loaded succesfully."



"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
END OF FILE
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""    