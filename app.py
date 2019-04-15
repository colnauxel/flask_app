from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from data import Articles
import pymysql
from functools import wraps
# from flaskext.mysql import MySQL
# from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt

# mysql = MySQL()
app=Flask(__name__)

# Config Mysql
conn=pymysql.connect(host="localhost",user="root",passwd="",db="myflaskapp", cursorclass=pymysql.cursors.DictCursor)

# app.config['MYSQL_HOST']='localhost'
# app.config['MYSQL_USER']='root'
# app.config['MYSQL_PASSWORD']=''
# app.config['MYSQL_DB']='myflaskapp'
# app.config['MYSQL_CURSORCLASS']='DictCursor'

# app.config['MYSQL_DATABASE_USER'] = 'root'
# app.config['MYSQL_DATABASE_PASSWORD'] = ''
# app.config['MYSQL_DATABASE_DB'] = 'myflaskapp'
# app.config['MYSQL_DATABASE_HOST'] = 'localhost'

# mysql=MySQL(app)
# mysql.init_app(app)

Articles=Articles()
#ROUTER
@app.route('/')
def index():
    return render_template('home.html')
@app.route('/about')
def about():
    return render_template('about.html')
@app.route('/articles')
def articles():
   # create cursor
    cur=conn.cursor()

    result=cur.execute("SELECT * FROM articles")

    articles=cur.fetchall()
    if result >0:
        return render_template('articles.html',articles=articles)
    else:
        msg='No Articles Found'
        return render_template('articles.html',msg=msg)
    
    cur.close()

@app.route('/article/<string:id>/')
def article(id):
    # create cursor
    cur=conn.cursor()

    result=cur.execute("SELECT * FROM articles WHERE id= %s ",[id])

    article=cur.fetchone()
    date=str(article['create_date'])
    date.split(' ')
    print(date[1])
    return render_template('article.html',article=article)



# form register
class RegisterForm(Form):
    name=StringField('Name',[validators.Length(min=1,max=50)])
    username=StringField('Username',[validators.Length(min=3,max=30)])
    email=StringField('Email',[validators.Length(min=6,max=50)])
    password=PasswordField('Password',[
        validators.DataRequired(),
        validators.EqualTo('confirm',message='Password do not match')
    ])
    confirm=PasswordField('Confirm Password')
# user register
@app.route('/register', methods=['GET','POST'])
def register():
    form=RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name=form.name.data
        email=form.email.data
        username=form.username.data
        password=sha256_crypt.encrypt(str(form.password.data))
        # craete cursor
        cur=conn.cursor()
        cur.execute("INSERT INTO users_test(name,email,username,password) VALUES (%s,%s,%s,%s)",(name,email,username,password))
        # Commit to DB
        conn.commit()
        # close connection
        cur.close()
        
        flash('You are now register and can login','success')
        
        return redirect(url_for('login'))
        
        
    return render_template('register.html',form=form)

# User login
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        # get Form Fields
        username=request.form['username']
        password_candidate=request.form['password']

        # Create cursor
        cur=conn.cursor()
        # get user by username
        result=cur.execute("SELECT * FROM users_test WHERE username= %s ",[username])

        if result > 0:
            # get stored hash
            data=cur.fetchone()
            password=str(data['password'])
            
            # compare password
            if sha256_crypt.verify(password_candidate,password):
                # passed
                session['logged_in']=True
                session['username']=username

                flash('You are now logged in','success')
                return redirect(url_for('dashboard'))
            else:
                error='Invalid login'
                return render_template('login.html',error=error)
                cur.close()
        else:
            error='Username not found'
            return render_template('login.html',error=error)
    return render_template('login.html')
# check if user logged in

def is_logged_in(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if 'logged_in' in session:
            return f(*args,**kwargs)
        else:
            flash('Unauthorized, Please login','danger')
            return redirect(url_for('login'))
    return wrap



# logout user
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out','success')
    return redirect(url_for('login'))
# route dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # create cursor
    cur=conn.cursor()

    result=cur.execute("SELECT * FROM articles")

    articles=cur.fetchall()
    if result >0:
        return render_template('dashboard.html',articles=articles)
    else:
        msg='No Articles Found'
        return render_template('dashboard.html',msg=msg)
    
    cur.close()

#  Article form class
class ArticleForm(Form):
    title=StringField('Title',[validators.Length(min=1,max=200)])
    body=TextAreaField('Body',[validators.Length(min=30)])
# route add_articleForm

@app.route('/add_article',methods=['GET','POST'])
@is_logged_in
def add_article():
    form=ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title=form.title.data
        body=form.body.data

        # Create Cursor
        cur=conn.cursor()

        # Execute 
        cur.execute("INSERT INTO articles(title,body,author) VALUES (%s,%s,%s)",(title,body,session['username']))
        
        conn.commit()
        cur.close()
        flash('Article Created','success')

        return redirect(url_for('dashboard'))
    return render_template('add_article.html',form=form)
# edit article
@app.route('/edit_article/<string:id>',methods=['GET','POST'])
@is_logged_in
def edit_article(id):
    # create cursor
    cur=conn.cursor()
    # get article by id
    cur.execute("SELECT * FROM articles WHERE id=%s ",[id])
    # get form
    article=cur.fetchone()

    # populate article form fields
    form=ArticleForm(request.form)
    form.title.data=article['title']
    form.body.data=article['body']
    
    if request.method == 'POST' and form.validate():
        title=request.form['title']
        body=request.form['body']

        # Create Cursor
        cur=conn.cursor()

        # Execute 
        cur.execute("UPDATE articles SET title = %s,body = %s WHERE id = %s",(title,body,id))
        
        conn.commit()
        cur.close()
        flash('Article Updated','success')

        return redirect(url_for('dashboard'))
    return render_template('edit_article.html',form=form)
# delete article
@app.route('/delete_article/<string:id>',methods=['POST'])
@is_logged_in
def delete_article(id):
    # create cursor
    cur=conn.cursor()
    
    cur.execute("DELETE FROM articles WHERE id= %s",[id])

    conn.commit()

    cur.close()
    flash('Article Deleted','success')
    return redirect(url_for('dashboard'))
#END ROUTER

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)