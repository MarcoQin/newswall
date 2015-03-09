$(document).ready(function() {
    if (!window.console) window.console = {};
    if (!window.console.log) window.console.log = function() {};

    $(function() {
        var $container = $('#newswall');
        $container.masonry({
            itemSelector: '.item',
            isAnimated: true,
        });

    });

    $('#postbtn').click(function() {
        newQuery({q: $("#postquery").val()});
        return false;
    });
});


function newQuery(form) {
    $.postJSON("/", form, function(response) {
        updater.showNews(response);
    });
}


jQuery.postJSON = function(url, args, callback) {
    $.ajax({url: url, data: args, dataType: "text", type: "POST",
            success: function(response) {
        if (callback) callback(response);
    }, error: function(response) {
        console.log("ERROR:", response)
    }});
};



var updater = {
    errorSleepTime: 500,
    cursor: null,

    poll: function() {
        $.ajax({url: "/updates", type: "POST", dataType: "text",
                data: '', success: updater.onSuccess,
                error: updater.onError});
    },

    onSuccess: function(response) {
        try {
            updater.newNews(response);
        } catch (e) {
            updater.onError();
            return;
        }
        updater.errorSleepTime = 500;
        window.setTimeout(updater.poll, 0);
    },

    onError: function(response) {
        updater.errorSleepTime *= 2;
        console.log("Poll error; sleeping for", updater.errorSleepTime, "ms");
        window.setTimeout(updater.poll, updater.errorSleepTime);
    },

    newNews: function(response) {
        updater.showNews(response);
    },

    showNews: function(newsblock) {
        $("#newswall").prepend(newsblock);
        $('#newswall').masonry('reload');
        window.setTimeout(updater.poll, 0);
    }
};
