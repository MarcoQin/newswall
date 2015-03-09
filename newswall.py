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

from tornado.concurrent import Future
from tornado import gen
from tornado.options import define, options, parse_command_line
from apscheduler.schedulers.tornado import TornadoScheduler
from apscheduler.schedulers.background import BackgroundScheduler

from extract import extract, extract_all

define("port", default=9000, help="run on the given port", type=int)
define("debug", default=False, help="run in debug mode")


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
        content = urllib2.urlopen(self.url)
        html = content.read()
        content.close()
        if first:
            self.cache[:] = []
        for block in extract_all('<div class=\\"WB_cardwrap S_bg2 clearfix\\">', '<\\/div>\\t<\\/div>\\n<\\/div>\\n', html):
            user_name = extract('<a class=\\"W_texta W_fb\\" nick-name=\\"', '\\" href=\\"http:\\/\\/weibo.com', block)
            start = '<p class=\\"comment_txt\\" node-type=\\"feed_list_content\\" nick-name=\\"%s\\">' % user_name
            content = extract(start, '<\\/p>', block).replace('\n', '')
            newsid = hashlib.new("md5", content).hexdigest()
            newsblock = dict(user_name=user_name, content=content, id=newsid)
            self.cache.append(newsblock)
            if first:
                self.idpool.append(newsid)
            else:
                self.parse_update(newsblock)

    def parse_update(self, block):
        if block.get('id', None) not in self.idpool:
            logging.info("Get update!")
            self.updatecache.append(block)
            self.idpool.append(block.get('id'))
            self.updatable = True
            self.cache.append(block)
            if len(self.cache) > self.cache_size:
                self.cache = self.cache[-self.cache_size:]


global_news_buffer = NewsBuffer()

scheduler = BackgroundScheduler()


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html", news=[])

    @gen.coroutine
    def post(self):
        query = self.get_argument("q", "zhihu")
        logging.info("Got requests: %s" % query)
        if isinstance(query, unicode):
            query = unicode.encode(query, 'utf-8')
        query = urllib2.quote(query)
        url = "http://s.weibo.com/wb/%s" % query
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
            scheduler.add_job(global_news_buffer.parse_url, 'interval', seconds=30)
            scheduler.start()
        except:
            raise
        news = global_news_buffer.cache
        allnews = ''
        for block in news:
            if block:
                allnews += self.render_string("newsblock.html", news=block)
        allnews = allnews.replace('\n', '')
        allnews = allnews.replace('<\\/a>', '</a>')
        allnews = allnews.replace('<\\/em>', '</em>')
        allnews = allnews.strip()
        allnews = allnews.decode('unicode-escape')
        logging.info("Sendding response!")
        self.write(allnews)


class StatusHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def post(self):
        while True:
            if global_news_buffer.updatable:
                break

        global_news_buffer.updatable = False
        newsblock = global_news_buffer.updatecache
        global_news_buffer.updatecache[:] = []
        allnews = ''
        for block in newsblock:
            if block:
                allnews += self.render_string("newsblock.html", news=block)
        allnews = allnews.replace('\n', '')
        allnews = allnews.replace('<\\/a>', '</a>')
        allnews = allnews.replace('<\\/em>', '</em>')
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