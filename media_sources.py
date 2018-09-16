import subprocess
import re
import requests
from bs4 import BeautifulSoup
from html.parser import HTMLParser
from urllib.parse import urlparse, parse_qs
class MediaPost:
  def get_meta_value(self, prop):
    meta = self.soup.find('meta', property=prop)
    if meta:
        return meta['content']
    else:
        return ''

  def get_thumb(self):
    return self.get_meta_value('og:image')

  def get_embed(self):
    raise NotImplementedError( "Must implement get_embed" )

  def get_soup(self):
    r = requests.get(self.url, verify=False)
    self.text = r.text
    return BeautifulSoup(r.text)

  def get_json(self):
    r = requests.get(self.url, verify=False)
    return r.json()

  def get_type(self):
    return "Video"

class SimpleMediaPost(MediaPost):
    def __init__(self, url, embed):
        self.url = url
        self.embed = embed

    def get_thumb(self):
        return self.url

    def get_embed(self):
        return self.embed

class LiveTV(MediaPost):

  def __init__(self, url):
    self.url = url
    self.soup = self.get_soup()
    self.container_soup = self.find_video_container_soup()
    self.init_attrs()

  def find_video_list_container(self, tag):
    return tag.has_attr("bgcolor") and tag["bgcolor"] == "#aaaaaa"

  def find_video_container_soup(self):
    return self.soup.find(self.find_video_list_container).find_all("tr")[0].find("td")

  def init_attrs(self):
     if "playwire" in str(self.container_soup):
        script = self.container_soup.find("script")
        config_url = script["data-config"]
        json = requests.get(config_url, verify=False).json()
        self.thumb = json["poster"]
        self.embed = str(script)

     elif "vk.com" in str(self.container_soup):
        iframe = self.container_soup.find("iframe")
        url = iframe["src"]
        vk = Vk(url)
        self.thumb = vk.get_thumb()
        self.embed = vk.get_embed()

     elif "youtube.com" in str(self.container_soup):
        iframe = self.container_soup.find("iframe")
        url = iframe["src"]
        query = urlparse(url)
        video_id = query.path.split('/')[2]
        youtube = YouTube(video_id)
        self.thumb = youtube.get_thumb()
        self.embed = youtube.get_embed()

     elif "dailymotion.com" in str(self.container_soup):
        iframe = self.container_soup.find("iframe")
        url = iframe["src"]
        query = urlparse(url)
        video_id = query.path.split('/')[3]
        dm = DailyMotion(video_id)
        self.thumb = dm.get_thumb()
        self.embed = dm.get_embed()

     elif "rutube.ru" in str(self.container_soup):
        iframe = self.container_soup.find("iframe")
        url = iframe["src"]
        query = urlparse(url)
        video_id = query.path.split('/')[3]
        ru = Rutube(video_id)
        self.thumb = 'http://i.imgur.com/UsIqkhm.jpg' #ru.get_thumb()
        self.embed = str(iframe)



  def get_thumb(self):
    return self.thumb
  
  def get_embed(self):
    return self.embed

class Vk(MediaPost):

  def __init__(self, embed_url):
    self.embed_url = embed_url
    self.urlparse = urlparse(self.embed_url)
    params = parse_qs(self.urlparse.query)
    oid = params['oid'][0]
    id = params['id'][0]
    self.url = 'http://vk.com/video' + oid + '_' + id
    self.soup = self.get_soup()

  def get_embed(self):
    width = self.get_meta_value("og:video:width")
    height = self.get_meta_value("og:video:height")
    return '<iframe src="' + self.embed_url + '" width="' + width + '" height="' + height + ' " frameborder="0"></iframe>'



class Videa(MediaPost):

  def __init__(self, url):
    self.url = url
    self.soup = self.get_soup()


  def get_embed(self):
    result = self.soup.find(id="player_embed_input")
    if result and result.string:
       return HTMLParser.HTMLParser().unescape(result.string)
    else:
      return None


class OkRu(MediaPost):

  def __init__(self, video_id):
    self.video_id = video_id
    self.url = "https://ok.ru/video/" + self.video_id
    self.soup = self.get_soup()


  def get_embed(self):
    result = '<iframe width="560" height="315" src="//ok.ru/videoembed/' + self.video_id + '" frameborder="0" allowfullscreen></iframe>'
    return result


class LastMinuteGoals(MediaPost):

  def __init__(self, video_id):
    self.video_id = video_id
    self.url = self.video_id
    self.soup = self.get_soup()
    self.urlparse = urlparse(self.url)


  # Nasty piece of work which gets the HTML that BeautifulSoup can actually parse
  def get_specific_html(self):
    lines = self.text.split("\n")
    start_line = 0;
    end_line = 0
    for idx, l in enumerate(lines):
      if "tabs_" in l:
        start_line = idx
        break
    for idx, l in enumerate(lines):
      if "</div><script" in l and idx > start_line:
        end_line = idx
        break
    segment = lines[start_line:end_line+1]
    html = ""
    for l in segment:
      html = html + l
    return html

  def get_embed(self):
    soup = BeautifulSoup(self.get_specific_html())
    # No fragment means get the second one (first is something weird)
    if self.urlparse.fragment == '':
      result = soup.find_all('div', id=re.compile("tabs"))
      div = result[1]
    else:
      div = soup.find(id=self.urlparse.fragment)

    if div:
      script = div.find_all(["script", "iframe"])
      if script and len(script) != 0:
        html = ""
        for s in script:
            html = html + unicode(s) + "<br/>"
        return html

    return None


    
class Webm(MediaPost):
  def __init__(self, url):
    self.url = url

  def get_thumb(self):
    return "/assets/nothumb.jpg"
    
  def get_embed(self):
    return '<video width="auto" height="auto" controls loop autoplay><source src="' + self.url + '" type="video/webm" /></video>'

