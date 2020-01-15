/*******************************************************************************
PREDICTION/STATIC/PREDICTION.js
*******************************************************************************/

var Pred = Pred || {};

var Period_Enum = {
    Initial: 0, 
    Prev: 1,
    Current: 2,
    Future: 3,
};

Pred.GAMES = [];
Pred.PREDICTIONS = [];
Pred.NOW = null;
Pred.PERIOD = Period_Enum.Initial;


Pred.SetCurrentPeriod = function()
{
    var game_dt = Date.parseString(Pred.GAMES[0].playLoc_st.substring(0,16), "yyyy-MM-dd HH:mm");
    var sunday_dt = new Date(game_dt.getTime()).clearTime();
    sunday_dt.setDate(sunday_dt.getDate() - sunday_dt.getDay());   
    var nextSunday_dt = new Date(sunday_dt.getTime());
    nextSunday_dt.add('d', 7);
    
    if (nextSunday_dt.isBefore(Pred.NOW))
        Pred.PERIOD = Period_Enum.Prev;
    
    else if (sunday_dt.isBefore(Pred.NOW) && nextSunday_dt.isAfter(Pred.NOW))
        Pred.PERIOD = Period_Enum.Current;
    
    else
        Pred.PERIOD = Period_Enum.Future;
}


Pred.GetMatchingPred = function(p_gameid)
{
    var matchPred = null;
    
    $.each(Pred.PREDICTIONS, function(key, pred) {
        if (pred.gameid == p_gameid)
            matchPred = pred;       // can't return here ?
    });
    
    return matchPred;
}


Pred.DisplayAbilities = function(p_abilsOwned, p_abilsUsed, p_user)
{
    
    if (p_user == 'AnonymousUser')
    {
        $('#abilities_table').html('<div class="inner_margin2">     \
                                   Abilities are for logged in users.   \
                                   </div>   ');
        return;
    }    
    
    if (Pred.PERIOD == Period_Enum.Prev)
    {
        $('#abilities_table').html('<div class="inner_margin2">         \
                                   Abilities are not available in the past.     \
                                   </div>   ');
        return;
    }
    
    if (Pred.PERIOD == Period_Enum.Future)
    {
        $('#abilities_table').html('<div class="inner_margin2">     \
                                   Abilities are not available in the future.   \
                                   </div>   ');
        return;
    }
    
    // create abilities data for current period
    
    var abils = [];
    
    if (p_abilsOwned.goalsG.uses > 0)
    {
        var available = "{0} of {1}".format(p_abilsOwned.goalsG.uses - p_abilsUsed.goalsG, p_abilsOwned.goalsG.uses);
        var abil = { Ability: "Goals Guess", Available: available };
        abils.push(abil);
    }
    if (p_abilsOwned.scorersG.uses > 0)
    {
        var available = "{0} of {1}".format(p_abilsOwned.scorersG.uses - p_abilsUsed.scorersG, p_abilsOwned.scorersG.uses);
        var abil = { Ability: "Scorers Guess", Available: available };
        abils.push(abil);
    }
    if (p_abilsOwned.secondChance.uses > 0)
    {
        var available = "{0} of {1}".format(p_abilsOwned.secondChance.uses - p_abilsUsed.secondChance, p_abilsOwned.secondChance.uses);
        var abil = { Ability: "Second Chance", Available: available };
        abils.push(abil);
    }
    if (p_abilsOwned.doubleDown.uses > 0)
    {
        var available = "{0} of {1}".format(p_abilsOwned.doubleDown.uses - p_abilsUsed.doubleDown, p_abilsOwned.doubleDown.uses);
        var abil = { Ability: "Double Down", Available: available };
        abils.push(abil);
    }
    if (p_abilsOwned.clubFav.uses > 0)
    {
        var available = ( p_abilsOwned.clubFav.uses - p_abilsUsed.clubFav ? "Available" : "In Use" );
        var abil = { Ability: "Club Favorite", Available: available };
        abils.push(abil);
    }
    
    if (abils.length > 0)
    { 
        //var colsClass = { Ability: "", Available: "format_center" };
        //var fullT = JSONtoFullTable(abils);
        //SetDataTable('#abilities_table', fullT, colsClass);
        
        Pred.SetDeluxeAbilities('#abilities_table', abils);
    }
    else 
    {
        $('#abilities_table').html('<div class="inner_margin2">     \
                                   You have no abilities. <br>Purchase abilities at the Upgrades page.   \
                                   </div>   ');
    }
}


Pred.SetDeluxeAbilities = function(p_tableID, p_abilities)
{       
    
    var table = $(p_tableID).DataTable( {
        data: p_abilities,
        aoColumns: [
            {
                title: "Ability",
                mData: "Ability",
                sClass: "format_fixline",
            },
            {
                title: "Icon",
                sClass: "",
                mRender: function (data, type, full) {
                    var html = "";
                    
                    if (full.Ability == "Goals Guess")
                        html = '<img class="icon_button" style="cursor:default;" src="/static/graphics/pred_goals.png"/>';
                    
                    else if (full.Ability == "Scorers Guess")
                        html = '<img class="icon_button" style="cursor:default;" src="/static/graphics/pred_scorers.png"/>';
                    
                    else if (full.Ability == "Second Chance")
                        html = '<img class="icon_button" style="cursor:default;" src="/static/graphics/pred_secondChance.png"/>';
                    
                    else if (full.Ability == "Double Down")
                        html = '<img class="icon_button" style="cursor:default;" src="/static/graphics/pred_ddownON.png"/>';
                    
                    else if (full.Ability == "Club Favorite")
                        html = '<img class="icon_button" style="cursor:default;" src="/static/graphics/pred_clubFav.png"/>';
                    
                    return html;
                },
            },
            {
                title: "Available",
                mData: "Available",
                sClass: "format_center",
            },
        ], 
        bSort: false,
        bFilter: false,
        bInfo: false,
        bDestroy: true,
        bLengthChange: false,
        paging: false,
    } );
    
}


