import sqlite3
import logging
import sys

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

#
countOfConnections=0
logFormat = '%(levelname)s:%(name)s:%(asctime)s, %(message)s'
dateFormat = '%m/%d/%Y,%H:%M:%S'
# set logger to handle STDOUT and STDERR 
stdout_handler =  logging.StreamHandler(sys.stdout)
stderr_handler =  logging.StreamHandler(sys.stderr) 
handlers = [stderr_handler, stdout_handler]
 

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    global countOfConnections
    countOfConnections+=1
    connection.row_factory = sqlite3.Row
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()    
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the health status route of the web application 
@app.route('/healthz')
def healthcheck():
    response = app.response_class(
            response=json.dumps({"result":"OK - healthy"}),
            status=200,
            mimetype='application/json'
    )
    app.logger.info('Status request successfull')
    app.logger.debug('DEBUG message')
    return response

@app.route('/metrics')
def metrics():
    global countOfConnections
    connection = get_db_connection()
    posts = connection.execute('SELECT count(*) FROM posts').fetchone()    
    connection.close()    
    output={"post_count":posts[0],"db_connection_count":countOfConnections}
    response = app.response_class(
            response=json.dumps(output),
            status=200,
            mimetype='application/json'
    )
    app.logger.info('Metrics request successfull')
    return response


# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()    
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      app.logger.info('A non-existing article %s is accessed and a 404 page is returned.',post_id)  
      return render_template('404.html'), 404
    else:
      app.logger.info('Article \"%s\" retrieved!',post['title'])  
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info('About Us page is retrieved.')  
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            app.logger.info('A new article is created - \"%s\"',title)
            
            return redirect(url_for('index'))

    return render_template('create.html')

# start the application on port 3111
if __name__ == "__main__":
   countOfConnections=0 
   # Stream logs to STDOUT and STDERR, and set the default log level to DEBUG
   logging.basicConfig(format=logFormat,datefmt=dateFormat,level=logging.DEBUG,handlers=handlers)
   app.run(host='0.0.0.0', port='3111')
