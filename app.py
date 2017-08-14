from flask import Flask, render_template, flash, redirect, request, url_for, session, logging
# from data import Articles
from flaskext.mysql import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
import pymysql
app = Flask(__name__)
app.debug = True

#Config MySQL
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'password'
app.config['MYSQL_DATABASE_DB'] = 'flasticles'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
#int MYSQL
mysql = MySQL(app)

# Pulls articles from files
# Articles = Articles()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    #Create cursor that return Dictionary
    conn = mysql.connect()
    cur = conn.cursor(pymysql.cursors.DictCursor)

    #Get Articles
    result = cur.execute("SELECT * FROM articles")
    #This must be in a Dictionary form -- json
    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html',articles=articles )
    else:
        msg = 'No Articles Found'
        return render_template('articles.html', msg=msg)
    #Close connection
    cur.close()

@app.route('/article/<string:id>/')
def article(id):
    #Create cursor that return Dictionary
    conn = mysql.connect()
    cur = conn.cursor(pymysql.cursors.DictCursor)

    #Get Article
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])
    article = cur.fetchone()


    return render_template('article.html', article=article)

class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confim Password')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        #Create the cursor
        conn = mysql.connect()
        cur = conn.cursor()

        #Execute query
        cur.execute("INSERT INTO users(name,email ,username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        #Commit to DB
        conn.commit()

        #Close connection
        cur.close()
        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)

#User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        #Get Form fields
        username = request.form['username']
        password_candidate = request.form['password']

        #Create a cursor
        conn = mysql.connect()
        cur = conn.cursor()

        #Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            #Get the stored hash
            data = cur.fetchone()
            password = data[4]

            #Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                #Passed
                session['logged_in'] = True
                session['username'] = username

                flash("Login successfull", 'success')
                return redirect(url_for('dashboard'))

            else:
                error = "Invalid login"
                return render_template('login.html',error=error)
            #Close Connection
            cur.close()
        else:
            error = "Username not found"
            return render_template('login.html',error=error)

    return render_template('login.html')



#Check if the User is logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Login to view this page', 'danger')
            return redirect(url_for('login'))
    return wrap


#Logout
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out", 'success')
    return redirect(url_for('login'))

#Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    #Create cursor that return Dictionary
    conn = mysql.connect()
    cur = conn.cursor(pymysql.cursors.DictCursor)

    #Get Articles
    result = cur.execute("SELECT * FROM articles")
    #This must be in a Dictionary form -- json
    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html',articles=articles )
    else:
        msg = 'No Articles Found'
        return render_template('dashboard.html', msg=msg)
    #Close connection
    cur.close()

class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])

@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # Create a cursor
        conn = mysql.connect()
        cur = conn.cursor()

        # Execute
        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)", (title, body, session['username']))

        #Commit
        conn.commit()

        #Close connection
        cur.close()
        flash('Article created', 'success')
        return redirect(url_for('dashboard'))


    return render_template('add_article.html', form=form)


@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    #Fill the form
    #Create cursor that return Dictionary
    conn = mysql.connect()
    cur = conn.cursor(pymysql.cursors.DictCursor)

    # Get the article by id

    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()

    #Get the form
    form = ArticleForm(request.form)

    #Populate article form fields
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():

        title = request.form['title']
        body = request.form['body']

        #Create cursor that return Dictionary
        conn = mysql.connect()
        cur = conn.cursor(pymysql.cursors.DictCursor)

        # Execute
        cur.execute("UPDATE articles SET title=%s,body=%s WHERE id = %s", (title, body, id))

        #Commit
        conn.commit()

        #Close connection
        cur.close()
        flash('Article Updated', 'success')
        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)

#Delete Article
@app.route('/delete_article/<string:id>', methods=["POST"])
@is_logged_in
def delete_article(id):
    #Create cursor that return Dictionary
    conn = mysql.connect()
    cur = conn.cursor(pymysql.cursors.DictCursor)

    #Execute
    cur.execute("DELETE FROM articles WHERE id = %s", [id])
    #Commit
    conn.commit()

    #Close connection
    cur.close()
    flash('Article Deleted', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run()