Pred.DisplayCalendar = function()
{
    // calendar initialization is only done on the first call
    
    $('#calendar').fullCalendar({
        //header: true,
        defaultView: 'agendaWeek',  // 'basicWeek'
        allDaySlot: false,
        height: 500,
        displayEventTime: false,
        timeFormat: { '': 'HH:mm' },
    });
    
    // refresh the events in the jquery calendar object
    
    var startDate_tx = Pred.GAMES[0]['playLoc_st']
    var startDate = Date.parseString(startDate_tx.substring(0,16), "yyyy-MM-dd HH:mm");
    $('#calendar').fullCalendar('gotoDate', startDate);
    
    var events = [];
    for (var g = 0; g <= 7; g++)
    {
        // add events for games
        
        var game = Pred.GAMES[g];
        var titleV = "{0} & {1}".format(game['home_club'].substring(0, 4), game['away_club'].substring(0, 4));
        var newEvt = {
            title: titleV,
            start: Date.parseString(game['playLoc_st'].substring(0,16), "yyyy-MM-dd HH:mm"),
            // no end necessary, default duration on calendar is 2 hours
        }
        events.push(newEvt);
        
        // add events for predictions
        // end date is for display purposes, not actual close date
        
        if (Pred.PERIOD != Period_Enum.Current)
            continue;
        
        var pred = Pred.GetMatchingPred(game.gameid);
        var open_dt = Date.parseString(pred['open_date'].substring(0,16), "yyyy-MM-dd HH:mm");
        var delta_dt = new Date(open_dt.getTime());
        delta_dt = delta_dt.add('m', 20);
        
        var newEvt = {
            title: titleV,
            start: open_dt,     
            end: delta_dt,
            backgroundColor: "LightSeaGreen",
        }
        events.push(newEvt);
    }
    
    var newEvt = {
        title: "Now",
        start: Pred.NOW,     
        end: new Date(Pred.NOW.getTime()).add('m', 20),
        backgroundColor: "crimson",
    }
    events.push(newEvt);
    
    $('#calendar').fullCalendar('removeEvents');
    $('#calendar').fullCalendar('addEventSource', events);         
    $('#calendar').fullCalendar('rerenderEvents' );
}



Pred.DisplayGameValues = function(p_game, p_no)
{
    $('#gid' + p_no + '_listing').text(p_game.gameid);
    
    var dateFmt = "E d, HH:mm";
    if (Pred.PERIOD != Period_Enum.Current)
        dateFmt = "NNN d, HH:mm";
    var play_dt = Date.parseString(p_game.playLoc_st.substring(0,16), "yyyy-MM-dd HH:mm");
    $('#playDate' + p_no + '_listing').text(play_dt.format(dateFmt));
    
    var path = '/static/club_images/' + FormatFileName(p_game.home_club) + ' logo.png'; 
    $('#homeLogo' + p_no + '_image').attr('src', path); 
    $('#homeClub' + p_no + '_normal').text(p_game.home_club);
    $('#homeGoals' + p_no + '_normal').text(
        (p_game.home_goals != null ? p_game.home_goals : "*") );
    if (p_game.home_scorers)
    {
        var scorers = p_game.home_scorers.replace(/,\s/g, '<br>').replace(',', '');
        $('#homeScorers' + p_no + '_normal').html(scorers); 
    }
    else
        $('#homeScorers' + p_no + '_normal').html(null); 
    
    var path = '/static/club_images/' + FormatFileName(p_game.away_club) + ' logo.png';
    $('#awayLogo' + p_no + '_image').attr('src', path);
    $('#awayClub' + p_no + '_normal').text(p_game.away_club);
    $('#awayGoals' + p_no + '_normal').text(
        (p_game.away_goals != null ? p_game.away_goals : "*") );
    if (p_game.away_scorers)
    {
        var scorers = p_game.away_scorers.replace(/,\s/g, '<br>').replace(',', '');
        $('#awayScorers' + p_no + '_normal').html(scorers);
    }
    else
        $('#awayScorers' + p_no + '_normal').html(null); 
}


