import csv
import sys
import os
from pathlib import Path
from markdownify import MarkdownConverter
import requests
import uuid
from urllib.parse import urlparse


csv_filename = sys.argv[1] if len(sys.argv) > 1 else 'posts.csv'
in_dir = sys.argv[2] if len(sys.argv) > 2 else 'posts'
out_dir = sys.argv[3] if len(sys.argv) > 3 else 'md_posts'
from_date = sys.argv[4] if len(sys.argv) > 4 else '2022-12-18'

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

# Create shorthand method for conversion
def md(html, **options):
    return ImageBlockConverter(**options).convert(html)

def process_post(post_id, post_date, post_title, post_subtitle):
    p = Path(in_dir) / Path(f'{post_id}.html')
    with open(p, 'r') as f:
        text = f.read()
        markdown = md(text)
        o = Path(out_dir) / Path(f'{post_id}.md')
        with open(o, 'w') as of:
            of.write(f'# {post_title}\n\n')
            if post_subtitle:
                of.write(f'**{post_subtitle}**\n\n')
            of.write(markdown)


with open(csv_filename) as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['type'] == 'newsletter' and row['post_date'] >= from_date:
            process_post(row['post_id'], row['post_date'],row['title'],row['subtitle'])
            print(row['post_id'], row['post_date'], row['title'], row['subtitle'])
