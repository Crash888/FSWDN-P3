from flask import (Flask, Response, render_template, request, redirect,
                   jsonify, url_for, flash)
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, CategoryItem, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
import xml.etree.ElementTree as ET
from io import BytesIO
from werkzeug import secure_filename
import os
from functools import wraps

app = Flask(__name__)

# Image settings
UPLOAD_FOLDER = './static/images/'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

#  Client id used for authentication purposes
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS

# Connect to Database and create database session
engine = create_engine('sqlite:///catalogmenu.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in login_session:
            return redirect(url_for('showLogin'))
        return f(*args, **kwargs)
    return decorated_function


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['credentials']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showCategories'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showCategories'))


#  Logic to connect using a Google identity
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(
                       json.dumps('Current user is already connected.'),
                       200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;'
    output += '-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("You are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# Google Disconnect Logic - Revoke a current user's token and reset their
# login_session
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] != '200':
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# User Helper Functions
# Create a new user as soon as login is successful
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


# Return a user based on a supplied user_id
def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


# Look up user idf based on e-mail.  (Used for Login)
def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# JSON API to view items for a category
@app.route('/catalog/<int:category_id>/JSON')
@app.route('/catalog/<int:category_id>/items/JSON')
def categoryItemsJSON(category_id):
    items = session.query(CategoryItem).filter_by(
        category_id=category_id).all()

    # If we have items to return then good, otherwise show the categories page
    if items:
        return jsonify(CategoryItems=[i.serialize for i in items])
    else:
        return redirect(url_for('showCategories'))


# JSON API to retrieve one Category Item
@app.route('/catalog/<int:category_id>/items/<int:categoryItem_id>/JSON')
def categoryItemJSON(category_id, categoryItem_id):
    categoryItem = session.query(CategoryItem).filter_by(id=categoryItem_id) \
                   .one()

    # If we have an item to return then good, otherwise show the
    # categories page
    if categoryItem:
        return jsonify(categoryItem=categoryItem.serialize)
    else:
        return redirect(url_for('showCategories'))


# JSON API to retrieve all categories
@app.route('/catalog/JSON')
def catalogJSON():
    categories = session.query(Category).all()

    # If we have categories to return then good otherwise show the
    # categories page
    if categories:
        return jsonify(categories=[r.serialize for r in categories])
    else:
        return redirect(url_for('showCategories'))


# XML APIs to view Catalog Information
@app.route('/catalog/<int:category_id>/XML')
@app.route('/catalog/<int:category_id>/items/XML')
def categoryItemsXML(category_id):

    # Top Node
    xmlDoc = ET.Element('CategoryItems')

    items = session.query(CategoryItem).filter_by(category_id=category_id) \
                                       .all()

    # if we have some items then put them in the file
    if items:
        for item in items:
            itemElement = ET.SubElement(xmlDoc, 'CategoryItem')

            for column in item.__table__.columns:
                if column.name in item.__columns__:
                    subElement = ET.SubElement(itemElement, column.name)
                    subElement.text = str(getattr(item, column.name))

        et = ET.ElementTree(xmlDoc)

        f = BytesIO()

        # Write the data to an in memory buffer and then return
        # Needed to return the XML declaration
        et.write(f, encoding='utf-8', xml_declaration=True)

        response = make_response(f.getvalue())
        response.headers['Content-Type'] = 'application/xml'

        return response
    else:
        return redirect(url_for('showCategories'))


# XML API to retrieve one Category Item
@app.route('/catalog/<int:category_id>/items/<int:categoryItem_id>/XML')
def categoryItemXML(category_id, categoryItem_id):

    # Top Node
    xmlDoc = ET.Element('CategoryItem')

    categoryItem = session.query(CategoryItem).filter_by(id=categoryItem_id) \
                                              .one()

    # if we have some items then put them in the file
    if categoryItem:
        for column in categoryItem.__table__.columns:
            if column.name in categoryItem.__columns__:
                subElement = ET.SubElement(xmlDoc, column.name)
                subElement.text = str(getattr(categoryItem, column.name))

        et = ET.ElementTree(xmlDoc)

        f = BytesIO()

        # Write the data to an in memory buffer and then return
        # Needed to return the XML declaration
        et.write(f, encoding='utf-8', xml_declaration=True)

        response = make_response(f.getvalue())
        response.headers['Content-Type'] = 'application/xml'

        return response
    else:
        return redirect(url_for('showCategories'))


