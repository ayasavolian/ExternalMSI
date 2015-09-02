'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

File Description:         This is the logic layer for the MSI application.
Author:                   Arrash Yasavolian
Date:                     9/2/2015
Team:                     MarketoLive

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from flask import session
import httplib2
import json
import urllib2
import operator
from soap import *
import xml.etree.ElementTree as ET

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

Purpose:      This function will return the list of best bets from our Marketo
              instance with best lead first
Description:  This uses an API call to get leads that exist in a list that we've defined within Marketo.
              The reason for this is because we can then create a list and update the list for every sales
              rep we have and create personalized Best Bets dashboards for each of them so they can easily
              see their prioritized leads. If it hasn't been done yet, the first step then should be to go 
              into Marketo and create a list within the lead database that you can reference here. 
              We use the "Get Multiple Leads by List Id" API call at developers.marketo.com after. 

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


def get_msi_data():

  '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

  Following the beginning steps at developers.marketo.com, we're first going to authenticate and get our access token
  using our marketo instance ID, our client Id, and our client_secret

  '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

  instance_id = "###-###-###"
  client_id = "#######-####-#####-##"
  client_secret = "##############-########"
  list_id = "####"

  get_token = urllib2.Request('https://'+instance_id+'.mktorest.com/identity/oauth/token?grant_type=client_credentials&client_id='+client_id+'&client_secret='+client_secret)
  token_response = urllib2.urlopen(get_token)
  get_token_convert = json.loads(token_response.read())
  token = get_token_convert['access_token']
  pageToken = True
  x = 0
  created_resp = []
  final_list = {}

  '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

  If the list of leads is greater than 300 we'll need to loop through the list using a pagingToken to grab the rest of 
  the leads

  '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

  while pageToken:
    if x == 0:
      req = urllib2.Request('https://'+instance_id+'.mktorest.com/rest/v1/list/'+list_id+'/leads.json?access_token='+token+'&fields=firstName,id,company,title,lastName,leadScore,relativeScore')
    else:
      req = urllib2.Request('https://'+instance_id+'.mktorest.com/rest/v1/list/'+list_id+'/leads.json?access_token='+token+'&nextPageToken='+paging+'&fields=firstName,id,company,title,lastName,leadScore,relativeScore')
    full_resp = json.loads(urllib2.urlopen(req).read())
    if 'nextPageToken' in full_resp:
      paging = full_resp['nextPageToken']
      created_resp.extend(full_resp['result'])
    else:
      pageToken = False
    x += 1 

  '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

  We'll then sort the list of leads by their leadScore. We can do additional logic here to organize it by the engagement score

  '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

  final_list = sorted(created_resp, key = lambda person : person['leadScore'], reverse=True)
  return final_list[:49]


'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

Purpose:      This function will grab an individual lead and all of their activity from Marketo
Description:  This uses the REST API to grab all of the fields/information from the lead record that we want based
              on the lead's ID which is passed from our API layer to our get_person function. We can
              then display this as their "record". We also use the SOAP API to grab the user's activity from Marketo.
              We reference a SOAP wrapper class created in order to use the SOAP API calls. 
              Instead of using a pageToken, I instead just used 4 different API calls with different filterTypes to grab
              their email activity, web activity, score change activity, and their interesting moments from Marketo.

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


