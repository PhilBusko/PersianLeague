/*******************************************************************************
MEMBERS/STATIC/MEMBERS.js
*******************************************************************************/

var Messages = Messages || {};

Messages.USER = "";
Messages.URL_OPENMSG = "";
Messages.URL_OPENCONVO = ""; 
Messages.URL_DELETECONVO = ""; 
Messages.URL_WRITEMSG = ""; 
Messages.URL_REPLYMSG = ""; 
Messages.URL_GETINBOX = ""; 
Messages.OPEN_MSGID = -1;
Messages.OPEN_THDID = -1;


Messages.InitControls = function()
{
    // messages area
    
    $("#close_clicker").click(function() {
        Messages.CloseMessages();
    });
    
    $("#reply_clicker").click(function() {
        $("#spacerComp_block").show();
        $("#compose_block").show("slow");
        CreateTooltip('#close_clicker', "Close & Discard Draft");
    });
    
    $("#delete_clicker").click(function() {
        Messages.DeleteOpenConv();
        Messages.CloseMessages();
    });
    
    CreateTooltip('#delete_clicker', "Delete", 'top');
    
    // on click of dynamic html must be bound to static html
    $("#messages_list").on("click", "#topRow_block", function() {
        var msgBlock = $(this).parent();   
        var collapBlock = msgBlock.find("#collapse_block");          
        collapBlock.slideToggle("fast");
    });
    
    // compose area
    
    $("#recOpts_ToUser").click();
    
    $("#send_button").click( function() {
        var isReply = $("#toUser_text").prop("disabled");
        
        if (!isReply)
            Messages.WriteMessage();
        else
            Messages.ReplyMessage();
    });
    
}


Messages.SetDeluxeInbox = function(p_messages)
{   
    var tableId = '#inbox_table';
    
    var table = $(tableId).DataTable( {
        data: p_messages,
        aoColumns: [
            {
                mData: "sender",
                sClass: "font_bold ",
            },
            {
                mData: "subject",
                mRender: function (data, type, full) {
                    html = '                                    \
                            <div class="{0}">                    \
                                <span class="format_fixline">{1}</span>      \
                            </div>                              \
                    '.format( ( full.read_at ? "format_cpointer" : "font_link" ),
                             full.subject ); 
                    return html;
                },
            }, 
            {
                mData: "sent_at",
                sClass: "format_center ",
                mRender: function (data, type, full) {
                    var sent = Date.parseString(data.substring(0,16), "yyyy-MM-dd HH:mm");
                    var now = new Date();
                    if (now.toDateString() === sent.toDateString())
                        var frmt = sent.format("HH:mm");
                    else
                        var frmt = sent.format("NNN d");
                    return frmt;
                },   
            },
            {
                mData: null,
                sClass: "format_center",
                mRender: function (data, type, full) {
                    html = '                                                                \
                            <div id="delete{0}_icon" class="inner_margin2 icon_button">     \
                                <i class="fa {1} fa-lg" style="color: {2}; cursor: pointer;"></i>            \
                            </div>                                                          \
                    '.format(full.id, "fa-trash", "#647382"); 
                    return html;
                },
            },
        ], 
        bSort: false,
        scrollCollapse: true,
        paging: true,
        bFilter: true,
        bInfo: true,
        bDestroy: true,                 // necessary to refresh the data
        fnRowCallback: function( nRow, aData, iDisplayIndex, iDisplayIndexFull ) {            
            // Row click
            $(nRow).on('click', function() {
            });
            
            // Cell click
            $('td', nRow).on('click', function() {
                var iCol = $(this).index();
                if (iCol == 1)
                {
                    if (aData.thread_id && aData.thread_id != 'None')
                        Messages.OpenConversation(aData.thread_id);
                    else 
                        Messages.OpenMessage(aData.id);
                    
                    var subject_jq = $(this).find('.font_link');
                    subject_jq.removeClass('font_link');
                    subject_jq.addClass('format_cpointer');
                }
                if (iCol == 3)
                {
                    if (aData.thread_id && aData.thread_id != 'None')
                        Messages.DeleteInboxConvo(null, aData.thread_id);
                    else 
                        Messages.DeleteInboxConvo(aData.id, null);
                }
            });
        },
        fnDrawCallback: function() {
            // remove headers
            $(tableId + ' thead').remove();
        },
        initComplete: function() {
            PostDraw();
        },
    } );
    
    $(tableId).on( 'draw.dt', function () {
        PostDraw();
    } );
    
    function PostDraw()
    {
        $.each(p_messages, function(idx, msg) {
            var ttID = '#delete{0}_icon'.format(msg.id);
            CreateTooltip(ttID, "Delete");
        });
    }
    
    var html = '<div class="outer_padding2" style="clear:both; color:black;">           \
        * Messages that are older than 2 weeks are deleted at midnight everyday.        \
        </div>';
    $('#inbox_table_wrapper').append(html); 
}


