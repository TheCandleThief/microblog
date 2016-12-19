# -*- coding: utf-8 -*-

from datetime import datetime
from flask import render_template, flash, redirect, session, url_for, request, g
from config import POSTS_PER_PAGE, MAX_SEARCH_RESULTS, LANGUAGES
from app import app, lm, db, oid, babel
from forms import LoginForm, EditForm, PostForm, SearchForm
from flask.ext.login import login_user, logout_user, current_user, login_required
from models import User, ROLE_USER, ROLE_ADMIN, Post
from emails import follower_notification
from flask.ext.babel import gettext


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@app.route('/index/<int:page>', methods=['GET', 'POST'])
@login_required  # 表明这个页面只有登录用户才能访问
def index(page=1):
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, timestamp=datetime.utcnow(), author=g.user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('index'))
    posts = g.user.followed_posts().paginate(page, POSTS_PER_PAGE, False)  # 返回整个paginate对象
    return render_template("index.html", title='Home', form=form, posts=posts)


@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler   # 告诉openid 这是登录试图函数
def login():
    # 全局变量g,在一个request周期中，用来存储和共享数据，将把已登录用户放到g中
    if g.user is not None and g.user.is_authenticated:  # 检测用户是否已经经过登录认证，如果一个用户已经登录了不让做二次登录
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        session['remember_me'] = form.remember_me.data
        # 通过openid来执行用户认证
        return oid.try_login(form.openid.data, ask_for=['nickname', 'email'])
    return render_template('login.html', title='Sign In', form=form, providers=app.config['OPENID_PROVIDERS'])


@oid.after_login
def after_login(resp):
    if resp.email is None or resp.email == "":  # 如果没有提供email将无法登录
        flash(gettext('Invalid login. Please try again.'))
        redirect(url_for('login'))
    user = User.query.filter_by(email=resp.email).first()  # 通过email查找数据库
    if user is None:       # 如果数据库没有该用户，将增加一个新用户
        nickname = resp.nickname
        if nickname is None or nickname == "":
            nickname = resp.email.split('@')[0]
        nickname = User.make_valid_nickname(nickname)
        nickname = User.make_unique_nickname(nickname)
        user = User(nickname=nickname, email=resp.email, role=ROLE_USER)
        db.session.add(user)
        db.session.commit()
        # make the user follow himself
        db.session.add(user.follow(user))
        db.session.commit()
    remember_me = False
    if 'remember_me' in session:
        remember_me = session['remember_me']
        session.pop('remember_me', None)
    login_user(user, remember=remember_me)
    # 重定向到下一个页面，或者如果在request请求中没有提供下个页面时，将重定向到index页面。
    return redirect(request.args.get('next') or url_for('index'))


# 登出
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


# 用户资料视图
@app.route('/user/<nickname>')
@app.route('/user/<nickname>/<int:page>')
@login_required
def user(nickname, page=1):
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('不存在用户：' + nickname + '!')
        return redirect(url_for('index'))
    posts = user.get_posts().paginate(page, POSTS_PER_PAGE, False)
    return render_template('user.html', user=user, posts=posts)


# 编辑资料
@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    form = EditForm(g.user.nickname)
    if form.validate_on_submit():
        g.user.nickname = form.nickname.data
        g.user.about_me = form.about_me.data
        db.session.add(g.user)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit'))
    else:
        form.nickname.data = g.user.nickname
        form.about_me.data = g.user.about_me
    return render_template('edit.html', form=form)


# 关注用户
@app.route('/follow/<nickname>')
@login_required
def follow(nickname):
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('User %s not found.' % nickname)
        return redirect(url_for('index'))
    if user == g.user:
        flash('You can\'t follow yourself!')
        return redirect(url_for('user', nickname=nickname))
    u = g.user.follow(user)
    if u is None:
        flash('Cannot follow ' + nickname + '.')
        return redirect(url_for('user', nickname=nickname))
    db.session.add(u)
    db.session.commit()
    flash('You are now following ' + nickname + '!')
    follower_notification(user, g.user)  # 给被关注者发送邮件提醒被关注
    return redirect(url_for('user', nickname=nickname))


# 取消关注
@app.route('/unfollow/<nickname>')
@login_required
def unfollow(nickname):
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('User %s not found.' % nickname)
        return redirect(url_for('index'))
    if user == g.user:
        flash('You can\'t unfollow yourself!')
        return redirect(url_for('user', nickname=nickname))
    u = g.user.unfollow(user)
    if u is None:
        flash('Cannot unfollow ' + nickname + '.')
        return redirect(url_for('user', nickname=nickname))
    db.session.add(u)
    db.session.commit()
    flash('You have stopped following ' + nickname + '!')
    return redirect(url_for('user', nickname=nickname))


# 提交的搜索请求，然后重定向到搜索处理页面
@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    if not g.search_form.validate_on_submit():
        return redirect(url_for('index'))
    return redirect(url_for('search_results', query=g.search_form.search.data))


# 处理搜索结果页
@app.route('/search_results/<query>')
@login_required
def search_results(query):
    results = Post.query.whoosh_search(query, MAX_SEARCH_RESULTS).all()
    return render_template('search_results.html', query=query, results=results)


# 语言选择
@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(LANGUAGES.keys())


# 删除post
@app.route('/delete/<int:id>')
@login_required
def delete(id):
    post = Post.query.get(id)
    if post is None:
        flash('Post not found.')
        return redirect(url_for('index'))
    if post.author.id != g.user.id:
        flash('You cannot delete this post.')
        return redirect(url_for('index'))
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted.')
    return redirect(url_for('index'))


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


# 在每次request请求被收到时提前与view方法执行，检查g.user来判断用户是否登录
@app.before_request
def before_request():
    g.user = current_user
    if g.user.is_authenticated:
        g.user.last_seen = datetime.utcnow()  # 添加登录时间到数据库
        db.session.add(g.user)
        db.session.commit()
        g.search_form = SearchForm()


# 错误处理程序
@app.errorhandler(404)
def internal_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()  # 回滚数据库
    return render_template('500.html'), 500



