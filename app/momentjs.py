# -*- coding: utf-8 -*-
from jinja2 import Markup


class Momentjs(object):
    def __init__(self, timestamp):
        self.timestamp = timestamp

    # 把字符串包裹在 Markup 对象里就是告诉 Jinja2 这个字符串是不需要转义的。
    def render(self, format):
        return Markup("<script>\ndocument.write(moment(\"%s\").%s);\n</script>" % (self.timestamp.strftime("%Y-%m-%dT%H:%M:%S Z"), format))

    def format(self, fmt):
        return self.render("format(\"%s\")" % fmt)

    def calendar(self):
        return self.render("calendar()")

    def fromNow(self):
        return self.render("fromNow()")
