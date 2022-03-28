# NOTES:
#   - This file is just for utility functions and functions that aren't directly tied to a route
#   - Trying to modulize my code and clean everything up a little bit
#

import pymysql
from passlib.hash import sha256_crypt
from flask import render_template, g, redirect, url_for, session
from datetime import datetime, timezone

def connect_to_DB():
  return pymysql.connect(
    user = 'thanshaw', password = 'Froger!3050', database = 'flask',
    autocommit = True, charset = 'utf8mb4', cursorclass = pymysql.cursors.DictCursor)

def get_db():
  if not hasattr(g, 'db'):
    g.db = connect_to_DB()
  return g.db

def verifyCredentials(username, password):
  cursor = get_db().cursor()
  cursor.execute('SELECT username, password, first_name, last_name, role FROM users WHERE username = %s', (username))
  row = cursor.fetchall()
  if(len(row) == 1): 
    if sha256_crypt.verify(password, row[0]['password']):
      setUserSessionVariables(row)
      return True
  return False

def setUserSessionVariables(row):
  session['logged_in'] = True
  session['role'] = row[0]['role']
  session['username'] = row[0]['username']
  session['full_name'] = row[0]['first_name'] + " " + row[0]['last_name']
  session['last_activity'] = datetime.now()

# After 5 minutes of inactivity you will have to re-log back in
def hasTimedOut():
  time_diff = datetime.now(timezone.utc).minute - session['last_activity'].minute
  print(time_diff)
  if time_diff > 5:
    clearSession()
    return True
  return False

# Sets the 'last_activity' session variable to the current time
def resetTimeOut():
  session['last_activity'] = datetime.now(timezone.utc)

# Using this instead of 'session.clear()' so I don't have to reset my session key each time
def clearSession():
  for key in list(session.keys()):
    session.pop(key)

def checkValidUser(render_page_on_success, optional_args = None):
  if not optional_args:
    if session['role'] != 'GUEST':
      return render_template(render_page_on_success)
    elif session['role'] == 'GUEST':
      return render_template(render_page_on_success)
      # return redirect(url_for('renderHome')) # Infinite redirect loop is happening right here
    else:
      return redirect(url_for('renderLogIn'))
  else:
    if session['role'] != 'GUEST':
      return render_template(render_page_on_success, args = optional_args)
    elif session['role'] == 'GUEST':
      return render_template(render_page_on_success, args = optional_args) # Added this in to patch bug for now
      # return redirect(url_for('renderHome')) # Infinite redirect loop is happening right here
    else:
      return redirect(url_for('renderLogIn'))

# 'role' has a default value of 'None', this is because a user with 'USER' privileges can only add 'GUEST' users
def addUserToDB(fname, lname, uname, password, role = None):
  cursor = get_db().cursor()
  if not role:
    cursor.execute('INSERT INTO users VALUES(0, %s, %s, %s, %s, \'GUEST\')', (fname, lname, uname, password))
  else:
    cursor.execute('INSERT INTO users VALUES(0, %s, %s, %s, %s, %s)', (fname, lname, uname, password, role))
  return cursor.rowcount > 0

def removeAllUsersWithRole(role):
  cursor = get_db().cursor()
  cursor.execute('DELETE FROM users WHERE role = %s', (role))
  return cursor.rowcount > 0

def removeUserFromDB(username):
  cursor = get_db().cursor()
  cursor.execute('DELETE FROM users WHERE username = %s', (username))
  return cursor.rowcount > 0

def getAllUserNames():
  cursor = get_db().cursor()
  cursor.execute('SELECT username FROM users WHERE role = \'USER\' OR role = \'GUEST\'')
  return cursor.fetchall()
