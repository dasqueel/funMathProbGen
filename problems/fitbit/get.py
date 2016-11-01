from flask import redirect, url_for
from pymongo import MongoClient
import json
from rauth import OAuth2Service
import requests
import base64

#connect to mongo
client = MongoClient('localhost')
userDb = client.Users

#aux funcs
def most_common(lst):
    return max(set(lst), key=lst.count)

def remove_values_from_list(the_list, val):
   return [value for value in the_list if value != val]

#get a new access token
#returns a string if successful or not
def getAccessFitbit(userName):
    #check to see if already authorized
    userDoc = userDb[userName].find_one({'userName':userName})
    imported = userDoc['imported']
    access_token = None
    refresh_token = None
    #check to see if user as already imported
    for imprt in imported:
        if imprt['provider'] == 'fitbit':
            access_token = imprt['accessToken']
            refresh_token = imprt['refreshToken']
    if access_token == None:
        print 'should get access'
        #first time adding fibit to imported
        #sets up authorization for user to user fitbit
        scopes = 'activity heartrate nutrition profile sleep weight'
        service = OAuth2Service(
                   name='fitbit',
                   client_id='227G4B',
                   client_secret='91d95c06c8d0558a0509c4f844696280',
                   access_token_url='https://api.fitbit.com/oauth2/token',
                   authorize_url='https://www.fitbit.com/oauth2/authorize')

        # the return URL is used to validate the request
        params = {'redirect_uri': 'http://127.0.0.1:5000/oauth2/fitbit',
                  'response_type': 'code',
                  'scope': scopes,
                  'client_id':'227G4B'}
        auth_url = service.get_authorize_url(**params)
        return redirect(auth_url)
    else:
        #refresh access token
        #access token is expired
        client_id = "227G4B"
        client_secret = "91d95c06c8d0558a0509c4f844696280"
        concat = client_id+":"+client_secret
        url = 'https://api.fitbit.com/oauth2/token'
        base = base64.b64encode(concat)
        headers = {"Authorization":"Basic " + base,"Content-Type":"application/x-www-form-urlencoded"}
        payload = {'grant_type':'refresh_token','refresh_token':refresh_token,'redirect_uri' : 'http://127.0.0.1:5000/oauth2/fitbit'}
        r = requests.post(url, params=payload,headers=headers)

        newAT = r.json()['access_token']
        newRT = r.json()['refresh_token']
        #update new tokens
        userDb[userName].update({'userName':userName,'imported.provider':'fitbit'},{'$set':{'imported.$.accessToken':newAT,'imported.$.refreshToken':newRT}})

        #get userData
        resource_url = 'https://api.fitbit.com/1/user/-/profile.json'
        headers = {'Authorization':'Bearer '+newRT}
        r = requests.get(resource_url, headers=headers)
        return 'added new access token'

def fitbitData(userName):
    #check to see if already authorized
    userDoc = userDb[userName].find_one({'userName':userName})
    imported = userDoc['imported']
    access_token = refresh_token = None
    #check to see if user as already imported
    for imprt in imported:
        if imprt['provider'] == 'fitbit':
            access_token = imprt['accessToken']
            refresh_token = imprt['refreshToken']
    date = 'today'
    period = '1y'
    resourcesUrls = [
        {'path':'activities/tracker/steps','key':'activities-tracker-steps','defaultVal':['0'],'dataKey':'recentSteps','unit':'steps taken'},
        {'path':'activities/tracker/distance','key':'activities-tracker-distance','defaultVal':['0.0'],'dataKey':'recentDistance','unit':'miles covered'},
        {'path':'activities/tracker/minutesSedentary','key':'activities-tracker-minutesSedentary','defaultVal':['1440'],'dataKey':'recentMinutesSedentary','unit':'sedentary mintues'},
        {'path':'activities/tracker/calories','key':'activities-tracker-calories','defaultVal':['1947','1952'],'dataKey':'recentCalories','unit':'calories burned'}
    ]
    #this is the dict where the available data will be stored
    data = {}
    for resource in resourcesUrls:
        resourcePath = resource['path']
        resource_url = 'https://api.fitbit.com/1/user/-/'+resourcePath+'/date/'+date+'/'+period+'.json'
        headers = {'Authorization':'Bearer '+access_token}
        r = requests.get(resource_url, headers=headers)
        if r.status_code == 401:
            #access token is expired, so get a new one
            #update access token
            if getAccessFitbit(userName) == 'added new access token':
                #restart function
                return fitbitData(userName)
            else:
                return 'error in refreshing access token'
        else:
            #data = {'recentSteps':None}
            resp = r.json()
            units = resp[resource['key']]
            units[:] = [d for d in units if d.get('value') not in resource['defaultVal']]
            units = units[::-1]
            #only add stats which there is data
            if len(units) != 0:
                finalData = []
                for datum in units:
                    rnd = round(float(datum['value']),2)
                    #rnd = float("{0:.2f}".format(i['value']))
                    finalData.append(rnd)
                mostcom = most_common(finalData)
                if float(finalData.count(mostcom))/float(len(finalData)) > 0.33:
                    #filter mostcom
                    finalData = remove_values_from_list(finalData, mostcom)
                data[resource['dataKey']] = finalData
    return data
