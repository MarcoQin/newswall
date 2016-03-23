# -*- coding:utf-8 -*-

__author__ = 'MarcoQin'

import logging
import tornado.escape
import tornado.ioloop
import tornado.web
import os.path
import uuid
import urllib2
import hashlib
import requests

from tornado.concurrent import Future
from tornado import gen
from tornado.options import define, options, parse_command_line
from apscheduler.schedulers.tornado import TornadoScheduler
from apscheduler.schedulers.background import BackgroundScheduler

from extract import extract, extract_all

define("port", default=9000, help="run on the given port", type=int)
define("debug", default=False, help="run in debug mode")

g_start = 0
g_end = 10


class NewsBuffer(object):
    def __init__(self):
        self.cache = []
        self.cache_size = 100
        self.updatable = False
        self.url = ''
        self.updatecache = []
        self.idpool = []

    def parse_url(self, first=False):
        logging.info("Start parsing url")
        #  content = urllib2.urlopen(self.url)
        #  html = content.read()
        #  content.close()
        headers =  {
            'host': 's.weibo.com',
            'connection': 'keep-alive',
            'pragma': 'no-cache',
            'cache_control': 'no-cache',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'upgrade_insecure_requests': '1',
            'user_agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.109 Safari/537.36',
            'referer': 'http://d.weibo.com/102803?topnav=1&mod=logo&wvr=6',
            'accept_encoding': 'gzip, deflate, sdch',
            'accept_language': 'zh-CN,zh;q=0.8,ja;q=0.6,en;q=0.4',
        }
        #  html = requests.get(self.url, headers=headers).text
        print "got html"
        if first:
            self.cache[:] = []
        #  for block in extract_all('<div class=\\"WB_cardwrap S_bg2 clearfix\\" >', '<\\/div>\\t<\\/div>\\n<\\/div>\\n', html):
        global g_start
        global g_end
        for i in range(g_start, g_end):

            #  user_name = extract('<a class=\\"W_texta W_fb\\" nick-name=\\"', '\\" href=\\"http:\\/\\/weibo.com', block)
            user_name = "test%s" % i

            start = '<p class=\\"comment_txt\\" node-type=\\"feed_list_content\\" nick-name=\\"%s\\">' % user_name

            #  content = extract(start, '<\\/p>', block).replace('\n', '')
            content = "hahahahahahahaha%s" % i

            newsid = hashlib.new("md5", content).hexdigest()
            newsblock = dict(user_name=user_name, content=content, id=newsid)
            self.cache.append(newsblock)

            if first:
                self.idpool.append(newsid)
            else:
                print 'parse update'
                self.parse_update(newsblock)
        g_start = g_end
        g_end += 10

    def parse_update(self, block):
        if block.get('id', None) not in self.idpool:
            logging.info("Get update!")
            # print block

            # print '*******',self.updatecache
            self.idpool.append(block.get('id'))
            if not self.updatable:
                self.updatecache[:] = []
            self.updatecache.append(block)
            self.updatable = True
            self.cache.append(block)
            if len(self.cache) > self.cache_size:
                self.cache = self.cache[-self.cache_size:]


global_news_buffer = NewsBuffer()

scheduler = BackgroundScheduler()


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html", news=[])

    # @gen.coroutine
    def post(self):
        query = self.get_argument("q", "zhihu")
        logging.info("Got requests: %s" % query)
        if isinstance(query, unicode):
            query = unicode.encode(query, 'utf-8')
        query = urllib2.quote(query)
        url = "http://s.weibo.com/%s" % query
        logging.info("Get url, parse start!->%s" % url)
        global_news_buffer.url = url
        try:
            if scheduler.running:
                scheduler.shutdown()
            scheduler.remove_all_jobs()
        except:
            pass
        try:
            global_news_buffer.parse_url(first=True)
            logging.info("adding func to scheduler")
            scheduler.add_job(global_news_buffer.parse_url, 'interval', seconds=3)
            scheduler.start()
        except:
            raise
        news = global_news_buffer.cache

        allnews = ''
        for block in news:
                allnews += self.render_string("newsblock.html", news=block)
        allnews = allnews.replace('\n', '')
        allnews = allnews.replace('<\\/a>', '</a>')
        allnews = allnews.replace('<\\/em>', '</em>')
        allnews = allnews.strip()
        allnews = allnews.decode('unicode-escape')
        logging.info("Sendding response!")

        self.write(allnews)
        self.finish()


class StatusHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @gen.coroutine
    def post(self):
        while True:
            if global_news_buffer.updatable:
                break
        print 'going to sending update'

        newsblock = global_news_buffer.updatecache
        global_news_buffer.updatable = False
        print "*************",type(newsblock)
        # global_news_buffer.updatecache[:] = []
        allnews = ''
        for block in newsblock:
            print block
            if block:
                allnews += self.render_string("newsblock.html", news=block)
                print allnews
        allnews = allnews.replace('\n', '')
        allnews = allnews.replace('<\\/a>', '</a>')
        allnews = allnews.replace('<\\/em>', '</em>')
        allnews = allnews.strip()
        allnews = allnews.decode('unicode-escape')
        logging.info("Sendding update!")
        self.write(allnews)
        self.finish()


def main():
    parse_command_line()
    app = tornado.web.Application(
        [
            (r"/", MainHandler),
            (r"/updates", StatusHandler),

        ],
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        debug=options.debug,
    )
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
