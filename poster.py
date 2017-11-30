from wordpress_xmlrpc import Client, WordPressPost, WordPressTerm
from wordpress_xmlrpc.methods.posts import GetPosts, EditPost
from wordpress_xmlrpc.methods  import posts
from wordpress_xmlrpc.methods import taxonomies

import datetime
import argparse
from urlparse import urlparse, parse_qs
import media_sources


class WordPressPoster:  
    def __init__(self, date, primary_category_name, secondary_category_name=None):      
        self.client = Client('http://www.instagoals.com/xmlrpc.php', 'admin', 'Arsenal14!$')
        self.date = date
        self.primary_category_name = primary_category_name
        self.secondary_category_name = secondary_category_name

    def format_date(self, date):
        return datetime.datetime.strptime(date, '%Y-%m-%d').date().strftime("%B %d %Y")


    def create_category(self, category_name, parent_category_id=None):
        category = WordPressTerm()
        category.taxonomy = 'category'
        if parent_category_id != None:
            category.parent = parent_category_id
        category.name = category_name
        category.id = self.client.call(taxonomies.NewTerm(category))
        return category

    def get_category(self, category_name):
        results = self.client.call(taxonomies.GetTerms('category', {'search': category_name}))
        if len(results) == 0:
            return None
        else:
            return results[0]

    def find_terms(self):
        cat_list = []
        cat = self.get_category(self.primary_category_name)
        if cat == None:
            cat = self.create_category(self.primary_category_name, 25) # Competition
        cat_list.append(cat)

        if self.secondary_category_name != None:
            cat = self.get_category(self.secondary_category_name)
            if cat == None:
                cat = self.create_category(self.secondary_category_name, 7) # Matches
            cat_list.append(cat)
        return cat_list



    def create_match_post(self, media_post, title, tags, extra):
        post = WordPressPost()
        post.title = title
        if extra == None:
            extra = ""
        post.content = media_post.get_embed() + extra
        post.terms_names = {
                'post_tag': tags
        }

        post.terms = self.find_terms()
        post.post_status = 'publish'
        post.custom_fields = [
            {
                'key': 'thumbnail',
                'value': media_post.get_thumb()
            },
            {
                'key': 'event_date',
                'value': self.date
            }           
        ]
        post.id = self.client.call(posts.NewPost(post))
        return post


class MediaPostFactory:
    @staticmethod
    def create(url):
        if url.endswith('.webm'):
            return media_sources.Webm(url)
        if url.endswith('.mp4'):
            return media_sources.Mp4(url)
        if url.endswith('.gif'):
            return media_sources.Gif(url)
        if url.endswith('.jpg') or url.endswith('.png'):
            return media_sources.Image(url)
           
        u = urlparse(url)
        params = parse_qs(u.query)
        print u.hostname
        if u.hostname == 'www.youtube.com' or u.hostname == 'm.youtube.com':
            return media_sources.YouTube(params['v'][0])
        elif u.hostname == 'ok.ru':
            return media_sources.OkRu(u.path.split('/')[2])
        elif u.hostname == 'youtu.be':
            return media_sources.YouTube(u.path.split('/')[1])
        elif u.hostname == 'vid.me':
            return media_sources.VidMe(u.path.split('/')[1])
        elif u.hostname == 'moevideo.net':
            return media_sources.MoeVideo(u.path.split('/')[2])
        elif u.hostname == 'videa.hu':
            return media_sources.Videa(url)
        elif u.hostname == 'www.lastminutegoals.org':
            return media_sources.LastMinuteGoals(url)
        elif u.hostname == 'www.facebook.com':
            if 'video_id' in params:
                return media_sources.Facebook(params['video_id'][0])
            elif 'v' in params:
                return media_sources.Facebook(params['v'][0])
        elif u.hostname == 'www.dailymotion.com':
            return media_sources.DailyMotion(u.path.split("/")[2])
        elif u.hostname == 'gfycat.com' or u.hostname == 'www.gfycat.com':
            return media_sources.Gfy(u.path.split("/")[1])
        elif u.hostname == 'streamable.com' or u.hostname == 'www.streamable.com':
            return media_sources.Streamable(u.path.split("/")[1])
        elif u.hostname == 'vine.co':
            return media_sources.Vine(u.path.split("/")[2])
        elif u.hostname == 'vimeo.com':
            return media_sources.Vimeo(u.path.split("/")[1])
        elif u.hostname == 'rutube.ru':
            return media_sources.Rutube(u.path.split("/")[2])
        elif u.hostname == 'mediacru.sh':
            return media_sources.MediaCrush(u.path.split("/")[1])
        elif u.hostname == 'livetv.sx':
            return media_sources.LiveTV(url)
        else:
            raise NotImplementedError("No MediaPost implemented for " + url) 


def main():
    p = argparse.ArgumentParser(description='Command')
    p.add_argument('-a', '--date', default=datetime.date.today().strftime('%Y-%m-%d'))
    p.add_argument('-g', '--tags', nargs="*", default=[])
    p.add_argument("-m", '--matchcategory', help="Match category", required=False)
    p.add_argument("-u", '--source', help="Source", required=False)

    p.add_argument('-d', '--description', required=True)
    p.add_argument("-s", '--sitecategory', help="Site category", required=True)
    p.add_argument('url')
    
    
    args = vars(p.parse_args())
    source = None
    if args['source']:
        source = '<p><a href="' + args['source'] + '">Source</a></p>'
    wpp = WordPressPoster(args['date'], args['sitecategory'], args['matchcategory'])
    wpp.create_match_post(MediaPostFactory.create(args['url']), args['description'], args['tags'], source)

if __name__ == '__main__':
    main()


"""h
python poster.py -t Zarar Siddiqi
atg -t tag1 tag2 -d 2014-09-28 epl home away title

"""
date = "2014-06-24"


#posts = client.call(posts.GetPosts())
#print posts[0].custom_fields

#dm = DailyMotion('x20o71o_things-tim-howard-could-save-next_lifestyle')
#print dm.get_embed()
