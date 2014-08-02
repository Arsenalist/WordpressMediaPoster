import subprocess
import re
import requests
from bs4 import BeautifulSoup


class MediaPost:
	def get_meta_value(self, prop):
		meta = self.soup.find('meta', property=prop)
		return meta['content']

	def get_thumb(self):
		return self.get_meta_value('og:image')

	def get_embed(self):
		raise NotImplementedError( "Must implement get_embed" )

	def get_soup(self):
		r = requests.get(self.url)
		return BeautifulSoup(r.text)

	def get_json(self):
		r = requests.get(self.url)
		return r.json()

class LastMinuteGoals(MediaPost):

    def __init__(self, video_id):
        self.video_id = video_id
        self.url = self.video_id
        self.soup = self.get_soup()


    def get_embed(self):
        result = self.soup.find_all('script', src=re.compile("playwire"))
        if len(result) != 0:
            return unicode(result[0])
        else:
            return None

class Webm(MediaPost):
	def __init__(self, url):
		self.url = url

	def get_thumb(self):
		return "/assets/nothumb.jpg"
		
	def get_embed(self):
		return '<video width="auto" height="auto" controls loop autoplay><source src="' + self.url + '" type="video/webm" /></video>'


class Gif(MediaPost):
	def __init__(self, url):
		self.url = url

	def get_thumb(self):
		output = subprocess.Popen(["./gif.sh", self.url], stdout=subprocess.PIPE).communicate()[0]
		return output.split("\n")[0]
		
	def get_embed(self):
		return '<img src="' + self.url +'"/>'
		
class Vimeo(MediaPost):
	def __init__(self, video_id):
		self.video_id = video_id
		self.url = 'http://vimeo.com/' + self.video_id
		self.soup = self.get_soup()

	def get_embed(self):
		return '<iframe src="//player.vimeo.com/video/' + self.video_id + '" width="500" height="281" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>'


class MediaCrush(MediaPost):
	def __init__(self, video_id):
		self.video_id = video_id
		self.url = 'https://mediacru.sh/' + self.video_id
		self.soup = self.get_soup()

	def get_embed(self):
		width = self.get_meta_value('twitter:player:width')
		height = self.get_meta_value('twitter:player:height')
		return '<iframe width="' + width + '" height="' + height + '" src="https://mediacru.sh/' + self.video_id + '/frame frameborder="0" allowFullscreen></iframe>'

class Rutube(MediaPost):
	def __init__(self, video_id):
		self.video_id = video_id
		self.url = 'http://rutube.ru/video/' + self.video_id + '/'
		self.soup = self.get_soup()

	def get_embed(self):
		result = self.soup.select('#embed-field iframe')
		if len(result) != 0:
			return unicode(result[0])
		else:
			return None


class Facebook(MediaPost):
	def __init__(self, video_id):
		self.video_id = video_id
		self.url =  'https://graph.facebook.com/' + self.video_id + '/?access_token=CAACEdEose0cBAECdQm4uWC7dZCPBFzQwZAgBXvRO6UBT98hUPSBZAnNGrHSPYDTbll6SqSnzS0uR5JJcftYEByUh9eJuvbDGJr6gkgz0FXBZB7hFjlEXbKN0BekPX3tZCF4XJ9Fz2FJcCBTuJ6z4X3y7nv7zvu6dIsMxtpT1ZADq5pQH8sguKbhGmqmo4wwasZD'
		self.json = self.get_json()

	def get_thumb(self):
		return self.json["picture"]


	def get_embed(self):
		return self.json['embed_html']


class Vine(MediaPost):
	def __init__(self, video_id):
		self.video_id = video_id
		self.url = 'https://vine.co/v/' + self.video_id
		self.soup = self.get_soup()

	def get_embed(self):
		return '<iframe class="vine-embed" src="https://vine.co/v/' + self.video_id +'/embed/simple" width="480" height="480" frameborder="0"></iframe><script async src="//platform.vine.co/static/scripts/embed.js" charset="utf-8"></script>'


class YouTube(MediaPost):
	def __init__(self, video_id):
		self.video_id = video_id
		self.url = 'http://youtube.com/watch?v=' + self.video_id
		self.soup = self.get_soup()

	def get_embed(self):
		return '<iframe width="560" height="315" src="//www.youtube.com/embed/' +  self.video_id + '" frameborder="0" allowfullscreen></iframe>'


class DailyMotion(MediaPost):
	def __init__(self, video_id):
		self.video_id = video_id
		self.url = 'http://dailymotion.com/video/' + self.video_id
		self.soup = self.get_soup()


	def get_embed(self):
		width = self.soup.find('meta', property='og:video:width')
		height = self.soup.find('meta', property='og:video:height')
		return '<iframe frameborder="0" width="' + width['content'] + '" height="' + height['content'] + '" src="//www.dailymotion.com/embed/video/' + self.video_id + '" allowfullscreen></iframe>'


class Gfy(MediaPost):
	def __init__(self, gfy):
		self.gfy = gfy
		self.url = 'http://gfycat.com/' + self.gfy
		self.soup = self.get_soup()

	def get_thumb(self):
		return 'http://thumbs.gfycat.com/' + self.gfy + '-thumb100.jpg'

	def get_embed(self):
		return '<img class="gfyitem" data-id="' + self.gfy + '" />'
		"""
		result = self.soup.find_all('span', text=re.compile("iframe"), class_="gfyShareLinkText")
		if len(result) != 0:
			return unicode(result[0].string)
		else:
			return None
		"""
