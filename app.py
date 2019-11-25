from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
#from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)
# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)

# Index
@app.route('/')
def index():
    return render_template('home.html')

@app.route('/view_excel')
def view_excel():
    return render_template('view_excel.html')

@app.route('/perhitungan_optimal')
def perhitungan_optimal():
    return render_template('perhitungan_optimal.html')

# About
@app.route('/about')
def about():
    return render_template('about.php')

@app.route('/coba')
def coba():
    # Create cursor
    cur = mysql.connection.cursor()
    # Get knapsack
    result = cur.execute("SELECT * FROM view_bc")
    coba = cur.fetchall()

    if result > 0:
        return render_template('coba.html', coba=coba)
    else:
        msg = 'No Coba Found'
        return render_template('coba.html', msg=msg)

    # Close connection
    cur.close()

# @app.route('/hasil')
# def hasil():
#     # Create cursor
#     cur = mysql.connection.cursor()
#
#     # Get articles
#     result = cur.execute("SELECT cek, COUNT(cek) AS frekuensii_cek, ROUND((COUNT(cek)/(SELECT COUNT(*) FROM coba))*100,0) AS presentase FROM coba where cek='False' GROUP BY cek")
#
#     hasil = cur.fetchall()
#
#     if result > 0:
#         return render_template('hasil.html', hasil=hasil)
#     else:
#         msg = 'No Coba Found'
#         return render_template('hasil.html', msg=msg)
#
#     # Close connection
#     cur.close()


@app.route('/knapsack')
def knapsack():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute("SELECT * FROM ks")

    knapsack = cur.fetchall()

    if result > 0:
        return render_template('knapsack.html', knapsack=knapsack)
    else:
        msg = 'No knapsack Found'
        return render_template('knapsack.html', msg=msg)
    # Close connection
    cur.close()

@app.route('/cek_loc')
def cek_loc():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute("SELECT * FROM cek_loc")

    cek_loc = cur.fetchall()

    if result > 0:
        return render_template('cek_loc.html', cek_loc=cek_loc)
    else:
        msg = 'No knapsack Found'
        return render_template('cek_loc.html', msg=msg)
    # Close connection
    cur.close()

# Articles
@app.route('/articles')
def articles():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('articles.html', msg=msg)
    # Close connection
    cur.close()


#Single Article
@app.route('/article/<string:id>/')
def article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()

    return render_template('article.html', article=article)


# Register Form Class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')


# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)


# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = sha256_crypt.encrypt('password')

            # Compare Passwords
            if sha256_crypt.verify('password', password):
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('knapsack'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    #result = cur.execute("SELECT * FROM articles")
    # Show articles only from the user logged in
    result = cur.execute("SELECT * FROM articles WHERE author = %s", [session['username']])

    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('dashboard.html', msg=msg)
    # Close connection
    cur.close()

# Article Form Class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])

# Add Article
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)",(title, body, session['username']))

        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Article Created', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)


# Edit Article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article by id
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()
    cur.close()
    # Get form
    form = ArticleForm(request.form)

    # Populate article form fields
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        # Create Cursor
        cur = mysql.connection.cursor()
        app.logger.info(title)
        # Execute
        cur.execute ("UPDATE articles SET title=%s, body=%s WHERE id=%s",(title, body, id))
        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Article Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)

# Delete Article
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM articles WHERE id = %s", [id])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    flash('Article Deleted', 'success')

    return redirect(url_for('dashboard'))

# knapsack Form Class
class knapsackForm(Form):
    part_number = StringField('part_number', [validators.Length(min=1, max=200)])
    W = StringField('W', [validators.Length(min=1, max=200)])
    P = TextAreaField('P', [validators.Length(min=1, max=200)])
    
# Add knapsack
@app.route('/add_knapsack', methods=['GET', 'POST'])
@is_logged_in
def add_knapsack():
    form = knapsackForm(request.form)
    if request.method == 'POST' and form.validate():
        part_number = form.part_number.data
        W = form.W.data
        P = form.P.data
                
        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO ks(part_number, W, P) VALUES(%s, %s, %s)",(part_number, W, P))

        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('knapsack Created', 'success')

        return redirect(url_for('knapsack'))

    return render_template('add_knapsack.html', form=form)

# Edit knapsack
@app.route('/edit_knapsack/<string:W>', methods=['GET', 'POST'])
@is_logged_in
def edit_knapsack(W):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get knapsack by part_number
    result = cur.execute("SELECT * FROM ks WHERE W = %s", [W])

    knapsack = cur.fetchone()
    cur.close()
    # Get form
    form = knapsackForm(request.form)

    # Populate knapsack form fields
    form.part_number.data = knapsack['part_number']
    form.W.data = knapsack['W']
    form.P.data = knapsack['P']

    if request.method == 'POST' and form.validate():

        part_number = request.form['part_number']
        W = request.form['W']
        P = request.form['P']
        
        # Create Cursor
        cur = mysql.connection.cursor()
        app.logger.info(wms)
        # Execute
        cur.execute("UPDATE ks SET part_number=%s, W=%s, P=%s", [part_number, W, P])
        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('knapsack Updated', 'success')

        return redirect(url_for('knapsack'))

    return render_template('edit_knapsack.html', form=form)

# Delete knapsack
@app.route('/delete_knapsack/<string:W>', methods=['POST'])
@is_logged_in
def delete_knapsack(W):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM ks WHERE W = %s", [W])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    flash('knapsack Deleted', 'success')

    return redirect(url_for('knapsack'))

class Cek_locForm(Form):
    part_number = StringField('part_number', [validators.Length(min=1, max=200)])
    w = StringField('W', [validators.Length(min=1, max=200)])
    P = TextAreaField('P', [validators.Length(min=1, max=200)])
    
# Add knapsack
@app.route('/add_cek_loc', methods=['GET', 'POST'])
@is_logged_in
def add_cek_loc():
    form = Cek_locForm(request.form)
    if request.method == 'POST' and form.validate():
        true_cek = form.true_cek.data
        false_cek = form.false_cek.data

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO cek_loc(true_cek, false_cek) VALUES(%s, %s)",(true_cek, false_cek))

        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('knapsack Created', 'success')

        return redirect(url_for('cek_loc'))

    return render_template('add_cek_loc.html', form=form)


if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)
