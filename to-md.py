import csv
import sys
import os
from datetime import date
from pathlib import Path
from markdownify import MarkdownConverter
import requests
import uuid
from urllib.parse import urlparse

csv_filename = sys.argv[1] if len(sys.argv) > 1 else 'posts.csv'
in_dir = sys.argv[2] if len(sys.argv) > 2 else 'posts'
out_dir = sys.argv[3] if len(sys.argv) > 3 else 'md_posts'
from_date = sys.argv[4] if len(sys.argv) > 4 else '2022-12-18'
base_prefix = sys.argv[5] if len(sys.argv) > 5 else 'https://newsletter.lnds.net/p/'

md_urls = dict()

if not os.path.exists(out_dir):
    os.mkdir(out_dir)
    os.mkdir(Path(out_dir)/Path('img'))

class ImageBlockConverter(MarkdownConverter):
    """
    Create a custom MarkdownConverter that adds two newlines after an image
    """
    def convert_img(self, el, text, convert_as_inline):
        src = el['src']
        path = urlparse(src).path
        ext = os.path.splitext(path)[1]
        img_data = requests.get(el['src']).content
        img_id = f'{str(uuid.uuid4())}{ext}'
        o = Path(out_dir) / Path('img') / Path(img_id)
        with open(o, 'wb') as of:
            of.write(img_data)
        el['src'] = f'img/{img_id}'
        return super().convert_img(el, text, convert_as_inline) + '\n\n'

    def convert_hn(self, n, el, text, convert_as_inline):
        return f'\n\n{super().convert_hn(n, el, text, convert_as_inline)}'

    def convert_a(self, el, text, convert_as_inline):
        href = el['href']
        if href.startswith(base_prefix):
            path = href.removeprefix(base_prefix).split('?')
            key = path[0] if len(path) > 0 else path
            if key in md_urls:
                return f'[[{md_urls[key]}]]'
        return super().convert_a(el, text, convert_as_inline)

# Create shorthand method for conversion
def md(html, **options):
    return ImageBlockConverter(**options).convert(html)

def process_post(post_id, post_date, post_title, post_subtitle):
    p = Path(in_dir) / Path(f'{post_id}.html')
    with open(p, 'r') as f:
        text = f.read()
        markdown = md(text)
        in_url = f'{post_title}.md'
        o = Path(out_dir) / Path(in_url)
        with open(o, 'w') as of:
            of.write('---\n')
            of.write(f'title: {post_title}\n')
            of.write(f'subtitle: {post_subtitle}\n')
            of.write(f'created: {post_date}\n')
            of.write(f"imported: {date.today().strftime('%Y-%m-%dT%H:%M%')}\n")
            of.write(f'tags: newsletter substack imported\n')
            of.write('--\n')
            of.write(f'# {post_title}\n\n')
            if post_subtitle:
                of.write(f'**{post_subtitle}**\n\n')
            of.write(markdown)

# pre process internal urls
with open(csv_filename) as f:
    reader = csv.DictReader(f)
    for row in reader:
        post_id = row['post_id']
        post_title = row['title']
        _, k = post_id.split('.') 
        in_url = f'{post_title}'
        md_urls[k] = in_url

# process files
with open(csv_filename) as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['type'] == 'newsletter' and row['post_date'] >= from_date:
            process_post(row['post_id'], row['post_date'],row['title'],row['subtitle'])
            print(row['post_id'], row['post_date'], row['title'], row['subtitle'])
