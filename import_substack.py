import click
import os
import csv
from datetime import date
from pathlib import Path
from markdownify import MarkdownConverter
import requests
import uuid
from urllib.parse import urlparse


class ImageBlockConverter(MarkdownConverter):

    def __init__(self, out_dir, base_prefix, md_urls, **options):
        self.out_dir = out_dir
        self.base_prefix = base_prefix
        self.md_urls = md_urls
        super().__init__(**options)

    """
    Create a custom MarkdownConverter that adds two newlines after an image
    """
    def convert_img(self, el, text, convert_as_inline):
        src = el['src']
        path = urlparse(src).path
        ext = os.path.splitext(path)[1]
        img_data = requests.get(el['src']).content
        img_id = f'img_{str(uuid.uuid4())}{ext}'
        o = Path(self.out_dir) / Path(img_id)
        with open(o, 'wb') as of:
            of.write(img_data)

        return f'![[{img_id}]]'

    def convert_hn(self, n, el, text, convert_as_inline):
        return f'\n\n{super().convert_hn(n, el, text, convert_as_inline)}'

    def convert_a(self, el, text, convert_as_inline):
        href = el['href']
        if href.startswith(self.base_prefix):
            path = href.removeprefix(self.base_prefix).split('?')
            key = path[0] if len(path) > 0 else path
            if key in self.md_urls:
                return f'[[{self.md_urls[key]}]]'
        return super().convert_a(el, text, convert_as_inline)

    def convert_iframe(self, el, text, convert_as_inline):
        return str(el)

# Create shorthand method for conversion
def md(html, path, base_prefix, md_urls,  **options):
    return ImageBlockConverter(path, base_prefix, md_urls, **options).convert(html)

def normalize_title(title):
    if '#' in title:
        title = title
    return " ".join(title.split())


def process_post(base_dir, in_dir, base_prefix, md_urls, post_id, post_date, post_title, post_subtitle):
    (year, month, _) = post_date.split('-')
    out_dir = Path(base_dir) / Path(year) / Path(month)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    p = Path(in_dir) / Path(f'{post_id}.html')
    with open(p, 'r') as f:
        text = f.read()
        markdown = md(text, out_dir, base_prefix, md_urls)
        in_url = f'{normalize_title(post_title)}.md'
        o = out_dir / Path(in_url)
        with open(o, 'w') as of:
            of.write('---\n')
            of.write(f'title: {normalize_title(post_title)}\n')
            of.write(f'subtitle: {post_subtitle}\n')
            of.write(f'created: {post_date}\n')
            of.write(f"imported: {date.today().strftime('%Y-%m-%dT%H:%M%')}\n")
            of.write(f'tags: newsletter substack imported\n')
            of.write('---\n\n')
            of.write(f'# {post_title}\n\n')
            if post_subtitle:
                of.write(f'**{post_subtitle}**\n\n')
            of.write(markdown)


@click.command()
@click.argument("csv_file", default='posts.csv', type=click.Path(exists=True))
@click.argument("input_folder", default='posts', type=click.Path(exists=True, dir_okay=True))
@click.argument("output_folder", default='md_posts', type=click.Path(exists=False))
@click.option("-f", "--from-date", default='2022-12-18', type=str)
@click.option("-p", "--base-prefix", default='https://newsletter.lnds.net/p/', type=str)
def import_from_substack(csv_file, input_folder, output_folder, from_date, base_prefix):
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)
    md_urls = dict()
    with open(csv_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            post_id = row['post_id']
            post_title = row['title']
            _, k = post_id.split('.')
            in_url = f'{normalize_title(post_title)}'
            md_urls[k] = in_url

        f.seek(0)

        for row in reader:
            if row['type'] == 'newsletter' and row['post_date'] >= from_date:
                process_post(output_folder, input_folder, base_prefix, md_urls, row['post_id'], row['post_date'], row['title'], row['subtitle'])
                print(row['post_id'], row['post_date'], row['title'], row['subtitle'])

if __name__ == '__main__':
    import_from_substack()