Pred.InitPredCtrls = function(p_players)
{
    var goalTypes = ["*", "0", "1", "2", "3+"];
    
    for (var p = 1; p <= 8; p++)
    {
        // result controls
        
        $('input:radio[name=result' + p + ']').filter('[value=Abstain]').prop('checked', true);
        $('input:radio[name=resultSC' + p + ']').filter('[value=Abstain]').prop('checked', true);
        $('#resultSave' + p + '_button').prop('disabled', true);
        
        $('input:radio[name=result' + p + ']').change(function() {
            var id = $(this).attr('id').match(/\d+/)[0];        
            $('#resultSave' + id + '_button').prop('disabled', false);
        });
        
        $('input:radio[name=resultSC' + p + ']').change(function() {
            var id = $(this).attr('id').match(/\d+/)[0];        
            $('#resultSave' + id + '_button').prop('disabled', false);
        });        
        
        // goals controls
        
        $.each(goalTypes, function(key, value) {
            $('#goalsHm' + p + '_select').append($('<option>', { value : value }).text(value));
            $('#goalsAw' + p + '_select').append($('<option>', { value : value }).text(value));        
            $('#goalsHmSC' + p + '_select').append($('<option>', { value : value }).text(value));
            $('#goalsAwSC' + p + '_select').append($('<option>', { value : value }).text(value));        
        });
        $('#goalsSave' + p + '_button').prop('disabled', true);
        
        $('#goalsHm' + p + '_select').change(function() {
            var id = $(this).attr('id').match(/\d+/)[0];
            var goalsHome = $('#goalsHm' + id + '_select option:selected').text();
            var goalsAway = $('#goalsAw' + id + '_select option:selected').text();    
            
            if (goalsHome != "*" && goalsAway != "*")
                $('#goalsSave' + id + '_button').prop('disabled', false);
            else
                $('#goalsSave' + id + '_button').prop('disabled', true);
        });
        
        $('#goalsAw' + p + '_select').change(function() {
            var id = $(this).attr('id').match(/\d+/)[0];
            var goalsHome = $('#goalsHm' + id + '_select option:selected').text();
            var goalsAway = $('#goalsAw' + id + '_select option:selected').text();    
            
            if (goalsHome != "*" && goalsAway != "*")
                $('#goalsSave' + id + '_button').prop('disabled', false);
            else
                $('#goalsSave' + id + '_button').prop('disabled', true);
        });
        
        $('#goalsHmSC' + p + '_select').change(function() {
            var id = $(this).attr('id').match(/\d+/)[0];
            var goalsHome = $('#goalsHmSC' + id + '_select option:selected').text();
            var goalsAway = $('#goalsAwSC' + id + '_select option:selected').text();    
            
            if (goalsHome != "*" && goalsAway != "*")
                $('#goalsSave' + id + '_button').prop('disabled', false);
            else
                $('#goalsSave' + id + '_button').prop('disabled', true);
        });
        
        $('#goalsAwSC' + p + '_select').change(function() {
            var id = $(this).attr('id').match(/\d+/)[0];
            var goalsHome = $('#goalsHmSC' + id + '_select option:selected').text();
            var goalsAway = $('#goalsAwSC' + id + '_select option:selected').text();    
            
            if (goalsHome != "*" && goalsAway != "*")
                $('#goalsSave' + id + '_button').prop('disabled', false);
            else
                $('#goalsSave' + id + '_button').prop('disabled', true);
        });
        
        // scorer controls
        
        $('#scorersSave' + p + '_button').prop('disabled', true);
        
        $('#scorersHm' + p + '_text').autocomplete({source: p_players, minLength: 4,
                                                    select: PlayerSelect, change: PlayerChange,});
        $('#scorersAw' + p + '_text').autocomplete({source: p_players, minLength: 4,
                                                    select: PlayerSelect, change: PlayerChange,});
        $('#scorersHmSC' + p + '_text').autocomplete({source: p_players, minLength: 4,
                                                    select: PlayerSelect, change: PlayerChange,});
        $('#scorersAwSC' + p + '_text').autocomplete({source: p_players, minLength: 4,
                                                    select: PlayerSelect, change: PlayerChange,});
        
        // options tooltips
        
        CreateTooltip('#goalsUnlock' + p + '_option', "Unlock");
        CreateTooltip('#goalsLock' + p + '_option', "Lock");
        CreateTooltip('#scorersUnlock' + p + '_option', "Unlock");
        CreateTooltip('#scorersLock' + p + '_option', "Lock");
        
        CreateTooltip('#scResult' + p + '_option', "Second Chance");
        CreateTooltip('#scResultUndo' + p + '_option', "Undo Second Chance");
        CreateTooltip('#scGoals' + p + '_option', "Second Chance");
        CreateTooltip('#scGoalsUndo' + p + '_option', "Undo Second Chance");
        CreateTooltip('#scScorers' + p + '_option', "Second Chance");
        CreateTooltip('#scScorersUndo' + p + '_option', "Undo Second Chance");
        
        CreateTooltip('#ddResult' + p + '_option', "Double Down is OFF");
        CreateTooltip('#ddResultUndo' + p + '_option', "Double Down is ON");
        CreateTooltip('#ddGoals' + p + '_option', "Double Down is OFF");
        CreateTooltip('#ddGoalsUndo' + p + '_option', "Double Down is ON");        
        CreateTooltip('#ddScorers' + p + '_option', "Double Down is OFF");
        CreateTooltip('#ddScorersUndo' + p + '_option', "Double Down is ON");        
        
        CreateTooltip('#cfResult' + p + '_option', "Club Favorite");
        CreateTooltip('#cfGoals' + p + '_option', "Club Favorite");
        CreateTooltip('#cfScorers' + p + '_option', "Club Favorite");
        
        // save buttons
        
        $('#resultSave' + p + '_button').click(function() {
            var id = $(this).attr('id').match(/\d+/)[0];        
            Pred.SavePrediction(id);
        });
        
        $('#goalsSave' + p + '_button').click(function() {
            var id = $(this).attr('id').match(/\d+/)[0];        
            Pred.SavePrediction(id);
        });
        
        $('#scorersSave' + p + '_button').click(function() {
            var id = $(this).attr('id').match(/\d+/)[0];        
            Pred.SavePrediction(id);
        });
        
        // options on click
        
        $('#goalsUnlock' + p + '_option').click(UnlockGoal);
        $('#goalsLock' + p + '_option').click(LockGoal);
        $('#scorersUnlock' + p + '_option').click(UnlockScorer);
        $('#scorersLock' + p + '_option').click(LockScorer);
        
        $('#scResult' + p + '_option').click(ShowResultSC);
        $('#scResultUndo' + p + '_option').click(HideResultSC);
        $('#scGoals' + p + '_option').click(ShowGoalSC);
        $('#scGoalsUndo' + p + '_option').click(HideGoalSC);
        $('#scScorers' + p + '_option').click(ShowScorerSC);
        $('#scScorersUndo' + p + '_option').click(HideScorerSC);
        
        $('#ddResult' + p + '_option').click(ShowResultDD);
        $('#ddResultUndo' + p + '_option').click(HideResultDD);
        $('#ddGoals' + p + '_option').click(ShowGoalDD);
        $('#ddGoalsUndo' + p + '_option').click(HideGoalDD);
        $('#ddScorers' + p + '_option').click(ShowScorerDD);
        $('#ddScorersUndo' + p + '_option').click(HideScorerDD);
        
    }
    
    function PlayerSelect(a, b)
    {       
        var id = $(this).attr('id').match(/\d+/)[0];
        $('#scorersSave' + id + '_button').prop('disabled', false);
    }
    
    function PlayerChange(event, ui)
    {
        if (ui.item === null || !ui.item)
            $(this).val("");
            
        var id = $(this).attr('id').match(/\d+/)[0];
        $('#scorersSave' + id + '_button').prop('disabled', false);
    }
    
    function CreateTooltip(p_id, p_text)
    {
        $(p_id).tooltip({
            items: p_id,
            tooltipClass: 'jqueryUI_tooltip',
            content: p_text,
            position: { at: 'right center', my: 'left+5% center' }
        });
    }
    
    
    // unlock goals and scorers
    
    function UnlockGoal()
    {
        var id = $(this).attr('id').match(/\d+/);           
        $('#goal' + id + '_overlay').hide();
        $('#goalsUnlock' + id + '_option').hide();
        $('#goalsLock' + id + '_option').show();
        
        Pred.SavePrediction(id);
    }
    
    function LockGoal()
    {
        var id = $(this).attr('id').match(/\d+/);      
        $('#goal' + id + '_overlay').show();
        $('#goalsUnlock' + id + '_option').show();
        $('#goalsLock' + id + '_option').hide();
        $('#goalsHm' + id + '_select').val($('#goalsHm' + id + '_select option:first').val());
        $('#goalsAw' + id + '_select').val($('#goalsAw' + id + '_select option:first').val());
        
        if ( $('#scGoalsUndo' + id + '_option').is(":visible") )
            $('#scGoalsUndo' + id + '_option').click();
            
        if ( $('#ddGoalsUndo' + id + '_option').is(":visible") )
            $('#ddGoalsUndo' + id + '_option').click();
        
        Pred.SavePrediction(id);
    }
    
    function UnlockScorer()
    {
        var id = $(this).attr('id').match(/\d+/);     
        $('#scorer' + id + '_overlay').hide();
        $('#scorersUnlock' + id + '_option').hide();
        $('#scorersLock' + id + '_option').show();
        
        Pred.SavePrediction(id);
    }
    
    function LockScorer()
    {
        var id = $(this).attr('id').match(/\d+/);          
        $('#scorer' + id + '_overlay').show();
        $('#scorersUnlock' + id + '_option').show();
        $('#scorersLock' + id + '_option').hide();
        $('#scorersHm' + id + '_text').val(null);
        $('#scorersAw' + id + '_text').val(null);
        
        if ( $('#scScorersUndo' + id + '_option').is(":visible") )
            $('#scScorersUndo' + id + '_option').click();
        
        if ( $('#ddScorersUndo' + id + '_option').is(":visible") )
            $('#ddScorersUndo' + id + '_option').click();
        
        Pred.SavePrediction(id);
    }
    
    
    // second chance for all guesses
    
    function ShowResultSC()
    {
        var id = $(this).attr('id').match(/\d+/);          
        $('#scResult' + id + '_option').hide();
        $('#scResultUndo' + id + '_option').show();
        $('#secondChance' + id + '_row').show();
        $('#resSC' + id + '_block').show();
        
        Pred.SavePrediction(id);
    }
    
    function HideResultSC()
    {
        var id = $(this).attr('id').match(/\d+/);          
        $('#scResult' + id + '_option').show();
        $('#scResultUndo' + id + '_option').hide();
        $('#secondChance' + id + '_row').hide();
        $('#resSC' + id + '_block').hide();
        
        Pred.SavePrediction(id);
    }
    
    function ShowGoalSC()
    {
        var id = $(this).attr('id').match(/\d+/);          
        $('#scGoals' + id + '_option').hide();
        $('#scGoalsUndo' + id + '_option').show();
        $('#secondChance' + id + '_row').show();
        $('#goalSC' + id + '_block').show();
        
        Pred.SavePrediction(id);
    }
    
    function HideGoalSC()
    {
        var id = $(this).attr('id').match(/\d+/);          
        $('#scGoals' + id + '_option').show();
        $('#scGoalsUndo' + id + '_option').hide();
        $('#secondChance' + id + '_row').hide();
        $('#goalSC' + id + '_block').hide();
        $('#goalsHmSC' + id + '_select').val($('#goalsHmSC' + id + '_select option:first').val());
        $('#goalsAwSC' + id + '_select').val($('#goalsAwSC' + id + '_select option:first').val());
        
        Pred.SavePrediction(id);
    }
    
    function ShowScorerSC()
    {
        var id = $(this).attr('id').match(/\d+/);          
        $('#scScorers' + id + '_option').hide();
        $('#scScorersUndo' + id + '_option').show();
        $('#secondChance' + id + '_row').show();
        $('#scorerSC' + id + '_block').show();
        
        Pred.SavePrediction(id);
    }
    
    function HideScorerSC()
    {
        var id = $(this).attr('id').match(/\d+/);          
        $('#scScorers' + id + '_option').show();
        $('#scScorersUndo' + id + '_option').hide();
        $('#secondChance' + id + '_row').hide();
        $('#scorerSC' + id + '_block').hide();
        $('#scorersHmSC' + id + '_text').val(null);
        $('#scorersAwSC' + id + '_text').val(null);
        
        Pred.SavePrediction(id);
    }
    
    
    // double down for all guesses
    
    function ShowResultDD()
    {
        var id = $(this).attr('id').match(/\d+/);      
        $('#ddResult' + id + '_option').hide(); 
        $('#ddResultUndo' + id + '_option').show();
        
        Pred.SavePrediction(id);
    }
    
    function HideResultDD()
    {
        var id = $(this).attr('id').match(/\d+/);
        $('#ddResult' + id + '_option').show();     
        $('#ddResultUndo' + id + '_option').hide();   
        
        Pred.SavePrediction(id);
    }
    
    function ShowGoalDD()
    {
        var id = $(this).attr('id').match(/\d+/);
        $('#ddGoals' + id + '_option').hide(); 
        $('#ddGoalsUndo' + id + '_option').show();   
        
        Pred.SavePrediction(id);
    }
    
    function HideGoalDD()
    {
        var id = $(this).attr('id').match(/\d+/);
        $('#ddGoals' + id + '_option').show();     
        $('#ddGoalsUndo' + id + '_option').hide();   
        
        Pred.SavePrediction(id);
    }
    
    function ShowScorerDD()
    {
        var id = $(this).attr('id').match(/\d+/);
        $('#ddScorers' + id + '_option').hide(); 
        $('#ddScorersUndo' + id + '_option').show();           
        
        Pred.SavePrediction(id);
    }
    
    function HideScorerDD()
    {
        var id = $(this).attr('id').match(/\d+/);
        $('#ddScorers' + id + '_option').show();     
        $('#ddScorersUndo' + id + '_option').hide();       
        
        Pred.SavePrediction(id);
    }    
    
}


