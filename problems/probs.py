from league.get import *
from fitbit.get import *
import statistics
import requests
import random
import string
import datetime

#could get the recent data from provider and personally store it
#instead of requesting the providers api everytime
#figure out probId
#returns 15 standard

def createProbs(concept,popSize,provider,providerUN,userName):
	#check to see if standard deviation conceptDoc has been created already
	if userDb[userName].find_one({'concept':concept}):
		#update probs attempted
		userDb[userName].update({"type":"problem",'concept':concept},{'$inc':{'attempted':1}})
	else:
		#add a conceptDoc for concept
		now = datetime.datetime.utcnow()
		conceptDoc = {'type':'problem','concept':concept,'attempted':1,'correct':0,'problems':[],'lastVisit':now}
		userDb[userName].insert(conceptDoc)
	if provider == 'league':
		stats = leagueStats(providerUN)
		dataNames = ['championsKilled','timePlayed','goldEarned','minionsKilled','assists','numDeaths']
		probs = []
		for data in dataNames:
			dataPop = sorted(stats[data], key=lambda k: random.random())[0:popSize]
			#create acceptable answer list
			answerList = []
			answer = None
			if concept == 'mean':
				answer = round(statistics.mean(dataPop),2)
			elif concept == 'standard deviation':
				answer = round(statistics.stdev(dataPop),2)
			elif concept == 'population standard deviation':
				answer = round(statistics.pstdev(dataPop),2)
			elif concept == 'population variance':
				answer = round(statistics.pvariance(dataPop),2)
			elif concept == 'variance':
				answer = round(statistics.variance(dataPop),2)
			answerList.append(str(answer))
			#handle the 4, 4.0, 4.00 expection
			if str(answer)[-2:] == '.0':
				answerList.append(str(answer).split('.')[0])
				answerList.append(str(answer)+'0')
			prob = {'data':dataPop,'answerList':answerList}
			prob['id'] = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(15))

			#add unit
			if data == 'championsKilled':
				prob['unit'] = 'champions killed'
			elif data == 'timePlayed':
				prob['unit'] = 'seconds played'
			elif data == 'goldEarned':
				prob['unit'] = 'gold earned'
			elif data == 'minionsKilled':
				prob['unit'] = 'minions killed'
			elif data == 'assists':
				prob['unit'] = 'assists'
			elif data == 'numDeaths':
				prob['unit'] = 'deaths'
			prob['question'] = 'Find the '+concept+' of '+prob['unit']+' in your recent League of Legend Games.  Round to the nearest hundreth (if necessary).'
			prob['attempts'] = 0
			prob['correct'] = False
			prob['concept'] = concept
			prob['answersGiven'] = []
			prob['lastVisit'] = datetime.datetime.utcnow()
			probs.append(prob)
		return probs

	elif provider == 'fitbit':
		#create a standard deviation problem within all dataNames
		datum = fitbitData(userName)
		dataNames = ['recentSteps','recentDistance','recentCalories','recentMinutesSedentary']
		probs = []
		for data in dataNames:
			if data in datum.keys() and len(datum[data]) >= popSize:
				dataPop = sorted(datum[data], key=lambda k: random.random())[0:popSize]
				#create acceptable answer list
				answerList = []
				answer = None
				if concept == 'mean':
					answer = round(statistics.mean(dataPop),2)
				elif concept == 'standard deviation':
					answer = round(statistics.stdev(dataPop),2)
				elif concept == 'population standard deviation':
					answer = round(statistics.pstdev(dataPop),2)
				elif concept == 'population variance':
					answer = round(statistics.pvariance(dataPop),2)
				elif concept == 'variance':
					answer = round(statistics.variance(dataPop),2)
				answerList.append(str(answer))
				#handle the 4, 4.0, 4.00 expection
				if str(answer)[-2:] == '.0':
					answerList.append(str(answer).split('.')[0])
					answerList.append(str(answer)+'0')
				prob = {'data':dataPop,'answerList':answerList}
				prob = {'data':dataPop,'answerList':answerList}
				prob['id'] = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(17))

				#add unit
				if data == 'recentSteps':
					prob['unit'] = 'daily steps taken'
				elif data == 'recentDistance':
					prob['unit'] = 'daily miles covered'
				elif data == 'recentCalories':
					prob['unit'] = 'daily calories burned'
				elif data == 'recentMinutesSedentary':
					prob['unit'] = 'daily sedentary minutes'
				prob['question'] = 'Find the '+concept+' of '+prob['unit']+' in your recent Fitbit use.  Round to the nearest hundreth (if necessary).'
				prob['attempts'] = 0
				prob['correct'] = False
				prob['concept'] = concept
				prob['answersGiven'] = []
				prob['lastVisit'] = datetime.datetime.utcnow()
				probs.append(prob)
		return probs

