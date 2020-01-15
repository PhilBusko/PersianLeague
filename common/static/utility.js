/*******************************************************************************
COMMON/STATIC/UTILITY.js
*******************************************************************************/


function cl(p_msg)
{
    console.log(p_msg)
}

function ErrorToStatus(p_error, p_func, p_status)
{
    var msg = DjangoSubError(p_error);  cl(msg);
    if (msg.length < p_error.length)
    {
        msg = p_func + "<br>" + msg;
        $(p_status).html(msg);
    }
    else
    {
        $(p_status).css('white-space', 'pre-line');
        msg = p_func + "\n" + msg;
        $(p_status).text(msg);  
    }
    $(p_status).parent().parent().show(); 
    $(p_status).parent().css('background-color', '#ffb3db');  //deeppink  
    $(p_status).parent().css('text-align', 'right');  
    $(p_status).parent().css('padding', '2px 4px'); 
}

function DjangoSubError(p_err)
{
    bg = p_err.search("Traceback");            
    nd = p_err.search("Request information");
    subErr = p_err;
    
    if (bg > 0)
    {
        subErr = p_err.substring(bg, nd);
        subErr = subErr.replace(/\. /g, ".<br>");
    }
    
    return subErr;
}


function MakeDialog(p_elemID, p_width, p_closeBtn)
{
    // old IE can't handle function default parameters
    p_width = p_width || 'auto';
    p_closeBtn = p_closeBtn || true;
    
    $(p_elemID).dialog({
        autoOpen: false,
        draggable: false,
        resizable: false,
        modal: true,        // can only focus on this 
        width: p_width,
        dialogClass: (p_closeBtn ? '' : 'noCloseButton'),
    });
}

function CreateTooltip(p_elemId, p_message, p_position)
{
    p_position = p_position || 'right';
    
    if (p_position == "left")
        pos = {my: 'right center', at: 'left+5% center'}
    
    else if (p_position == "top")
        pos = {my: 'center bottom', at: 'center top+5%'}
    
    else if (p_position == "bottom")
        pos = {my: 'center top', at: 'center bottom+5%'}
    
    else 
        pos = {my: 'left center', at: 'right+5% center'}
    
    $(p_elemId).tooltip({
        items: p_elemId,
        tooltipClass: 'jqueryUI_tooltip',
        content: p_message,
        position: pos,
    });
}