Pred.InitPredLocks = function()
{
    for (var p = 1; p <= 8; p ++)
    {
        // the overlay div prevents the controls from being in focus, thus disabling them
        
        var backTransp = 'rgba(211, 211, 211, 0.4)';            // lightgrey
        var myLinGrad = 'repeating-linear-gradient(45deg, \
            rgba(102, 102, 102, 0.8) 0px, rgba(102, 102, 102, 0.8) 10px, \
            transparent 10px, transparent 20px )';
        
        $('#goal' + p + '_overlay').css('background', backTransp);
        $('#goal' + p + '_overlay').css('background-image', myLinGrad);
        $('#goal' + p + '_overlay').show();
        
        $('#scorer' + p + '_overlay').css('background-color', backTransp);
        $('#scorer' + p + '_overlay').css('background-image', myLinGrad);
        $('#scorer' + p + '_overlay').show();
    }
}


Pred.DisablePrediction = function(p_no)
{
    $('#openDate' + p_no + '_listing').parent().parent().addClass('format_disable');
    $('#closeDate' + p_no + '_listing').parent().parent().addClass('format_disable');
    $('#primary' + p_no + '_row').addClass('format_disable');
    $('#secondChance' + p_no + '_row').addClass('format_disable');
    $('#saveNpoints' + p_no + '_row').addClass('format_disable');
}


Pred.EnablePrediction = function(p_no)
{
    $('#openDate' + p_no + '_listing').parent().parent().removeClass('format_disable');
    $('#closeDate' + p_no + '_listing').parent().parent().removeClass('format_disable');
    $('#primary' + p_no + '_row').removeClass('format_disable');
    $('#secondChance' + p_no + '_row').removeClass('format_disable');
    $('#saveNpoints' + p_no + '_row').removeClass('format_disable');
}