# XML API to retrieve all categories
@app.route('/catalog/XML')
def catalogXML():

    # Top Node
    xmlDoc = ET.Element('Categories')

    categories = session.query(Category).all()

    # if we have some items then put them in the file
    if categories:
        for category in categories:
            itemElement = ET.SubElement(xmlDoc, 'Category')

            for column in category.__table__.columns:
                if column.name in category.__columns__:
                    subElement = ET.SubElement(itemElement, column.name)
                    subElement.text = str(getattr(category, column.name))

        et = ET.ElementTree(xmlDoc)

        f = BytesIO()

        # Write the data to an in memory buffer and then return
        # Needed to return the XML declaration
        et.write(f, encoding='utf-8', xml_declaration=True)

        response = make_response(f.getvalue())
        response.headers['Content-Type'] = 'application/xml'

        return response
    else:
        return redirect(url_for('showCategories'))


# Show all categories
@app.route('/')
@app.route('/catalog/')
def showCategories():
    categories = session.query(Category).order_by(asc(Category.name))

    latest_items = session.query(CategoryItem).join(Category) \
                          .order_by(desc(CategoryItem.id)).limit(10)

    # Different templates for authenticated and non-authenticated people
    if 'username' not in login_session:
        return render_template('publiccategories.html',
                               categories=categories,
                               latest_items=latest_items)
    else:
        return render_template('categories.html',
                               categories=categories,
                               latest_items=latest_items)


# Enter a new category
@app.route('/category/new/', methods=['GET', 'POST'])
@login_required
def newCategory():

    if request.method == 'POST':

        categoryName = request.form['name'].strip()
        errors = ""

        # Form edits
        if not categoryName:
            flash("Name cannot be blank", "error")
            errors = "YES"

        if not errors:
            newCategory = Category(name=categoryName,
                                   user_id=login_session['user_id'])
            session.add(newCategory)
            flash('New Category "%s" Successfully Created' % newCategory.name)
            session.commit()
            return redirect(url_for('showCategories'))
        else:
            return redirect(url_for('newCategory'))
    else:
        return render_template('newCategory.html')


# Edit a category
@app.route('/category/<int:category_id>/edit/', methods=['GET', 'POST'])
@login_required
def editCategory(category_id):

    editedCategory = session.query(Category).filter_by(id=category_id).one()
    
    print ("editedCategory.user_id: " + str(editedCategory.user_id))
    print ("login_session.user_id: " + str(login_session['user_id']))
    
    # Can only edit categories created by you
    if editedCategory.user_id != login_session['user_id']:
        return "<script>function myFunction() " \
               "{alert('You are not authorized to edit this category. " \
               "Please create your own category in order to edit.');}" \
               "</script><body onload='myFunction()''>"
    errors = ""

    if request.method == 'POST':

        categoryName = request.form['name'].strip()

        # Form edits
        if not categoryName:
            flash("Name cannot be blank", "error")
            errors = "YES"

        if not errors:
            editedCategory.name = categoryName
            session.add(editedCategory)
            session.commit()
            
            flash('Category "%s" Successfully Edited' % editedCategory.name)

            return redirect(url_for('showCategoryItems',
                                    category_id=category_id))
        else:
            return redirect(url_for('editCategory', category_id=category_id))
    else:
        return render_template('editCategory.html', category=editedCategory)


# Delete a category
@app.route('/category/<int:category_id>/delete/', methods=['GET', 'POST'])
@login_required
def deleteCategory(category_id):

    categoryToDelete = session.query(Category).filter_by(id=category_id).one()
    categoryItemsToDelete = session.query(CategoryItem) \
                                   .filter_by(category_id=category_id).all()

    # Can only delete categories created by you
    if categoryToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() " \
               "{alert('You are not authorized to delete this category. " \
               "Please create your own category in order to delete.');}" \
               "</script><body onload='myFunction()''>"

    if request.method == 'POST':
        # Make sure to remove all images with the records
        for categoryItem in categoryItemsToDelete:
            if categoryItem.picture:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'],
                                       categoryItem.picture))
            session.delete(categoryItem)
        session.delete(categoryToDelete)
        flash('Category "%s" Successfully Deleted' % categoryToDelete.name)
        session.commit()
        return redirect(url_for('showCategories', category_id=category_id))
    else:
        return render_template('deleteCategory.html',
                               category=categoryToDelete)


# Display category items for one category
@app.route('/category/<int:category_id>/')
@app.route('/category/<int:category_id>/items/')
def showCategoryItems(category_id):

    category = session.query(Category).filter_by(id=category_id).one()
    creator = getUserInfo(category.user_id)
    categoryItems = session.query(CategoryItem).filter_by(
        category_id=category_id).all()
    
    print ("showcatitems: " + str(creator.id) + " " + str(login_session['user_id']))
    
    if 'username' not in login_session or \
       creator.id != login_session['user_id']:
        return render_template('publiccategoryitems.html',
                               categoryItems=categoryItems,
                               category=category, creator=creator)
    else:
        return render_template('categoryItems.html',
                               categoryItems=categoryItems,
                               category=category, creator=creator)


