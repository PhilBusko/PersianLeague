"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
COMMON/UTILITY.py
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import logging
prog_lg = logging.getLogger('progress')
excp_lg = logging.getLogger('exception')


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
BASIC DATA TYPES
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import datetime
import pytz

#.strftime(CU.FORMAT_DTSTR)

FORMAT_DTSTR = "%Y-%m-%d %H:%M %Z"

FORMAT_DTSTR_SECS = "%Y-%m-%d %H:%M:%S"

FORMAT_DTSTR_DT = "%Y-%m-%d"

def Pad2(p_no):
    return "0" + str(p_no) if int(p_no) < 10 else str(p_no)

def Pad5(p_no):
    pad = p_no
    if p_no <= 9:
        pad = "0000" + str(p_no)
    elif p_no <= 99:
        pad = "000" + str(p_no)
    elif p_no <= 999:
        pad = "00" + str(p_no)
    elif p_no <= 9999:
        pad = "0" + str(p_no)
    
    return pad

def TZStringToDT(p_dateUnaware):
    # python can't create TZ-aware datetimes, so must implement custom solution
    # http://stackoverflow.com/questions/1703546/parsing-date-time-string-with-timezone-abbreviated-name-in-python
    
    import dateutil.parser as dp
    
    tz_str = '''-12 Y
    -11 X NUT SST
    -10 W CKT HAST HST TAHT TKT
    -9 V AKST GAMT GIT HADT HNY
    -8 U AKDT CIST HAY HNP PST PT
    -7 T HAP HNR MST PDT
    -6 S CST EAST GALT HAR HNC MDT
    -5 R CDT COT EASST ECT EST ET HAC HNE PET
    -4 Q AST BOT CLT COST EDT FKT GYT HAE HNA PYT
    -3 P ADT ART BRT CLST FKST GFT HAA PMST PYST SRT UYT WGT
    -2 O BRST FNT PMDT UYST WGST
    -1 N AZOT CVT EGT
    0 Z EGST GMT UTC WET WT
    1 A CET DFT WAT WEDT WEST
    2 B CAT CEDT CEST EET SAST WAST
    3 C EAT EEDT EEST IDT MSK
    4 D AMT AZT GET GST KUYT MSD MUT RET SAMT SCT
    5 E AMST AQTT AZST HMT MAWT MVT PKT TFT TJT TMT UZT YEKT
    6 F ALMT BIOT BTT IOT KGT NOVT OMST YEKST
    7 G CXT DAVT HOVT ICT KRAT NOVST OMSST THA WIB
    8 H ACT AWST BDT BNT CAST HKT IRKT KRAST MYT PHT SGT ULAT WITA WST
    9 I AWDT IRKST JST KST PWT TLT WDT WIT YAKT
    10 K AEST ChST PGT VLAT YAKST YAPT
    11 L AEDT LHDT MAGT NCT PONT SBT VLAST VUT
    12 M ANAST ANAT FJT GILT MAGST MHT NZST PETST PETT TVT WFT
    13 FJST NZDT
    11.5 NFT
    10.5 ACDT LHST
    9.5 ACST
    6.5 CCT MMT
    5.75 NPT
    5.5 SLT
    4.5 AFT IRDT
    3.5 IRST
    -2.5 HAT NDT
    -3.5 HNT NST NT
    -4.5 HLV VET
    -9.5 MART MIT'''
    
    tzd = {}
    for tz_descr in map(str.split, tz_str.split('\n')):
        tz_offset = int(float(tz_descr[0]) * 3600)
        for tz_code in tz_descr[1:]:
            tzd[tz_code] = tz_offset
    
    date_tz = dp.parse(p_dateUnaware, tzinfos=tzd)
    
    return date_tz

def mean(numbers):
    return float(sum(numbers)) / max(len(numbers), 1)


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
LOGGING
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

class SimpleFmt(logging.Formatter):
    def format(self, record):
        msg = "\n" + "%s -> %s()" % (record.pathname[29:], record.funcName)
        msg += "\n" + super(SimpleFmt, self).format(record) + "\n"
        return msg

class CompleteFmt(logging.Formatter):
    def format(self, record):
        cDate = datetime.datetime.fromtimestamp(record.created)
        frmtDate = cDate.strftime("%Y-%m-%d %H:%M:%S")
        
        msg = "\n" + "%s @ %s" % (record.levelname, frmtDate)
        msg += "\n" + "%s : %s()" % (record.pathname[29:], record.funcName)
        msg += "\n" + super(CompleteFmt, self).format(record) + "\n"
        
        return msg


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
RETURN STRUCTURES
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

# deprecate ?
class HttpReturn(object):
    def __init__(self):
        self.results = None
        self.status = None
    def __str__(self):
         return "HttpReturn: results.len {} | status {} ".format(
            len(self.results), self.status)  
    def __repr__(self):
        return self.__str__()


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
FILE SYSTEM
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

def GetFileNames(baseDir):
    # baseDir must be an absolute path
    from os import walk
    fileNames = []
    for (dirpath, dirnames, filenames) in walk(baseDir):
        fileNames.extend(filenames)
        break
    return fileNames

def FormatFile(p_str):
    frm = p_str.lower()
    frm = frm.replace(" ", "_")
    return frm


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
END OF FILE
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""