Pred.DisplayPrediction = function(p_pred, p_no, p_abilsOwned, p_abilsUsedRound)
{
    var abilsUsed = p_pred.abilsUsed;
    
    // set the abilities owned in past and future to 0 so that they don't display 
    
    if (Pred.PERIOD != Period_Enum.Current)
        p_abilsOwned = {
            'goalsG': {'uses': 0},
            'scorersG': {'uses': 0},
            'secondChance': {'uses': 0},
            'doubleDown': {'uses': 0},
            'clubFav': {'uses': 0},            
        }
    
    // closure functions calls
    
    DisplayGeneral();
    
    DisplayResult();
    
    DisplayGoalsGuess();
    
    DisplayScorersGuess();
    
    // closure function definitions
    
    function DisplayGeneral()
    {   
        var openDate = Date.parseString(p_pred.open_date.substring(0,16), "yyyy-MM-dd HH:mm");
        var closeDate = Date.parseString(p_pred.close_date.substring(0,16), "yyyy-MM-dd HH:mm");
        var endDate = new Date(closeDate.getTime()).add('m', 150);       // 150 min = 2:30 hrs
        
        var dateFmt = "E HH:mm";
        if (Pred.PERIOD != Period_Enum.Current)
            dateFmt = "NNN d, HH:mm";
        
        $('#openDate' + p_no + '_listing').text(openDate.format(dateFmt));
        $('#closeDate' + p_no + '_listing').text(closeDate.format(dateFmt));
        
        
        if (Pred.PERIOD == Period_Enum.Prev)
        {
            DisplayPoints();
            Pred.DisablePrediction(p_no);
        }
        
        else if (Pred.PERIOD == Period_Enum.Current)
        {
            if (Pred.NOW.isBefore(openDate))
            {
                Pred.DisablePrediction(p_no);
            }
            
            else if ( Pred.NOW.isAfter(openDate) && Pred.NOW.isBefore(closeDate) )
            {
                $('#phase' + p_no + '_group').parent().css('background', 'limegreen');
            }
            
            else if ( Pred.NOW.isAfter(closeDate) && Pred.NOW.isBefore(endDate) )
            {
                Pred.DisablePrediction(p_no);
                $('#phase' + p_no + '_group').parent().css('background', 'Chocolate');
            }
            
            else if ( Pred.NOW.isAfter(endDate) )
            {
                DisplayPoints();
                Pred.DisablePrediction(p_no);
            }
        }
        
        else // Period_Enum.Future
        {
            Pred.DisablePrediction(p_no);
        }
    }
    
    
    function DisplayPoints()
    {
        $('#phase' + p_no + '_group').show();
        $('#phase' + p_no + '_listing').text((p_pred.pnts_total ? p_pred.pnts_total : '-'));
        
        $('#resultSave' + p_no + '_group').hide();
        $('#resultPoints' + p_no + '_group').show();
        $('#resultPoints' + p_no + '_normal').text('Points: ' + (p_pred.pnts_result ? p_pred.pnts_result : '-'));
        
        $('#goalsSave' + p_no + '_group').hide();
        $('#goalsPoints' + p_no + '_group').show();
        $('#goalsPoints' + p_no + '_normal').text('Points: ' + (p_pred.pnts_goals ? p_pred.pnts_goals : '-'));
        
        $('#scorersSave' + p_no + '_group').hide();
        $('#scorersPoints' + p_no + '_group').show();
        $('#scorersPoints' + p_no + '_normal').text('Points: ' + (p_pred.pnts_scorers ? p_pred.pnts_scorers : '-'));
    }
    
    
    function DisplayResult()
    {
        // results guess
        
        if (!p_pred.result || p_pred.result == 0)
            $('#result' + p_no + '_Abstain').prop('checked', true);
        else if (p_pred.result == 1)
            $('#result' + p_no + '_HomeWin').prop('checked', true);
        else if (p_pred.result == 2)
            $('#result' + p_no + '_AwayWin').prop('checked', true);
        else if (p_pred.result == 3)
            $('#result' + p_no + '_Tie').prop('checked', true);
        
        // ability: second chance
        
        if (abilsUsed && abilsUsed.secondChance && 'result' in abilsUsed.secondChance)      // "result in" is true when result=0
        {
            if (abilsUsed.secondChance.result == 0)
                $('#resultSC' + p_no + '_Abstain').prop('checked', true);
            else if (abilsUsed.secondChance.result == 1)
                $('#resultSC' + p_no + '_HomeWin').prop('checked', true);
            else if (abilsUsed.secondChance.result == 2)
                $('#resultSC' + p_no + '_AwayWin').prop('checked', true);
            else if (abilsUsed.secondChance.result == 3)
                $('#resultSC' + p_no + '_Tie').prop('checked', true);
            
            $('#scResult' + p_no + '_option').hide();
            $('#scResultUndo' + p_no + '_option').show();
            $('#secondChance' + p_no + '_row').show();
            $('#resSC' + p_no + '_block').show();
        }
        else if (p_abilsOwned.secondChance.uses > p_abilsUsedRound.secondChance)
        {
            $('#scResult' + p_no + '_option').show();
        }
        else 
        {
            $('#scResult' + p_no + '_option').hide();
        }
        
        // ability: double down
        
        if (abilsUsed && abilsUsed.doubleDown && 'result' in abilsUsed.doubleDown)
        {
            $('#ddResult' + p_no + '_option').hide(); 
            $('#ddResultUndo' + p_no + '_option').show();
        }
        else if (p_abilsOwned.doubleDown.uses > p_abilsUsedRound.doubleDown)
        {
            $('#ddResult' + p_no + '_option').show();
        }
        else 
        {
            $('#ddResult' + p_no + '_option').hide();
        }
        
        // club favorite: show all three guesses here
        // use visibility css (as opposed to display none) so that the column space is always there
        
        var homeClub = $('#homeClub' + p_no + '_normal').text();    
        var awayClub = $('#awayClub' + p_no + '_normal').text();
        
        if ([homeClub, awayClub].indexOf(p_abilsOwned.clubFav.club) >= 0) 
        {
            $('#cfResult' + p_no + '_option').css('visibility', 'visible');  
            $('#cfGoals' + p_no + '_option').css('visibility', 'visible');
            $('#cfScorers' + p_no + '_option').css('visibility', 'visible');
        }
    }
    
    
    function DisplayGoalsGuess()
    {
        // unlock and guess values
        
        if (abilsUsed && abilsUsed.goalsG)
        {
            $('#goalsHm' + p_no + '_select option[value="' +
                (p_pred.goals_home != null ? p_pred.goals_home : '*') + '"]'
                ).prop('selected', true);
            $('#goalsAw' + p_no + '_select option[value="' +
                (p_pred.goals_away != null ? p_pred.goals_away : '*') + '"]'
                ).prop('selected', true);
            
            $('#goal' + p_no + '_overlay').hide();
            $('#goalsUnlock' + p_no + '_option').hide();
            $('#goalsLock' + p_no + '_option').show();
        }
        else if (p_abilsOwned.goalsG.uses > p_abilsUsedRound.goalsG)
        {
            $('#goalsUnlock' + p_no + '_option').show();   
        }
        else
        {
            $('#goalsUnlock' + p_no + '_option').hide();       
        }
        
        // second guess
        
        if (abilsUsed && abilsUsed.secondChance && 'goals' in abilsUsed.secondChance)
        {
            var gH = abilsUsed['secondChance']['goals']['home'];
            var gA = abilsUsed['secondChance']['goals']['away'];
            
            $('#goalsHmSC' + p_no + '_select option[value="' + (gH != null ? gH : '*') + '"]'
                ).prop('selected', true);
            $('#goalsAwSC' + p_no + '_select option[value="' + (gA != null ? gA : '*') + '"]'
                ).prop('selected', true);
            
            $('#scGoals' + p_no + '_option').hide();
            $('#scGoalsUndo' + p_no + '_option').show();
            $('#secondChance' + p_no + '_row').show();
            $('#goalSC' + p_no + '_block').show();
        }
        else if (p_abilsOwned.secondChance.uses > p_abilsUsedRound.secondChance)
        {
            $('#scGoals' + p_no + '_option').show();
        }
        else 
        {
            $('#scGoals' + p_no + '_option').hide();
        }
        
        // double down
        
        if (abilsUsed && abilsUsed.doubleDown && abilsUsed.doubleDown.goals)
        {
            $('#ddGoals' + p_no + '_option').hide(); 
            $('#ddGoalsUndo' + p_no + '_option').show();   
        }
        else if (p_abilsOwned.doubleDown.uses > p_abilsUsedRound.doubleDown)
        {
            $('#ddGoals' + p_no + '_option').show();
        }
        else
        {
            $('#ddGoals' + p_no + '_option').hide();
        }
        
        // club favorite is at result guess
    }
    
    
    function DisplayScorersGuess()
    {
        // unlock scorers guess
        
        if (abilsUsed && abilsUsed.scorersG)
        {
            $('#scorersHm' + p_no + '_text').val(p_pred.scorer_home);
            $('#scorersAw' + p_no + '_text').val(p_pred.scorer_away);
            
            $('#scorer' + p_no + '_overlay').hide();
            $('#scorersUnlock' + p_no + '_option').hide();
            $('#scorersLock' + p_no + '_option').show();    
        }
        else if (p_abilsOwned.scorersG.uses > p_abilsUsedRound.scorersG)
        {
            $('#scorersUnlock' + p_no + '_option').show();
        }
        else
        {
            $('#scorersUnlock' + p_no + '_option').hide();
        }
        
        // second chance
        
        if (abilsUsed && abilsUsed.secondChance && abilsUsed.secondChance.scorers)
        {
            $('#scorersHmSC' + p_no + '_text').val(abilsUsed['secondChance']['scorers']['home']);
            $('#scorersAwSC' + p_no + '_text').val(abilsUsed['secondChance']['scorers']['away']);
            
            $('#scScorers' + p_no + '_option').hide();
            $('#scScorersUndo' + p_no + '_option').show();
            $('#secondChance' + p_no + '_row').show();
            $('#scorerSC' + p_no + '_block').show();
        }
        else if (p_abilsOwned.secondChance.uses > p_abilsUsedRound.secondChance)
        {
            $('#scScorers' + p_no + '_option').show();
        }
        else
        {
            $('#scScorers' + p_no + '_option').hide();
        }
        
        // double down
        
        if (abilsUsed && abilsUsed.doubleDown && abilsUsed.doubleDown.scorers)
        {
            $('#ddScorers' + p_no + '_option').hide(); 
            $('#ddScorersUndo' + p_no + '_option').show();           
        }
        else if (p_abilsOwned.doubleDown.uses > p_abilsUsedRound.doubleDown)
        {
            $('#ddScorers' + p_no + '_option').show();
        }
        else 
        {
            $('#ddScorers' + p_no + '_option').hide();
        }
        
        // club favorite is at result guess
    }
    
}


