import tweepy
import requests
import base64
import urllib.parse
import json
from pprint import pprint

class TwitterAPI():
	def __init__(self):
		with open('auth.json') as f:
			auth_data = json.load(f)
			consumer_key = auth_data['consumer_key']
			consumer_secret = auth_data['consumer_secret'] 
			access_token = auth_data['access_token'] 
			access_token_secret = auth_data['access_secret']
		auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
		auth.set_access_token(access_token, access_token_secret)
		self.rfc1738_token = urllib.parse.quote_plus(consumer_key)+":"+urllib.parse.quote_plus(consumer_secret)
		self.api = tweepy.API(auth)
		self.session = requests.session()
		self.generate_bearer_token()
		self.rule = None

	def __call__(self):
		return self.auth_header

	def generate_bearer_token(self):
		header = {
			"User-Agent": "My Twitter App",
			"Authorization":"Basic "+base64.b64encode(self.rfc1738_token.encode()).decode(),
			"Content-Type":"application/x-www-form-urlencoded;charset=UTF-8",
			"Accept-Encoding":"gzip"
		}
# Twitter now forces a unique Bearer token per API keyset
		bearer_token = "AAAAAAAAAAAAAAAAAAAAAHB5MAEAAAAAwwYcB3T5cRB6jRMEGxVpZl4GpCY%3DY9iG9Uclhn3yF28QYe8WJzm5TJVJqFyjBJQwvHCsHIxlvPgcog"		
#		 auth = self.session.post(
#			 'https://api.twitter.com/oauth2/token',
#			 headers=header,
#			 data="grant_type=client_credentials"
#			 )
#		 if auth.status_code==200:
#			 bearer_token = auth.json()['access_token']
	
		self.auth_header = {
			"User-Agent":"My Twitter App",
			"Authorization":"Bearer "+bearer_token,
			"Content-type":"application/json",
			"Accept-Encoding":"gzip"
		}

	def get_user(self, user_ids):
		# user_ids is a list
		r = requests.get(
			'https://api.twitter.com/1.1/users/lookup.json?user_id='+str.join(',',user_ids),
			headers = self.auth_header
		)
		return [user['screen_name'] for user in r.json()]

	def query_tweets(self, query_term, result_type):
		# query_term : space delimited query strings up to 500 characters
		# ensure the string is urlencoded
		'''
		Operator							Finds Tweets...
		watching now						containing both “watching” and “now”. This is the default operator.
		“happy hour”						containing the exact phrase “happy hour”.
		love OR hate						containing either “love” or “hate” (or both).
		beer -root							containing “beer” but not “root”.
		#haiku								containing the hashtag “haiku”.
		from:interior						sent from Twitter account “interior”.
		list:NASA/astronauts-in-space-now	sent from a Twitter account in the NASA list astronauts-in-space-now
		to:NASA								a Tweet authored in reply to Twitter account “NASA”.
		@NASA								mentioning Twitter account “NASA”.
		politics filter:safe				containing “politics” with Tweets marked as potentially sensitive removed.
		puppy filter:media					containing “puppy” and an image or video.
		puppy -filter:retweets				containing “puppy”, filtering out retweets
		puppy filter:native_video			containing “puppy” and an uploaded video, Amplify video, Periscope, or Vine.
		puppy filter:periscope				containing “puppy” and a Periscope video URL.
		puppy filter:vine					containing “puppy” and a Vine.
		puppy filter:images					containing “puppy” and links identified as photos, including third parties such as Instagram.
		puppy filter:twimg					containing “puppy” and a pic.twitter.com link representing one or more photos.
		hilarious filter:links				containing “hilarious” and linking to URL.
		puppy url:amazon					containing “puppy” and a URL with the word “amazon” anywhere within it.
		superhero since:2015-12-21			containing “superhero” and sent since date “2015-12-21” (year-month-day).
		puppy until:2015-12-21				containing “puppy” and sent before the date “2015-12-21”.
		movie -scary :)						containing “movie”, but not “scary”, and with a positive attitude.
		flight :(							containing “flight” and with a negative attitude.
		traffic ?							containing “traffic” and asking a question.
		'''
		param = {
			"q":query_term,
			"include_entities":True,
			"tweet_mode":"extended",
			"result_type":result_type
		}
		r = requests.get(
			'https://api.twitter.com/1.1/search/tweets.json',
			params = param,
			headers = self.auth_header
			)
		return r.json()

	def get_trends(self, woeid='23424775'):
		# WOEID 23424775=Canada
		r = self.session.get(
			'https://api.twitter.com/1.1/trends/place.json?id='+woeid,
			headers = self.auth_header)
		return r.json()

	def filtered_tweets(self, keyword, location='142.72682,85.08136,52.72682,4.56547'):
		r = self.session.post(
			'https://stream.twitter.com/1.1/statuses/filter.json',
			headers = self.auth_header,
			params = {
				"track": keyword,
				"locations": location
				}
			)
		return r

	def get_rule(self):
		print("Grabbing current rules")
		r = requests.get(
			"https://api.twitter.com/labs/1/tweets/stream/filter/rules",
			headers = self.auth_header
			)
		if r.status_code is not 200:
			raise Exception("Cannot get rules (HTTP {}): {}".format(r.status_code, r.text))
		return r.json()

	def reset_rule(self):
		print("Resetting rules")
		rules = self.get_rule()
		ids = list(map(lambda rule: rule['id'], rules['data']))
		payload = {
			"delete": {
				"ids": ids
				}
			}

		r = requests.post(
			"https://api.twitter.com/labs/1/tweets/stream/filter/rules",
			headers = self.auth_header,
			json = payload
			)
		if r.status_code is not 200:
			raise Exception("Cannot reset rules (HTTP {}): {}".format(r.status_code, r.text))

	def build_rule(self, keywords, reset = True, tag = None):
		
		if reset:
			self.reset_rule()

		print("Building new rule")

		payload = {
			"value": keywords + " (place_country:CA OR bio_location:Canada) (lang:en OR lang:fr) -is:retweet -is:quote"
			}
		if tag:
			payload['tag'] = tag

		r = requests.post(
				"https://api.twitter.com/labs/1/tweets/stream/filter/rules",
				headers = self.auth_header,
				json = {
					"add": [payload]
				}
			)
		if r.status_code is not 201:
			raise Exception("Cannot create rules (HTTP {}): {}".format(r.status_code, r.text))
		self.rule = self.get_rule()

	def stream_tweets(self, keywords = None):
		if not self.rule or not 'data' in self.rule:
			if keywords is None:
				raise Exception ("No keyword parameters have been passed to stream tweets by")
			self.build_rule(keywords)
		else:
			print("Using existing rule:", self.rule)
		r = requests.get(
				"https://api.twitter.com/labs/1/tweets/stream/filter?format=detailed",
				headers = self.auth_header,
				stream=True)
		print("Stream connection status:", r.status_code)

		print("Streaming started")
		for l in r.iter_lines():
			if l:
				with open('tweets.json', 'a+') as f:
					json.dump(json.loads(l), f)
					f.write(',\n')