Messages.OpenMessage = function(p_msgID)
{
    $("#messages_list").html(null);
    $("#messages_status").html(null);
    
    $.ajax({
        url: Messages.URL_OPENMSG, 
        data: { 'msgID': p_msgID },
        success: function(p_data) {         cl(p_data);
            var message = p_data.message;
            $('#m2_strong').text(message.subject);
            $('#msgCtrl_group').show();
            $('#messages_list').html(null);
            $('#messages_list').show();
            
            Messages.DisplayMessage(message, 0);
            Messages.PrepareReply(message);
            
            Messages.OPEN_MSGID = message.id;
            Messages.OPEN_THDID = -1;
            
            Messages.UpdateNotifier(p_data.unreadCnt);      // don't implement for admin messages
        },
        error: function(p_err) {
            ErrorToStatus(p_err.responseText, "OpenMessage()", '#messages_status');
        } 
    });
}


Messages.OpenConversation = function(p_thdID)
{
    $("#messages_list").html(null);
    $("#messages_status").html(null);
    
    $.ajax({
        url: Messages.URL_OPENCONVO, 
        data: { 'thdID': p_thdID },
        success: function(p_data) {
            var messages = p_data.messages;
            var subj = messages[messages.length-1].subject;
            $('#m2_strong').text(subj);
            $('#msgCtrl_group').show();
            $('#messages_list').html(null);
            $('#messages_list').show();
            
            $.each(messages, function(index, value) {
                var order = 2;
                if (index == 0)
                    order = 1;
                else if (index == messages.length -1)
                    order = 3;
                Messages.DisplayMessage(value, order);                
            });
            
            var lastMsg = messages[messages.length -1];
            Messages.PrepareReply(lastMsg);
            
            Messages.OPEN_MSGID = -1;
            Messages.OPEN_THDID = lastMsg.thread;
            
            Messages.UpdateNotifier(p_data.unreadCnt);      // don't implement for admin messages
        },
        error: function(p_err) {
            ErrorToStatus(p_err.responseText, "OpenConversation()", '#messages_status');
        } 
    });
}


Messages.DeleteInboxConvo = function(p_msgID, p_thdID)
{   
    var dConv = {};
    if (p_msgID)
        dConv['pks'] = [p_msgID,];
    else
        dConv['tpks'] = [p_thdID,];
    
    $.ajax({
        type: 'POST',
        url: Messages.URL_DELETECONVO, 
        data: dConv,
        success: function(p_data) {
            Messages.LoadInbox();
        },
        error: function(p_err) {
            ErrorToStatus(p_err.responseText, "DeleteInboxConvo()", '#messages_status');
        } 
    });
}