Pred.SavePrediction = function(id)
{    
    $("body").css("cursor", "wait");
    
    // weak get the game id, UI can get hacked
    // but server checks for prediction window and abilities used, so nothing to gain by hacking UI
    
    var gameid = $('#gid' + id + '_listing').text();
    var pred_dx = Pred.GetMatchingPred(gameid);
    pred_dx['abilsUsed'] = {};
    var abilsUsed = pred_dx['abilsUsed'];
    
    
    // get result guess
    
    var resultOpt = $("input[name=result" + id + "]").filter(":checked").val();
    switch(resultOpt) {
        case "HomeWin":     pred_dx.result = 1; break;
        case "AwayWin":     pred_dx.result = 2; break;
        case "Tie":         pred_dx.result = 3; break;
        default:            pred_dx.result = 0; break;
    }
    
    if ( $('#scResultUndo' + id + '_option').is(':visible') )
    {
        if ( !('secondChance' in abilsUsed) )
            abilsUsed.secondChance = {};
        
        var resultOpt = $('input[name=resultSC' + id + ']').filter(':checked').val();
        switch(resultOpt) {
            case 'HomeWin':     abilsUsed.secondChance.result = 1; break;
            case 'AwayWin':     abilsUsed.secondChance.result = 2; break;
            case 'Tie':         abilsUsed.secondChance.result = 3; break;
            default:            abilsUsed.secondChance.result = 0; break;
        }
    }
    
    if ( $('#ddResultUndo' + id + '_option').is(':visible') )
    {
        if ( !('doubleDown' in abilsUsed) )
            abilsUsed.doubleDown = {};
            
        abilsUsed.doubleDown.result = "used";
    }
    
    if ( $('#cfResult' + id + '_option').css('visibility') == 'visible' )
    {
        abilsUsed.clubFav = "used";
    }
    
    
    // get goals guess

    if ( $('#goalsLock' + id + '_option').is(":visible") )
    {   
        var goalsHome = $('#goalsHm' + id + '_select option:selected').text();
        var goalsAway = $('#goalsAw' + id + '_select option:selected').text();    
        pred_dx['goals_home'] = ( goalsHome == "*" ? null : goalsHome );
        pred_dx['goals_away'] = ( goalsAway == "*" ? null : goalsAway );
        
        abilsUsed['goalsG'] = "used";        
    }
    
    if ( $('#scGoalsUndo' + id + '_option').is(":visible") )
    {   
        if ( !('secondChance' in abilsUsed) )
            abilsUsed.secondChance = {};
            
        var goalsHome = $('#goalsHmSC' + id + '_select option:selected').text();
        var goalsAway = $('#goalsAwSC' + id + '_select option:selected').text();    
        abilsUsed.secondChance.goals = {};
        abilsUsed.secondChance.goals.home = ( goalsHome == '*' ? null : goalsHome );
        abilsUsed.secondChance.goals.away = ( goalsAway == '*' ? null : goalsAway );
    }
    
    if ( $('#ddGoalsUndo' + id + '_option').is(":visible") )
    {
        if ( !('doubleDown' in abilsUsed) )
            abilsUsed.doubleDown = {};
        
        abilsUsed.doubleDown.goals = "used";
    }
        
    
    // get scorers guess
    
    if ( $('#scorersLock' + id + '_option').is(":visible") )
    {   
        var scorerHome = $('#scorersHm' + id + '_text').val();
        var scorerAway = $('#scorersAw' + id + '_text').val();
        pred_dx.scorer_home = ( scorerHome == '' ? null : scorerHome );
        pred_dx.scorer_away = ( scorerAway == '' ? null : scorerAway );
        
        abilsUsed['scorersG'] = "used";        
    }
    
    if ( $('#scScorersUndo' + id + '_option').is(":visible") )
    {
        if ( !('secondChance' in abilsUsed) )
            abilsUsed.secondChance = {};
        
        var scorerHome = $('#scorersHmSC' + id + '_text').val();
        var scorerAway = $('#scorersAwSC' + id + '_text').val();
        abilsUsed.secondChance.scorers = {};
        if (scorerHome) 
            abilsUsed.secondChance.scorers.home = scorerHome;
        else if (scorerAway)
            abilsUsed.secondChance.scorers.away = scorerAway;
    }
    
    if ( $('#ddScorersUndo' + id + '_option').is(":visible") )
    {
        if ( !('doubleDown' in abilsUsed) )
            abilsUsed.doubleDown = {};
        
        abilsUsed.doubleDown.scorers = "used";
    }
    
    
    // send the ajax
    
    var pred_st = JSON.stringify(pred_dx);         // cl(pred_dx);
    
    $.ajax({
        type: 'POST',
        url: '/prediction/universal_jx/update_prediction/',
        data: {'pred_st': pred_st},
        success: function(p_data) {     //cl(p_data);
            
            Pred.PREDICTIONS = p_data.predictions;
            Pred.NOW = Date.parseString(p_data.now_dt.substring(0,16), "yyyy-MM-dd HH:mm");
            Pred.SetCurrentPeriod();
            
            Pred.DisplayAbilities(p_data.abilsOwned, p_data.abilsUsedRound);
            
            for (var p = 1; p <= 8; p ++)
            {
                var gameid = $('#gid' + p + '_listing').text();    if (!gameid) continue;
                var currPred = Pred.GetMatchingPred(gameid);
                Pred.DisplayPrediction(currPred, p, p_data.abilsOwned, p_data.abilsUsedRound)
                Pred.DisplayStoreLink(p, p_data.abilsOwned, p_data.abilsUsedRound);
            }
            
            $('#resultError' + id + '_group').hide();
            $('#resultError' + id + '_normal').text("");
            $('#goalsError' + id + '_group').hide();
            $('#goalsError' + id + '_normal').text("");
            $('#scorersError' + id + '_group').hide();
            $('#scorersError' + id + '_normal').text("");
        }, 
        error: function(p_err) {     //cl(p_err);
            // client error
            if (p_err.status >= 400 & p_err.status <= 499) {
                $('#scorersError' + id + '_group').show();
                var jError = $.parseJSON(p_err.responseText);
                cl(jError);
                $('#scorersError' + id + '_normal').text(jError.saveRes);
            }
            // server error
            else {
                ErrorToStatus(p_err.responseText, "SavePrediction()", '#preds_status');
            }
        },
        complete : function() {
            $('#resultSave' + id + '_button').prop('disabled', true);
            $('#goalsSave' + id + '_button').prop('disabled', true);
            $('#scorersSave' + id + '_button').prop('disabled', true);
            $('body').css('cursor', 'default');
        }
    });
    
}


