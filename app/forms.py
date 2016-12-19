# -*- coding: utf-8 -*-
from flask.ext.wtf import Form
from wtforms import StringField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length
from app.models import User


class LoginForm(Form):
    openid = StringField('openid', validators=[DataRequired()])
    remember_me = BooleanField('remember_me', default=False)


class EditForm(Form):
    nickname = StringField('nickname', validators=[DataRequired()])
    about_me = TextAreaField('about_me', validators=[Length(min=0, max=140)])

    def __init__(self, original_nickname, *args, **kw):
        Form.__init__(self, *args, **kw)
        self.origin_nickname = original_nickname

    def validate(self):
        if not Form.validate(self):  # 判断昵称是否修改
            return False
        if self.nickname.data == self.origin_nickname:
            return True
        user = User.query.filter_by(nickname=self.nickname.data).first()
        if user is not None:
            self.nickname.errors.append('This nickname is already in use. Please choose another one.')
            return False
        return True


# 提交新的文章的表单
class PostForm(Form):
    post = StringField('post', validators=[DataRequired()])


# 搜索表单
class SearchForm(Form):
    search = StringField('search', validators=[DataRequired()])
