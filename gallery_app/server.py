# NOTE:
#   - If running this yourself, create a flask virtual environment with this command:
#     - python3 -m venv name_here
#   - Then as long as you have the 'static' folder and the 'templates' folder then you will be able to upload files
#   - This app will automatically create the file upload directory on start

from flask import Flask, render_template, request, flash, make_response, url_for, redirect
from stat import *
from os import *
from glob import glob
from werkzeug.utils import secure_filename

# This file path is for a remote server
# So if you want to use this code you must change this to be reletive to your directory
UPLOAD_FOLDER = '/home/thanshaw/PG6/static/uploaded_imgs'
ALLOWED_EXTENSIONS = { 'png', 'jpg', 'jpeg', 'gif', 'PNG' }

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'super.secret'

# If the directory I'm saving my images in does not exist, then create it
if not path.isdir(app.config['UPLOAD_FOLDER']):
  makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Pulled this from the Flask documentation on file input
# Link: https://flask.palletsprojects.com/en/2.1.x/patterns/fileuploads/
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function that gets all of the image files in the static/uploaded_imgs directory
# I use this to display each image
# Key: directory name   Value: file name
def fetchSavedMedia():
  mediaPaths = {}
  for file in glob(app.config['UPLOAD_FOLDER'] + '/*'):
    st = stat(file)
    if not S_ISREG(st.st_mode):
      cut = file.find('gs/')
      name = file[cut + 3:]
      mediaPaths[name] = []
      for sub_file in glob(file + '/*'):
        sta = stat(sub_file)
        if S_ISREG(sta.st_mode):
          fcut = sub_file.find(name)
          fname = sub_file[fcut + (len(name) + 1):]
          mediaPaths[name].append(fname)
  return mediaPaths

# I had to do this same procss for both the remove and add routes below
# So I made a function for it to reduce redundant code
def constructFilePath(folder_name, file_name):
  return folder_name + '/' + file_name

# Checks if there are any user created directories that are empty (no files in them)
# Removes these empty directories
def checkForEmptyFolders(folders):
  for folder, files in folders.items():
    if not files:
      rmdir(app.config['UPLOAD_FOLDER'] + '/' + folder)
  return folders

# NOTE: If you remove the last photo in one of the files I remove the file so I don't have a list of empty files
@app.route('/')
@app.route('/home')
def renderHome():
  media = fetchSavedMedia()
  return render_template('home.html', pics = media)

# Check if valid file being uploaded, check if they gave a directory name or not
# Then I add to the given directory (or create it if not found)
# The 'public' directory is used when no directory name is given
# NOTE: Possibly check if this image has already been added? If it has don't add it and send a flash message
@app.route('/addImage', methods = ['GET', 'POST'])
def addImage():
  if 'file_in' not in request.files:
    flash('No file found...')
    return redirect(url_for('renderHome'))
  file = request.files['file_in']
  if file.filename == '':
    flash('Please select a file before adding one...')
    return redirect(url_for('renderHome'))
  if file and allowed_file(file.filename):
    if len(request.form['uname']) != 0:
      path_with_uname = app.config['UPLOAD_FOLDER'] + '/' + request.form['uname']
    else:
      path_with_uname = app.config['UPLOAD_FOLDER'] + '/public'
    if not path.isdir(path_with_uname):
      makedirs(path_with_uname, exist_ok=True)
    filename = secure_filename(file.filename)
    file.save(path.join(path_with_uname, filename))
    flash('You have successfully uploaded the file \'' + filename[:-4] + '\'!')
    return redirect(url_for('renderHome'))
  else:
    flash('Please submit a valid file...')
    return redirect(url_for('renderHome'))

# Passing the file name and directory name with a 'GET' call
# Names are in the URL - for example: /viewImage?folder=tylor&file=cat.jpg
@app.route('/viewImage', methods = ['GET', 'POST'])
def renderViewImage():
  file_name = request.args.get('file')
  fpath = constructFilePath(request.args.get('folder'), file_name)
  return render_template('display_img.html', img = '/static/uploaded_imgs/' + fpath, img_name = file_name[:-4])

# I will remove the image chosen by the user here then redirect back to the home page
# I also check if the folder is empty or not, if it is I remove the directory
@app.route('/removeImage', methods = ['GET', 'POST'])
def removeImage():
  file_name = request.args.get('file')
  fpath = constructFilePath(request.args.get('folder'), file_name)
  media_path = app.config['UPLOAD_FOLDER'] + '/' + fpath
  if path.exists(media_path):
    remove(media_path)
    # This is a little ambiguous but I grab all the folders/files and if any folders are emoty I remove them
    checkForEmptyFolders(fetchSavedMedia())
    flash('The image \'' + file_name + '\' has successfully been removed!')
    return redirect(url_for('renderHome'))
  else:
    flash('This file does not exist, something has gone wrong.')
    return redirect(url_for('renderHome'))


if __name__ == '__main__':
  app.run(debug = True) # Only use this when running on my local machine
  # app.run(host='0.0.0.0', debug=True) # Only use this when running on server