Pred.RefreshPage = function(p_round)
{
    $("body").css("cursor", "wait");    
    
    Pred.ResetPage();
    
    $.ajax({
        url: '/prediction/universal_jx/get_predictions/',
        data: {'round': p_round},
        success: function(p_data) {     cl(p_data);
            
            Pred.GAMES = p_data.fixture;
            Pred.PREDICTIONS = p_data.predictions;
            Pred.NOW = Date.parseString(p_data.now_dt.substring(0,16), "yyyy-MM-dd HH:mm");
            Pred.SetCurrentPeriod();
            
            Pred.DisplayAbilities(p_data.abilsOwned, p_data.abilsUsedRound, USER);
            Pred.DisplayCalendar();
            
            for (var p = 1; p <= 8; p ++)
            {
                var game = Pred.GAMES[p -1];
                var pred = Pred.GetMatchingPred(game.gameid);
                
                Pred.DisplayGameValues(game, p);
                Pred.DisplayPrediction(pred, p, p_data.abilsOwned, p_data.abilsUsedRound);
                Pred.DisplayStoreLink(p, p_data.abilsOwned, p_data.abilsUsedRound);
            }
        }, 
        error: function(p_err) {     //cl(p_err);
            ErrorToStatus(p_err.responseText, "RefreshPage()", '#options_status');
        },
        complete : function() {
            $('body').css('cursor', 'default');
        }
    });
}


Pred.ResetPage = function(p_round)
{
    $('#abilities_table').html(null);
    
    for (var p = 1; p <= 8; p++)
    {
        Pred.ResetGame(p);
        Pred.ResetPred(p);
        Pred.EnablePrediction(p);
    }
    
    Pred.InitPredLocks();
}


Pred.ResetGame = function(p_no)
{
    $('#gid' + p_no + '_listing').text("");        
    $('#date' + p_no + '_listing').text("");
    
    var path = '/static/club_images/_club logo.png'; 
    $('#homeLogo' + p_no + '_image').attr('src', path); 
    $('#homeClub' + p_no + '_normal').text("");
    $('#homeGoals' + p_no + '_normal').text("-");
    $('#homeScorers' + p_no + '_normal').html(""); 
    
    $('#awayLogo' + p_no + '_image').attr('src', path);
    $('#awayClub' + p_no + '_normal').text("");
    $('#awayGoals' + p_no + '_normal').text("-");
    $('#awayScorers' + p_no + '_normal').html("");    
}


