import flask
from flask import *
from passlib.hash import pbkdf2_sha256
from operator import itemgetter
import datetime
from rauth import OAuth1Service
import requests
from oauth import *
from problems.probs import createProbs
from random import randint
import datetime

app = flask.Flask(__name__)
app.secret_key = 'super secret string'

import flask.ext.login as flask_login

login_manager = flask_login.LoginManager()

login_manager.init_app(app)

from pymongo import MongoClient
from rauth import OAuth2Service
import base64

#connect to mongo
client = MongoClient('localhost')
userDb = client.Users
generalDb = client.General

generalDoc = generalDb['general'].find_one({'doc':'general'})
registeredEmails = generalDoc['registeredEmails']
userNameEmails = generalDoc['userNameEmail']
registeredUserNames = generalDoc['registeredUserNames']

class User(flask_login.UserMixin):
    def __init__(self, userName, email, firstName):
            self.userName = userName
            self.id = email
            self.email = email
            self.firstName = firstName

            @property
            def is_authenticated(self):
                return True

            @property
            def is_active(self):
                return True

            @property
            def is_anonymous(self):
                return False

            def get_id(self):
                try:
                    return unicode(self.id)  # python 2
                except NameError:
                    return str(self.id)  # python 3

            def __repr__(self):
                return '<User %r>' % (self.userName)

@login_manager.user_loader
def user_loader(email):
    generalDoc = generalDb['general'].find_one({'doc':'general'})
    registeredEmails = generalDoc['registeredEmails']
    userNameEmails = generalDoc['userNameEmail']

    if email not in registeredEmails:
        return
    userName = None
    for user in userNameEmails:
        if user['email'] == email:
            userName = user['userName']
    #from email get users attributes, firstName, etc...
    userDoc = userDb[userName].find_one({'userName':userName})
    user = User(userName,email,userDoc['firstName'])

    return user

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    elif request.method == 'POST':
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        email = request.form['email']
        pwd = request.form['pwd']
        rpwd = request.form['rpwd']
        hashpwd = pbkdf2_sha256.encrypt(pwd, rounds=20000, salt_size=16)

        #start checking user validation
        error = None
        if email=='' or firstName=='' or lastName=='' or pwd=='' or rpwd=='':
            error = 'please fill in all data'
            return render_template('register.html', error=error)
        elif pwd != rpwd:
            error = 'passwords dont match, try again'
            return render_template('register.html', error=error)
        elif email in registeredEmails:
            error = email+' has already been registered'
            return render_template('register.html', error=error)
        else:
            #insert the user to database

            #create an unqiue userName
            invalidUserNames = ['questions','login','archived','liked','import','logout']
            userName = None
            if (firstName+lastName).lower() not in registeredUserNames:
                userName = str((firstName+lastName).lower())
            elif (lastName+firstName).lower() not in registeredUserNames:
                userName = str((lastName+firstName).lower())
            else:
                #do the number naming
                x = 1
                while(x < 200):
                    if (firstName+lastName+str(x)).lower() not in registeredUserNames:
                        userName = str((firstName+lastName+str(x)).lower())
                        break
                    else:
                        x += 1
                        pass
            userDoc = {
                'userName':userName,
                'firstName':firstName,
                'lastName':lastName,
                'pwd':hashpwd,
                'email':email,
                'imported':[]
            }

            #create mongo stuff
            userCol = userDb[userName]
            userCol.insert(userDoc)

            #add userName and email to registered
            userNameEmail = {"userName":userName,"email":email}
            generalDb['general'].update({"doc":"general"},{"$push":{"registeredEmails":email,"registeredUserNames":userName,"userNameEmail":userNameEmail}})

            #create session for user
            user = User(userName,email,firstName)

            flask_login.login_user(user)

            return redirect(url_for('home'))

@app.route('/login', methods=['GET','POST'])
def login():
    error = None

    if request.method == 'GET':
        return render_template('login.html')

    elif request.method == 'POST':
        email = request.form['email']

        #get userName from email
        userName = None
        for user in userNameEmails:
            if user['email'] == email:
                userName = user['userName']
        userDoc = userDb[userName].find_one({'userName':userName})
        #check to see if email is registered
        if email not in registeredEmails:
            error = email+' is not registered.'
            return render_template('login.html',error=error)
        #proceed to checking password
        else:
            pwd = request.form['pwd']
            userDoc = userDb[userName].find_one({'userName':userName})
            hashpwd = userDoc['pwd']
            pwdCheck = pbkdf2_sha256.verify(pwd, hashpwd)
            if pwdCheck == False:
                error = 'incorrect password'
                return render_template('login.html',error=error)
            else:
                #creating the session

                user = User(userName,email,userDoc['firstName'])

                flask_login.login_user(user)
                return redirect(url_for('home'))
    else:
        return render_template('login.html')

