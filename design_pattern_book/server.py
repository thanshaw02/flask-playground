from flask import Flask, render_template, request, flash, url_for, redirect, g, session
import pymysql
app = Flask(__name__)
app.secret_key = 'super.secret'

def connect_to_DB():
  return pymysql.connect(
    user = 'thanshaw', password = 'secret', database = 'thanshaw$default', host ='thanshaw.mysql.pythonanywhere-services.com',
    autocommit = True, charset = 'utf8mb4', cursorclass = pymysql.cursors.DictCursor)

def get_db():
  if not hasattr(g, 'db'):
    g.db = connect_to_DB()
  return g.db

@app.teardown_appcontext
def close_db(error):
  if hasattr(g, 'db'):
    g.db.close()

def checkForConnectingPatterns(patterns, prec_or_foll):
  connectingPatterns = {}
  for i in range(len(patterns)):
    patternId = patterns[i]['id']
    for j in range(len(patterns)):
      if i != j:
        if patterns[i][prec_or_foll] == patterns[j]['name']:
          connectingPatterns[patternId] = patterns[j]['id']
          break
  return connectingPatterns

# Returns True if the user is logged in as 'admin' (can edit, add, and remove patterns)
# Return False if the user is logged in as a 'guest' or not logged in at all
def loggedInAsAdmin():
  if 'logged_in' in session:
    return session['logged_in'] == 'admin'
  return False

@app.route('/')
@app.route('/login')
def renderLogin():
  if loggedInAsAdmin():
    return redirect(url_for('renderHome'))
  else:
    return render_template('/login.html')

@app.route('/attemptLogin', methods = ['POST'])
def attemptLoginPost():
  username = request.form['username']
  password = request.form['password']
  if username == 'thanshaw' and password == 'cs326patterns':
    session['logged_in'] = 'admin'
    return redirect(url_for('renderHome'))
  else:
    flash('Please enter a valid username and password')
    return redirect(url_for('renderLogin'))

@app.route('/attemptLogin', methods = ['GET'])
def redirectFromAttemptLogin():
  flash('Please enter the correct username and password to login as the admin')
  return redirect(url_for('renderLogin'))

@app.route('/logout', methods = ['POST'])
def logoutAsAdmin():
  session['logged_in'] = 'guest'
  return redirect(url_for('renderLogin'))

@app.route('/home', methods = ['GET'])
def renderHome():
  if 'logged_in' not in session:
    session['logged_in'] = 'guest'
  cursor = get_db().cursor()
  cursor.execute('SELECT * FROM patterns')
  rows = cursor.fetchall()
  matching_preceding_patterns = checkForConnectingPatterns(rows, 'preceding_patterns')
  matching_following_patterns = checkForConnectingPatterns(rows, 'following_patterns')
  return render_template(
    'home.html',
    patterns = rows,
    preceding = matching_preceding_patterns,
    following = matching_following_patterns,
    logged_in_as = session['logged_in']
  )

@app.route('/addPatternForm', methods = ['POST'])
def renderAddPatternForm():
  if not loggedInAsAdmin():
    return redirect(url_for('renderHome'))
  else:
    return render_template('add_pattern.html')

@app.route('/addPatternForm', methods = ['GET'])
def redirectToHomeFromForm():
  return redirect(url_for('renderHome'))

@app.route('/addPattern', methods = ['POST'])
def addPatternToDB():
  if not loggedInAsAdmin():
    return redirect(url_for('renderHome'))
  else:
    cursor = get_db().cursor()
    name = request.form['pattern_name']
    forces = request.form['pattern_forces']
    resolution = request.form['pattern_resolution']
    code_examples = request.form['code_examples']
    preceding_pattern = request.form['preceding_patterns']
    following_pattern = request.form['following_patterns']
    cursor.execute(
      'INSERT INTO patterns VALUES(0, %s, %s, %s, %s, %s, %s)',
      (name, forces, resolution, code_examples, preceding_pattern, following_pattern)
    )
    if cursor.rowcount >= 1:
      flash('Pattern has successfully been added!')
      return redirect(url_for('renderAddPatternForm'))
    else:
      flash('Pattern was not added to the database...')
      return redirect(url_for('renderAddPatternForm'))

@app.route('/addPattern', methods = ['GET'])
def rerouteToAddPatternForm():
  flash('You must fill out the form to enter a pattern, or login as an admin')
  return redirect(url_for('renderAddPatternForm'))

@app.route('/removePattern', methods = ['POST'])
def removePattern():
  if not loggedInAsAdmin():
    flash('Log in as an admin to remove a pattern...')
    return redirect(url_for('renderHome'))
  else:
    cursor = get_db().cursor()
    pattern_id = request.form['pattern_id']
    cursor.execute('DELETE FROM patterns WHERE id = %s', (pattern_id))
    if cursor.rowcount >= 1:
      flash('Pattern was successfully removed!')
      return redirect(url_for('renderHome'))
    else:
      flash('Pattern was not removed from the database...')
      return redirect(url_for('renderHome'))

# If the user tries to go to the 'removePattern' page they will be redirected to the home page
@app.route('/removePattern', methods = ['GET'])
def redirectToHomeFromRemove():
  flash('You must choose a pattern to remove first, or login as an admin')
  return redirect(url_for('renderHome'))

@app.route('/editPattern', methods = ['POST'])
def editPattern():
  if not loggedInAsAdmin():
    flash('Log in as an admin to edit a pattern...')
    return redirect(url_for('renderHome'))
  else:
    cursor = get_db().cursor()
    pattern_id = request.form['edit_pattern_id']
    name = request.form['pattern_name']
    forces = request.form['pattern_forces']
    resolution = request.form['pattern_resolution']
    code_examples = request.form['code_examples']
    preceding_pattern = request.form['preceding_patterns']
    following_pattern = request.form['following_patterns']
    cursor.execute(
      'UPDATE patterns SET name = %s, forces = %s, resolution = %s, code_examples = %s, preceding_patterns = %s, following_patterns = %s WHERE id = %s',
      (name, forces, resolution, code_examples, preceding_pattern, following_pattern, pattern_id)
    )
    if cursor.rowcount == 1:
      flash('Successfully updated the \'{}\' pattern!'.format(name))
      return redirect(url_for('renderHome'))
    else:
      flash('Something went wrong... was not able to update the \'{}\' pattern.'.format(name))
      return redirect(url_for('renderHome'))

@app.route('/editPattern', methods = ['GET'])
def redirectToHomeFromEdit():
    flash('Please choose a pattern to edit, or login as an admin')
    return redirect(url_for('renderHome'))