#!/usr/bin/python

import requests
import hmac
import hashlib
from itertools import count
import time
import json
import sys
import os
import ConfigParser

try:
	inparams = ConfigParser.ConfigParser()
	inparams.read(sys.argv[2])
	secret = inparams.get('settings','secret')
	key = inparams.get('settings','key')
	action = sys.argv[1]
except:
	print "No Action Given: Sell , Buy , data"


headers = { 'nonce': '', 'Key' : key, 'Sign': '',}

def makecall():
	payload = { 'command': 'returnBalances'}

	# store as a global variable
	NONCE_COUNTER = count(int(time.time() * 1000))
	payload['nonce'] = next(NONCE_COUNTER)

	request = requests.Request( 'POST', 'https://poloniex.com/tradingApi', data=payload, headers=headers)

	prepped = request.prepare()
	signature = hmac.new(secret, prepped.body, digestmod=hashlib.sha512)
	prepped.headers['Sign'] = signature.hexdigest()

	with requests.Session() as session:
	    response = session.send(prepped)
	    return response

def getticker():
	r = requests.get("https://poloniex.com/public?command=returnTicker")
	return json.loads(r.text)


def buy(currencyPair,rate,amount):
	payload = { 'command': 'buy', 'currencyPair': currencyPair, 'rate': rate, 'amount': amount, 'fillOrKill': 1}

	# store as a global variable
	NONCE_COUNTER = count(int(time.time() * 1000))
	payload['nonce'] = next(NONCE_COUNTER)

	request = requests.Request( 'POST', 'https://poloniex.com/tradingApi', data=payload, headers=headers)

	prepped = request.prepare()
	signature = hmac.new(secret, prepped.body, digestmod=hashlib.sha512)
	prepped.headers['Sign'] = signature.hexdigest()

	with requests.Session() as session:
	    response = session.send(prepped)
	    return response

def sell(currencyPair,rate,amount):
	payload = { 'command': 'sell', 'currencyPair': currencyPair, 'rate': rate, 'amount': amount, 'fillOrKill': 1}

	# store as a global variable
	NONCE_COUNTER = count(int(time.time() * 1000))
	payload['nonce'] = next(NONCE_COUNTER)

	request = requests.Request( 'POST', 'https://poloniex.com/tradingApi', data=payload, headers=headers)

	prepped = request.prepare()
	signature = hmac.new(secret, prepped.body, digestmod=hashlib.sha512)
	prepped.headers['Sign'] = signature.hexdigest()

	with requests.Session() as session:
	    response = session.send(prepped)
	    return response

def show_orders(currencyPair):
	payload = { 'command': 'returnOpenOrders', 'currencyPair': currencyPair}

	# store as a global variable
	NONCE_COUNTER = count(int(time.time() * 1000))
	payload['nonce'] = next(NONCE_COUNTER)

	request = requests.Request( 'POST', 'https://poloniex.com/tradingApi', data=payload, headers=headers)

	prepped = request.prepare()
	signature = hmac.new(secret, prepped.body, digestmod=hashlib.sha512)
	prepped.headers['Sign'] = signature.hexdigest()

	with requests.Session() as session:
	    response = session.send(prepped)

def sellcall(coins, loop):
	for c in coins:
		print "|||||||||||||||| Selling: " + str(c) + " ||||||||||||||||"
		p = sell(c, coins[c]['value'], coins[c]['coinstosell'])
		print json.loads(p.text)
		time.sleep(.25)


def buycall(coins, loop):
	for c in coins:
		print "|||||||||||||||| Buying: " + str(c) + " ||||||||||||||||"
		buyprice = coins[c]['value']
		# buyprice = float(coins[c]['value']) * 1.01
		p = buy(c, buyprice , coins[c]['coinstobuy'])
		print json.loads(p.text)
		cin = 0
		if loop and "error" in json.loads(p.text):
			while json.loads(p.text)['error'] == "Unable to fill order completely." and cin <=10:
				print "WORKED"
				cin += 1
		time.sleep(.25)

exclusions = ["BTC_POT"]

# Get Current Ticker of exchange
curticker = getticker()
# Get USD Value of BTC
curbtc_to_usd = float(curticker["USDT_BTC"]["last"])

