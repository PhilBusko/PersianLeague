"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
COMMON/TEMPLATETAGS/UTILITY_TTAGS.py
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import os
from random import randint

from django import template
from django.utils.html import format_html
from django.conf import settings

import common.utility as CU

# function decorator
register = template.Library()


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
HTML EDIT TEXT
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


@register.simple_tag
def ctrl_text(name, value="", cssClass=""):
    html = format_html("""
        <div class="inner_margin2 {}">
            <span id="{}_text" class=""> {} </span>
        </div>
        """,
        cssClass, name, value);
    return html

# deprecate for ctrl_text
@register.simple_tag
def ctrl_normal(name, value="", style=""):
    html = format_html("""
        <div class="inner_margin2">
            <span id="{}_normal" style="{}"> {} </span>
        </div>
        """,
        name, style, value);
    return html

# deprecate for ctrl_text
@register.simple_tag
def ctrl_strong(name, value=""):
    html = format_html("""
        <div class="inner_margin2">
            <span id="{}_strong" class="font_strong format_fixline"> {} </span>
        </div>
        """,
        name, value);
    return html


@register.simple_tag
def ctrl_status(name):
    html = format_html("""
        <div class="inner_margin2">
            <span id="{}_status" class="font_small"
                style="white-space: normal; word-wrap: normal; text-align: right;"> </span>
        </div>
        """,
        name);
    return html


@register.simple_tag
def ctrl_link(name, label):
    html = format_html("""
        <div class="inner_margin2">
            <span id="{}_link" class="font_link">{}</span>
        </div>""",
        name, label);
    return html


@register.simple_tag
def ctrl_linkA(name, url, label, othertab=False):
    html = format_html("""
        <div class="inner_margin2">
            <a id="{}_link" class="font_link font_strong" {} href="{}">{}</a>
        </div>""",
        name, ('target="blank"' if othertab else ""), url, label);
    return html


@register.simple_tag
def ctrl_listing(name, label, value=""):   
    html = format_html("""
        <div class="display_cellM">
            <span class="inner_margin2" style=""><b>{}:</b></span>
        </div>
        <div class="display_cellM">
            <span class="inner_margin2" id="{}_listing"> {} </span>
        </div>
        """,
        label, name, value);
    return html


@register.simple_tag
def ctrl_paragraph(name):
    html = format_html("""
        <div class="inner_margin2" style="">
            <span id="{}_paragT" class="font_strong"> </span>
            <span id="{}_paragX"> </span>
        </div>
        """,
        name, name);
    return html


@register.simple_tag
def ctrl_entry(name):
    html = format_html("""
        <div class="inner_margin2" style="">
            <span id="{}_entryT" class="font_bold"> </span>
            <span id="{}_entryX"> </span>
        </div>
        """,
        name, name);
    return html


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
HTML CUSTOM ACCESSOR
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


@register.simple_tag
def ctrl_button(name, label, typeSubmit=False):
    html = format_html("""
        <div class="inner_margin2">
            <input id="{}_button" type="{}" value="{}"  
                class="format_button" style="">
            </input>
        </div>
        """,
        name,
        "button"   if not typeSubmit   else "submit",
        label);
    return html


@register.simple_tag
def ctrl_select(name, label):
    html = format_html("""
        <div class="display_cellM">
            <span class="inner_margin2" style="white-space: nowrap;">{}:</span>
        </div>
        <div class="display_cellM">
            <select id="{}_select" class="inner_margin2 format_cpointer"
                style="color: black;">
            </select>
        </div>
        """,
        label, name)
    return html


@register.simple_tag
def ctrl_inputText(name, label, extend=False):
    html = format_html("""
        <div class="display_cellM">
            <span class="inner_margin2" style="white-space: nowrap;">{}: </span>
        </div>
        <div class="display_cellM" style="{}">
            <input id="{}_text" type="text" maxlength="100" size="5"
                class="inner_margin2" style="overflow: hidden; color: black; {}"> </input>
        </div>""",
        label,
        "width: 100%;" if not extend  else "width: 100%;",
        name,
        "" if not extend  else "width: 96%; box-sizing: border-box; -webkit-box-sizing:border-box; -moz-box-sizing: border-box;",
        )
    return html


