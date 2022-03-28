# Roles and what they mean:
#   - 'GUEST': Can only view the home/secret page and possibly media that is posted??
#   - 'USER': Can view the home/secret page, Add User page, and add media
#     - Users can also add new user's but only user's with the 'GUEST' and 'USER' roles
#   - 'ADMIN': Can view all pages, they can also remove any user (including another Admin)
#     - Admin's can also create other admins along with guests and users
#
#   - Maybe try to put all functions that aren't relying on routes into another file to clean things up a bit??
#   - Look into how to include other Python files
#

from passlib.hash import sha256_crypt
from flask import Flask, request, render_template, g, redirect, url_for, session, flash, make_response
from flask_session import Session
from datetime import timedelta
app = Flask(__name__)
app.config.update(
  SESSION_PERMANENT = False,
  SESSION_TYPE = 'memcached',
  SECRET_KEY = 'super.secret'
)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes = 60) # This sets the timeout to 3 minutes
sess = Session()

# Importing a file that holds all of my functions that don't require routing
import utility_scripts as us

# Using this global variable to hold onto the role chosen when adding a new user
# This is a temporary solution to the Bootstrap drop-down menu issue I'm having
add_role = ""

# Using this global variable to hold onto the user that will be edited
# This is a temporary solution to the Bootstrap drop-down menu issue I'm having
edit_user = ""

# Menu items for each page #
home_menu = { "Log Out" : "logout", "Add User" : "renderAddUser", "Remove User" : "renderRemoveUser", "Edit User" : "renderEditUser" }
add_user_menu = { "Log Out" : "logout", "Home" : "renderHome", "Remove User" : "renderRemoveUser", "Edit User" : "renderEditUser" }
remove_user_menu = { "Log Out" : "logout", "Home" : "renderHome", "Add User" : "renderAddUser", "Edit User" : "renderEditUser" }
edit_user_menu = { "Log Out" : "logout", "Home" : "renderHome", "Add User" : "renderAddUser", "Remove User" : "renderRemoveUser" }

@app.teardown_appcontext
def close_db(error):
  if hasattr(g, 'db'):
    g.db.close()

# Testing route for debugging
@app.route('/testdb')
def testHashing():
  cursor = us.get_db().cursor()
  cursor.execute('SELECT username, password FROM users')
  row = cursor.fetchall()
  return "<h1>" + str(sha256_crypt.verify('thanshaw', row[0]['password'])) + "</h1>";

@app.route('/logout')
def logout():
  us.clearSession()
  return redirect(url_for('renderLogIn'))

@app.route('/login')
def renderLogIn():
  login_attempt = request.args.get('login_fail')
  if not 'logged_in' in session:
    return render_template('web_pages/login.html', login_fail = login_attempt)
  else:
    return redirect(url_for('renderHome'))

@app.route('/login/verify', methods = ['GET', 'POST'])
def verifyLogin():
  if request.method == 'POST':
    if 'logged_in' in session:
      return redirect(url_for('renderHome'))
    elif us.verifyCredentials(request.form['uname'], request.form['pass']):
      print(request.cookies.get('visited_page'))
      return redirect(url_for('renderHome'))
    else:
      return redirect(url_for('renderLogIn', login_fail = True))
  else:
    return redirect(url_for('renderLogIn'))

@app.route('/home', methods = ['GET', 'POST'])
@app.route('/', methods = ['GET', 'POST'])
def renderHome():
  if 'logged_in' in session:
    if us.hasTimedOut():
      return redirect(url_for('renderLogIn'))
    else:
      session['last_page_visited'] = 'renderHome'
      us.resetTimeOut()
      return us.checkValidUser('web_pages/home.html', (session['full_name'], session['role'], home_menu)) # Turning the two arguments into a tuple
  else:
    resp = make_response("Cookies")
    resp.set_cookie("visited_page", "renderHome") # Probably not secure opening my back end functions up to the public like this
    return redirect(url_for('renderLogIn'))

# Come back to this, as of now if you're logged in you can type this page in the url and go here
# But if I want to keep that then I don't need to check what method was used to get to this page (GET or POST)
# So I have to decide whether I only want POST's to come here or both
@app.route('/addUser', methods = ['GET', 'POST'])
def renderAddUser():
  if 'logged_in' in session:
    if us.hasTimedOut():
      return redirect(url_for('renderLogIn'))
    elif session['role'] == 'GUEST':
      return redirect(url_for('renderHome'))
    else:
      session['last_page_visited'] = 'renderAddUser'
      us.resetTimeOut()
      return us.checkValidUser('web_pages/add_user.html', (session['role'], add_user_menu))
  else:
    resp = make_response("Cookies")
    resp.set_cookie("visited_page", "renderAddUser") # Probably not secure opening my back end functions up to the public like this
    return redirect(url_for('renderLogIn'))

@app.route('/removeUser', methods = ['GET', 'POST'])
def renderRemoveUser():
  if 'logged_in' in session:
    if us.hasTimedOut():
      return redirect(url_for('renderLogIn'))
    elif session['role'] == 'GUEST':
      return redirect(url_for('renderHome'))
    else:
      session['last_page_visited'] = 'renderRemoveUser'
      us.resetTimeOut()
      return us.checkValidUser('web_pages/remove_user.html', (session['role'], remove_user_menu))
  else:
    resp = make_response("Cookies")
    resp.set_cookie("visited_page", "renderRemoveUser") # Probably not secure opening my back end functions up to the public like this
    return redirect(url_for('renderLogIn'))