### Getting Currently Owned Coins
mycoins = {}
total_btc_value = float(0)
getmycoins = makecall()
getmycoins = json.loads(getmycoins.text)

total_btc_value += float(getmycoins["BTC"])


# Get total Number of BTC AltCoins
btcex = {}
for i in curticker:
	if str(i).startswith("BTC_") and str(i) not in exclusions: # FILTERS TO BTC EXCHANGE ONLY
		btcex[i] = {}
		btcex[i]['value'] = float(curticker[i]['last'])
		# Get total BTC Value of each 
		btcex[i]['total_value'] = float(btcex[i]['value']) * float(getmycoins[i.split("_")[1]])
		# Get USD Value of each
		btcex[i]['total_usd_value'] = btcex[i]['total_value'] * curbtc_to_usd
		# Get USD value per coin
		btcex[i]['usd_value'] = btcex[i]['value'] * curbtc_to_usd
		# Add to total BTC value
		total_btc_value += float(btcex[i]['total_value'])
		btcex[i]['quantity'] = getmycoins[i.split("_")[1]]


total_usd_value = total_btc_value * curbtc_to_usd

# Get how much BTC of each coin to be even
totalaltcoins = len(btcex)
desired_btc_per_coin = (total_btc_value / totalaltcoins) * 0.99 # 99% to leave purchase room if prices fluctuate during script
desired_usd_per_coin = desired_btc_per_coin * curbtc_to_usd

for i in btcex:
	btcex[i]['desired_amount'] = desired_btc_per_coin / float(btcex[i]['value'])


# FIND owned coins with greater percentage over/under desired average
coinstobuy = {}
coinstosell = {}
for i in btcex:
	if ( float(btcex[i]['quantity']) / btcex[str(i)]['desired_amount'] ) > 1.15:
		btcex[i]['coinstosell'] = float(btcex[i]['quantity']) - btcex[str(i)]['desired_amount']
		coinstosell[i] = btcex[i]
		coinstosell[i]['sell_total_usd_value'] = btcex[i]['coinstosell'] * btcex[i]['usd_value']
		print "Selling: $" + str(coinstosell[i]['sell_total_usd_value']) + " of " + str(i)
	if ( float(btcex[i]['quantity']) / btcex[str(i)]['desired_amount'] ) < .85:
		btcex[i]['coinstobuy'] = btcex[str(i)]['desired_amount'] - float(btcex[i]['quantity'])
		coinstobuy[i] = btcex[i]
		coinstobuy[i]['buy_total_usd_value'] = btcex[i]['coinstobuy'] * btcex[i]['usd_value']
		print "Buying: $" + str(coinstobuy[i]['buy_total_usd_value']) + " of " + str(i)

print "SELL"
print coinstosell
print "BUY"
print coinstobuy

if action == "data":
	filer = open('out.txt', 'r')
	filew = open('out-temp.txt', 'w')
	cdate = time.strftime("%m/%d/%Y | %H:%M:%S")
	fullfile = filer.readlines()
	firstline = fullfile[0].rstrip()
	currentlen = len(firstline.split(','))
	filew.write(firstline + "," + cdate + "\n")
	for c in mycoins:
		currentlytracked = 0
		filer = open('out.txt', 'r')
		for r in filer.readlines():
			r = r.rstrip()
			csp = r.split(',')
			if csp[0] == c:
				currentlytracked = 1
				filew.write(r + "," + str(mycoins[c]['total_usd_value']) + '\n')
		if currentlytracked == 0:
			catchuprow = ""
			# for cl in range(currentlen-1):
			# 	catchuprow += ",0"
			filew.write(c + catchuprow + "," + str(mycoins[c]['total_usd_value']) + "\n")

	filer.close()
	filew.close()
	os.remove('out.txt')
	os.rename('out-temp.txt', 'out.txt')

### SELL SECTION
if action == "sell":
	sellcall(coinstosell, 0)

if action == "buy":
	buycall(coinstobuy, 0)

if action == "trade":
	sellcall(coinstosell,0)
	buycall(coinstobuy,0)

if action == "show_orders":
	p = show_orders('all')
	if p:
		print json.loads(p.text)
	else:
		print "No Open Orders"

print "Desired USD per Coin : " +  str(desired_usd_per_coin)
print "Total BTC in Market : " + str(total_btc_value)
print "Total USD in Market : " + str(total_usd_value)
