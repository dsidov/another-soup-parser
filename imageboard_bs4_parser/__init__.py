#!/usr/bin/env python
# coding: utf-8

# %%
# This script is for 4chan threads scraping. More about dealing with already downloaded html files (and dashchan archive files), but working with web scraping as well.
# If you want to use ONLY web scraping, maybe it's better to use 4chan API, it's faster - https://github.com/4chan/4chan-API

from bs4 import BeautifulSoup
import requests
import os
import datetime
import shutil


def _unix_to_utc(unix_time, datetime_offset=0, utc_local=True):
    if type(unix_time) is str:
        unix_time = float(unix_time)
    if utc_local:
        date_time = datetime.datetime.fromtimestamp(unix_time+datetime_offset).strftime('%Y-%m-%d %H:%M:%S')
    else:
        date_time = datetime.datetime.utcfromtimestamp(unix_time+datetime_offset).strftime('%Y-%m-%d %H:%M:%S')
    return date_time

def _id_to_int(id, left=0):
    # usually ids look like 'id (OP)'
    # also using for quotes iq formatting '>> id (OP)'
    # if exception generated - id = None
    right = len(id) - 1

    while not id[left].isdigit():
        left += 1
    while not id[right].isdigit():
        right -= 1

    try:
        id_num = int(id[left:(right+1)])
    except ValueError as VE:
        id_num = None
        print(VE)
    return id_num