@app.route('/logout')
def logout():
    flask_login.logout_user()
    #return 'Logged out'
    return redirect(url_for('login'))

@login_manager.unauthorized_handler
def unauthorized_handler():
    return redirect(url_for('login'))

##### concepts end points #####
@app.route('/<userName>')
def profile(userName):
    #get userDoc and display users information
    userCol = userDb[userName]

    #grab all of users conceptLinkObjs
    userCursor = userCol.find({"concept":{'$exists': True}})
    userLinks = []
    for concept in userCursor:
        for expl in concept['explanations']:
            userLinks.append(expl)
        for expl in concept['practice']:
            userLinks.append(expl)

    return render_template('profile.html', userName=userName, userLinks=userLinks)

@app.route('/home')
@flask_login.login_required
def home():
    #get all users concepts
    return render_template('home.html')

@app.route('/problem')
@flask_login.login_required
def choose():
    return render_template('choose.html')

@app.route('/problem/<concept>')
@flask_login.login_required
def select(concept):
    #return listing of provider contexts
    userDoc = userDb[flask_login.current_user.userName].find_one({'userName':flask_login.current_user.userName})
    imported = userDoc['imported']
    providers = []
    for imprt in imported:
        providers.append(imprt['provider'])
    return render_template('select.html',concept=concept,providers=providers)

@app.route('/import', methods=['GET','POST'])
@flask_login.login_required
def imports():
    if request.method == 'GET':
        return render_template('import.html')
    elif request.method == 'POST':
        provider = request.form.get("provider")
        khan(flask_login.current_user.userName)
        return 'Khan Academy experience updated!'
        #return provider

@app.route('/importProvider')
@flask_login.login_required
def importProvider():
    #provider = request.form['provider']
    provider = request.args.get("provider")
    if provider == 'khan':
        return khan(flask_login.current_user.userName)
    elif provider == 'league':
        return redirect(url_for('importleague'))
        #or could have a popup asking for summoner name, instead of redirecting to importLeague
    elif provider == 'yahoo':
        return yahoo(flask_login.current_user.userName)
    elif provider == 'fitbit':
        return fitbit(flask_login.current_user.userName)

@app.route('/requesttoken')
@flask_login.login_required
def requesttoken():
    userName = flask_login.current_user.userName
    #callback for service, get access token and store it
    #provider = request.args.get('provider')
    oauth_token_secret = request.args.get('oauth_token_secret')
    oauth_verifier = request.args.get('oauth_verifier')
    oauth_token = request.args.get('oauth_token')

    request_token = OAuthToken(oauth_token, oauth_token_secret)
    request_token.set_verifier(oauth_verifier)

    if provider == 'khan':
        consumer = OAuthConsumer('9YrRjqYAjMWWF7ZP','Y45DZt2vCGV9w8W2')

        oauth_request = OAuthRequest.from_consumer_and_token(
                consumer,
                token=request_token,
                verifier=request_token.verifier,
                http_url="https://www.khanacademy.org/api/auth/access_token"
                )

        oauth_request.sign_request(OAuthSignatureMethod_HMAC_SHA1(), consumer, request_token)

        resp = urllib2.urlopen(oauth_request.to_url())
        accessToken = resp.read()
        #store access token
        #check to see if its first time importing or refreshing the token
        #refresh a token
        if userDb[userName].find_one({'userName':userName,'imported.site':provider}):
            userDb[userName].update({'userName':userName,'imported.site':provider},{'$set':{'imported.$.accessToken':accessToken}})
            #return redirect(url_for('imports'))
            return khan(userName)
        #first time importing
        else:
            #make /api/v1/user call to get users khan username
            access_token = OAuthToken.from_string(accessToken)
            oauth_request = OAuthRequest.from_consumer_and_token(
                    consumer,
                    token=access_token,
                    http_url="https://www.khanacademy.org/api/v1/user"
                    )
            oauth_request.sign_request(OAuthSignatureMethod_HMAC_SHA1(), consumer, access_token)

            resp = urllib2.urlopen(oauth_request.to_url())
            response = resp.read()
            respJson = json.loads(response)
            khanUsername = respJson['student_summary']['username']

            doc = {'provider':provider,'accessToken':accessToken,'providerUsername':khanUsername}
            userDb[userName].update({'userName':userName},{'$push':{'imported':doc}})
            #return redirect(url_for('imports'))
            return khan(userName)
    elif provider == 'yahoo':
        consumer = OAuthConsumer('dj0yJmk9cFJDT2lHalFmbWJRJmQ9WVdrOWJYbDBTa3MxTTJVbWNHbzlNQS0tJnM9Y29uc3VtZXJzZWNyZXQmeD1iMA','87415c3786bd2d835644ff7a65949c6f5ecb4c32')

        oauth_request = OAuthRequest.from_consumer_and_token(
                consumer,
                token=request_token,
                verifier=request_token.verifier,
                http_url="https://www.khanacademy.org/api/auth/access_token"
                )

        oauth_request.sign_request(OAuthSignatureMethod_HMAC_SHA1(), consumer, request_token)

        resp = urllib2.urlopen(oauth_request.to_url())
        accessToken = resp.read()

