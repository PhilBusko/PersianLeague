"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
FOOTBALL/MODELS/ETL_PERSIANLEAGUE.py
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import requests
import lxml
import datetime 
import time
import pytz
import re

import common.utility as CU
import football.models.tables as FT

import logging
prog_lg = logging.getLogger('progress')
excp_lg = logging.getLogger('exception')


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
PERSIAN LEAGUE CLASS
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

class Editor(object):
    
    @staticmethod
    def RunImportFixture(p_url):
        
        page_flat = Editor.GetFixtureFlatPage(p_url)
        fixture_dict = Editor.GetFixtureData(page_flat)
        Editor.InsertFixtureData(fixture_dict)
        
        hret = CU.HttpReturn()
        hret.results = "Fixture imported."
        hret.status = 201
        return hret
    
    
    @staticmethod
    def GetFixtureFlatPage(p_url):
        
        page = requests.get(p_url)
        page_flat = page.text
        
        nStart = page_flat.find('<head>')
        nStart += len('<head>')
        nStop = page_flat.find('</head>')
        page_flat = page_flat[0 : nStart] + page_flat[nStop : len(page_flat)]
        
        page_flat = re.sub("(?i)(<b>|</b>)", "", page_flat)
        page_flat = re.sub("(?i)(\n|\t)", "", page_flat)
        # page_flat = re.sub("(?i)(<br)", "", page_flat)
        # page_flat = re.sub("(?i)(/>)", "", page_flat)
        
        #excp_lg.warning(page_flat)
        
        return page_flat
    
    
    @staticmethod
    def GetFixtureData(p_htmlflat):
        
        html = lxml.etree.HTML(p_htmlflat)
        
        body = html.find('.//body/div')
        #excp_lg.warning( bytes.decode(lxml.etree.tostring(body)) )
        
        fixture_el = html.xpath("//div[contains(@class, 'roundlist')]")[0] 
                
        # get header info
        
        bracketInfo_el = fixture_el.xpath("//div[contains(@class, 'roundlist-week')]")[0]        
        bracketInfo_tx = bracketInfo_el.xpath('string()').strip() 
        
        rx_bracket = re.compile(r'[a-zA-Z:\s]+([0-9]+)-[0-9a-zA-Z:]+\s+([0-9]+)')
        season = rx_bracket.search(bracketInfo_tx).group(1);
        season = "IPL" + season
        roundv = rx_bracket.search(bracketInfo_tx).group(2);
        roundv = CU.Pad2(int(roundv))
        
        # get games data
        
        games_data = [];
        rx_datetime = re.compile(r'([0-9\-]+)\s+([0-9:]+)')
        rx_clubs = re.compile(r'([a-zA-Z\s]+)([^a-zA-Z]+)([a-zA-Z\s]+)')
        
        for child in fixture_el:
            
            childClass = child.get('class')
            
            if childClass == 'roundlist-clandar':
                rawStr = child.xpath('string()').strip() 
                createGame = {}
                createGame['playDate'] = rx_datetime.search(rawStr).group(1)
                createGame['playTime'] = rx_datetime.search(rawStr).group(2)
            
            elif childClass == 'roundlist-team':
                rawStr = child.xpath('string()').strip() 
                createGame['homeClub'] = rx_clubs.search(rawStr).group(1).strip()
                createGame['awayClub'] = rx_clubs.search(rawStr).group(3).strip()
            
            elif childClass == 'roundlist-detail':
                games_data.append(createGame)
            
        results = {
            'season': season,
            'round': roundv,
            'games': games_data,
        }
        
        return results
    
    
    @staticmethod
    def InsertFixtureData(fixture_dict):
        
        season_m = FT.Season.objects.get(Season=fixture_dict['season'])
        
        for game_dx in fixture_dict['games']:
            
            # get the data together
            
            try:
                homeClub_m = FT.Club.objects.get(Club_PL=game_dx['homeClub'])
            except FT.Club.DoesNotExist as ex:
                message = "Club not found: {}".format(game_dx['homeClub'])
                excp_lg.error(message)
                raise ex
            
            try:
                awayClub_m = FT.Club.objects.get(Club_PL=game_dx['awayClub'])
            except FT.Club.DoesNotExist:
                message = "Club not found: {}".format(game_dx['awayClub'])
                excp_lg.error(message)
                raise ex
            
            dateTimeRaw = "{} {}".format(game_dx['playDate'], game_dx['playTime'])
            playDateTime = datetime.datetime.strptime(dateTimeRaw, '%Y-%m-%d %H:%M')
            playDateTime = pytz.timezone("Asia/Tehran").localize(playDateTime)
            
            # create game in database
            
            try:
                new_game, created = FT.Game.objects.get_or_create(
                    SeasonFK = season_m,
                    Round = fixture_dict['round'],
                    ClubHomeFK = homeClub_m,
                    ClubAwayFK = awayClub_m,
                    PlayDate = playDateTime
                )
            except Exception as ex:
                message = "Type: {0}\nArguments:{1!r}".format(type(ex).__name__, ex.args)
                excp_lg.error(message)
                raise ex
        
        return






  
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
END OF FILE
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""    