@register.simple_tag
def ctrl_table(name, center=False, fullWidth=False, title=""):
    html = format_html("""
        <div class="inner_margin2" style="display: block;">
            <span style="margin-bottom: 4px; display: block; font-weight: bold;">{}</span>
            <table id="{}_table" class="row-border" 
                style="{} margin: {} padding-top: 2px; 
                border: 1px solid black; background: white; color: black;">
            </table>
        </div>
        """,
        title,
        name,
        "width: auto !important;"  if not fullWidth  else "",
        "0 !important;"  if not center  else "0px auto;",
        );
    return html


@register.simple_tag
def ctrl_tableDeluxe(name):
    html = format_html("""
        <div class="display_block inner_margin2 format_frame">
            <div style="background: white; padding: 6px;">
                <table id="{}_table" class="format_full row-border"
                    style="color: black;"></table>
            </div>
        </div>
        """,
        name,
        );
    return html


@register.simple_tag
def ctrl_radio(p_name, p_options = []):
    html = format_html("""
        <div class="inner_margin2" style="margin-bottom: 0px;">
        """)
    for opt in p_options:
        html += format_html("""
            <input type="radio" name={} value={}
                id={}_{} class="" style="margin:0px; cursor: pointer;"></input>
            <label for="{}_{}" style="position: relative; top: -3px; cursor: pointer;" > {} </label> <br>
            """,
            p_name, opt.replace(" ", ""),
            p_name, opt.replace(" ", ""),
            p_name, opt.replace(" ", ""), opt)
    html += format_html("""
        </div>
        """)
    return html


@register.simple_tag
def ctrl_radioVert(p_name, p_options = []):
    html = format_html("""
        <div class="inner_margin2" style="margin-bottom: 0px;">
        """)
    for opt in p_options:
        html += format_html("""
            <input type="radio" name={} value={}
                id={}_{} class="" style="margin: 0px; cursor: pointer;"></input>
            <label for="{}_{}" class="format_fixline"
                style="position: relative; top: -3px; cursor: pointer;" > {} </label>
                &emsp;
            """,
            p_name, opt.replace(" ", ""),
            p_name, opt.replace(" ", ""),
            p_name, opt.replace(" ", ""), opt)
    html += format_html("""
        </div>
        """)
    return html


@register.simple_tag
def ctrl_checkbox(p_name, p_label):
    html = format_html("""
        <div class="inner_margin2">
            <input id="{}_checkbox" type="checkbox"></input>
            <label for="{}_checkbox"> {}</label>
        </div>""",
        p_name, p_name, p_label);
    return html


@register.simple_tag
def ctrl_datepicker(name, label):
    html = format_html("""
        <div class="display_cellM">
            <span class="inner_margin2" style="white-space: nowrap;">{}: </span>
        </div>
        <div class="display_cellM">
            <input id="{}_datepicker" type="text" 
                class="inner_margin2 format_center" style="width: 110px; color: black;"> 
        </div>""",
        label, name, )
    return html



@register.simple_tag
def ctrl_image(name, cssClass="", source=""):
    # send in: image_actualSize, image_smallSize, format_frame
    html = format_html("""
        <div class="format_center">
            <div class="inner_margin2">
               <img id="{}_image" class="{}" src="{}"> </img>
            </div>
        </div>""",
        name, cssClass, source);
    return html


@register.simple_tag
def ctrl_imageIcon(p_name, p_border=True):
    html = format_html("""
        <div style="height: 50px; width: 50px; margin: auto;
                position: relative; {} background-color: white; " >
            <img id="{}_image" src=""
                style="max-height: 100%; max-width: 100%;
                    position: absolute; margin: auto; top: 0; left: 0; right: 0; bottom: 0;"> </img>
        </div>""",
        "border: 1px solid black;"   if p_border   else "",
        p_name, );
    return html