#uri for refreshing oauth2 token
@app.route('/oauth2/<provider>')
@flask_login.login_required
def oauth2(provider):
    if provider == 'fitbit':
        userName = flask_login.current_user.userName
        client_id = "227G4B"
        client_secret = "91d95c06c8d0558a0509c4f844696280"
        concat = client_id+":"+client_secret
        url = 'https://api.fitbit.com/oauth2/token'
        base = base64.b64encode(concat)
        code = request.args.get('code')

        headers = {"Authorization":"Basic " + base,"Content-Type":"application/x-www-form-urlencoded"}
        payload = {'code': code,
                'redirect_uri' : 'http://127.0.0.1:5000/oauth2/fitbit',
                'grant_type': 'authorization_code',
                'client_id':'227G4B'}
        r = requests.post(url, params=payload,headers=headers)
        access_token = r.json()['access_token']
        refresh_token = r.json()['refresh_token']
        #store the tokens
        if userDb[userName].find_one({'userName':userName,'imported.provider':'fitbit'}):
            userDb[userName].update({'userName':userName,'imported.provider':'fitbit'},{'$set':{'imported.$.accessToken':access_token,'imported.$.refreshToken':refresh_token}})
        else:
            doc = {'provider':'fitbit','accessToken':access_token,'refreshToken':refresh_token,'providerFull':'Fitbit'}
            userDb[userName].update({'userName':userName},{'$push':{'imported':doc}})

        return redirect(url_for('importdata'))

@app.route('/getAccessToken')
@flask_login.login_required
def getAccessToken():
    #provider = request.args.get('provider')
    consumer = OAuthConsumer('9YrRjqYAjMWWF7ZP','Y45DZt2vCGV9w8W2')
    callback = 'http://127.0.0.1:5000/requesttoken'
    oauth_request = OAuthRequest.from_consumer_and_token(
            consumer,
            callback=callback,
            http_url="https://www.khanacademy.org/api/auth/request_token"
            )

    oauth_request.sign_request(OAuthSignatureMethod_HMAC_SHA1(), consumer, None)
    return redirect(oauth_request.to_url())

@app.route('/importleague', methods=['GET','POST'])
@flask_login.login_required
def importleague():
    if request.method == 'GET':
        return render_template('/importleague.html')
    elif request.method == 'POST':
        summonername = request.form['summonername']
        #add to import
        if userDb[flask_login.current_user.userName].find_one({'userName':flask_login.current_user.userName,'imported.provider':'league'}):
            userDb[flask_login.current_user.userName].update({'userName':flask_login.current_user.userName,'imported.provider':'league'},{'$set':{'imported.$.providerUsername':summonername}})
            return redirect(url_for('importdata'))
        else:
            importObj = {'provider':'league','providerUsername':summonername,'providerFull':'League of Legends'}
            userDb[flask_login.current_user.userName].update({'userName':flask_login.current_user.userName},{'$push':{'imported':importObj}})
            return redirect(url_for('importdata'))

@app.route('/importdata', methods=['GET','POST'])
@flask_login.login_required
def importdata():
    if request.method == 'GET':
        userName = flask_login.current_user.userName
        provList = ['fitbit','league']
        providers = [{'name':'League of Legends','varName':'league'},{'name':'Fitbit','varName':'fitbit'}]
        imported = []
        userDoc = userDb[userName].find_one({'userName':userName})
        for imprt in userDoc['imported']:
            if imprt['provider'] in provList:
                provObj = [d for d in providers if d.get('varName') == imprt['provider']][0]
                imported.append(provObj)
                #remove from providers
                providers[:] = [d for d in providers if d.get('varName') != imprt['provider']]
        return render_template('importdata.html',providers=providers,imported=imported)
    elif request.method == 'POST':
        #add providers to imported
        #data = request.form.getlist('data[]')
        #do provider oauth if necessary, store token and add to imports
        provider = request.form['provider']
        if provider == 'fitbit':
            if getAccessFitbit(flask_login.current_user.userName) == 'added new access token':
                #return render_template('importdata')
                return 'refreshed token'
            else:
                return 'problem'
        else:
            return 'nope'