class Mp4(MediaPost):
  def __init__(self, url):
    self.url = url

  def get_thumb(self):
    return "http://i.imgur.com/Ej1oWfr.jpg"
    
  def get_embed(self):
    return '<link href="http://vjs.zencdn.net/5.11.6/video-js.css" rel="stylesheet"><script src="http://vjs.zencdn.net/ie8/1.1.2/videojs-ie8.min.js"></script><video id="my-video" class="video-js" controls preload="auto" width="640" height="360" data-setup="{}"><source src="' + self.url + '"><p class="vjs-no-js">Please enable JavaScript</p></video><script src="http://vjs.zencdn.net/5.11.6/video.js"></script>'





class Gif(MediaPost):
  def __init__(self, url):
    self.url = url

  def get_thumb(self):
    output = subprocess.Popen(["/root/allthegoalspostergit/gif.sh", self.url], stdout=subprocess.PIPE).communicate()[0]
    return output.split("\n")[0]
    
  def get_embed(self):
    return '<img src="' + self.url +'"/>'

  def get_type(self):
    return "GIF"

    
class Image(MediaPost):
  def __init__(self, url):
    self.url = url

  def get_thumb(self):
    output = subprocess.Popen(["/root/allthegoalspostergit/gif.sh", self.url], stdout=subprocess.PIPE).communicate()[0]
    return output.split("\n")[0]
    
  def get_embed(self):
    return '<img src="' + self.url +'"/>'

  def get_type(self):
    return "Image"


class MoeVideo(MediaPost):
  def __init__(self, video_id):
    self.video_id = video_id
    self.url = 'http://moevideo.net/video/' + self.video_id
    self.soup = self.get_soup()

  def get_embed(self):
    return '<iframe width="640" height="360" src="http://moevideo.net/framevideo/' + self.video_id + '?width=640&#038;height=360"  frameborder="0" allowfullscreen ></iframe>'



class VidMe(MediaPost):
  def __init__(self, video_id):
    self.video_id = video_id
    self.url = 'http://vid.me/' + self.video_id
    self.soup = self.get_soup()

  def get_embed(self):
    result = self.soup.select('.video_actions_embed a')
    if len(result) != 0:
        width = result[0]['data-width']
        height = result[0]['data-height']
        return '<iframe src="https://vid.me/e/' + self.video_id + '" width="' + width + '" height="' + height + '" frameborder="0" allowfullscreen webkitallowfullscreen mozallowfullscreen scrolling="no"></iframe>'




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
    
    #graph = facebook.GraphAPI('CAADX6q2xheEBACjERsor8CZBsxzoZC3Tw7JSsDY4q1Scu3LlVQS34XYjwxyQMeqvoi0odIkWXOZApMWdrdixvS5HuN7d7yKuo4qbtGAYpKAk7sVZBikoNgk1GWXy9xxdgr8S0w2PmyPxBaHCUF5x0Laszw0gIyDrmXFdsKPjGcTnJpIumSvVZByxKJxuPhikZD')
    self.url =  'https://graph.facebook.com/' + self.video_id + '/?access_token=CAADX6q2xheEBACjERsor8CZBsxzoZC3Tw7JSsDY4q1Scu3LlVQS34XYjwxyQMeqvoi0odIkWXOZApMWdrdixvS5HuN7d7yKuo4qbtGAYpKAk7sVZBikoNgk1GWXy9xxdgr8S0w2PmyPxBaHCUF5x0Laszw0gIyDrmXFdsKPjGcTnJpIumSvVZByxKJxuPhikZD'
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

  def get_type(self):
    return "Vine"


class Streamable(MediaPost):
  def __init__(self, video_id):
    self.video_id = video_id
    self.url = 'http://streamable.com/' + self.video_id
    #self.soup = self.get_soup()

  def get_embed(self):
    #result = self.soup.find(id="embed")
    #return result['value']  + "<center><a href='" + self.url + "'>Direct Link</a></center>"
    return '<iframe src="https://streamable.com/e/' + self.video_id + '" width="640" height="360" frameborder="0" allowfullscreen="" webkitallowfullscreen="" mozallowfullscreen="" scrolling="no" style=""></iframe> <p><a href="' + self.url + '">Direct Link</a></p>'

  def get_thumb(self):

    #result = MediaPost.get_thumb(self)
    return "https://cf-e2.streamablevideo.com/image/" + self.video_id + ".jpg?token=1507998947-Cp0%2BPmXhylnwEqee%2Fm2h9XLCvD3LJuqXtw8cdl9aA%2Bk%3D"
    return result


class Streamja(MediaPost):
  def __init__(self, video_id):
    self.video_id = video_id
    self.url = 'https://streamja.com/' + self.video_id
    self.soup = self.get_soup()

  def get_embed(self):
    return '<iframe src="https://streamja.com/embed/'+ self.video_id + '" frameborder="0" width="640" height="360" allowfullscreen></iframe>' + '<p><a href="' + self.url + '">Direct Link</a></p>'

  def get_thumb(self):
    attrs = self.soup.select('#video_container video[poster]')
    return attrs[0]['poster']



class YouTube(MediaPost):
  def __init__(self, video_id):
    self.video_id = video_id
    self.url = 'http://youtube.com/watch?v=' + self.video_id

  def get_thumb(self):
    return "http://img.youtube.com/vi/" + self.video_id + "/mqdefault.jpg"



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
    return '<img class="gfyitem" data-id="' + self.gfy + '" /><br/><center><a href="'+ self.url + '">Direct Link</a></center>'

  def get_type(self):
    return "GFY"

class GfyWordpress(Gfy):
  def get_embed(self):
    return '[gfy]' + self.gfy + '[/gfy]'



