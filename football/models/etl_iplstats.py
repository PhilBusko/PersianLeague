"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
FOOTBALL/MODELS/ETL_IPLSTATS.py
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import csv
import requests
from lxml import etree
import datetime 
import time
import pytz
import re
import random

from django.db.models import Q, Value
from django.db.models.functions import Concat

import common.utility as CU
import football.models.tables as FT

import logging
prog_lg = logging.getLogger('progress')
excp_lg = logging.getLogger('exception')


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
PLAYER SQUAD
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

class IPLS_Squad(object):
    
    
    @staticmethod
    def RunPlayerSquadData(p_season):
                 
        # first: load all player data
        IPLS_Squad.ETLPlayersData(p_season)
        
        # second: load squad data for each club
        IPLS_Squad.RunSquadsData(p_season)
        
        hret = CU.HttpReturn()
        hret.results = "Load Player Data Complete"
        hret.status = 201
        return hret
    
    
    @staticmethod
    def ETLPlayersData(p_season):
        
        if p_season == 'IPL2013': 
            url_players = 'http://iplstats.com/website13-14/allplayers.htm'
        elif p_season == 'IPL2014': 
            url_players = 'http://iplstats.com/website14-15/allplayers.htm'
        elif p_season == 'IPL2015':
            url_players = 'http://iplstats.com/website15-16/allplayers.htm'
        elif p_season == 'IPL2016':
            url_players = 'http://iplstats.com/website16-17/allplayers.htm'
        else:
            url_players = 'http://iplstats.com/allplayers.htm'
            #raise ValueError("{0} has no config".format(p_season))
        
        try:
            page = requests.get(url_players)
        except Exception as ex:
            template = "HTML Request Error. Type: {0}. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            excp_lg.error(message)
            time.sleep(30)              # if network lost, wait until it comes back
            return IPLS_Squad.ETLPlayersData(p_season)
        
        
        html = etree.HTML(page.text)    
        table = html.find('.//body/b/table')   # get first table element        
        
        for childRow in table:
            
            try:
                cells = childRow.findall('.//td')
                lastname = cells[1].text.strip()
                firstname = cells[2].text.strip()
                nation = cells[3].text.strip()
                club = cells[4].text.strip()
            except Exception as ex:
                msg = "Create player error. \n"
                msg += "Type: {0} \n".format(type(ex).__name__)
                msg += "Arguments:{0!r} \n".format(ex.args)
                excp_lg.error(msg)
                continue
            
            # skipping header row ?
            if not firstname:
                continue
            
            # S2014 correction
            if p_season == "IPL2014":
                if firstname == "Mohsen" and lastname == "Karimi" and nation == "Brazil":
                    nation = "Iran"
                lastname = re.sub("Diogo de Oliveira", "de Oliveira", lastname)
                lastname = re.sub("karimi", "Karimi", lastname)
                        
            player_m, created = FT.Player.objects.get_or_create(
                FirstName = firstname, LastName = lastname,
                Nationality = nation, DateOfBirth = datetime.date.min, )
            
            if not created:
                msg = "Player not created: {0} {1}".format(firstname, lastname)
                excp_lg.warning(msg)
        
        return
    
    
    @staticmethod
    def RunSquadsData(p_season):
                
        config_file = "football/static/data/IPLStats/" + p_season + " Squad.csv"
        
        with open(config_file) as fhandle:
            reader = csv.reader(fhandle)
            next(reader)  # skip header row
            for row in reader:
                season = row[0]
                club = row[1]
                url = row[2]
                IPLS_Squad.ETLSquadData(season, club, url)
        
        return 0
    
    
    @staticmethod
    def ETLSquadData(p_season, p_club, p_url):
                
        season_m = FT.Season.objects.get(Season = p_season)
        
        try:
            club_m = FT.Club.objects.get(Club=p_club)
        except Exception as ex:
            msg = "Club not found: {0}".format(p_club)
            excp_lg.error(msg)
            return 
        
        # skip processing this club so worker doesn't time out
        
        plic_mdl = FT.PlayerInClub.objects.filter(SeasonFK__Season=p_season, ClubFK__Club=p_club)
        
        if plic_mdl:
            return
        
        # cortesy don't overwhelm the source server with requests
        time.sleep(5)
        
        try:
            page = requests.get(p_url)
        except Exception as ex:
            template = "HTML Request Error. Type: {0}. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            excp_lg.error(message)
            time.sleep(30)              # if network lost, wait until it comes back
            return IPLS_Squad.ETLSquadData(p_season, p_club, p_url)
        
        html = etree.HTML(page.text)    
        table = html.find('.//body/b/table')   # get first table element        
        
        for childRow in table:
            
            try:
                cells = childRow.findall('.//td')
                shirtno = cells[1].text.strip()
                player = cells[2].text.strip().replace('  ', ' ')
                position = cells[3].text.strip()
                nation = cells[8].text.strip()
            except Exception as ex:
                msg = "Squad page error. \n"
                msg += "Type: {0} \n".format(type(ex).__name__)
                msg += "Arguments: {0!r} \n".format(ex.args)
                msg += "Club: {0} \n".format(p_club)
                excp_lg.error(msg)
                continue   
            
            # header row doesn't have .text member, text is inside a <b>
            if not player:
                continue
            
            if p_season == "IPL2014":
                player = re.sub("Diogo de Oliveira Diogo", "de Oliveira Diogo", player)
                player = re.sub("karimi", "Karimi", player)
            
            try:
                player_mdls = FT.Player.objects.annotate(LastFirst=Concat('LastName', Value(' '), 'FirstName'))
                player_m = player_mdls.get(LastFirst=player)
                
                squad_m, created = FT.PlayerInClub.objects.get_or_create( 
                    SeasonFK = season_m, ClubFK = club_m, 
                    PlayerFK = player_m, PositionDef = position, ShirtNo = shirtno, )
                
                if not created:
                    msg = "Player not added to squad. \n"
                    msg += p_club + "\n"
                    msg += player + "\n"
                    excp_lg.warning(msg)
            
            except Exception as ex:
                msg = "Squad insert error. \n"
                msg += "Type: {0} \n".format(type(ex).__name__)
                msg += "Arguments: {0!r} \n".format(ex.args)
                msg += "Club: {0} \n".format(p_club)
                msg += "Player: {0} \n".format(player)
                excp_lg.error(msg)
        
        return



