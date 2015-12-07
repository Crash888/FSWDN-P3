from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
 
from database_setup import Base, Category, CategoryItem, User

import shutil
 
engine = create_engine('sqlite:///catalogmenu.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine
 
DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create dummy user
User1 = User(name="John Smith", email="john_smith@sample.com",
             picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User1)
session.commit()

#Movie Category
category1 = Category(user_id=1, name = "Movies")

session.add(category1)
session.commit()


categoryItem1 = CategoryItem(user_id=1, name = "Inside Out", description = "Fun movie for kids", picture = "inside_out.jpg", category = category1)

session.add(categoryItem1)
shutil.copyfile('samplecategories_images/inside_out.jpg', 'static/images/inside_out.jpg')
session.commit()

categoryItem2 = CategoryItem(user_id=1, name = "The Avengers: Age of Ultron", description = "Action superhero movie", picture = "avengers_aou.jpg", category = category1)

session.add(categoryItem2)
shutil.copyfile('samplecategories_images/avengers_aou.jpg', 'static/images/avengers_aou.jpg')
session.commit()

categoryItem3 = CategoryItem(user_id=1, name = "The Terminator", description = "Fun sci-fi movie", picture = "terminator.jpg", category = category1)

session.add(categoryItem3)
shutil.copyfile('samplecategories_images/terminator.jpg', 'static/images/terminator.jpg')
session.commit()


#Albums Category
category1 = Category(user_id=1, name = "Albums")

session.add(category1)
session.commit()


categoryItem1 = CategoryItem(user_id=1, name = "Led Zeppelin IV", description = "Led Zeppelin - 1971 Hard Rock", picture = "Led_Zeppelin_-_Led_Zeppelin_IV.jpg", category = category1)

session.add(categoryItem1)
shutil.copyfile('samplecategories_images/Led_Zeppelin_-_Led_Zeppelin_IV.jpg', 'static/images/Led_Zeppelin_-_Led_Zeppelin_IV.jpg')
session.commit()

categoryItem2 = CategoryItem(user_id=1, name = "Thriller", description = "Michael Jackson - 1982.  Best Selling album of all time.", picture = "Michael_Jackson_Thriller.png", category = category1)

session.add(categoryItem2)
shutil.copyfile('samplecategories_images/Michael_Jackson_Thriller.png', 'static/images/Michael_Jackson_Thriller.png')
session.commit()

categoryItem3 = CategoryItem(user_id=1, name = "Dark Side of the Moon", description = "Pink Floyd - 1973.  3rd Best Selling album of all time", picture = "PinkFloyd-Dark_Side_of_the_Moon.png", category = category1)

session.add(categoryItem3)
shutil.copyfile('samplecategories_images/PinkFloyd-Dark_Side_of_the_Moon.png', 'static/images/PinkFloyd-Dark_Side_of_the_Moon.png')
session.commit()

categoryItem4 = CategoryItem(user_id=1, name = "Black Album", description = "Metallica - 1991.  Great heavy metal tunes.", picture = "", category = category1)

session.add(categoryItem4)
session.commit()

categoryItem5 = CategoryItem(user_id=1, name = "One Elephant, Deux Elephants", description = "Sharon, Lois and Bram - 1978.  Yes, cannot forget the kids music", picture = "OneElephant1.jpg", category = category1)

session.add(categoryItem5)
shutil.copyfile('samplecategories_images/OneElephant1.jpg', 'static/images/OneElephant1.jpg')
session.commit()


categoryItem6 = CategoryItem(user_id=1, name = "Please Hammer, Don't Hurt 'Em", description = "MC Hammer - 1990.  Shhhh...don't tell anybody I have this one.", picture = "Please_Hammer_Don't_Hurt_'Em.jpg", category = category1)

session.add(categoryItem6)
shutil.copyfile("samplecategories_images/Please_Hammer_Don't_Hurt_'Em.jpg", "static/images/Please_Hammer_Don't_Hurt_'Em.jpg")
session.commit()

#Books Category
category1 = Category(user_id=1, name = "Books")

session.add(category1)
session.commit()


categoryItem1 = CategoryItem(user_id=1, name = "The Lord of the Rings", description = "J.R.R. Tolkien - 1954.  Awesome Series.  Movies were good as well", picture = "First_Single_Volume_Edition_of_The_Lord_of_the_Rings.gif", category = category1)

session.add(categoryItem1)
shutil.copyfile('samplecategories_images/First_Single_Volume_Edition_of_The_Lord_of_the_Rings.gif', 'static/images/First_Single_Volume_Edition_of_The_Lord_of_the_Rings.gif')
session.commit()

categoryItem2 = CategoryItem(user_id=1, name = "The Da Vinci Code", description = "Dan Brown - 2003.  Pretty good book.  Over 80 Million Sold", picture = "DaVinciCode.jpg", category = category1)

session.add(categoryItem2)
shutil.copyfile('samplecategories_images/DaVinciCode.jpg', 'static/images/DaVinciCode.jpg')
session.commit()


print "added category items!"