Messages.DisplayMessage = function(p_msg, p_order)
{
    // order = 0: single message
    // order = 1: first in conversation
    // order = 2: middle of conversation
    // order = 3: last in conversation
    
    CreateTooltip('#close_clicker', "Close", 'top');  
    
    var template = $("#message_template").clone();
    
    template.find("#from_listing").text(p_msg.sender);
    var dt = Date.parseString(p_msg.sent_at.substring(0,16), "yyyy-MM-dd HH:mm");
    template.find("#sent_listing").text(dt.format("MM-dd HH:mm"));  
    template.find("#to_listing").text(p_msg.recipient);
    if (p_msg.read_at)
    {
        var dt = Date.parseString(p_msg.read_at.substring(0,16), "yyyy-MM-dd HH:mm");
        var read = dt.format("MM-dd HH:mm");
    }
    else if (p_msg.recipient == Messages.USER) 
        var read = "Now";
    else
        var read = "Unread";
    template.find("#read_listing").text(read);
    template.find("#subject_normal").text(p_msg.subject);
    
    template.find("#body_normal").html(p_msg.body);          // secure ?
    
    var noReply = (p_msg.replied_at ? p_msg.replied_at.substring(0,10) : "" );
    
    if (p_order == 0)
    {       
        template.find("#topRow_block").removeClass("format_hoverLink");
        var msgBlock = $(this).parent();   
        var collapBlock = msgBlock.find("#collapse_block");     
        collapBlock.prop('id','noCollapse_block');      // doesn't work because it's dynamic html
        
        if (noReply == "1000-01-01")
        {
            CreateTooltip('#reply_clicker', "Reply Unavailable", 'top');
            $('#reply_clicker').off('click');
            $('#replyMsg_icon').css('color', 'grey');   
        }
        else
        {
            CreateTooltip('#reply_clicker', "Reply", 'top');
            $('#reply_clicker').off('click');
            $("#reply_clicker").on("click", function() {
                $("#spacerComp_block").show();
                $("#compose_block").show("slow");
                CreateTooltip('#close_clicker', "Close & Discard Draft", 'top');
            });
            $('#replyMsg_icon').css('color', 'green');
        }
    }
    else if (p_order == 1 || p_order == 2)
    {
        template.find('#collapse_block').hide();        
    }
    else if (p_order == 3)
    {
        if (noReply == "1000-01-01")
        {
            CreateTooltip('#reply_clicker', "Reply Unavailable", 'top');            
            $('#reply_clicker').off('click');
            $('#replyMsg_icon').css('color', 'grey');
        }
        else if (p_msg.sender != Messages.USER)
        {
            CreateTooltip('#reply_clicker', "Reply", 'top');
            $('#reply_clicker').off('click');
            $("#reply_clicker").on("click", function() {
                $("#spacerComp_block").show();
                $("#compose_block").show("slow");
                CreateTooltip('#close_clicker', "Close & Discard Draft");
            });
            $('#replyMsg_icon').css('color', 'green');
        }
        else
        {
            CreateTooltip('#reply_clicker', "Can't reply to own message", 'top');
            $('#reply_clicker').off('click');
            $('#replyMsg_icon').css('color', 'grey');            
        }
    }
    
    var fullH = $("#messages_list").html();
    var filled = template.html();
    $("#messages_list").html(fullH + "" + filled);
}


Messages.PrepareReply = function(p_msg)
{
    $("#compose_block").hide();
    $("#msgType_group").hide();
    $("#msgType_row").hide();
    var recip = (p_msg.sender == Messages.USER ? p_msg.recipient : p_msg.sender );
    $("#toUser_text").val(recip);
    $("#toUser_text").prop("disabled", true);
    $("#subject_text").val(p_msg.subject);
    $("#subject_text").prop("disabled", true);
    $("#msgID_data").text(p_msg.id);
    $("#body_text").val(null);     
    $("#send_normal").empty();
}


Messages.CloseMessages = function()
{
    $("#messages_list").hide();
    $("#compose_block").hide();
    $("#msgCtrl_group").hide();
    
    $("#m2_strong").text("Compose");
    $("#messages_list").empty();
    $("#recOpts_ToUser").click();
    $("#msgType_group").show();
    $("#toUser_text").val(null);
    $("#toUser_text").prop("disabled", false);
    $("#subject_text").val(null);
    $("#subject_text").prop("disabled", false);
    $("#msgID_data").empty();
    $("#body_text").val(null);
    $("#send_normal").empty();
    
    $("#compose_block").show();
}