"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
GAME EVENTS
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

class IPLS_GameEvents(object):
    
    
    # manager function for loading game data for a whole season
    @staticmethod
    def RunGameData(p_season, p_rndStart=1):
        
        #p_season = "test1"
        config_file = "football/static/data/IPLStats/" + p_season + " Game.csv"
        currRound = 0
        
        with open(config_file) as fhandle:
            reader = csv.reader(fhandle)
            next(reader)  # skip header row
            for row in reader:
                
                try:
                    season = row[0]
                    game_round = row[1]
                    url = row[2]
                except Exception as ex:
                    template = "Config Error. Type: {0}. Arguments:\n{1!r}"
                    message = template.format(type(ex).__name__, ex.args)
                    message += "\n" + "File: " + config_file
                    excp_lg.error(message)
                    continue
                
                if int(game_round) >= int(p_rndStart):
                    page_flat = IPLS_GameEvents.GetGameFlatPage(url)
                    game_data = IPLS_GameEvents.GetGameData(page_flat)
                    IPLS_GameEvents.InsertGameData(season, game_round, game_data)
                
                elif int(game_round) > currRound:
                    msg = "Config Round Skipped: " + str(game_round)
                    prog_lg.info(msg)
                    currRound += 1
        
        hret = CU.HttpReturn()
        hret.results = "Load Game Data Complete"
        hret.status = 201
        return hret
    
    
    # helper for RunGameData()
    @staticmethod
    def GetGameFlatPage(p_url):
        
        # cortesy don't overwhelm the source server with requests
        time.sleep(5)
        
        try:
            page = requests.get(p_url)
        except Exception as ex:
            template = "HTML Request Error. Type: {0}. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            excp_lg.error(message)
            time.sleep(30)          # if network lost, wait until it comes back
            return IPLS_GameEvents.GetGameFlatPage(p_url)
        
        page_flat = page.text
        
        page_flat = re.sub("(?i)(<b>|</b>)", "", page_flat)
        
        font_rx = r'(?i)<font[a-zA-z0-9"=\s]+>\n*'
        page_flat = re.sub(font_rx, r' @FONT ', page_flat) 
        page_flat = re.sub("(?i)(</font>)", "", page_flat)
        
        # S2014 R13, S2015 R15 has folders in image path
        img_rx = r'(?i)<img[a-zA-z0-9"=\s]+src="([a-zA-Z0-9\.\/]+/)*([a-zA-Z0-9\.]+)"\s+[a-zA-z0-9"=\s]+>'
        page_flat = re.sub(img_rx, r' @IMG \2 ', page_flat) 
        
        page_flat = page_flat.replace("In <--", "@IN")
        page_flat = page_flat.replace("Out -->", "@OUT")
        
        # correct for double-yellow card
        dyellow_rx = r'@IMG yellowcard.gif\s+@IMG redcard.gif' 
        page_flat = re.sub(dyellow_rx, r'@IMG redcard.gif', page_flat)
        
        dyellow_rx = r'@IMG yellowcard.gif\s+@IMG yellowcard.gif' 
        page_flat = re.sub(dyellow_rx, r'@IMG redcard.gif', page_flat)
        
        # S2016 data corruption
        if p_url == "http://www.iplstats.com/Week20/ZOB_SAB_20.htm":
            page_flat = page_flat.replace('@IMG goal.gif Saba QOM', 'Saba QOM')
            page_flat = page_flat.replace('Seyed Mehdi Hossaini (84)', '@IMG goal.gif Seyed Mehdi Hossaini (84)')
        
        # S2016 R27 one game is duplicated, so one is missing
        if p_url == "http://www.iplstats.com/Week27/PAD_TST_27.htm":
            page_flat = page_flat.replace('Paykan TEH', 'Padideh MSH')
            page_flat = page_flat.replace('Zobahan ESF', 'Teraktor TBZ')
        
        # S2016 R20 has fonts mixed in with images
        page_flat = re.sub(r'@FONT\s+@IMG', '@IMG', page_flat)
        
        # correct for overtime events
        page_flat = page_flat.replace("(90+1)", "(91)")
        page_flat = page_flat.replace("(90+2)", "(92)")
        page_flat = page_flat.replace("(90+3)", "(93)")
        page_flat = page_flat.replace("(90+4)", "(94)")
        page_flat = page_flat.replace("(90+5)", "(95)")
        page_flat = page_flat.replace("(90+6)", "(96)")
        page_flat = page_flat.replace("(90+7)", "(97)")
        page_flat = page_flat.replace("(90+8)", "(98)")
        page_flat = page_flat.replace("(90+9)", "(99)")
        page_flat = page_flat.replace("(90+10)", "(100)")
        page_flat = page_flat.replace("(90+11)", "(101)")
        page_flat = page_flat.replace("(90+12)", "(102)")
        page_flat = page_flat.replace("(90+13)", "(103)")
        page_flat = page_flat.replace("(90+14)", "(104)")
        page_flat = page_flat.replace("(90+15)", "(105)")
        page_flat = page_flat.replace("(90+16)", "(106)")
        page_flat = page_flat.replace("(90+17)", "(107)")
        page_flat = page_flat.replace("(90+18)", "(108)")
        page_flat = page_flat.replace("(90+19)", "(109)")
        page_flat = page_flat.replace("(90+20)", "(110)")
        page_flat = page_flat.replace("(90+21)", "(111)")
        page_flat = page_flat.replace("(90+22)", "(112)")
        page_flat = page_flat.replace("(90+23)", "(113)")
        page_flat = page_flat.replace("(90+24)", "(114)")
        page_flat = page_flat.replace("(90+25)", "(115)")
        page_flat = page_flat.replace("(90+26)", "(116)")
        page_flat = page_flat.replace("(90+27)", "(117)")
        page_flat = page_flat.replace("(90+28)", "(118)")
        page_flat = page_flat.replace("(90+29)", "(119)")
        page_flat = page_flat.replace("(90+30)", "(120)")
        
        return page_flat
    
    
    # helper for RunGameData()
    @staticmethod
    def GetGameData(p_htmlflat):
                
        html = etree.HTML(p_htmlflat)    
        table = html.find('.//body/table')   # get first table element        
        
        rx_date = re.compile(r'([0-9]+/[0-9]+/[0-9]+)')
        rx_club = re.compile(r'@FONT\s+([a-zA-Z\s]{2,})')
        rx_img_left = re.compile(r'([a-zA-Z\s-]+)\s+\(*([0-9]*)\)*\s*([a-z\.]*)\s*@IMG\s+([a-zA-Z0-9\.\/]+)')
        rx_img_right = re.compile(r'@IMG\s+([a-zA-Z0-9\.\/]+)\s+([a-zA-Z\s-]+)\s*\(*([0-9]*)\)*\s*([a-z\.]*)')
        rx_lineup = re.compile(r'^([a-zA-Z][a-zA-Z\s]+[a-zA-Z])$')
        rx_subin = re.compile(r'@IN\s+([a-zA-Z][a-zA-Z\s]+)\s+\(*([0-9]*)\)*')
        rx_subout = re.compile(r'@OUT\s+([a-zA-Z][a-zA-Z\s]+)\s+\(*([0-9]*)\)*')
        
        game_date = "";
        home_club = "";
        away_club = "";
        home_events = [];
        away_events = [];
        game_events = [];
        
        for childRow in table:      # each row is a tr
            
            try:
                cells = childRow.findall('.//td')
                blank = cells[0]
                left = cells[1].xpath('string()').strip() 
                middle = cells[2]
                right = cells[3].xpath('string()').strip() 
                
                if rx_date.search(left):
                    game_date = rx_date.search(left).group(1)
                
                elif rx_club.search(left):
                    home_club = rx_club.search(left).group(1)
                
                elif rx_img_left.search(left):
                    g = rx_img_left.search(left).groups(0)
                    image = g[3]
                    
                    if "goal.gif" in image:
                        event = "Goal"
                        if g[2] == "pen.": event = "Penalty Scored"
                        if g[2] == "pen": event = "Penalty Scored"
                        if g[2] == "o.g.": event = "Goal, Own"
                        home_events.append({'player': g[0], 'time': g[1], 'event': event})
                    elif "yellowcard.gif" in image: 
                        home_events.append({'player': g[0], 'time': 1, 'event': "Card: Yellow"})
                    elif "redcard.gif" in image: 
                        home_events.append({'player': g[0], 'time': 1, 'event': "Card: Red"})
                
                elif rx_lineup.search(left):
                    g = rx_lineup.search(left).groups(0)
                    home_events.append({'player': g[0], 'time': 0, 'event': "Player in Line-up"})
                
                elif rx_subin.search(left):
                    g = rx_subin.search(left).groups(0)
                    home_events.append({'player': g[0], 'time': g[1], 'event': "Player Sub-in"})
                
                elif rx_subout.search(left):
                    g = rx_subout.search(left).groups(0)
                    home_events.append({'player': g[0], 'time': g[1], 'event': "Player Sub-out"}) 
                    home_events.append({'player': g[0], 'time': 0, 'event': "Player in Line-up"})
                
                
                if rx_club.search(right):
                    away_club = rx_club.search(right).group(1)
                
                elif rx_img_right.search(right):
                    g = rx_img_right.search(right).groups(0)
                    image = g[0]
                    if "goal.gif" in image: 
                        event = "Goal"
                        if g[3] == "pen.": event = "Penalty Scored"
                        if g[3] == "o.g.": event = "Goal, Own"
                        away_events.append({'player': g[1], 'time': g[2], 'event': event})
                    elif "yellowcard.gif" in image: 
                        away_events.append({'player': g[1], 'time': 1, 'event': "Card: Yellow"})
                    elif "redcard.gif" in image: 
                        away_events.append({'player': g[1], 'time': 1, 'event': "Card: Red"})
                
                elif rx_lineup.search(right):
                    g = rx_lineup.search(right).groups(0)
                    away_events.append({'player': g[0], 'time': 0, 'event': "Player in Line-up"})
                
                elif rx_subin.search(right):
                    g = rx_subin.search(right).groups(0)
                    away_events.append({'player': g[0], 'time': g[1], 'event': "Player Sub-in"})
                
                elif rx_subout.search(right):
                    g = rx_subout.search(right).groups(0)
                    away_events.append({'player': g[0], 'time': g[1], 'event': "Player Sub-out"}) 
                    away_events.append({'player': g[0], 'time': 0, 'event': "Player in Line-up"})
                
                
            except Exception as ex:
                template = "Parse Error - Game. Type: {0}. Arguments:\n{1!r}"
                message = template.format(type(ex).__name__, ex.args)
                excp_lg.error(message) 
                continue   
        #end loop over tr
        
        # correct for missing game in 2016 R27, clubs are switched elsewhere prior to this
        if game_date == "4/15/2017" and home_club =="Padideh MSH":
            prog_lg.debug("found missing game")
            game_date = "4/14/2017"
            home_events = []
            away_events = [ {'player': "Hadi Mohamadi", 'time': "9", 'event': "Goal"} ]
            
        
        # add admin events
        
        game_events.append({'player': None, 'time': 0,  'event': "Game Half1 Start"})
        game_events.append({'player': None, 'time': 46, 'event': "Game Half1 Stop"})
        game_events.append({'player': None, 'time': 47, 'event': "Game Half2 Start"})
        game_events.append({'player': None, 'time': 99, 'event': "Game Half2 Stop"})
        game_events.append({'player': None, 'time': 100, 'event': "Game End"})          # this must be the last event
                
        game_data = {
            'play_date': game_date,
            'home_club': home_club,
            'away_club': away_club,
            'home_events': home_events,
            'away_events': away_events,
            'game_events': game_events, }
        return game_data
    
    
    # helper for RunGameData
    @staticmethod
    def InsertGameData(p_season, p_round, p_gamedata):
        
        season_mdl = FT.Season.objects.get(Season = p_season)
        homeclub_mdl = FT.Club.objects.get(Club = p_gamedata['home_club'])
        awayclub_mdl = FT.Club.objects.get(Club = p_gamedata['away_club'])
        
        rx_date = re.compile(r'([0-9]+)/([0-9]+)/([0-9]+)')
        g = rx_date.search(p_gamedata['play_date']).groups(0)
        startHr = random.randint(16,21)
        halfHr = random.randint(0,3) *15
        play_date = datetime.datetime(int(g[2]), int(g[0]), int(g[1]), startHr, halfHr)
        play_date = pytz.timezone("Asia/Tehran").localize(play_date)        
        padrnd = CU.Pad2(p_round)
        
        new_game, created = FT.Game.objects.get_or_create(
            SeasonFK = season_mdl, Round = padrnd,
            ClubHomeFK = homeclub_mdl, ClubAwayFK = awayclub_mdl, PlayDate = play_date  )
        
        IPLS_GameEvents.InsertGameEvents(season_mdl, new_game,
                                  homeclub_mdl, p_gamedata['home_events'])
        IPLS_GameEvents.InsertGameEvents(season_mdl, new_game,
                                  awayclub_mdl, p_gamedata['away_events'])
        IPLS_GameEvents.InsertGameEvents(None, new_game,
                                  None, p_gamedata['game_events'])
    
    
    # helper for InsertGameData, InsertGameEventsOnly
    @staticmethod
    def InsertGameEvents(p_seasonobj, p_game, p_clubobj, p_rawevents):
                
        for curr_event in p_rawevents:
            
            event_obj = FT.Event.objects.get(Event=curr_event['event'])
            
            timeRaw =  curr_event['time']   if curr_event['time']   else 0
            ev_time = (datetime.datetime(100,1,1,0,0,0) + datetime.timedelta(minutes=int(timeRaw))).time()
            
            if curr_event['player']:
                pl_match = curr_event['player']
                pl_match = re.sub('\s\s+', ' ', pl_match).strip()
                
                # IPLstats S2014 corrections
                if p_seasonobj.Season == 'IPL2014':
                    pl_match = re.sub('Naghizedh', 'Naghizadeh', pl_match)
                    pl_match = re.sub('Mydavoodi', 'Maydavoodi', pl_match)
                    pl_match = re.sub('Kamel Jahanteegh', 'Bahman Jahantigh', pl_match)
                    pl_match = re.sub('Sina Ravani', 'Sina Rabbani', pl_match)
                    pl_match = re.sub('Mohamad Mah Nazari', 'Mohamad Mahdi Nazari', pl_match)  
                    pl_match = re.sub(r'Zahra$', 'Abdul-Zahra', pl_match)
                    pl_match = re.sub('Damid Reza Deevsalar', 'Hamid Reza Deevsalar', pl_match)
                    pl_match = re.sub(r'Ebram$', 'Ebdam', pl_match)
                    pl_match = re.sub(r'Ebrahim Sadegh$', 'Ebrahim Sadeghi', pl_match)
                    pl_match = re.sub(r'Hossain Badamak$', 'Hossain Badamaki', pl_match)
                
                # IPLstats S2015 corrections
                if p_seasonobj.Season == 'IPL2015':
                    pl_match = re.sub('Zohaivi', 'Zahivi', pl_match)
                    pl_match = re.sub('Taji', 'Naji', pl_match)
                    pl_match = re.sub('Vasseghi', 'Vassei', pl_match)
                    pl_match = re.sub(' pen', '', pl_match)
                    pl_match = re.sub(r'^Ali Mardani', 'Mardani', pl_match)
                    pl_match = re.sub('Zaydi', 'Zobaydi', pl_match)
                    
                    if p_clubobj.Club == 'Naft TEH':
                        pl_match = re.sub('Ezzati', 'Ezzat Keramat', pl_match)
                
                # IPLstats S2016 corrections
                if p_seasonobj.Season == 'IPL2016':
                    pl_match = re.sub('Mamashli', 'Mamshali', pl_match)
                    pl_match = re.sub('Abdolah Zadeh', 'Abodollah Zadeh', pl_match)
                    pl_match = re.sub('RabiKhah', 'Rabikhah', pl_match)
                    pl_match = re.sub('Lari Zadeh', 'Dari Zadeh', pl_match)
                    pl_match = re.sub('Afrasiabia', 'Afrasiabi', pl_match)
                    pl_match = re.sub('Azarbaad', 'Azarpaad', pl_match)
                    pl_match = re.sub('Ibragimov', 'Ibrahimov', pl_match)
                
                # first look in club squad
                
                squad_mdls = FT.PlayerInClub.objects.annotate( FirstLast=Concat('PlayerFK__FirstName', Value(' '), 'PlayerFK__LastName') )
                
                try:
                    squad = squad_mdls.get(
                        Q(FirstLast = pl_match) | Q(PlayerFK__LastName = pl_match),
                        SeasonFK = p_seasonobj, ClubFK = p_clubobj)
                
                except Exception:
                # second look in any squad 
                # arbitrarily take first alphabetical player
                    squad = squad_mdls.filter(
                        Q(FirstLast = pl_match) | Q(PlayerFK__LastName = pl_match),
                        SeasonFK = p_seasonobj
                        ).order_by('PlayerFK__FirstName').first()
                
                try:
                    player_obj = squad.PlayerFK 
                    ev_pos = squad.PositionDef
                
                except Exception as ex:
                    message = "\nError @ InsertGameEvents(): Match Player\n"
                    message += "Arguments: {0!r}".format(ex.args) + "\n"
                    message += "Round: " + p_game.Round + "\n"
                    message += "Event: " + curr_event['event'] + "\n"
                    message += "Club: " + p_clubobj.Club  + "\n"
                    message += "Player: " + pl_match
                    excp_lg.error(message) 
                    continue   
            
            else:
                player_obj = None
                ev_pos = None
            
            FT.GameEvent.objects.get_or_create(
                GameFK = p_game,
                EventFK = event_obj,
                EventTime = ev_time,
                EventClubFK = p_clubobj,
                PlayerFK = player_obj,
                Position = ev_pos
                )



