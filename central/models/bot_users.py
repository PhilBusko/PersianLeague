"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
MEMBERS/MODELS/BOT_USERS.py
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import os
from random import randint

from django.db.models import Count, F, Q 
from django.contrib.auth.models import User  
from django.conf import settings

import allauth.account.models as LM

import common.utility as CU
import members.models.tables as MT
import members.models.members as MM
import football.models.tables as FT
import football.models.football as FM
import prediction.models.universal as PU

import logging
prog_lg = logging.getLogger('progress')
excp_lg = logging.getLogger('exception')


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
TEST USERS EDITOR
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


class TestUsers_Editor(object):
    
    
    @staticmethod
    def DeleteUsers():
        
        # delete icons
        
        botProf_mdls = MT.Profile.objects.filter(UserFK__username__icontains="botuser")
        
        for prof in botProf_mdls:
            if prof.Icon:
                iconPath = os.path.join(settings.BASE_DIR, "members/static/user_icons/" + prof.Icon)
                if os.path.isfile(iconPath):
                    os.remove(iconPath)
        
        # delete users
        
        usersDel = User.objects.filter(username__icontains="botuser")
        numDel = len(usersDel)
        usersDel.delete()
        
        msg = "Deleted Users: " + str(numDel)
        prog_lg.info(msg)
        
        # delete verification
        
        emailsDel = LM.EmailAddress.objects.filter(email__icontains="botuser")
        numDel = len(emailsDel)
        emailsDel.delete()
        
        msg = "Deleted Emails: " + str(numDel)
        prog_lg.info(msg)
        
        # return succesfull results
        
        hret = CU.HttpReturn()
        hret.results = msg
        hret.status = 201
        return hret
    
    
    @staticmethod
    def CreateUsers(p_userNum, p_season):
        
        userNum = int(p_userNum) +1
        
        for u in range(1, userNum, 1):
            
            # create base user
            
            userID = "botuser" + CU.Pad5(u)
            email = userID + "@ufo.com"
            newUser = User.objects.create_user(userID, email, userID)
            
            # add profile traits at random
            
            prof_m = MT.Profile.objects.get(UserFK=newUser)
            
            geo_dx = TestUsers_Editor.GetRandomGeoData()
            prof_m.Country = geo_dx['country']
            prof_m.TimeZone = geo_dx['timezone']
            
            prof_m.FavClubFK = TestUsers_Editor.GetRandomClub(p_season)
            prof_m.Slogan = TestUsers_Editor.GetRandomSlogan()
            prof_m.Icon = TestUsers_Editor.CreateRandomIcon(newUser)
            
            prof_m.BotAI = randint(0, 2)
            
            prof_m.save()
            
            # verify the user's email so they can log in
            
            emdd_m, crtd = LM.EmailAddress.objects.get_or_create(
                user=newUser, email=email, verified=True, primary=True)
            
            # create universal prediction roster as if they had gone to a page
            
            season_m = FT.Season.objects.get(Season=p_season)
            rost_m, crtd = PU.Univ_Roster.objects.get_or_create(UserFK=newUser, SeasonFK=season_m)
        
        
        TestUsers_Editor.CreateRandomRels()
        
        # return succesfull results
        
        hret = CU.HttpReturn()
        hret.results = "Test Users Created"
        hret.status = 201
        return hret
    
    
    # helper for CreateUsers()
    @staticmethod
    def GetRandomGeoData():
        
        geos = [
            {'country': 'United States', 'timezone': 'America/New_York'},
            {'country': 'United States', 'timezone': 'America/Indiana/Knox'},
            {'country': 'United States', 'timezone': 'America/Denver'},
            {'country': 'Canada', 'timezone': 'America/Vancouver'},
            {'country': 'Iran', 'timezone': 'Asia/Tehran'},
            {'country': 'Germany', 'timezone': 'Europe/Berlin'},
            {'country': '', 'timezone': ''},
        ]
        
        randv = randint(0, len(geos)-1)
        geo = geos[randv]
        
        return geo
    
    
    # helper for CreateUsers()
    @staticmethod
    def GetRandomClub(p_season):
        
        # 20% chance of no club
        
        if randint(1,10) >= 9:
            return None
        
        # otherwise get random club
                
        club_names = FM.Reports_General.GetClubs(p_season)
        
        if len(club_names) == 1:
            return None
        
        numClubs = len(club_names)
        
        randv = randint(0, numClubs-1)
        if randv > 10:                          # favor the lower alphabetical clubs
            randv = randint(0, numClubs-1)
        
        club_name = club_names[randv]
        club_m = FT.Club.objects.get(Club = club_name)
        
        return club_m
    
    
    # helper for CreateUsers()
    @staticmethod
    def GetRandomSlogan():
        
        # 40% chance of no slogan
        
        if randint(1,10) >= 7:
            return None
        
        # otherwise get random slogan
        
        slogans = [
            "Ple Zocca !",
            "ThunderCats! HOOO!!",
            "Semper Fi",
            "I'm feeling Lucky",
            "The Web framework for perfectionists with deadlines",
            "Beauty Outside. Beast Inside",
            "I'm evil ... ish",
            "It's me! Maario!!",
            "Get in my belly!",
            "May the force be with you.",
            "  \,,/.<(*_*)> live long and prosper ",
            "Jon Snow Lives",
            "Okily Dokily!",
            "Goo Goo G'joob!",
            "Eat my shorts, man!",
            "A mind is a terrible thing to waste",
            "The opposite of love is indiffirence ...",
            "Play my cock",
            "It went off in my hand!",
            "DEAD BABIES",
            "Cards Against Humanity ain't got nothing on this shit",
            "I'm with stupid (that's me)",
            " ;P ",
            ":D",
            "It could be worse. It could be you.",
            "Shut your fucking face UncleFucker!!",
            "Yeaarrgh!!!",
            "Cheers mate!",
            "Just Do EEEEtt!!",
            "White, Blue, Black, Red, Green",
            "I'm on the soapbox",
            "(-.-)Zzz...",
            "     )xxxxx[;;;;;;;;;>       ",
            "I will have my vengeance!",
            "Viva la Revolucion!",
            "The old 4-4-2",
            "From each according to his ability, to each according to his needs.",
            "All we have to fear is fear itself.",
            "Great minds discuss ideas; average minds discuss events; small minds discuss people.",
            "If you cannot do great things, do small things in a great way.",
            "Life should be great rather than long.",
            "Only those who dare to fail greatly can ever achieve greatly.",
            "And what he greatly thought, he nobly dared.",
            "Success is getting what you want. Happiness is wanting what you get.",
            "With great power comes great responsibility.",
            "May the forces of evil become confused on the way to your house.",
            "A Zen statement never refers to itself.",
            "Kickin' ass since 1980!",
            "The demon code prevents me From declining a rock off challenge!",
            "What is best in life?",
        ]
        
        randv = randint(0, len(slogans)-1)
        slogan = slogans[randv]
        
        return slogan
    
    
    # helper for CreateUsers()
    @staticmethod
    def CreateRandomIcon(user):
        
        # 50% chance of no icon
        
        if randint(1,10) >= 6:
            return None
        
        # get random icon from source folder
        
        baseDir = os.path.join(settings.BASE_DIR, "members/static/icons_source")
        
        fileNames = CU.GetFileNames(baseDir)
        randv = randint(0, len(fileNames)-1)
        fileNm = fileNames[randv]
        
        # create an icon copy in user icons folder
        
        from django.core.files import File
        from django.core.files.uploadedfile import SimpleUploadedFile 
        
        filePath = os.path.join(baseDir, fileNm)        
        fileHandler = File(open(filePath, 'rb'))
        simpleFile = SimpleUploadedFile(filePath, fileHandler.read())
        
        records = MM.Profile_Editor.SaveIcon(user, simpleFile)
        iconFileName = records.results['iconFileName']
        
        return iconFileName
    
    
    # helper for CreateUsers()
    @staticmethod
    def CreateRandomRels():
        
        primaryList = User.objects.filter(Q(username__icontains="botuser") | Q(username="admin"))
        secondaryList = User.objects.filter(username__icontains="botuser")
        userCnt = len(primaryList)
        
        # 5% chance that any user is friends with any other user
        
        for primary in primaryList:
            for secondary in secondaryList:
                isFriend = randint(1, 100)
                if isFriend <= 5:
                    rel_m, created = MT.Relationship.objects.get_or_create(
                        User1FK = primary, User2FK = secondary, RelationValue = 1)
                    rel_m, created = MT.Relationship.objects.get_or_create(
                        User1FK = secondary, User2FK = primary, RelationValue = 1)
                elif isFriend <= 6:
                    rel_m, created = MT.Relationship.objects.get_or_create(
                        User1FK = primary, User2FK = secondary, RelationValue = -1)
        return
    
    
    @staticmethod
    def MakePredictions(p_season, p_round):
        
        bot_mdls = User.objects.filter(username__icontains="botuser")
        
        for bot_m in bot_mdls:
            prof = MT.Profile.objects.get(UserFK=bot_m)
            game_mdls = FT.Game.objects.filter(SeasonFK__Season=p_season, Round=p_round)
            
            # 1% chance of not making predictions for the week
            
            skip = randint(1, 100)
            if skip <= 1:
                continue
            
            # make predictions for each game
            
            for game_m in game_mdls:
                dates = PU.Reporter_Common.GetPredictionWindow(game_m.PlayDate)
                
                pred_m, created = PU.Univ_Prediction.objects.get_or_create(
                    UserFK=bot_m, GameFK=game_m, OpenDate=dates['open'], CloseDate=dates['close'])
                
                pred_m.Result = TestUsers_Editor.GetRandomWinSpectrum(prof.BotAI)
                pred_m.save()
        
        
        hret = CU.HttpReturn()
        hret.results = "Test Users Predictions Made"
        hret.status = 201
        return hret
    
    
    # helper for MakePredictions()
    @staticmethod
    def GetRandomWinSpectrum(p_ai):
        
        # 10% chance of no prediction
        
        if randint(1,10) >= 10:
            return 0
        
        # otherwise get random win spectrum
                
        randv = randint(1, 10)
        
        if p_ai == 1 and randv >= 5:
            randv = randint(1, 10)
        if p_ai == 2 and randv >= 5:
            randv = randint(1, 10)
        
        if randv <= 4:       # home club wins
            winv = 1
        elif randv <= 8:     # away club wins
            winv = 2
        else:                # game ties
            winv = 3
        
        return winv
    

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
TEST USERS REPORTS
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

class TestUsers_Reports(object):
    
    
    @staticmethod
    def GetTestUserCount():
        
        botusers = User.objects.filter(username__icontains="botuser"
            ).annotate(event_count=Count('id'))
        userCnt = len(botusers)
        
        # return results
        
        res = {'userCnt': userCnt}
        
        hret = CU.HttpReturn()
        hret.results = res
        hret.status = 201
        return hret
    
    
    @staticmethod
    def GetTestUserDetails():
        
        botprofs = MT.Profile.objects.filter(UserFK__username__icontains="botuser"
            ).values_list('FavClubFK__Club'
            ).annotate(total=Count('id')
            ).annotate(slogan=Count('Slogan')
            ).annotate(icon=Count('Icon')
            ).order_by('FavClubFK__Club')
        
        data = []  
        for c, botClub in enumerate(botprofs):            
            newRow = lambda: None
            newRow.club = botClub[0]
            newRow.total = botClub[1]
            newRow.slogan = botClub[2]
            newRow.icon = botClub[3]
            data.append(newRow.__dict__)
        
        # return results
        
        hret = CU.HttpReturn()
        hret.results = data
        hret.status = 201
        return hret


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
END OF FILE
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""    