RESTful event call test
===================

What is this?
-------------
This is a test project for learning ryu event handling by using RESTful
interface.
RESTful service is create by [Django REST
Framework](http://www.django-rest-framework.org/)

Structure
---------
![Structure](https://raw.githubusercontent.com/TakeshiTseng/SDN-Work/master/rest_event_test/structure.png)

Install
-------
Before use it, you need to install:

> 1. [Python 2.7.6 or higher](https://www.python.org/)
> 2. [Ryu SDN Framework](https://osrg.github.io/ryu/)
> 3. [Django](https://www.djangoproject.com/)
> 4. [Django REST Framework](http://www.django-rest-framework.org/)

How to use it?
--------------
Start ryu application
> $ ryu-manager simple_event_app.py

Start restful server
> $ python manager runserver 0.0.0.0:8000

Send request to RESTful service
> $ curl lab.takeshi.tw:8000/hello