def createStnDev(popSize,provider,providerUN,userName):
	#check to see if standard deviation conceptDoc has been created already
	if userDb[userName].find_one({'type':'problem','concept':'standard deviation'}):
		#update probs attempted
		userDb[userName].update({"type":"problem",'concept':'standard deviation'},{'$inc':{'attempted':1}})
	else:
		#add a conceptDoc for standard deviation
		now = datetime.datetime.utcnow()
		conceptDoc = {'type':'problem','concept':'standard deviation','attempted':1,'correct':0,'problems':[],'lastVisit':now}
		userDb[userName].insert(conceptDoc)
	if provider == 'league':
		stats = leagueStats(providerUN)
		dataNames = ['championsKilled','timePlayed','goldEarned','minionsKilled','assists','numDeaths']
		probs = []
		for data in dataNames:
			dataPop = sorted(stats[data], key=lambda k: random.random())[0:popSize]
			#create acceptable answer list
			answerList = []
			answer = round(statistics.stdev(dataPop),2)
			answerList.append(str(answer))
			if str(answer)[-2:] == '.0':
				answerList.append(str(answer).split('.'))
				answerList.append(str(answer).split('.')+'.00')
			prob = {'data':dataPop,'answerList':answerList}
			prob['id'] = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(15))

			#add unit
			if data == 'championsKilled':
				prob['unit'] = 'champions killed'
			elif data == 'timePlayed':
				prob['unit'] = 'seconds played'
			elif data == 'goldEarned':
				prob['unit'] = 'gold earned'
			elif data == 'minionsKilled':
				prob['unit'] = 'minions killed'
			elif data == 'assists':
				prob['unit'] = 'assists'
			elif data == 'numDeaths':
				prob['unit'] = 'deaths'
			prob['question'] = 'Find the standard deviation of '+prob['unit']+' in your recent League of Legend Games.  Round to the nearest hundreth (if necessary).'
			prob['attempts'] = 0
			prob['correct'] = False
			prob['concept'] = 'standard deviation'
			probs.append(prob)
		return probs

	elif provider == 'fitbit':
		#create a standard deviation problem within all dataNames
		datum = fitbitData(userName)
		print datum
		dataNames = ['recentSteps','recentDistance','recentCalories','recentMinutesSedentary']
		probs = []
		for data in dataNames:
			if data in datum.keys() and len(datum[data]) >= popSize:
				dataPop = sorted(datum[data], key=lambda k: random.random())[0:popSize]
				#create acceptable answer list
				answerList = []
				answer = round(statistics.stdev(dataPop),2)
				answerList.append(str(answer))
				if str(answer)[-2:] == '.0':
					answerList.append(str(answer).split('.'))
					answerList.append(str(answer).split('.')+'.00')
				prob = {'data':dataPop,'answerList':answerList}
				prob = {'data':dataPop,'answerList':answerList}
				prob['id'] = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(17))

				#add unit
				if data == 'recentSteps':
					prob['unit'] = 'daily steps taken'
				elif data == 'recentDistance':
					prob['unit'] = 'daily miles covered'
				elif data == 'recentCalories':
					prob['unit'] = 'daily calories burned'
				elif data == 'recentMinutesSedentary':
					prob['unit'] = 'daily sedentary minutes'
				prob['question'] = 'Find the standard deviation of '+prob['unit']+' in your recent Fitbit use.  Round to the nearest hundreth (if necessary).'
				prob['attempts'] = 0
				prob['correct'] = False
				prob['concept'] = 'standard deviation'
				probs.append(prob)
		return probs
