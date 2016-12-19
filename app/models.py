# -*- coding: utf-8 -*-


from app import db, app
from hashlib import md5  # md5加密
import sys

if sys.version_info >= (3, 0):
    enable_search = False
else:
    enable_search = True
    import flask.ext.whooshalchemy as whooshalchemy

ROLE_USER = 0  # 普通用户
ROLE_ADMIN = 1  # 管理员

# 关注者与被关注者的辅助表
followers = db.Table('followers',
                     db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
                     db.Column('followed_id', db.Integer, db.ForeignKey('user.id')))


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    role = db.Column(db.SmallInteger, default=ROLE_USER)
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime)   # 上一次登录
    followed = db.relationship('User',
                               secondary=followers,
                               primaryjoin=(followers.c.follower_id == id),
                               secondaryjoin=(followers.c.followed_id == id),
                               backref=db.backref('followers', lazy='dynamic'),
                               lazy='dynamic')

    def is_authenticated(self):  # 通常这个方法应该返回True，除非对象代表一个由于某种原因没有被认证的用户。
        return True

    def is_active(self):  # 为用户返回True除非用户不是激活的
        return True

    def is_anonymous(self):  # 为那些不被获准登录的用户返回True
        return False

    def get_id(self):      # 为用户返回唯一的unicode标识符
        return unicode(self.id)

    def avatar(self, size):
        # avatar将会返回用户头像图片的地址, 根据你的需要来请求你想要的图片尺寸像素。
        """
        从Gravatar上得到图像图片很简单。你只需要用md5把用户的邮箱hash加密之后合并成上面的那种url形式即可。
        当然你也可以自由选择自 定义图像大小。其中“d=mm”是设置用户在没有Gravatar账号的情况下显示的默认头像。
        “mm”选项会返回一张只有人轮廓的灰色图片，称之为“谜 样人”。而“s=”选项是用来设置返回你给定的图片尺寸像素。
        """
        return 'http://www.gravatar.com/avatar/' + md5(self.email).hexdigest() + '?d=mm&s=' + str(size)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)
            return self

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)
            return self

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    # 通过数据库将查找的被关注者的blog排序  连接，过滤以及排序
    def followed_posts(self):
        return Post.query.join(followers, (followers.c.followed_id == Post.user_id)).filter(followers.c.follower_id == self.id).order_by(Post.timestamp.desc())

    # 通过数据库将查找的该主页用户的所有文章排序
    def get_posts(self):
        return self.posts.filter().order_by(Post.timestamp.desc())

    # 选择唯一用户名
    # 简单的添加一个计数器来生成一个唯一的昵称名
    @staticmethod  # 设为静态方法，该操作不适用于任何类的实例
    def make_unique_nickname(nickname):
        if User.query.filter_by(nickname=nickname).first() is None:
            return nickname
        version = 2
        while True:
            new_nickname = nickname + str(version)
            if User.query.filter_by(nickname=new_nickname).first() is None:
                break
            version += 1
        return new_nickname

    # 转换一个无效的nickname成一个有效昵称(为了避免用户输入不安全的非转义字符)
    @staticmethod
    def make_valid_nickname(nickname):
        # return re.sub('[^a-zA-Z0-9_\.]', '', nickname)
        return nickname

    def __repr__(self):
        return '<User %r>' % (self.nickname)


class Post(db.Model):
    __searchable__ = ['body']   # 为body字段建立搜索索引
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post %r>' % (self.body)

if enable_search:
    whooshalchemy.whoosh_index(app, Post)  # 通过调用whoosh_index 函数，为这个模型初始化了全文搜索索引