Pred.ResetPred = function(p_no)
{
    $('#phase' + p_no + '_group').hide();
    $('#phase' + p_no + '_listing').text("");
    $('#phase' + p_no + '_group').parent().css('background', 'white');
    
    $('#openDate' + p_no + '_listing').text("");
    $('#closeDate' + p_no + '_listing').text("");
    
    $('#result' + p_no + '_Abstain').prop('checked',true);
    $('#resultSC' + p_no + '_Abstain').prop('checked',true);
    
    $('#goalsHm' + p_no + '_select').val($('#goalsHm' + p_no + '_select option:first').val());
    $('#goalsAw' + p_no + '_select').val($('#goalsAw' + p_no + '_select option:first').val());
    $('#goalsHmSC' + p_no + '_select').val($('#goalsHmSC' + p_no + '_select option:first').val());
    $('#goalsAwSC' + p_no + '_select').val($('#goalsAwSC' + p_no + '_select option:first').val());
    
    $('#scorersHm' + p_no + '_text').val(null);
    $('#scorersAw' + p_no + '_text').val(null);
    $('#scorersHmSC' + p_no + '_text').val(null);
    $('#scorersAwSC' + p_no + '_text').val(null);
    
        
    $('#resultSave' + p_no + '_group').show();
    $('#resultPoints' + p_no + '_group').hide();
    $('#resultError' + p_no + '_group').hide();
    $('#resultPoints' + p_no + '_normal').text(null);
    $('#resultError' + p_no + '_normal').text(null);
    
    $('#goalsSave' + p_no + '_group').show();
    $('#goalsPoints' + p_no + '_group').hide();
    $('#goalsError' + p_no + '_group').hide();    
    $('#goalsPoints' + p_no + '_normal').text(null);
    $('#goalsError' + p_no + '_normal').text(null);
    
    $('#scorersSave' + p_no + '_group').show();
    $('#scorersPoints' + p_no + '_group').hide();
    $('#scorersError' + p_no + '_group').hide();    
    $('#scorersPoints' + p_no + '_normal').text(null);
    $('#scorersError' + p_no + '_normal').text(null);
    
    
    $('#secondChance' + p_no + '_row').hide();
    
    $('#scResult' + p_no + '_option').hide();
    $('#scResultUndo' + p_no + '_option').hide();
    $('#ddResult' + p_no + '_option').hide();
    $('#ddResultUndo' + p_no + '_option').hide();
    $('#cfResult' + p_no + '_option').css('visibility', 'hidden');
    
    $('#goalsUnlock' + p_no + '_option').hide();
    $('#goalsLock' + p_no + '_option').hide();
    $('#scGoals' + p_no + '_option').hide();
    $('#scGoalsUndo' + p_no + '_option').hide();
    $('#ddGoals' + p_no + '_option').hide();
    $('#ddGoalsUndo' + p_no + '_option').hide();
    $('#cfGoals' + p_no + '_option').css('visibility', 'hidden');
    
    $('#scorersUnlock' + p_no + '_option').hide();
    $('#scorersLock' + p_no + '_option').hide();
    $('#scScorers' + p_no + '_option').hide();
    $('#scScorersUndo' + p_no + '_option').hide();
    $('#ddScorers' + p_no + '_option').hide();
    $('#ddScorersUndo' + p_no + '_option').hide();
    $('#cfScorers' + p_no + '_option').css('visibility', 'hidden');
}


Pred.DisplayStoreLink = function(p_no, p_abilsOwned, p_abilsUsedRound)
{
    //cl("have " + p_abilsOwned.goalsG.uses + " used " + p_abilsUsedRound.goalsG)
    
    var overlayId = '#goal{0}_overlay'.format(p_no);      // cl(overlayId);
    $(overlayId).off('mouseenter mouseleave');
    
    if (p_abilsOwned.goalsG.uses == p_abilsUsedRound.goalsG)
    {
        var html = '<div id="storeG{0}_group" class="store_parent" style="display: none;">        \
                        <div class="store_child">           \
                                                            \
                            <div class="display_table">             \
                                <div class="display_row">       \
                                    <div class="display_cellM">     \
                                        <span style="color: black; ">Unlock With </span>    \
                                    </div>      \
                                    <div class="display_cellM" style="min-width: 30px;">        \
                                        <i class="fa fa-diamond fa-lg icon_exDiamond" style="padding-left: 4px;"></i>     \
                                    </div>      \
                                </div>          \
                            </div>              \
                                                \
                        </div>          \
                    </div> '.format(p_no);
        
        $(overlayId).html(html);
        
        $(overlayId).click(function() {
            var host = window.location.hostname;
            var page = '/central/store/';
            var url = "http://{0}{1}".format(host, page);
            //cl(url);
            window.location = url;
        });
        
        $(overlayId).hover(function() {
            var htmlID = $(this).attr('id');     
            var id = htmlID.match(/\d+/)[0];      
            var storeId = '#storeG{0}_group'.format(id);
            
            $(storeId).slideToggle();
        });
    }
    
    
    var overlayId = '#scorer{0}_overlay'.format(p_no);      // cl(overlayId);
    $(overlayId).off('mouseenter mouseleave');
    
    if (p_abilsOwned.scorersG.uses == p_abilsUsedRound.scorersG)
    {
        var html = '<div id="storeS{0}_group" class="store_parent" style="display: none;">        \
                        <div class="store_child">           \
                                                            \
                            <div class="display_table">             \
                                <div class="display_row">       \
                                    <div class="display_cellM">     \
                                        <span style="color: black; ">Unlock With </span>    \
                                    </div>      \
                                    <div class="display_cellM" style="min-width: 30px;">        \
                                        <i class="fa fa-diamond fa-lg icon_exDiamond" style="padding-left: 4px;"></i>     \
                                    </div>      \
                                </div>          \
                            </div>              \
                                                \
                        </div>          \
                    </div> '.format(p_no);
        
        $(overlayId).html(html);
        
        $(overlayId).click(function() {
            var host = window.location.hostname;
            var page = '/central/store/';
            var url = "http://{0}{1}".format(host, page);
            //cl(url);
            window.location = url;
        });
        
        $(overlayId).hover(function() {
            var htmlID = $(this).attr('id');     
            var id = htmlID.match(/\d+/)[0];      
            var storeId = '#storeS{0}_group'.format(id);
            
            $(storeId).slideToggle();
        });
    }
    
}


