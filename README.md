# newswall
A real-time newswall, getting data from twitter or weibo.

## Description
```
一个实时的新闻墙,给定指定的话题获取新浪微博(或twitter)上对应话题的最新内容。
当微博(或twitter)上的内容更新后，新闻墙这边同步更新。
```

因为是要从新浪或Twitter服务器上获取数据，所以在服务端使用了`apscheduler`模块来进行计划任务，用间隔很短的时间向新浪服务器请求数据，然后对数据进行分析。

遗憾的是搞不到新浪和Twitter的API token，所以在数据请求方面有些问题，达不到“实时推送”的要求。因为不能用这两个服务器的API，所以退而求其次，使用新浪的普通搜索端口”http://s.weibo.com/wb/”。这个端口对搜索频率有很大的限制，所以一定程度上来说，这个服务器并不是“实时”的。但若能够使用API，那直接切换便可以实时推送新浪的更新，也省去了对新浪那不规则的html进行分析了（泪目）。

前端使用了`jQuery`以及`jQuery`的`masonry`（瀑布流）插件。这个插件可以动态地对前端的新闻块儿进行排列，非常好看。

用户在首页输入想要跟踪的话题，后端便开始向新浪搜索接口请求数据，向`scheduler`添加请求函数，定时（理论上以非常短的间隔）向新浪请求数据，用`NewsBuffer`类分析请求到的html，通过`hashlib.md5`模块来筛选出最新且不重复的块儿，然后通过`StatusHandler`向前端推送。用JS捕获后端的response，然后动态地将其插入页面，用`masonry`重排版面，保证最新的消息在最前面显示。