# I don't like the nested if() statements here, when I get time try to make this cleaner
# But there are a lot of cases that could happen when removing users from the DB
@app.route('/removeUser/removing', methods = ['GET', 'POST'])
def removingUser():
  global add_role
  if request.method == 'POST':
    if 'check_box' in request.form and request.form['check_box'] != None:
      if 'username' in request.form and 'remove_single' in request.form:
        username = request.form['username']
        if us.removeUserFromDB(username) == 1:
          flash("You have successfully removed the user '" + username + "' from the database!")
          return redirect(url_for('renderRemoveUser'))
        else:
          flash("The user '" + username + "' does not exist...")
          return redirect(url_for('renderRemoveUser'))
      elif 'remove_all' in request.form and add_role != "":
        # role = request.form['role']
        if us.removeAllUsersWithRole(add_role) > 0:
          flash("You have successfully removed all users with the role of '" + add_role + "'!")
          add_role = ""
          return redirect(url_for('renderRemoveUser'))
        else:
          flash("There are no users with the role of '" + add_role + "'...")
          add_role = ""
          return redirect(url_for('renderRemoveUser'))
    elif session['role'] != 'ADMIN':
      flash("Make sure to verify the removal by checking the 'checkbox' and entering a valid username.")
      return redirect(url_for('renderRemoveUser'))
    else:
      flash("Make sure to verify the removal by checking the 'checkbox' and entering a valid username or role.")
      return redirect(url_for('renderRemoveUser'))
  else:
    return redirect(url_for('renderHome'))


# Bug where if the insert fails instead of the flash message showing a Python error page will display
# But the insert is working!
# Maybe try to put this into a seperate function?
@app.route('/addUser/adding', methods = ['GET', 'POST'])
def addingUser():
  global add_role
  if request.method == 'POST':
    if add_role != "":
      rows_affected = us.addUserToDB(request.form['first_name'], request.form['last_name'], request.form['username'], 
                      sha256_crypt.hash(request.form['password']), add_role)
      add_role = ""
    else:
      rows_affected = us.addUserToDB(request.form['first_name'], request.form['last_name'], request.form['username'], 
                      sha256_crypt.hash(request.form['password']))
    if rows_affected > 0:
      flash("The user '" + request.form['username'] + "' was successfully added to the database!")
      return redirect(url_for('renderAddUser'))
    else:
      flash("The user '" + request.form['username'] + "' was not added to the database...")
      return redirect(url_for('renderAddUser'))
  else :
    return redirect(url_for('renderAddUser'))

# This is a hacky trick to get my Bootstrap drop-down menu to work
@app.route('/addUser/<role>', methods = ['GET', 'POST'])
def setRoleForAddUser(role):
  global add_role
  add_role = role
  return redirect(url_for('renderAddUser'))

# This is a hacky trick to get my Bootstrap drop-down menu to work
@app.route('/removeUser/<role>', methods = ['GET', 'POST'])
def setRoleForRemoveUser(role):
  global add_role
  add_role = role
  return redirect(url_for('renderRemoveUser'))

@app.route('/editUser', methods = ['GET', 'POST'])
def renderEditUser():
  if 'logged_in' in session and session['role'] == 'ADMIN':
    # if edit_user != "": print(edit_user)
    # if add_role != "": print(add_role)
    session['last_page_visited'] = 'renderEditUser'
    users = us.getAllUserNames()
    return us.checkValidUser('web_pages/edit_user.html', (session['role'], edit_user_menu, users))
  else:
    if 'logged_in' in session:
      return redirect(url_for(session['last_page_visited']))
    else:
      resp = make_response("Cookies")
      resp.set_cookie("visited_page", "renderEditUser") # Probably not secure opening my back end functions up to the public like this
      return redirect(url_for('renderLogIn'))

@app.route('/editUser/editing', methods = ['GET', 'POST'])
def editingUser():
  if request.method == 'POST' and 'logged_in' in session and session['role'] == 'ADMIN':
    global add_role, edit_user
    if not add_role and not edit_user:
      flash("Please choose a user to edit and a role for that user.")
      return redirect(url_for('renderEditUser'))
    else:
      password = request.form['password']
      verify_password = request.form['verify_password']
      if password != verify_password:
        flash('Please enter the same password twice.')
        return redirect(url_for('renderEditUser'))
      if us.editUser(edit_user, add_role, request.form['first_name'], request.form['last_name'], 
                    request.form['username'], request.form['password']):
        flash("The user '" + edit_user + "' has been updated successfully!")
        edit_user = ""
        add_role = ""
        return redirect(url_for('renderEditUser'))
      else:
        flash("The user '" + edit_user + "' was not updates successfully...")
        return redirect(url_for('renderEditUser'))
        
# I want to turn this into a more vague method, so the add and remove pages can call this to!
@app.route('/editUser/chooseUser/<username>/<page>', methods = ['GET', 'POST'])
def setUserToEdit(username, page):
  if 'logged_in' in session and session['role'] == 'ADMIN':
    global edit_user
    edit_user = username
    return redirect(url_for(page))
  else:
    if 'logged_in' in session: return redirect(url_for(session['last_page_visited']))
    else: return redirect(url_for('renderLogIn'))

# I want to turn this into a more vague method, so the add and remove pages can call this to!
@app.route('/editUser/chooseRole/<role>/<page>', methods = ['GET', 'POST'])
def chooseRole(role, page):
  if 'logged_in' in session and session['role'] == 'ADMIN':
    global add_role
    add_role = role
    return redirect(url_for(page))
  else:
    if 'logged_in' in session: return redirect(url_for(session['last_page_visited']))
    else: return redirect(url_for('renderLogIn'))


if(__name__ == '__main__'):
  app.run(debug=True)