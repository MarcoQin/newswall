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
        $.postJSON("/updates","test", function(response) {
        try {
//        alert('success get update');
//        alert(response);
        console.info(response);
            updater.newNews(response);
        } catch (e) {
            updater.onError();
            return;
        }
        updater.errorSleepTime = 500;
        window.setTimeout(updater.poll, 0);
    });
    },

    onSuccess: function(response) {
        try {
//        alert('success get update');
        alert(response);
//        console.info(response);
            updater.newNews(response);
        } catch (e) {
            updater.onError();
            return;
        }
        updater.errorSleepTime = 500;
        window.setTimeout(updater.poll, 0);
    },

    onError: function(response) {
//        alert('error!');
        updater.errorSleepTime *= 2;
        console.log("Poll error; sleeping for", updater.errorSleepTime, "ms");
        window.setTimeout(updater.poll, updater.errorSleepTime);
    },

    newNews: function(response) {
//        alert('push news');
        updater.showNews(response);
    },

    showNews: function(newsblock) {
//    var newsblock = newsblock;
//        console.info(newsblok);
        $("#newswall").prepend(newsblock);
        $('#newswall').masonry('reload');
        window.setTimeout(updater.poll, 0);
    }
};
