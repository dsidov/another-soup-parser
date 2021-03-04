# 4chan/Dashchan thread parser

This script made for 4chan/Dashchan threads scraping from existing html files.
It doesn't matter which boards Dashchan archives are.


Script works fine with 4chan web treads scraping too, but, because of beautifulsoup4, his perfomance is not so good. 
For better perfomance use [4Chan API](https://github.com/4chan/4chan-API).


## Dependencies
* Python 3.7+
* BeautifulSoup4
`pip3 install beautifulsoup4`

## Example
parsing data could be: 'files', 'poster', 'quotes', 'text' or 'all' (and their combinations)

For local html files & Dashchan archives:
```
from imageboard_bs4_parser import ImageboardThread
var = ImageboardThread(path, parsing_data)
```

For web 4chan threads
```
from imageboard_bs4_parser import ImageboardThread
var = ImageboardThread(link, process_folder, parsing_data)
var.update()
var.move_thread(new_path)
```

#### Class ImageboardThread operational attributes (parsing_data must have a matching variable)
* `id` - int
* `unix_time` - int
* `time` - str from unix_time (%Y-%m-%d %H:%M:%S)
* `posts` - FourchanPost/DashchanPost object list

#### Class FourchanPost/DashchanPost operational attributes (parsing_data must have a matching variable)
* `id` - int
* `unix_time` - int 
* `time` - str from unix_time (%Y-%m-%d %H:%M:%S)
* `file` - dict with all file params (name, size, md5, thumb/src web links, thumb/src downloaded paths, etc.)
* `poster` - dict with all information about poster if board has any (poster id, name, country, etc.)
* `quotes` - list of post ids referenced by the post
* `quoted_by` - list of posts ids that reply to this post
* `text` - str