@app.route('/accesstoken')
@flask_login.login_required
def accesstoken():
    provider = request.args.get("provider")
    if provider == 'fitbit':
        userName = flask_login.current_user.userName
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

@app.route('/problemmenu')
def problemmenu():
    #get users imported providers
    error = None
    redirectError = request.args.get('error')
    if redirectError:
        error = request.args.get('error')
    userDoc = userDb[flask_login.current_user.userName].find_one({'userName':flask_login.current_user.userName})
    imported = userDoc['imported']
    providers = []
    for imprt in imported:
        imprtObj = {}
        imprtObj['full'] = imprt['providerFull']
        imprtObj['val'] = imprt['provider']
        providers.append(imprtObj)
    return render_template('prob2.html', providers=providers, error=error)

@app.route('/problem/<concept>/<provider>', methods=['GET','POST'])
@flask_login.login_required
def problem(concept,provider):
    concept = concept.lower()
    userName = flask_login.current_user.userName
    if request.method == 'GET':
        providerUN = None
        userDoc = userDb[userName].find_one({'userName':userName})
        for imprt in userDoc['imported']:
            if imprt['provider'] == provider:
                if 'providerUsername' in imprt.keys():
                    providerUN = imprt['providerUsername']
        #create probs
        probs = None
        if concept == 'standard deviation':
            probs = createProbs(concept='standard deviation',popSize=5,provider=provider,providerUN=providerUN,userName=userName)
        elif concept == 'population standard deviation':
            probs = createProbs(concept='population standard deviation',popSize=5,provider=provider,providerUN=providerUN,userName=userName)
        elif concept == 'mean':
            probs = createProbs(concept='mean',popSize=5,provider=provider,providerUN=providerUN,userName=userName)
        elif concept == 'variance':
            probs = createProbs(concept='variance',popSize=5,provider=provider,providerUN=providerUN,userName=userName)
        elif concept == 'population variance':
            probs = createProbs(concept='population variance',popSize=5,provider=provider,providerUN=providerUN,userName=userName)

        #return problem
        if probs != []:
            #check to see if the users conceptDoc is created
            userDb[userName].find_one({'userName':userName})
            #grab random prob from the 5 generated (probably should only generate one)
            rand = randint(0,len(probs)-1)
            prob = probs[rand]
            prob['dataStr'] = str(prob['data'])[1:-1]
            now = datetime.datetime.utcnow()
            userDb[userName].update({"type":"problem","concept":prob['concept']},{"$push":{"problems":prob},"$set":{"lastVisit":now}})
            #update concepts listVisit
            return render_template('problem.html', prob=prob,concept=concept)
        #insufficient data to create problem
        else:
            #insufficient data for problem
            error = 'There is not enough '+provider+' data to generate problems.  Try using your '+provider+' account to generate more data.'
            return redirect(url_for('problemmenu',error=error))

    #checking answer code
    elif request.method == 'POST':
        probId = request.form['probId']
        concept = request.form['concept']
        outcome = request.form['outcome']
        usersAnswer = request.form['usersAnswer']
        now = datetime.datetime.utcnow()

        #if outcome is incorrect: increment attempts
        if outcome == 'incorrect':
            #increment problem attempts
            userDb[userName].update({"type":"problem",'concept':concept,'problems.id':probId},{'$inc':{'problems.$.attempts':1},'$push':{'problems.$.answersGiven':usersAnswer},'$set':{'lastVisit':now}})
            #add usersAnswer to answersGiven
            #userDb[userName].update({"type":"problem",'concept':concept,'problems.id':probId},{'$push':{'problems.$.answersGiven':usersAnswer}})
            #store answer given
            return 'updated: incorrect'
        #elf if outcome is correct: increment attempts, change correct to True, and get another problem
        else:
            #increment problem attempts
            userDb[userName].update({"type":"problem",'concept':concept,'problems.id':probId},{'$inc':{'problems.$.attempts':1}, '$set':{'lastVisit':now,'problems.$.correct':True}})
            #set correct to True
            #userDb[userName].update({"type":"problem",'concept':concept,'problems.id':probId},{'$set':{'problems.$.correct':True}})
            #increment number of correct in conceptDoc
            userDb[userName].update({"type":"problem",'concept':concept},{'$inc':{'correct':1}})
            #add usersAnswer to answersGiven
            userDb[userName].update({"type":"problem",'concept':concept,'problems.id':probId},{'$push':{'problems.$.answersGiven':usersAnswer}})
            return 'updated: correct'

if __name__ == '__main__':
    app.run(debug = True)
