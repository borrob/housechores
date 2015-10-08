# housechores
> When was the last time we swept the floor?

## Introducton
Live is always busy and you hardly ever *want* to do chores, but from time to time, you *have to*. Some chores have to be done more regularly than others. Especially for the chores that you don't need to do very often -like: clean and deforst the fridge- I always loose track on when the last time was when we did this.

To keep track on all the house chores and making sure every one of them is done regularly (not too late, but also not too early), I made this small application. It shows list overviews of all the chores and your actions. How many days ago the bed sheets were changes, how many days since showing the vacuum cleaner around the house: all these chores are presented in a nice and clear table.

## Technology
The application is written in python and makes use of the [Flask microframework](http://flask.pocoo.org). The application manages a simple database. I used [sqlite](https://www.sqlite.org), but you can plug your favourite databse in there if you want to. There is [bootstrap](http://getbootstrap.com) to make everything look nice.

## Install
Make sure you have python and flask installed. You can start the application by running the python file 'housechores.py' in the 'app' directory. Open a browser and goto [localhost:5000](http://localhost:5000). You can also install the application under apache with the wsgi module. I've included a simple example conf-file for the configuration setup.

## Current version
The current version is 0.3.

## Questions and suggestions
Any questions or suggestions? Let me know. Leave a comment or open an issue. Thank you.
