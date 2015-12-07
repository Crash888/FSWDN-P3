Product Catalog
===============

Description
-----------
 	
	This project consists of an application to view and, if authenticated, 
    create/edit/delete categories and items.

    Categories are entirely user defined and item descriptions and pictures
    are provided by the user as well.    
    
    Authentication is provided by Google, so a Google account is required for
    update access to the application.  Note, edits and deletes are only 
    available on items that the current logged in user has created.  Categories
    and items created by another user will need to be edited or deleted by
    that user.
    
    A sample category and item load is provided for demonstration purposes.
    
  
Requirements
------------	
	### Files
        -  application.py - Catalog Application
        -  client_secrets.json - Google file to register application for Google login
        -  database_setup.py - Script to setup the database
		-  README.md - Application description and instructions
        -  samplecategories.py - Script to load sample categories and items

        - samplecategories_images\
            -  avengers_aou.jpg
            -  DaVinciCode.jpg
            -  First_Single_Volume_Edition_of_The_Lord_of_the_Rings.gif
            -  inside_out.jpg
            -  Led_Zeppelin_-_Led_Zeppelin_IV.jpg
            -  Michael_Jackson_Thriller.png
            -  OneElephant1.jpg
            -  PinkFloyd-Dark_Side_of_the_Moon.png
            -  Please_Hammer_Don't_Hurt_'Em.jpg
            -  raffi_singablesongs.jpg
            -  terminator.jpg
            
        -  static\
            -  images\
                -  No-Image.jpg
            -  blank_user.gif
            -  styles.css - Application style sheet
            -  top-banner.jpg - Banner for the application
            
        - templates\
            -  categories.html - Category List
            -  categoryitems.html - Category Item list
            -  deletecategory.html - Delete a Category
            -  deletecategoryitem.html - Delete a Category Item
            -  editcategory - Edit a Category
            -  editcategoryitem.html - Edit a Category Item
            -  formerrors.html - Template to display form entry errors
            -  header.html - Top page links, Login and home page
            -  login.html - Login Page
            -  main.html - Main application page.  Load style sheets and bootstrap
            -  newcategory.html - Setup a new category
            -  newcategoryitem.html - Create a new Category Item
            -  publiccategoryitems.html - Category Item list for non-authenticated users
            -  publiccategories.html - Category List for non-authenticated users
       
	### Python version 2.7.6 installed
	
Setup Instructions
------------------
	
    Run Application
    ---------------
    1.  Run application.py to start server
    2.  Go to localhost:5000 to see main page 
    
    To Add Categories and Items
    ---------------------------
    1.  Go to localhost:5000/login
    2.  Login using your Google account
    3.  If successful, you will be redirected to the main page.  An 
        'Add Category' button shuld appear
        
    Load Sample Data
    ----------------
    If you would like to see an example of the application in action just
    follow the below instructions:
    1.  Run samplecategories.py
    2.  Run application.py to start the server
    3.  Go to localhost:5000 to see the main page.  3 Categories and a number
        of items will have been created
       
             
Database Schema
---------------
    The database is an SQLite database and it consists of 3 tables.
    
    Tables
        User - User Information of individuals who have successfully logged in
        Category - Basic Category Information
        CategoryItem - Information for a Category Item.  One Category can have
                       zero to many CategoryItems

                       