function GetRandomInt(min, max) {
    // inclusive of end-points
    min = Math.ceil(min);
    max = Math.floor(max);
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

function SecondsToTimeDelta(p_secs)
{
    var timeDelta = {
        'hours': Math.floor(p_secs / 60 / 60),
        'minutes': Math.floor( (p_secs / 60) % 60 ), 
        'seconds': Math.floor(p_secs % 60),
    };
        
    return timeDelta;
}


/*******************************************************************************
STRINGS
*******************************************************************************/


function Pad2(p_num)
{
    var num = p_num.toString();
    if (num.length == 1 )
        return "0" + p_num.toString();    
    return p_num.toString();
}

// deprecate this when file paths are defined in server
function FormatFileName(p_msg)
{
    var frm = String(p_msg).toLowerCase();
    var n = frm.lastIndexOf(" ");
    frm = frm.substring(0, n) + "_" + frm.substring(n+1, n+4);
    frm = frm.replace(" ", "");
    return frm;
}

function TitleCase(value)
{
    //words = value.toLowerCase().split(' ');
    var words = value.split(' ');
    for(var i = 0; i < words.length; i++) {
        var letters = words[i].split('');
        letters[0] = letters[0].toUpperCase();
        words[i] = letters.join('');
    }
    return words.join(' ');
}

String.prototype.format = function()
{
    var formatted = this;
    for (var i = 0; i < arguments.length; i++) {
        var regexp = new RegExp('\\{'+i+'\\}', 'gi');
        formatted = formatted.replace(regexp, arguments[i]);
    }
    return formatted;
}

String.prototype.replaceAll = function(search, replacement)
{
    var target = this;
    return target.replace(new RegExp(search, 'g'), replacement);
}


/*******************************************************************************
JQUERY DATATABLES
*******************************************************************************/


function JSONtoFullTable(listJSON)
{
    // create the column names
    
    var cols = []
    var data1 = listJSON[0];
    
    for (var key in data1)
    {
        var title = key.replace(/_/g, " ");
        title = TitleCase(title);
        cols.push(title);
    }
    
    // create records array
    
    var recs = [];
    
    listJSON.forEach( function (obj)
    {
        var newRow = [];
        for (var key in obj)
        {
            var value = obj[key];
            newRow.push(value);
        }
        recs.push(newRow);
    });
    
    // display data on table
    
    var fullTable = {'columns': cols, 'records': recs};
    
    return fullTable;
}

function JObjToFullTable(jObj)
{
    // create the column names
    
    var cols = []
    
    for (var key in jObj)
    {
        var title = key.replace(/_/g, " ");
        title = TitleCase(title);
        cols.push(title);
    }
    
    // create records array
    
    var recs = [];
    
    var newRow = [];
    for (var key in jObj)
    {
        var value = jObj[key];
        newRow.push(value);
    }
    recs.push(newRow);
    
    // display data on table
    
    var fullTable = {'columns': cols, 'records': recs};
    
    return fullTable;
}


function CheckForErrors(p_tableID, p_fullTable)
{
    if ($(p_tableID).length === 0) 
        return "Table HTML-ID not found:" + p_tableID;
    
    if (!p_fullTable)
        return "Data parameter is null.";
    
    if (!p_fullTable.hasOwnProperty("columns") || !p_fullTable.hasOwnProperty("records")) 
        return "Data doesn't have FullTable format.";
    
    if (p_fullTable.columns.length === 0 || p_fullTable.records.length === 0) 
        return "FullTable has no records.";
    
    return null;
}

function SetDataTableColumns(p_tableID, p_columns)
{
    var tableHtml = '';
    tableHtml += '<thead>\n';
    tableHtml += '   <tr role=\'row\'>\n';    
    
    for (var c = 0; c < p_columns.length; c++) {
        tableHtml += '      <th class=\'\' style=\'text-align: left; padding: 8px 10px;\'>' + p_columns[c] + '</th>\n';
    }
    
    tableHtml += '   </tr>\n';
    tableHtml += '</thead>\n';
    
    $(p_tableID).html(tableHtml);
}

function SetDataTable(p_tableID, p_fullTable, p_colsClass, p_hlValue)
{
    p_colsClass = p_colsClass || {};
    p_hlValue = p_hlValue || "";

    var errors = CheckForErrors(p_tableID, p_fullTable);
    if (errors) {
        console.log(errors);
        return;   
    }
    
    SetDataTableColumns(p_tableID, p_fullTable.columns);    
    
    var colDefs = [];
    $.each(p_fullTable.columns, function(idx, val) {
        var colDef = { aTargets: [idx,] };
        $.each(p_colsClass, function(key, val2) {
            if (val.toLowerCase() == key.toLowerCase().replace(/_/g, " ")) {
                colDef['sClass'] = val2;
            }
        });
        colDefs.push(colDef);
    });
    
    $(p_tableID).DataTable( {
        data: p_fullTable.records,
        aoColumnDefs: colDefs,
        bSort: false,
        scrollCollapse: true,
        paging: false,
        bFilter: false,
        bInfo: false,
        bAutoWidth: false,
        bDestroy: true,        // necessary to refresh the data
        "createdRow": function( row, data, dataIndex ) {            
            if ( p_hlValue && $.inArray(p_hlValue, data) >= 0 )   // inArray returns the index
            {
                $(row).children().each(function (index, td) {
                       $(this).addClass('format_highlight');
                });
            }
        },
    } );
    
}


function TransposeFullTable(p_fullT)
{
    var cols = ["Property", "Value"];
    var values = [];
    var conv = {columns: cols, records: values};
    
    if (p_fullT.records.length == 0)
        return conv;
    
    for (var c = 0; c < p_fullT.columns.length; c++)
    {
        var prop = p_fullT.columns[c];
        var value = p_fullT.records[0][c];
        var row = [prop, value];
        values.push(row);        
    }
    
    return conv;
}

function SetVerticalTable(p_tableID, p_fullTable)
{
    var errors = CheckForErrors(p_tableID, p_fullTable);
    if (errors) {
        cl(errors);
        return;   
    }
        
    // set the transposed full-table with jquery datatables 
    
    $(p_tableID).DataTable( {
        data: p_fullTable.records,
        aoColumnDefs: [
            {
                aTargets: [0],
                sClass: "table_cell",
                mRender: function (data, type, full) {
                    html = '<div style="white-space: nowrap;">';
                    html += '<b>' + data + '</b>';
                    html += '</div>';
                    return html;
                },  
            },
            {
                aTargets: [1],
                sClass: "table_cell",
            } 
        ],
        bSort: false,
        scrollCollapse: true,
        paging: false,
        bFilter: false,
        bInfo: false,
        bAutoWidth: false,
        bDestroy: true,                 // necessary to refresh the data
        fnDrawCallback: function() {
            // remove headers
            $(p_tableID + ' thead').remove();
        },
    } );
    
}


/*******************************************************************************
CURRENCY ANIMATION
*******************************************************************************/


function Trajectory(p_start, p_end, p_animTime)
{
    var xDiff = p_end.x - p_start.x;
    var yDiff = p_end.y - p_start.y;
    
    var origAngleDeg = Math.atan(xDiff/yDiff) * 180 / Math.PI;    
    var explodeAngle = (origAngleDeg - 70 + GetRandomInt(0, 140)) * Math.PI / 180;
    var explodeLen = GetRandomInt(30, 70);
    
    var pnt2X = p_start.x - explodeLen * Math.sin(explodeAngle);
    var pnt2Y = p_start.y - explodeLen * Math.cos(explodeAngle);
    
    this.pnt1 = {'x': p_start.x, 'y': p_start.y};
    this.pnt2 = {'x': pnt2X, 'y': pnt2Y};
    this.pnt3 = {'x': p_end.x, 'y': p_end.y};
    
    var frames1 = 800 / p_animTime; 
    var frames2 = 1200 / p_animTime; 
    this.incr1 = {  'x': (this.pnt2.x - this.pnt1.x)/frames1,
                    'y': (this.pnt2.y - this.pnt1.y)/frames1   };
    this.incr2 = {  'x': (this.pnt3.x - this.pnt2.x)/frames2,
                    'y': (this.pnt3.y - this.pnt2.y)/frames2   };
    
    this.currPnt = {'x': p_start.x, 'y': p_start.y};
    this.currSegm = 1;
}

Trajectory.prototype.Advance = function() {
    
    if (this.currSegm == 1)
    {
        this.currPnt.x += this.incr1.x;
        this.currPnt.y += this.incr1.y;
        
        if ( (this.incr1.x > 0 && this.currPnt.x >= this.pnt2.x) ||
             (this.incr1.x < 0 && this.currPnt.x <= this.pnt2.x)  )
            this.currSegm = 2;
    }
    else if (this.currSegm == 2)
    {
        this.currPnt.x += this.incr2.x;
        this.currPnt.y += this.incr2.y;
        
        if ( (this.incr2.x > 0 && this.currPnt.x >= this.pnt3.x) ||
             (this.incr2.x < 0 && this.currPnt.x <= this.pnt3.x)  )
            this.currSegm = 3;
    }
};


function RunAnimClaimRewards(p_resources, p_dmdsPath, p_tokenPath)
{            
    RunAnimTokens();
    
    function RunAnimTokens()
    {
        var offset = $('#claim_button').offset();
        var width = $('#claim_button').outerWidth();
        var height = $('#claim_button').outerHeight();
        var startPnt = {'x': offset.left + width, 'y': offset.top + height/2};
        
        var offset = $('#token_image').offset();
        var width = $('#token_image').outerWidth();
        var height = $('#token_image').outerHeight();
        var endPnt = {'x': offset.left + width/2, 'y': offset.top + height/2};
        
        var bias = 70;
        var clearLeft = startPnt.x -bias;
        if (endPnt.x < startPnt.x)
            clearLeft = endPnt.x -bias;
        
        var clearTop = startPnt.y -bias;
        if (endPnt.y < startPnt.y)
            clearTop = endPnt.y -bias;
        
        var clearWidth = Math.abs(endPnt.x - startPnt.x) +bias*2;
        var clearHeight = Math.abs(endPnt.y - startPnt.y) +bias*2;
        
        $('#tokens_canvas').show();
        var canvas = document.getElementById('tokens_canvas');
        var ctx = canvas.getContext('2d');
        var img = new Image();  
        img.src = p_tokenPath;    // scaled to 26x26 on canvas
        
        var numSteps = 40;
        var animTime = 2000 / numSteps;
        var currStep = 0;
        var trajex = [ ];
        var tokens_intr = setInterval(IconAnimStep, animTime);
        
        function IconAnimStep()
        {            
            if (currStep < 7)
            {
                var toSpawn = GetRandomInt(1,2);
                
                for (var t=0; t<toSpawn; t++)
                {
                    var newTraj = new Trajectory(startPnt, endPnt, animTime);
                    trajex.push(newTraj);
                }
            }
            
            currStep += 1;
            ctx.clearRect(clearLeft, clearTop, clearWidth, clearHeight);    // invalidate small rect for less memory        
            var finished = true;
            
            $.each(trajex, function(idx, traj) {                
                ctx.drawImage(img, traj.currPnt.x -13, traj.currPnt.y -13, 26, 26);
                traj.Advance();
                if (traj.currSegm != 3)
                    finished = false;
            });
            
            if (finished)
            {
                clearInterval(tokens_intr);        
                $('#tokens_canvas').hide();
                ctx.clearRect(0, 0, canvas.width, canvas.height);   
                AnimNumbers();
            }
        }
    }
    
    RunAnimDiamonds();
    
    function RunAnimDiamonds()
    {
        var offset = $('#claim_button').offset();
        var width = $('#claim_button').outerWidth();
        var height = $('#claim_button').outerHeight();
        var startPnt = {'x': offset.left + 0, 'y': offset.top + height/2};
        
        var offset = $('#diamond_image').offset();
        var width = $('#diamond_image').outerWidth();
        var height = $('#diamond_image').outerHeight();
        var endPnt = {'x': offset.left + width/2, 'y': offset.top + height/2};
        
        var bias = 100;
        var clearLeft = startPnt.x -bias;
        if (endPnt.x < startPnt.x)
            clearLeft = endPnt.x -bias;
        
        var clearTop = startPnt.y -bias;
        if (endPnt.y < startPnt.y)
            clearTop = endPnt.y -bias;
        
        var clearWidth = Math.abs(endPnt.x - startPnt.x) +bias*2;
        var clearHeight = Math.abs(endPnt.y - startPnt.y) +bias*2;
        
        $('#diamonds_canvas').show();
        var canvas = document.getElementById('diamonds_canvas');
        var ctx = canvas.getContext('2d');
        var img = new Image();  
        img.src = p_dmdsPath;    // scaled to 26x26 on canvas
        
        var numSteps = 40;
        var animTime = 2000 / numSteps;
        var currStep = 0;
        var trajex = [ ];
        var dmds_intr = setInterval(IconAnimStep, animTime);
        
        function IconAnimStep()
        {            
            if (currStep < 7)
            {
                var toSpawn = GetRandomInt(1,2);
                
                for (var t=0; t<toSpawn; t++)
                {
                    var newTraj = new Trajectory(startPnt, endPnt, animTime);
                    trajex.push(newTraj);
                }
            }
            
            currStep += 1;
            ctx.clearRect(clearLeft, clearTop, clearWidth, clearHeight);    // invalidate small rect for less memory        
            var finished = true;
            
            $.each(trajex, function(idx, traj) {                
                ctx.drawImage(img, traj.currPnt.x -13, traj.currPnt.y -13, 26, 26);
                traj.Advance();
                if (traj.currSegm != 3)
                    finished = false;
            });
            
            if (finished)
            {
                clearInterval(dmds_intr);        
                ctx.clearRect(0, 0, canvas.width, canvas.height);   
                $('#diamonds_canvas').hide();
            }
        }
    }
    
    function AnimNumbers()
    {
        var animDuration = 2000;        // lasts 2 sec
        var animSteps = 40;             // frames for whole duration
        var animTime = animDuration / animSteps;
        
        var diamondIncr = (p_resources.diamond_new - p_resources.diamond_old) / animSteps;
        var tokenIncr =  (p_resources.token_new - p_resources.token_old) / animSteps;
        var diamondDisplay = p_resources.diamond_old;
        var tokenDisplay = p_resources.token_old;
        
        var numbers_intr = setInterval(NumbersAnimStep, animTime);
        
        function NumbersAnimStep()
        {
            diamondDisplay += diamondIncr;
            tokenDisplay += tokenIncr;
            
            $('#menu_diamondsText').text(Math.round(diamondDisplay));
            $('#tokens_listing').text(Math.round(tokenDisplay));
            
            if (diamondDisplay > p_resources.diamond_new)
            {
                clearInterval(numbers_intr);
                $('#menu_diamondsText').text(p_resources.diamond_new);   // deal with any rounding errors
                $('#tokens_listing').text(p_resources.token_new);
            }
        }
    }
    
}


/*******************************************************************************
THE LIGHTNING
*******************************************************************************/


function RecursiveLightning(p_cssClass)
{
    var delay = 20000 + GetRandomInt(0, 20000);      // milisecs
    
    setTimeout(function() {
        RunLightning(p_cssClass);
        RecursiveLightning(p_cssClass);
    }, delay);
}

function RunLightning(p_cssClass)
{
    var coinToss = GetRandomInt(0, 1);
    if (coinToss == 0 || !p_cssClass)
        var frameClass = '.menu_item';
    else
        var frameClass = p_cssClass;
    
    var elem = GetRandomElem(frameClass);
    AnimateLightning(elem);
}

function GetRandomElem(p_cssClass)
{    
    var elements = $(p_cssClass);
    var randIdx = GetRandomInt(0, elements.length -1);
    var item = elements[randIdx];
    
    if (p_cssClass.indexOf('frame_') >= 0)
    {
        if ( $(item).height() < 50 )
            return GetRandomElem(p_cssClass);
    }
    
    return item;
}

function AnimateLightning(p_elem)
{
    /* frame element: the content block that has a bright border
     * full length: the maximum start/end points for the lightning
     * segment: the part of the lightning currently being displayed in animation
     * chain lightning: break up the segment with periodic ties to the main line */
    
    // get the vertices of the frame element
    
    var offset = $(p_elem).offset();
    var width = $(p_elem).outerWidth();
    var height = $(p_elem).outerHeight();
    var boltColor = $(p_elem).css("border-top-color");    
    
    var elemVerts = [{x: parseInt(offset.left), y: parseInt(offset.top)}, 
                {x: parseInt(offset.left + width), y: parseInt(offset.top)}, 
                {x: parseInt(offset.left + width), y: parseInt(offset.top + height)},
                {x: parseInt(offset.left), y: parseInt(offset.top + height)}]
    
    var startIdx = GetRandomInt(0,3);
    var endIdx = (startIdx -1 + GetRandomInt(0,1)*2 +4) % 4;    // can be before or after mod 4
    
    if ($(p_elem).attr('class').indexOf('menu_') >= 0)
        if ( (startIdx == 0 && endIdx == 3) || (startIdx == 3 && endIdx == 0) ) 
            return AnimateLightning(p_elem);
    
    var fullStartPnt = elemVerts[startIdx];
    var fullEndPnt = elemVerts[endIdx];
    
    // prepare animation positions
    
    var xDelta = fullEndPnt.x - fullStartPnt.x;
    var yDelta = fullEndPnt.y - fullStartPnt.y;
    
    var segmLen = 50;
    var segmIncrX = ( xDelta == 0 ? 0 : segmLen * Math.sign(xDelta) );
    var segmIncrY = ( yDelta == 0 ? 0 : segmLen * Math.sign(yDelta) );
    
    var segmStart = {x: fullStartPnt.x, y: fullStartPnt.y};
    var segmEnd = {x: fullStartPnt.x + segmIncrX *2, y: fullStartPnt.y + segmIncrY *2};
    
    if ($(p_elem).attr('class').indexOf('menu_') >= 0)
        fullEndPnt.y += segmIncrY * GetRandomInt(2,4);
    
    var actualEnd = {x: fullEndPnt.x + segmIncrX, y: fullEndPnt.y + segmIncrY};
    
    // prepare animation components
    
    var lt = new lightning({
        detail: 3,
        displace: 35,
        boltWidth: 3,
        boltColor: boltColor,
        glow: true,
        glowWidth: 20,
        glowColor: '#E0FFFF',
        glowAlpha: 0.1
    });    
    
    if ($(p_elem).attr('class').indexOf('menu_') >= 0)
        var animTime = 160;        // milisec
    else
        var animTime = 120;
    
    var myInterval = setInterval(AnimationStep, animTime);
    
    var canvas = document.getElementById('lightning_canvas');
    var ctx = canvas.getContext('2d');
    
    // run animation
    
    $('#lightning_canvas').show();
    ChainLightning(segmStart.x, segmStart.y, segmEnd.x, segmEnd.y)
    ctx.clearRect(offset.left, offset.top, width , height ); 
    
    function AnimationStep()
    {   
        segmStart.x += segmIncrX; //  + GetRandomInt(0, 20);
        segmStart.y += segmIncrY ;
        segmEnd.x += segmIncrX; //  + GetRandomInt(0, 20);
        segmEnd.y += segmIncrY;
        
        lt.hide();
        ChainLightning(segmStart.x, segmStart.y, segmEnd.x, segmEnd.y);
        ctx.clearRect(offset.left, offset.top, width, height);         
        //ctx.fillRect(offset.left, offset.top, width , height );         
        
        if ( (xDelta > 0 && segmStart.x > actualEnd.x) ||
             (xDelta < 0 && segmStart.x < actualEnd.x) ||
             (yDelta > 0 && segmStart.y > actualEnd.y) ||
             (yDelta < 0 && segmStart.y < actualEnd.y) ) 
        {
            clearInterval(myInterval);
            $('#lightning_canvas').hide();
            lt.hide();
        }
    }
    
    function ChainLightning(startX, startY, endX, endY)
    {        
        var noSegments = 2;
        var xIncr = segmLen / noSegments *2 * Math.sign(xDelta);
        var yIncr = segmLen / noSegments *2 * Math.sign(yDelta);
        
        var currX1 = startX;
        var currY1 = startY;
        var currX2 = startX + xIncr;
        var currY2 = startY + yIncr;
        
        while ( (xIncr > 0 && currX1 < endX) ||
                (xIncr < 0 && currX1 > endX) ||
                (yIncr > 0 && currY1 < endY) ||
                (yIncr < 0 && currY1 > endY) )
        {
            lt.show(currX1, currY1, currX2, currY2);
            
            currX1 += xIncr;
            currY1 += yIncr;
            currX2 += xIncr;
            currY2 += yIncr;
        }
    }

}


/*******************************************************************************
AJAX AUTHENTICATION
*******************************************************************************/


function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

var csrftoken = getCookie('csrftoken');

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

$.ajaxSetup({
    crossDomain: false, // obviates need for sameOrigin test
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type)) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});


/*******************************************************************************
END OF FILE
*******************************************************************************/