"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
GAME EVENTS PARTIAL
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

class IPLS_GVPartial(object):
    
    
    # manager function for loading game data for fixtures only
    @staticmethod
    def RunFixturesOnly(p_season, p_rndStart, p_rndEnd):
        
        #p_season = "test1"
        config_file = "football/static/data/IPLStats/" + p_season + " Game.csv"
        
        with open(config_file) as fhandle:
            reader = csv.reader(fhandle)
            next(reader)  # skip header row
            for row in reader:
                
                try:
                    season = row[0]
                    game_round = row[1]
                    url = row[2]
                except Exception as ex:
                    template = "Game Config Error. Type: {0}. Arguments:\n{1!r}"
                    message = template.format(type(ex).__name__, ex.args)
                    message += "\nFile: " + config_file
                    excp_lg.error(message)
                
                # only get rounds within filter
                if CU.Pad2(game_round) >= CU.Pad2(p_rndStart) and CU.Pad2(game_round) <= CU.Pad2(p_rndEnd):
                    page_flat = IPLS_GameEvents.GetGameFlatPage(url)
                    game_data = IPLS_GameEvents.GetGameData(page_flat)
                    IPLS_GVPartial.InsertGameFixture(season, game_round, game_data)
        
        # return results
        
        hret = CU.HttpReturn()
        hret.results = "Load Fixtures Only Succesfull"
        hret.status = 201
        return (hret)
    
    
    # helper for RunFixturesOnly()
    @staticmethod
    def InsertGameFixture(p_season, p_round, p_gamedata):
        
        season_mdl = FT.Season.objects.get(Season = p_season)
        homeclub_mdl = FT.Club.objects.get(Club = p_gamedata['home_club'])
        awayclub_mdl = FT.Club.objects.get(Club = p_gamedata['away_club'])
        padrnd = CU.Pad2(p_round)
        
        rx_date = re.compile(r'([0-9]+)/([0-9]+)/([0-9]+)')
        g = rx_date.search(p_gamedata['play_date']).groups(0)
        startHr = random.randint(16,21)
        halfHr = random.randint(0,3) *15
        play_date = datetime.datetime(int(g[2]), int(g[0]), int(g[1]), startHr, halfHr)
        play_date = pytz.timezone("Asia/Tehran").localize(play_date)
        
        # get_or_create uses every data field, so if game is post-processed, it may error out
        try:
            new_game, created = FT.Game.objects.get_or_create(
                SeasonFK = season_mdl,
                Round = padrnd,
                ClubHomeFK = homeclub_mdl,
                ClubAwayFK = awayclub_mdl,
                PlayDate = play_date
            )
        except Exception as ex:
            message = "Type: {0}\nArguments:{1!r}".format(type(ex).__name__, ex.args)
            excp_lg.error(message)
            raise ex
        
        prog_lg.debug("Import fixture complete: R{0}".format(p_round))
    
    
    # manager function for loading game events for one round only
    @staticmethod
    def RunGameOneRound(p_season, p_round):
        
        #p_season = "test1"
        config_file = "football/static/data/IPLStats/" + p_season + " Game.csv"
        
        if not p_season:
            raise Exception("p_season is null")
        if not p_round:
            raise Exception("p_round is null")
        
        with open(config_file) as fhandle:
            reader = csv.reader(fhandle)
            next(reader)  # skip header row
            for row in reader:
                
                try:
                    season = row[0]
                    game_round = row[1]
                    url = row[2]
                except Exception as ex:
                    template = "Game Config Error. Type: {0}. Arguments:\n{1!r}"
                    message = template.format(type(ex).__name__, ex.args)
                    message += "\nFile: " + config_file
                    excp_lg.error(message)
                
                if CU.Pad2(game_round) == CU.Pad2(p_round):
                    page_flat = IPLS_GameEvents.GetGameFlatPage(url)
                    game_data = IPLS_GameEvents.GetGameData(page_flat)
                    IPLS_GVPartial.InsertGameEventsOnly(season, game_round, game_data)
        
        # return results
        
        hret = CU.HttpReturn()
        hret.results = "RunGameOneRound Succesfull"
        hret.status = 201
        return (hret)
    
    
    # helper for RunGameOneRound
    @staticmethod
    def InsertGameEventsOnly(p_season, p_round, p_gamedata):
        
        season_obj = FT.Season.objects.get(Season = p_season)
        homeclub_obj = FT.Club.objects.get(Club = p_gamedata['home_club'])
        awayclub_obj = FT.Club.objects.get(Club = p_gamedata['away_club'])
        
        rx_date = re.compile(r'([0-9]+)/([0-9]+)/([0-9]+)')
        g = rx_date.search(p_gamedata['play_date']).groups(0)
        padrnd = CU.Pad2(p_round)
        
        try:
            game_mdl = FT.Game.objects.get(
                SeasonFK = season_obj, Round = padrnd, ClubHomeFK = homeclub_obj)
        except FT.Game.DoesNotExist:
            excp_lg.error("Game not found: S]%s R]%s" % (p_season, p_round))
            return None
        
        IPLS_GameEvents.InsertGameEvents(season_obj, game_mdl,
                                  homeclub_obj, p_gamedata['home_events'])
        IPLS_GameEvents.InsertGameEvents(season_obj, game_mdl,
                                  awayclub_obj, p_gamedata['away_events'])
        IPLS_GameEvents.InsertGameEvents(None, game_mdl,
                                  None, p_gamedata['game_events'])
    
    
    @staticmethod
    def RunSingleGame(p_gameUrl):
        
        page_flat = IPLS_GameEvents.GetGameFlatPage(p_gameUrl)
        
        excp_lg.warning(page_flat)
        
        game_data = IPLS_GameEvents.GetGameData(page_flat)
        
        excp_lg.warning(game_data)
        
        #IPLS_GVPartial.InsertGameEventsOnly(season, game_round, game_data)
        
        hret = CU.HttpReturn()
        hret.results = "RunSingleGame complete."
        hret.status = 201
        return hret






"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
END OF FILE
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""    