# Create a new category item
@app.route('/catalog/<int:category_id>/menu/new/', methods=['GET', 'POST'])
@login_required
def newCategoryItem(category_id):

    errors = ""
    filename = ""
    category = session.query(Category).filter_by(id=category_id).one()

    # can only add items to categories you created
    if login_session['user_id'] != category.user_id:
        return "<script>function myFunction() " \
               "{alert('You are not authorized to add items to this " \
               "category. Please create your own category in order to " \
               "add items.');}</script><body onload='myFunction()''>"

    if request.method == 'POST':

        categoryItemName = request.form['name'].strip()
        categoryItemDescription = request.form['description'].strip()
        file = request.files['file']

        # Form edits
        if not categoryItemName:
            flash("Name cannot be blank", "error")
            errors = "YES"

        if not errors:

            if file and allowed_file(file.filename):
                # Logic to handle file uploads
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            newItem = CategoryItem(name=categoryItemName,
                                   description=categoryItemDescription,
                                   category_id=category_id,
                                   user_id=category.user_id,
                                   picture=filename)
            session.add(newItem)
            session.commit()
            flash('New Catalog Item "%s" Successfully Created'
                  % (newItem.name))
            return redirect(url_for('showCategoryItems',
                                    category_id=category_id))
        else:
            return redirect(url_for('newCategoryItem',
                                    category_id=category_id))
    else:
        return render_template('newcategoryitem.html',
                               category_id=category_id,
                               category_name=category.name)


# Edit a category item
@app.route('/category/<int:category_id>/items/<int:categoryItem_id>/edit',
           methods=['GET', 'POST'])
@login_required
def editCategoryItem(category_id, categoryItem_id):

    errors = ""
    filename = ""
    editedItem = session.query(CategoryItem).filter_by(id=categoryItem_id) \
                                            .one()
    category = session.query(Category).filter_by(id=category_id).one()

    # Can only edit items that you created
    if login_session['user_id'] != editedItem.user_id:
        return "<script>function myFunction() " \
               "{alert('You are not authorized to edit items in this " \
               "category. Please create your own category in order to " \
               "edit items.');}</script><body onload='myFunction()''>"

    if request.method == 'POST':

        categoryItemName = request.form['name'].strip()
        categoryItemDescription = request.form['description'].strip()
        file = request.files['file']
        removeImage = 'removeImage' in request.form

        # Form edits
        if not categoryItemName:
            flash("Name cannot be blank", "error")
            errors = "YES"

        if removeImage and file:
            flash("Choose File OR Remove Image...not both", "error")
            errors = "YES"

        if not errors:
            # If new file selected or Remove Image chosen then delete
            # the current file
            if editedItem.picture and (removeImage or file):
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'],
                                       editedItem.picture))
                editedItem.picture = ""

            #  If file selected then upload it
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                editedItem.picture = filename

            editedItem.name = categoryItemName
            editedItem.description = categoryItemDescription

            session.add(editedItem)
            session.commit()
            flash('Catalog Item "%s" Successfully Edited' % (editedItem.name))
            return redirect(url_for('showCategoryItems',
                                    category_id=category_id))
        else:
            return redirect(url_for('editCategoryItem',
                                    category_id=category_id,
                                    categoryItem_id=categoryItem_id))
    else:
        return render_template('editcategoryitem.html',
                               category_id=category_id,
                               category_name=category.name,
                               item_id=categoryItem_id,
                               item=editedItem)


# Delete a catalog item
@app.route('/category/<int:category_id>/items/<int:categoryItem_id>/delete',
           methods=['GET', 'POST'])
@login_required
def deleteCategoryItem(category_id, categoryItem_id):

    category = session.query(Category).filter_by(id=category_id).one()
    itemToDelete = session.query(CategoryItem).filter_by(id=categoryItem_id) \
                                              .one()

    # Can only delete an item that you created
    if login_session['user_id'] != itemToDelete.user_id:
        return "<script>function myFunction() " \
               "{alert('You are not authorized to delete this item. " \
               "Please create your own category in order to " \
               "delete items.');}</script><body onload='myFunction()''>"

    if request.method == 'POST':
        if request.form['submit'] == 'submit':
            if itemToDelete.picture:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'],
                                       itemToDelete.picture))

            session.delete(itemToDelete)
            session.commit()
            flash('Catalog Item Successfully Deleted')
        return redirect(url_for('showCategoryItems', category_id=category_id))
    else:
        return render_template('deleteCategoryItem.html', item=itemToDelete)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