Messages.WriteMessage = function(args)
{
    var recipients = Messages.GetRecipient();       // must be implemented by each page
    var subject = $('#subject_text').val();
    var body = $('#body_text').val();
    
    if (!recipients) {
        $('#send_normal').text('User: This field is required.');
        return;
    }
    
    if (!subject) {
        $('#send_normal').text('Subject: This field is required.');
        return;
    }
    
    if (!body) {
        $('#send_normal').text('Body: This field is required.');
        return;
    }
    
    var fData = new FormData();
    fData.append('recipients', recipients);
    fData.append('subject', subject);
    fData.append('body', body);
    
    $.ajax({
        type: 'POST',
        url: Messages.URL_WRITEMSG, 
        data: fData, 
        processData: false, 
        contentType: false, 
        success: function(p_data) {  
            $('#toUser_text').val(null);
            $('#subject_text').val(null);
            $('#body_text').val(null);
            $('#send_normal').text(p_data);
        },
        error: function(p_err) {    //cl(p_err.responseText)
            try {
                JsonError(p_err.responseText);
            }
            catch(ex) {
                ErrorToStatus(p_err.responseText, "WriteMessage()", '#messages_status');
            }
        },
        complete: function() {
        }
    });
    
    function JsonError(p_obj)
    {
        var errors = JSON.parse(p_obj);
        var errors2 = JSON.parse(errors);        // not sure why it needs to be called twice
        
        var msg = "Uninitialized Error";
        
        if (errors2.hasOwnProperty('recipients'))
            msg = "User: " + errors2.recipients[0];
        
        else if (errors2.hasOwnProperty('subject'))
            msg = "Subject: " + errors2.subject[0];
        
        $('#send_normal').text(msg);
    }
    
}


Messages.ReplyMessage = function(args)
{
    var recipients = $("#toUser_text").val();
    var subject = $("#subject_text").val();
    var body = $("#body_text").val();
    var message_id = $("#msgID_data").text();    // cl(message_id);
    
    if (!body) {
        $('#send_normal').text("Body: This field is required.");
        return;
    }
    
    var fData = new FormData();
    fData.append('recipients', recipients);
    fData.append('subject', subject);
    fData.append('body', body);
    fData.append('message_id', message_id); 
    
    $.ajax({
        type: 'POST',
        url: Messages.URL_REPLYMSG,
        data: fData, 
        processData: false, 
        contentType: false, 
        success: function(p_data) {  
            $("#toUser_text").val(null);
            $("#subject_text").val(null);
            $("#body_text").val(null);
            $('#send_normal').text(p_data);
            Messages.LoadInbox();
            Messages.CloseMessages();
        },
        error: function(p_err) {    //cl(p_err.responseText)
            try {
                JsonError(p_err.responseText);
            }
            catch(ex) {
                ErrorToStatus(p_err.responseText, "ReplyMessage()", '#messages_status');
            }
        }
    });
    
    function JsonError(p_obj)
    {
        var errors = JSON.parse(p_obj);
        var errors2 = JSON.parse(errors);        // not sure why it needs to be called twice
                
        var msg = "Uninitialized Error";
        
        if (errors2.hasOwnProperty('recipients'))
            msg = "User: " + errors2.recipients[0];
        
        else if (errors2.hasOwnProperty('subject'))
            msg = "Subject: " + errors2.subject[0];
        
        $('#send_normal').text(msg);
    }

}


Messages.DeleteOpenConv = function()
{   
    var dConv = {};
    if (Messages.OPEN_MSGID != -1)
        dConv['pks'] = [Messages.OPEN_MSGID,];
    else
        dConv['tpks'] = [Messages.OPEN_THDID,];
    
    var msgType = 'admin';
    
    $.ajax({
        type: 'POST',
        url: Messages.URL_DELETECONVO,
        data: dConv,
        success: function(p_data) {
            Messages.LoadInbox();
        },
        error: function(p_err) {
            ErrorToStatus(p_err.responseText, "DeleteOpenConv()", '#messages_status');
        } 
    });
}


// deprecate this
// have delete message return new inbox
Messages.LoadInbox = function()
{   
    Messages.OPEN_MSGID = -1;
    Messages.OPEN_THDID = -1;
    
    $.ajax({
        type: 'GET',
        url: Messages.URL_GETINBOX, 
        data: {},
        success: function(p_data) {             //cl(p_data);
            $('#inbox_table').empty();          // destruct the tooltips
            Messages.SetDeluxeInbox(p_data);
        },
        error: function(p_err) {
            ErrorToStatus(p_err.responseText, "LoadInbox()", '#messages_status');
        } 
    });
}