def get_person(passed_id):
  score_list = []
  moments_list = []
  webpage_list = []
  email_list = []

  '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

  We'll grab the user's field information using the REST API. 

  '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

  get_token = urllib2.Request('https://'+instance_id+'.mktorest.com/identity/oauth/token?grant_type=client_credentials&client_id='+client_id+'&client_secret='+client_secret)
  token_response = urllib2.urlopen(get_token)
  get_token_convert = json.loads(token_response.read())
  token = get_token_convert['access_token']
  req = urllib2.Request('https://'+instance_id+'.mktorest.com/rest/v1/lead/'+passed_id+'.json?access_token='+token+'&fields=firstName,email,id,company,phone,title,country,state,city,postalCode,lastName,leadScore,relativeScore,industry')
  payload = json.loads(urllib2.urlopen(req).read())

  '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

  We'll set the SOAP API values that we'll need to reference using our marketo instance

  '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

  marketo_soap_endpoint     = "################"
  marketo_user_id           = "################"
  marketo_secret_key        = "################"
  marketo_name_space        = "################"

  '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

  Using our SOAP wrapper we'll initiate our client in order to make our calls. 

  '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

  client = Client(marketo_soap_endpoint, marketo_user_id, marketo_secret_key)

  '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

  Once we're initiated, we can start making our 4 different API Calls. The first
  call we'll start with is interesting moments. Within the array of objects response_list
  we'll need to iterate through it and grab the important information. We'll then store it in
  an array of dictionaries. 

  '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

  moments_response = client.get_lead_activity(passed_id, "IDNUM", "Interesting Moments")
  for response_list in moments_response.activityRecordList:
    for activity in response_list[1]:
      activity_type = activity.activityType
      activity_datetime = activity.activityDateTime
      activity_mktg_asset_name = activity.mktgAssetName
      activity_description = ""
      activity_score_value = ""
      for attributes in activity.activityAttributes:
        for attribute in attributes[1]:
          if attribute.attrName == "Description":
            activity_description = attribute.attrValue
      moments_list.append(dict(activity_type = activity_type, activity_datetime = activity_datetime, activity_mktg_asset_name = activity_mktg_asset_name, activity_description = activity_description, activity_score_value = activity_score_value))    

  '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

  The second call we'll make is to grab the webpage activity. We'll then store it in
  an array of dictionaries 

  '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

  webpage_response = client.get_lead_activity(passed_id, "IDNUM", "Website Activity")
  for response_list in webpage_response.activityRecordList:
    for activity in response_list[1]:
      activity_type = activity.activityType
      activity_datetime = activity.activityDateTime
      activity_mktg_asset_name = activity.mktgAssetName
      activity_description = ""
      activity_score_value = ""
      webpage_list.append(dict(activity_type = activity_type, activity_datetime = activity_datetime, activity_mktg_asset_name = activity_mktg_asset_name, activity_description = activity_description, activity_score_value = activity_score_value))    

  '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

  The third call we'll make is to grab the score activity. We'll then store it in
  an array of dictionaries 

  '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

  score_response = client.get_lead_activity(passed_id, "IDNUM", "Score")
  for response_list in score_response.activityRecordList:
    for activity in response_list[1]:
      activity_type = activity.activityType
      activity_datetime = activity.activityDateTime
      activity_mktg_asset_name = activity.mktgAssetName
      activity_description = ""
      activity_score_value = ""
      for attributes in activity.activityAttributes:
        for attribute in attributes[1]:
          if attribute.attrName == "Change Value":
            activity_description = attribute.attrValue
      score_list.append(dict(activity_type = activity_type, activity_datetime = activity_datetime, activity_mktg_asset_name = activity_mktg_asset_name, activity_description = activity_description, activity_score_value = activity_score_value))    

  '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

  The fourth call we'll make is to grab the email activity. We'll then store it in
  an array of dictionaries 

  '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

  email_response = client.get_lead_activity(passed_id, "IDNUM", "Email Activity")
  for response_list in email_response.activityRecordList:
    for activity in response_list[1]:
      activity_type = activity.activityType
      activity_datetime = activity.activityDateTime
      activity_mktg_asset_name = activity.mktgAssetName
      activity_description = ""
      activity_score_value = ""
      email_list.append(dict(activity_type = activity_type, activity_datetime = activity_datetime, activity_mktg_asset_name = activity_mktg_asset_name, activity_description = activity_description, activity_score_value = activity_score_value))    

  '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

  We'll then take all four arrays and store it in an object which we'll return back to
  our API layer to pass to our templating engine to show the information

  '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

  return_array = {"info" : payload['result'], "email": email_list, "score": score_list, "webpage": webpage_list, "moments": moments_list}
  return return_array