@register.simple_tag
def ctrl_iconAwesome(name, icon, color="black"):
    html = format_html("""
        <div class="inner_margin2 format_iconBtn">
            <i id="{}_icon" class="fa {} fa-lg" style="color: {};"></i>
        </div>
        """,
        name, icon, color);
    return html


@register.simple_tag
def ctrl_plot(name, style="height: 400px;"):
    html = format_html("""
        <div class="display_block inner_margin2 format_outline outer_padding1" style="background: white;">
            <div id="{}_plot" class="" style="{}">
            </div>
        </div>""",
        name, style);
    return html



"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
APP SPECIFIC
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


@register.simple_tag
def format_url(p_url, p_label):
    # used in email body
    html = format_html("""
        <a href="{}">{}</a> 
        """,
        str(p_url), p_label);
    return html


@register.simple_tag
def bkgd_detail():
    storageDir = os.path.join(settings.BASE_DIR, 'common/static/images/bkgd_detail')
    fileNames = CU.GetFileNames(storageDir)
    randv = randint(0, len(fileNames)-1)
    fileName = fileNames[randv]
    
    style = 'background-image: url(/static/images/bkgd_detail/{0});'.format(fileName)
    return style


@register.simple_tag
def bkgd_content():
    storageDir = os.path.join(settings.BASE_DIR, 'common/static/images/bkgd_content')
    fileNames = CU.GetFileNames(storageDir)
    randv = randint(0, len(fileNames)-1)
    fileName = fileNames[randv]
    
    style = 'url(/static/images/bkgd_content/{0})'.format(fileName)
    #style = 'background: url(/static/images/bkgd_content/{0}) fixed top left;'.format(fileName)
    return style


@register.simple_tag
def play_music():
    storageDir = os.path.join(settings.BASE_DIR, 'common/static/music')
    fileNames = CU.GetFileNames(storageDir)
    randv = randint(0, len(fileNames)-1)
    fileName = fileNames[randv]
    
    style = '/static/music/{0}'.format(fileName)
    return style


@register.simple_tag
def random_background():
    
    # for dev
    #return None
    
    # get list of files in backgrounds directory
    # must be absolute path, relative path must not start with /
    
    from os import walk
    bkgdPath = os.path.join(settings.BASE_DIR, "common/static/images/backgrounds/")
    fileNames = []
    for (bkgdPath, dirnames, filenames) in walk(bkgdPath):
        fileNames.extend(filenames)
        break
    
    # assume screen size as per notes
    # all points are at top-left 
    
    imageDiam = 270
    widthMin = -50
    widthMax = 2000 - imageDiam
    heightMin = -50
    heightMax = 2600 - imageDiam
    
    
    # use as many random non-overlapping positions as possible
    
    from random import randrange
    from math import hypot
    
    positions = []
    trialThreshold = 100
    trialCurrent = 0
    
    while trialCurrent < trialThreshold:
        randX = randrange(widthMin, widthMax +1)
        randY = randrange(heightMin, heightMax +1)
        
        valid = True
        for pos in positions:
            dist = hypot(randX - pos[0], randY - pos[1])
            if dist <= imageDiam * 0.95:
                valid = False
        
        if valid:
            positions.append([randX, randY])
            trialCurrent = 0
        else:
            trialCurrent += 1
    
    numBacks = len(positions)   
    
    
    # create styling starting with random files 
    
    numImages = len(fileNames)
    style = "background: "
    
    for m in range(1, numBacks +1, 1):
        randImageName = fileNames[randrange(0, numImages)]
        style += "url('/static/images/backgrounds/{}')".format(randImageName)
        if m != numBacks:
            style += ", \n"
        else:
            style += "; \n"    
    
    # other styling components
    
    style += "background-position: "
    
    for pos in positions:
        style += " {}px {}px, ".format(pos[0], pos[1])
    
    style = "; \n".join(style.rsplit(",", 1))
        
    style += "background-size: {}px {}px; \n".format(imageDiam, imageDiam)
    style += "background-repeat: no-repeat; \n"
    
    #prog_lg.debug(style)
    
    return style



"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
END OF FILE
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""