from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from data import Articles
import pymysql
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
    return render_template('articles.html',articles=Articles)

@app.route('/article/<string:id>/')
def article(id):
    return render_template('article.html',id=id)




class RegisterForm(Form):
    name=StringField('Name',[validators.Length(min=1,max=50)])
    username=StringField('Username',[validators.Length(min=3,max=30)])
    email=StringField('Email',[validators.Length(min=6,max=50)])
    password=PasswordField('Password',[
        validators.DataRequired(),
        validators.EqualTo('confirm',message='Password do not match')
    ])
    confirm=PasswordField('Confirm Password')

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
# route dashboard
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')
#END ROUTER

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)