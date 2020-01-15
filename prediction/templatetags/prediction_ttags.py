"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
PREDICTION/TEMPLATETAGS/UTILITY_TTAGS.py
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

from django import template
from django.utils.html import format_html
import common.templatetags.utility_ttags as u

# module-level variable requirement
register = template.Library()

import logging
prog_lg = logging.getLogger('progress')
excp_lg = logging.getLogger('exception')


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
HEADQUARTERS
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


@register.simple_tag
def multi_ability(abilID, name, abilLevel, abilDesc, iconPath):
    html = format_html("""
            <div id="{}" class="display_block inner_margin2 format_frame outer_padding2"
                         style="background-color: white; display: none;">
                <div class="format_full format_inside">
                    <div class="display_table format_full format_inside">
                        <div class="display_cellM" style="padding-left: 4px;">
                            <img class="icon_button" style="cursor:default; " src="{}"/>
                        </div>
                        <div class="display_cellM" style="width: 80%;">
                            """ + u.ctrl_strong(abilID, name) + """
                        </div>
                        <div class="display_cellM" style="width: 20%;">
                             """ + u.ctrl_listing(abilID, "Level", abilLevel) + """ 
                        </div>
                    </div>
                    <div class="display_table format_full format_inside" style="">
                        <div class="display_cellM" style="">
                            """ + u.ctrl_listing(abilID, "Ability", abilDesc) + """
                        </div>
                    </div>
                </div>
            </div>
        """,
        abilID, iconPath
        )
    return html


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
UPGRADE STORE
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


@register.simple_tag
def multi_upgradeTitle(upgradeName, idPrefix, iconPath, available):
    html = format_html("""
            <div class="display_block inner_margin2 format_inside">
                <div class="format_full format_inside outer_padding2">
                    
                    <div class="display_table format_full">
                        <div class="display_cellM" style="padding: 0px 4px;">
                            <img class="icon_button" style="cursor:default;" src="{}"/>
                        </div>
                        <div class="display_cellM">
                            """ + u.ctrl_strong(idPrefix, upgradeName) + """
                        </div>
                        <div class="display_cellM" style="width: 90%; padding: 0px 6px; position: relative;">
                            <div class="" style="position: absolute; top: -12px; display: {};">
                                <i class="fa fa-angle-double-up anim_updown"
                                    style="color: lime; font-weight: 900; font-size: 320%;"></i>
                            </div>
                        </div>
                        <div class="display_cellM format_center">
                            <div class="inner_margin2" >
                                <div id="{}_expand" style="di splay: inline;">
                                    <i class="fa fa-caret-square-o-down fa-2x format_cpointer"
                                       style="color: ForestGreen;" aria-hidden="true"> </i>
                                </div>
                                <div id="{}_fold" class="" style="display: none;">
                                    <i class="fa fa-caret-square-o-up fa-2x format_cpointer"
                                       style="color: blue;" aria-hidden="true"> </i>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                </div>
            </div>
        """,
        iconPath, "show" if available else "none", idPrefix, idPrefix
        )
    return html


@register.simple_tag
def multi_upgLevelsHeader(idPrefix):
    html = format_html("""                
            <tr class="format_inside2 font_bold">
                <th class="format_center" style="width: 15%;">
                    <span class="inner_margin2"> Level </span>
                </th>
                <th class="format_center" style="width: 25%;">
                    <span class="inner_margin2"> Cost </span>
                </th>
                <th class="" style="width: 35%;">
                    <span class="inner_margin2"> Ability </span>
                </th>
                <th class="format_center" style="width: 25%;">
                    <span class="inner_margin2"> Buy </span>
                </th>
            </tr>
        """,
        idPrefix
        )
    return html


@register.simple_tag
def multi_upgLevelsRow(upgradeName, idPrefix, level, cost, abilityDesc, userLevel):
    
    html = format_html("""
            <tr class="format_inside2">
                <td class="format_center">
                    <span class="inner_margin2"> {} </span>
                </td>
                <td class="format_center font_tokens format_fixline">
                    <span class="inner_margin2"> {}</span>
                    <img class="" src="/static/graphics/currency_pu_bkgd.png" style="max-width: 23px;" />
                </td>
                <td class="">
                    <span class="inner_margin2"> {} </span>
                </td>
                <td class="format_center" style="cursor: default;">
                    *BUTTON*
                </td>
            </tr>
        """,
        level,
        cost,
        #(upgradeName + " Lv " + str(int(level) -1) if level != 1 else "None"),
        abilityDesc
        )
    
    if (level -1) < int(userLevel):
        button = format_html("""
                    <i class="fa fa-check-square-o fa-lg" style="color: BlueViolet;"> </i>
                """)
    elif (level -1) == int(userLevel):
        button = format_html("""
                    <i id="{}_buy" class="fa fa-plus-square-o fa-lg format_cpointer"
                       style="color: green;" upgradeLevel="{}"> </i>
                """,
                idPrefix, level)
    else:
        button = format_html("""
                    <i class="fa fa-times-circle fa-lg" style="color: FireBrick;"> </i>
                """)
    
    html = html.replace("*BUTTON*", button)
    html = format_html(html)
    
    return html





"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
END OF FILE
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""