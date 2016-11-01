import requests

champsMap = {1: u'Annie', 2: u'Olaf', 3: u'Galio', 4: u'Twisted Fate', 5: u'Xin Zhao', 6: u'Urgot', 7: u'LeBlanc', 8: u'Vladimir', 9: u'Fiddlesticks', 10: u'Kayle', 11: u'Master Yi', 12: u'Alistar', 13: u'Ryze', 14: u'Sion', 15: u'Sivir', 16: u'Soraka', 17: u'Teemo', 18: u'Tristana', 19: u'Warwick', 20: u'Nunu', 21: u'Miss Fortune', 22: u'Ashe', 23: u'Tryndamere', 24: u'Jax', 25: u'Morgana', 26: u'Zilean', 27: u'Singed', 28: u'Evelynn', 29: u'Twitch', 30: u'Karthus', 31: u"Cho'Gath", 32: u'Amumu', 33: u'Rammus', 34: u'Anivia', 35: u'Shaco', 36: u'Dr. Mundo', 37: u'Sona', 38: u'Kassadin', 39: u'Irelia', 40: u'Janna', 41: u'Gangplank', 42: u'Corki', 43: u'Karma', 44: u'Taric', 45: u'Veigar', 48: u'Trundle', 50: u'Swain', 51: u'Caitlyn', 53: u'Blitzcrank', 54: u'Malphite', 55: u'Katarina', 56: u'Nocturne', 57: u'Maokai', 58: u'Renekton', 59: u'Jarvan IV', 60: u'Elise', 61: u'Orianna', 62: u'Wukong', 63: u'Brand', 64: u'Lee Sin', 67: u'Vayne', 68: u'Rumble', 69: u'Cassiopeia', 72: u'Skarner', 74: u'Heimerdinger', 75: u'Nasus', 76: u'Nidalee', 77: u'Udyr', 78: u'Poppy', 79: u'Gragas', 80: u'Pantheon', 81: u'Ezreal', 82: u'Mordekaiser', 83: u'Yorick', 84: u'Akali', 85: u'Kennen', 86: u'Garen', 89: u'Leona', 90: u'Malzahar', 91: u'Talon', 92: u'Riven', 96: u"Kog'Maw", 98: u'Shen', 99: u'Lux', 101: u'Xerath', 102: u'Shyvana', 103: u'Ahri', 104: u'Graves', 105: u'Fizz', 106: u'Volibear', 107: u'Rengar', 110: u'Varus', 111: u'Nautilus', 112: u'Viktor', 113: u'Sejuani', 114: u'Fiora', 115: u'Ziggs', 117: u'Lulu', 119: u'Draven', 120: u'Hecarim', 121: u"Kha'Zix", 122: u'Darius', 126: u'Jayce', 127: u'Lissandra', 131: u'Diana', 133: u'Quinn', 134: u'Syndra', 143: u'Zyra', 150: u'Gnar', 154: u'Zac', 157: u'Yasuo', 161: u"Vel'Koz", 201: u'Braum', 202: u'Jhin', 203: u'Kindred', 222: u'Jinx', 223: u'Tahm Kench', 236: u'Lucian', 238: u'Zed', 245: u'Ekko', 254: u'Vi', 266: u'Aatrox', 267: u'Nami', 268: u'Azir', 412: u'Thresh', 420: u'Illaoi', 421: u"Rek'Sai", 429: u'Kalista', 432: u'Bard'}
summonersMap = {'unknown matrix':34015260, 'tetrixs':35259971,'alcyrae':32276464}

key = '458c84df-0156-4a67-a600-2557770c9b8a'
params = {'api_key':key}
base = 'https://na.api.pvp.net/'

def getSumId(summonername):
	url = base+'api/lol/na/v1.4/summoner/by-name/'+summonername
	r = requests.get(url, params=params)
	return r.json()[summonername]['id']

#print getSumId('alcyrae')
def getRecent(summonername):
	#sumId = str(getSumId(summonername))
	sumId = str(summonersMap[summonername])
	base = 'https://na.api.pvp.net/'
	resource = 'api/lol/na/v1.3/game/by-summoner/'+sumId+'/recent'
	url = base+resource

	r = requests.get(url, params=params)
	return r.json()['games']

def leagueStats(summonername):
	doc = {
		'minionsKilled':[],
		'championsKilled':[],
		'assists':[],
		'numDeaths':[],
		'goldEarned':[],
		'timePlayed':[],
		'champions':[]
	}
	recentGames = getRecent(summonername)
	for game in recentGames:
		if game == None:
			pass
		else:
			try:
				doc['minionsKilled'].append(game['stats']['minionsKilled'])
				doc['championsKilled'].append(game['stats']['championsKilled'])
				doc['assists'].append(game['stats']['assists'])
				doc['numDeaths'].append(game['stats']['numDeaths'])
				doc['goldEarned'].append(game['stats']['goldEarned'])
				doc['timePlayed'].append(game['stats']['timePlayed'])
				doc['champions'].append(champsMap[game['championId']])
			except:
				pass
	return doc
