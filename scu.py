'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

File Description:         This is the API layer for the MSI application.
Author:                   Arrash Yasavolian
Date:                     9/2/2015
Team:                     MarketoLive

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#Imported libraries that we'll be using.

from flask import Flask, render_template, redirect, jsonify, request, url_for, session
import httplib2
import json
from urllib import urlencode
from logic import run_class, get_msi_data, get_person
import string
import random
import os

#initiation of our flask server

app = Flask(__name__)


#Set your secret key here that can be used for security purposes

app.secret_key = "###"

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

Purpose:      This is the route that will lead to the best bets dashboard
Description:  This route uses a function in the logic layer (logic.py) that 
              will use API calls from developers.marketo.com to pull information
              using the REST API from a marketo instance. It will then pass 
              that information to our templating engine (jinja2) for msi.html

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

@app.route('/msi')
def msi():
  msi_list = get_msi_data()
  return render_template('apps/msi.html',
                         user = session['username'],
                         msi_list = msi_list)


'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

Purpose:      This will allow us to see an individual who we click on from Best Bets
Description:  This route uses a function in the logic layer (logic.py) that will be 
              passed a leads ID and will then use that lead ID to pull a person's information 
              using API calls from developers.marketo.com (both SOAP & REST) from a marketo instance. 
              It will then pass that information to our templating engine for msi-person.html

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


@app.route('/person')
def person():
  person_id = request.args.get("id")
  person = get_person(person_id)
  return render_template('apps/msi-person.html',
                         user = session['username'],
                         person = person['info'][0],
                         moments = person['moments'],
                         webpage = person['webpage'],
                         email = person['email'],
                         score = person['score'])

#intiatiing main for our flask server to run

if __name__ == '__main__':
    app.secret_key = "###"
    app.run()
