# -*- coding: utf-8 -*-

import os
basedir = os.path.abspath(os.path.dirname(__file__))

# 数据库配置
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

CSRF_ENABLED = True  # 配置了启用跨站请求攻击保护
SECRET_KEY = 'you-will-never-guess'  # 当CSRF启用有效时，将生成一个加密的token供表单验证使用

# 一些公共账号服务商提供的openID
OPENID_PROVIDERS = [
    {'name': 'Google', 'url': 'https://www.google.com/accounts/o8/id'},
    {'name': 'Yahoo', 'url': 'https://me.yahoo.com'},
    {'name': 'AOL', 'url': 'http://openid.aol.com/<username>'},
    {'name': 'Flickr', 'url': 'http://www.flickr.com/<username>' },
    {'name': 'MyOpenID', 'url': 'https://www.myopenid.com'}]

# 配置邮件服务器，发送错误日志到邮件
# mail server settings
MAIL_SERVER = 'smtp.qq.com'
MAIL_PORT = 465
MAIL_USE_TLS = False
MAIL_USE_SSL = True
MAIL_USERNAME = "627573954"
MAIL_PASSWORD = "qndlqsxzbfcnbfgb"

# administrator list
ADMINS = ['627573954@qq.com']

# 分页  每页显示的blog数的配置项
POSTS_PER_PAGE = 3

# 全文搜索 配置flask-whooshAlchemy
WHOOSH_BASE = os.path.join(basedir, 'search.db')
MAX_SEARCH_RESULTS = 50   # 搜索结果返回的最大数量

# 添加语言版本
LANGUAGES = {
    'en': 'English',
    'es': 'Español',
    'zh': 'Chinese'
}


