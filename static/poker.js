/**
 * Created by user on 2016/5/25.
 */
$(document).ready(function() {
    ws = new WebSocket('ws://' + location.hostname + ':' + location.port + location.pathname + '/18653828881/get')
    ws.onopen = function(msg){
    }
    ws.onmessage = function(msg) {
        $("#game").append('<div>'+msg.data+'</div>');
    }

    $("#bank").live("click", function() {
        ws.send(JSON.stringify({"data":{"area":"bank", "count":100}, "type": "bet"}));
        return false;
    });
     $("#player").live("click", function() {
        ws.send(JSON.stringify({"data":{"area":"player", "count":100}, "type": "bet"}));
        return false;
    });
     $("#tie").live("click", function() {
        ws.send(JSON.stringify({"data":{"area":"tie", "count":100}, "type": "bet"}));
        return false;
    });
});