# %%
class ImageboardThread:
    DEF_PROC_FOLDER = 'in_progress' # folder where html & thread files contain while it still active
    DEF_ARCH_FOLDER = 'archive' # folder where closed threads are moved
    
    DATETIME_OFFSET = 0 # offset relative to utc (in seconds) 
    USE_LOCAL_UTC = True

    class ImageboardPost:
        DEF_THUMB_FOLDER = 'thumb'
        DEF_SRC_FOLDER = 'src'
        CONTENT_FOLDER_SUFFIX = '_files' # suffix for 'web-browser downloads' like
       
        @staticmethod
        def _format_web_path(link):
            if link.startswith('//'):
                link = 'https:' + link
            else: pass
            return link

        @staticmethod
        def _format_path(path, trailing_slash=False):
            path = os.path.abspath(path)
            if '\\' in path: path = path.replace('\\','/')
            if trailing_slash:
                if not path.endswith('/'): path = f'{path}/'
            return path


        @staticmethod
        def _format_parsing_data(parsing_data): # format str, list, etc. to set
            pars_data_type = type(parsing_data) # because bsoup is slow af
            # todo - add lowering case function, checking is list 
            if pars_data_type is set:
                pass
            elif pars_data_type is str:
                parsing_data = {parsing_data}
            elif pars_data_type is list:
                parsing_data = set(parsing_data)
            else: 
                parsing_data = {'all'}
            
            if 'all' in parsing_data: # because parsing data is using in ChanThread like hasattr idenificator
                parsing_data = {'files','time','poster', 'quotes', 'text'}

            return parsing_data

        def __init__(self, post_soup, board):
            self.soup = post_soup
            self.board = board


        def _download_files(self, check_existance=True):
            # the name of every file is unique, check_existance usually True, except re-downloads
            def _download_file(self, key, check_existance):
                key_web = f'{key}_web'
                key_abspath = f'{key}_abspath'
                key_downloaded = f'{key}_downloaded'
                if check_existance:
                    if self.stats[key_downloaded] or (os.path.isfile(self.file[key_abspath]) and (os.stat(self.file[key_abspath]).st_size > 0)):
                        print('file_exists')
                else: pass
                data = requests.get(self.file[key_web])

                with open(self.file[key_abspath], 'wb') as f:
                    f.write(data.content)  
                if os.path.isfile(self.file[key_abspath]) and (os.stat(self.file[key_abspath]).st_size > 0):
                    self.stats[key_downloaded] = True
                else:
                    self.warnings['file_downloading'] = 'Creating empty files'

            # add download src only option
            if hasattr(self, 'file') and (self.file is not None):
                for keys in ('thumb', 'src'):
                    _download_file(self,keys, check_existance)

              

            
    class DashchanPost(ImageboardPost): # Files ONLY
        
        def __init__(self, post_soup, board, imageboard, is_op_post=False, parsing_data={'all'}):
            # parsing data params = all, files, time, poster, quotes, text 
            # op_post soup = thread soup
            super().__init__(post_soup, board)       
            self.warnings = dict()
            self.stats = dict()
            
            if is_op_post:
                self.id = _id_to_int(self.soup.find('span')['data-number'])
            else:
                self.id = _id_to_int(self.soup['id'])


            if parsing_data is not None:
                #file
                if 'files' in parsing_data:
                    post_file = self.soup.find('span',{'class':'filesize'})
                    if post_file is None:
                        self.file = None
                    else:
                        self.file = dict()
                        #todo - add abspath
                        self.file['name'] = post_file['data-original-name']
                        self.file['thumb_relpath'] = post_file['data-thumbnail']
                        self.file['src_relpath'] = post_file['data-file']

                        info_split = post_file.find('em').string.split(',')[0:2]
                        self.file['info'] = ','.join(info_split).replace('Г—','x')
                else: pass

                # time
                if 'time' in parsing_data:
                    # if is_op_post:
                    try:
                        self.unix_time = int(self.soup.find('span',{'class':'postername'}).next_sibling.next_sibling['data-timestamp'][0:-3])
                    except ValueError as VE:
                        self.unix_time = None
                        self.warnings['unix_time'] = VE
                else: pass

                # poster
                if 'poster' in parsing_data:
                    self.poster = dict()
                    post_author = self.soup.find('span',{'class':'postername'})
                    
                    if board == 'pol': # ONLY 4CHAN HAS POL, INCREASE IF MORE IMAGEBOARDS WILL BE ADDED
                        self.poster['country'] = self.soup.find('img',{'class':'postericon'})['title']
                        self.poster['id'] = post_author['data-identifier']
                    poster_name = post_author['data-name']
                    if poster_name == 'Anonymous': poster_name = None
                    self.poster['name'] = poster_name
                else: pass

                
                if ('quotes' in parsing_data):
                    self.quotes = list() 
                    if is_op_post:
                        pass # no quotes in OpPost For Now (are they exist?)
                    else:
                        # self.quoted_by = list() # adding elements later from ChanThread func
                        if not hasattr(self,'message_soup'):
                            self.message_soup = self.soup.find('blockquote')
                        for quotes in self.message_soup.find_all(['a','href']):
                            quote_num = _id_to_int(quotes.string, left=1)
                            if quote_num is not None:
                                self.quotes.append(quote_num)
                            else: pass # add warnings
                else: pass
                # text
                if 'text' in parsing_data:
                    if not hasattr(self,'message_soup'):
                        self.message_soup = self.soup.find(['blockquote','data-comment'])
                    
                    text = ''
                    for i in self.message_soup.children: # making message text line-by-line, </br>.string is None
                        if i.string is None:
                            text = f'{text}\n'
                        else:
                            text = f'{text}{i.string}'
                    
                    if text.startswith('\n'): text = text[1:]
                    if text.endswith('\n'): text = text[:-1]
                    self.text = text
                else: 
                    pass

    class FourchanPost(ImageboardPost):
        
        @classmethod
        def _get_id(cls, post_soup):
            id = _id_to_int(str(post_soup.div['id']))
            return id

        def __init__(self, post_soup, board, download_folder=None, parsing_data={'all'}):
            # download_folder - None means that it's file or don't download
            # parsing data params = all, files, time, poster, quotes, text 
            # todo - add lowering case function, checking is list 


            super().__init__(post_soup, board)

            self.warnings = dict()
            
            # id & board are always available
            self.id = self._get_id(self.soup)

            #stats
            self.stats = dict()
            self.stats['active'] = True
            if parsing_data is not None:
            #file
                if 'files' in parsing_data:
                    post_file = self.soup.find('div',{'class':'file'})
                    if post_file is None:
                        self.file = None
                    else:
                        self.file = dict()
                        if len(post_file.find('div',{'class':'fileText'}).select('[title]')) > 0:
                            self.file['name'] = post_file.find('div',{'class':'fileText'}).a['title']
                        else:
                            self.file['name'] = post_file.find('div',{'class':'fileText'}).a.string
                        thumb_web = post_file.find('img')['src']
                        src_web = post_file.find('a',{'class':'fileThumb'})['href']
                        self.file['info'] = post_file.find('div').contents[-1][2:-1] # op_file.contents[0].contents[-1][2:-1]
                        self.file['md5'] = post_file.find('img')['data-md5'] # op_file.contents[1].img['data-md5']
                        self.stats['thumb_downloaded'] = False
                        self.stats['src_downloaded'] = False

                        if download_folder is not None: # for web htmls
                            download_folder_rel = download_folder.split('/')[-2]
                            thumb_name, thumb_extention = os.path.splitext(self.file['name'])
                            thumb_relpath = f'{self.DEF_THUMB_FOLDER}/{thumb_name}-fourchan-{self.board}-{self.id}{thumb_extention}'
                            src_name, src_extention = os.path.splitext(self.file['name'])
                            src_relpath = f'{self.DEF_SRC_FOLDER}/{src_name}-fourchan-{self.board}-{self.id}{src_extention}'
                            self.file['thumb_web'] = self._format_web_path(thumb_web) # op_file.contents[1].img['src']
                            self.file['src_web'] = self._format_web_path(src_web) # op_file.contents[1]['href']
                            self.file['thumb_abspath'] = f'{download_folder}{thumb_relpath}' # for downloading
                            self.file['thumb_relpath'] = f'/{download_folder_rel}/{thumb_relpath}' # relpath is for local html file
                            self.file['thumb'] = thumb_web # for changing links in final html doc
                            self.file['src_abspath'] = f'{download_folder}{src_relpath}'
                            self.file['src_relpath'] = f'/{download_folder_rel}/{src_relpath}'
                            self.file['src'] = src_web
                        else: # for local htmsl
                            self.file['thumb_relpath'] = thumb_web # op_file.contents[1].img['src']
                            self.file['src_relpath'] = src_web # op_file.contents[1]['href']
                else: pass

                # time
                if 'time' in parsing_data:
                    try:
                        print(self.soup)
                        self.unix_time = int(self.soup.find('span',{'class':'dateTime'})['data-utc'])
                        
                    except ValueError as VE:
                        self.unix_time = None
                        self.warnings['unix_time'] = VE
                else: pass

                # poster
                if 'poster' in parsing_data:
                    self.poster = dict()
                    post_author = self.soup.find('span',{'class','nameBlock'})
                    
                    if board == 'pol':
                        self.poster['country'] = post_author.contents[4]['title']
                        self.poster['id'] = post_author.find('span',{'class':'hand'}).string #%timeit str(post_author.contents[2]['class'][1])[3:]
                    poster_name = self.soup.find('span',{'class':'nameBlock'}).span.string
                    if poster_name == 'Anonymous': poster_name = None
                    self.poster['name'] = poster_name
                else: pass

                # quotes - list of ids on which THIS POST is quoting, not list of answering posts ids
                if 'quotes' in parsing_data:
                    self.quotes = list() 
                    # self.quoted_by = list() # adding elements later from ChanThread func
                    if not hasattr(self,'message_soup'):
                        self.message_soup = self.soup.find('blockquote')
                    for quotes in self.message_soup.find_all('a',{'class':'quotelink'}):
                        quote_num = _id_to_int(quotes.string, left=2)
                        if quote_num is not None:
                            self.quotes.append(quote_num)
                        else: pass # add warnings
                else: pass
                
                # text
                if 'text' in parsing_data:
                    if not hasattr(self,'message_soup'):
                        self.message_soup = self.soup.find('blockquote')
                    
                    text = ''
                    for i in self.message_soup.children: # making message text line-by-line, </br>.string is None
                        if i.string is None:
                            text = f'{text}\n'
                        else:
                            text = f'{text}{i.string}'
                        self.text = text
                else: 
                    pass
    
    # --- Imageboard Thread Methods ---

    def _make_folders(self, has_files=False):
        if not os.path.exists(self.file_paths_process):
            try: 
                os.makedirs(self.file_paths_content)
            except FileExistsError:
                pass
        if has_files:
            thumbs_path = f'{self.file_paths_content}{self.FourchanPost.DEF_THUMB_FOLDER}/'
            src_path = f'{self.file_paths_content}{self.FourchanPost.DEF_SRC_FOLDER}/'
            for path in (self.file_paths_content, thumbs_path, src_path):

                if not os.path.exists(path):
                    try:
                        os.makedirs(path)
                    except FileExistsError:
                        pass

    def _fourchan_is_404(self): # is 404 at 4chan, not web
        if self.soup.find('div',{'id':'bd'}) is not None: 
            return True
        else: return False

    def _check_stats(self): # archived status
        self.stats = dict()
        if self.data_src == 'dashchan':
            pass
        elif self.data_src == 'fourchan':
            if (self.soup.find('div',{'class':'closed'}) is not None) or (self.soup.find('form',{'name':'post'}) is None):
                self.stats['closed'] = True
            else:
                self.stats['closed'] = False
        self.stats['posts'] = len(self.posts)
        if hasattr(self.posts[0],'file'):
            self.stats['files'] = 0
            for posts in self.posts:
                if posts.file is not None:
                    self.stats['files'] += 1

    def _soup_to_html(self):
        if hasattr(self, 'file_paths_html'):
            with open(self.file_paths_html, 'wb') as f:
                f.write(self.soup.prettify('utf-8'))
        else: print('NO HTML PATH') # add warning

    def _make_soup(self, link_or_path, its_file=False, attr='soup'):
    # save html - save html at disk BUT only if thread is not 404
        if its_file:
            with open(link_or_path, 'r') as f:
                setattr(self, attr, BeautifulSoup(f, 'html.parser'))
        else:
            page_src = requests.get(link_or_path)
            if page_src.status_code != 404:
                self.html_src = page_src.content
                setattr(self, attr, BeautifulSoup(page_src.content,'html.parser'))
            else: print('4CHAN IS DOWN')
            # add warnings here


    def _save_html_src(self, filename=None):
        if hasattr(self, 'html_src'):
            if filename is None:
                file_path = self.file_paths_html
            else:
                file_path = f'{self.file_paths_process}{filename}'
            with open(file_path,'wb') as f:
                f.write(self.html_src)
        else:
            print('no HTML SRC')

    def _count_quotes(self): # making quoted_by attr in self.posts
        quoted_by_dict = dict()
        for post in self.posts:
            for quote in post.quotes:
                if quote not in quoted_by_dict:
                    quoted_by_dict[quote] = list()
                quoted_by_dict[quote].append(post.id)
        for post in self.posts:
            if post.id in quoted_by_dict:
                post.quoted_by = quoted_by_dict[post.id]
            else:
                post.quoted_by = None

    def _make_fourchan_posts(self, op_post_only=False):
        self.posts = list()
        self.posts_ids = set()
        op_post = self.soup.find('div', {'class':'postContainer opContainer'})            
        self.subject = op_post.find('span', {'class':'subject'}).string
        self.posts.append(self.FourchanPost(op_post,self.board,self.file_paths_content,self.parsing_data))
        if not op_post_only:
            for reply_post in self.soup.find_all('div', {'class':'postContainer replyContainer'}):
                post = self.FourchanPost(reply_post,self.board,self.file_paths_content,self.parsing_data)
                self.posts.append(post)
                self.posts_ids.add(post.id)

    def _make_dashchan_posts(self, op_post_only=False):
        self.posts = list()
        self.posts_ids = set()
        op_post = self.soup
        self.subject = op_post.find('span',{'class':'replytitle'}).string
        self.posts.append(self.DashchanPost(op_post, self.board, self.data_src, True, self.parsing_data))
        if not op_post_only:
            for reply_post in self.soup.find_all('td',{'class':'reply'}):
                post = self.DashchanPost(reply_post,self.board,self.data_src, False, self.parsing_data)
                self.posts.append(post)
                self.posts_ids.add(post.id)   


    def __init__(self, link_or_filepath, process_folder=None, archive_folder=None, op_post_only=False, parsing_data={'files'}):
        def _recognize_file_type(self):
            try:
                imgb_str = self.soup.find('p').text.lower()
                if 'dashchan' in imgb_str:
                    imageboard = 'dashchan'
                else:
                    imageboard = 'fourchan'
            except:
                imageboard = 'fourchan'
            self.data_src = imageboard

        def _its_file(link_or_filepath):
            if link_or_filepath.startswith('http'):
                return False
            else: return True

        def _make_file_paths(self, link_or_filepath, process_folder, archive_folder, its_file):
        # process_folder - where html is contained & thread files folder
        # also script decide is it file or web on folders existance
            if its_file:
                path = self.ImageboardPost._format_path(link_or_filepath)
                # if '\\' in path: path = path.replace('\\','/')
                content_path, _ = os.path.splitext(path)
                if self.data_src == 'fourchan':
                    self.file_paths_content = f'{content_path}{self.ImageboardPost.CONTENT_FOLDER_SUFFIX}/'
                elif self.data_src == 'dashchan':
                    self.file_paths_content = f'{content_path}/'
                self.file_paths_html = path
            else:
                self.file_paths_link = link_or_filepath
             
                if process_folder is None: proc_path = self.ImageboardPost._format_path('',trailing_slash=True)
                else: proc_path = self.ImageboardPost._format_path(process_folder,trailing_slash=True)
                
                if process_folder is None: 
                    self.file_paths_process = f'{proc_path}{self.DEF_PROC_FOLDER}/'
                    path = f'{self.file_paths_process}fourchan-{self.board}-{self.id}'
                else: 
                    self.file_paths_process = proc_path
                    path = f'{proc_path}fourchan-{self.board}-{self.id}'
                
                self.file_paths_html = f'{path}.html'
                self.file_paths_content = f'{path}{self.ImageboardPost.CONTENT_FOLDER_SUFFIX}/'

                if archive_folder is None:
                    # self.file_paths_archive = None
                    pass
                else:
                    arch_path = self.ImageboardPost._format_path(archive_folder,trailing_slash=True)
                    if arch_path == proc_path: self.file_paths_archive = None
                    else: self.file_paths_archive = arch_path

        #self.__init__ body
        its_file = _its_file(link_or_filepath)
        self._make_soup(link_or_filepath, its_file)
        if its_file:
            _recognize_file_type(self)
        else:
            self.data_src = 'fourchan'
        self.parsing_data = self.ImageboardPost._format_parsing_data(parsing_data)

        if its_file:
            _make_file_paths(self, link_or_filepath, None, None, its_file)
            if self.data_src == 'dashchan':  # --- DASHCHAN ---
                src_link_splitted = self.soup.find('div',{'id':'delform'})["data-thread-uri"].split('/')
                self.board = src_link_splitted[-3]
            elif self.data_src == 'fourchan':
                self.board = self.soup.find('div',{'class':'boardTitle'}).string.split('/')[1] 
                # self.time = self.soup.find('span',{'class':'dateTime'})['data-utc']
        else: # if web link
            link_splitted = link_or_filepath.split('/')
            self.board = link_splitted[3]
            self.id = _id_to_int(link_splitted[5])
            _make_file_paths(self, link_or_filepath, process_folder, archive_folder, its_file)
            self._make_folders(has_files=False)
            self._save_html_src()
         # 
            # self._download_html()

        if not self._fourchan_is_404() or (self.data_src == 'dashchan'):
            # making post list with subject
            if self.data_src == 'fourchan':
                self._make_fourchan_posts(op_post_only)
            elif self.data_src == 'dashchan':
                self._make_dashchan_posts(op_post_only)
            self._check_stats()
            self.id = self.posts[0].id
        
            # self.op_post = op_post.find('blockquote').text # op_post.contents[-1].blockquote.text
            # posts set
        else:
            print('Thread is 404')
                
        if hasattr(self, 'file_paths_process') and ('files' in self.stats) and (self.stats['files'] > 0):
            self._make_folders(has_files=True)
            for posts in self.posts:
                posts._download_files(check_existance=True)

        if hasattr(self.posts[0],'quotes'):
            self._count_quotes()
        if hasattr(self.posts[0],'unix_time'):
            self._convert_time()
            self.unix_time = self.posts[0]
            self.time = self.posts[0].time

    def _convert_time(self):
        for post in self.posts:
            if not hasattr(post,'time'):
                post.time = _unix_to_utc(post.unix_time,self.DATETIME_OFFSET, self.USE_LOCAL_UTC)

    def update(self, consider_moderation=False): 
        # moderation - remove files and post from obj if jannies removed it from thread (they do it for free)
        if hasattr(self, 'file_paths_process'):
            posts_num = len(self.posts)
            self._make_soup(self.file_paths_link, attr='soup')
            if not self._fourchan_is_404():
                self._save_html_src()
                for reply_post in self.soup.find_all('div', {'class':'postContainer replyContainer'}):
                    post_id = ImageboardThread.FourchanPost._get_id(reply_post)
                    if post_id in self.posts_ids:
                        continue
                    else:
                        post = self.FourchanPost(reply_post,self.board,self.file_paths_content,self.parsing_data)
                        self.posts.append(post)
                        self.posts_ids.add(post.id)
            self._check_stats()

            if  ('files' in self.stats) and (self.stats['files'] > 0):
                self._make_folders(has_files=True)
                for posts in self.posts:
                    posts._download_files()

            if hasattr(self.posts[0],'quotes'):
                self._count_quotes()    
            if hasattr(self.posts[0],'unix_time'):
                self._convert_time()
            print(f'added {posts_num-len(self.posts)} posts')
            # if consider_moderation:
            #     replies_ids_updated = set()
            # self._check_stats(count_all=False)

            # if consider_moderation: 
            #     replies_ids_updated.add(post.id)
            # if post.id not in self.thread_ids:
            #     self.posts.append(post)
            #     self.replies_ids.add(post.id)
            # if consider_moderation:
            #     replies_diff = self.replies_ids.difference(replies_ids_updated)
            #     if len(replies_diff) > 0:
            #         for post in self.posts:
            #             if post.id in replies_diff:
            #                 pass
            #                 # post._remove_files()
        else:
            print('its not working with files')
    
    def move_thread(self, new_path, sorting_pattern=None): # move html file with files
        # sorting_pattern - 'day', 'month', 'year'. ONLY if data in _parsing_data. Creates folder like '2020-12' in new_path
        new_path = self.ImageboardPost._format_path(new_path,trailing_slash=True)
        if type(sorting_pattern) is str:
            sorting_pattern = sorting_pattern.lower()
        else: sorting_pattern = None
        if (sorting_pattern is not None) and hasattr(self.posts[0],'time'):
            date_time = self.posts[0].time
            if sorting_pattern == 'day':
                new_path = f'{new_path}{date_time[:10]}/'
            if sorting_pattern == 'month':
                new_path = f'{new_path}{date_time[:7]}/'
            if sorting_pattern == 'year':
                new_path = f'{new_path}{date_time[:4]}/'     
        if not os.path.exists(new_path):
            try: 
                os.makedirs(new_path)
            except FileExistsError:
                pass
        print(new_path)
        print(self.file_paths_html)
        print(self.file_paths_content)
        try:
            shutil.move(self.file_paths_html, new_path)
            shutil.move(self.file_paths_content, new_path)
        except Exception as error:
            print(error)

def _format_search_urls(board, search_text):
    if ' ' in search_text:
        search_text = search_text.replace(' ','%20')
    search_url = 'https://boards.4chan.org/' + board + '/catalog#s=' + search_text        
    return search_url
