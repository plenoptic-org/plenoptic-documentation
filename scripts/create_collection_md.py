#!/usr/bin/env python3

import yaml
import argparse
import os
import os.path as op
from glob import glob
from packaging.version import Version

REDIRECT_HTML="""<head>
  <meta http-equiv="Refresh" content="0; URL={}" />
</head>
"""

BROWSE_MD = """---
layout: default
---
{{% assign sublinks="{sublinks}" | split: "," %}}
{{% include browse.html target="{site}" sublinks=sublinks %}}
"""
# throughout this, we do something like `op.split(variable[:-1])[-1]` to grab the folder
# name. that's because we glob strings that end in /, so we need to drop that before
# using op.split


def collection_md(site):
    md_file = {}
    md_file['base_url'] = site
    with open(op.join(site, '.gh_path')) as f:
        md_file['gh_repo'] = 'https://github.com/' + f.read().strip()
    md_file['name'] = op.split(site[:-1])[-1].replace('-', ' ')
    md_file['jekyll_id'] = op.split(site[:-1])[-1]
    branches = glob(op.join(site, 'branch', '*/'))
    md_file['branches'] = []
    md_file['main_url'] = ''
    for branch in branches:
        if 'main' in branch:
            md_file['main_url'] = op.join(site, 'branch', 'main')
        md_file['branches'].append(op.split(branch[:-1])[-1])
    md_file['releases'] = sorted([op.split(p[:-1])[-1] for p in glob(op.join(site, 'tags/*/'))],
                                 key=Version)[::-1]
    md_file['pulls'] = sorted([op.split(p[:-1])[-1] for p in glob(op.join(site, 'pulls/*/'))])[::-1]
    with open(f'site/_docs/{op.split(site[:-1])[-1]}.md', 'w') as f:
        f.write('---\n')
        yaml.safe_dump(md_file, f)
        f.write('---')
    return md_file


def redirect_pages(site, md_file, write_files=True):
    redirect_url = None
    if redirect_url is None and 'main' in md_file['branches']:
        redirect_url = "branch/main/"
    if redirect_url is None and len(md_file['releases']) > 0:
        redirect_url = f"tags/{md_file['releases'][0]}"
    if redirect_url is None and len(md_file['pulls']) > 0:
        redirect_url = f"pulls/{md_file['pulls'][0]}"
    if redirect_url is None and len(md_file['branches']) > 0:
        redirect_url = f"branch/{md_file['branches'][0]}"
    if write_files:
        with open(op.join(site, 'index.html'), 'w') as f:
           f.write(REDIRECT_HTML.format(redirect_url))
        if op.exists(op.join(site, 'branch')):
            with open(op.join(site, 'branch', 'index.html'), 'w') as f:
               f.write(REDIRECT_HTML.format('../' + redirect_url))
        if op.exists(op.join(site, 'pulls')):
            with open(op.join(site, 'pulls', 'index.html'), 'w') as f:
               f.write(REDIRECT_HTML.format('../' + redirect_url))
        if op.exists(op.join(site, 'tags')):
            with open(op.join(site, 'tags', 'index.html'), 'w') as f:
               f.write(REDIRECT_HTML.format('../' + redirect_url))
    return redirect_url


def browse_pages(site, md_file):
    os.makedirs(op.join('site', 'browse_pages', site), exist_ok=True)
    with open(op.join('site', 'browse_pages', site, 'index.md'), 'w') as f:
        f.write(BROWSE_MD.format(site=md_file['jekyll_id'], sublinks="branches,pulls,releases"))
    if op.exists(op.join(site, 'branch')):
        os.makedirs(op.join('site', 'browse_pages', site, 'branch'), exist_ok=True)
        with open(op.join('site', 'browse_pages', site, 'branch', 'index.md'), 'w') as f:
            f.write(BROWSE_MD.format(site=md_file['jekyll_id'], sublinks="branches"))
    if op.exists(op.join(site, 'pulls')):
        os.makedirs(op.join('site', 'browse_pages', site, 'pulls'), exist_ok=True)
        with open(op.join('site', 'browse_pages', site, 'pulls', 'index.md'), 'w') as f:
            f.write(BROWSE_MD.format(site=md_file['jekyll_id'], sublinks="pulls"))
    if op.exists(op.join(site, 'tags')):
        os.makedirs(op.join('site', 'browse_pages', site, 'tags'), exist_ok=True)
        with open(op.join('site', 'browse_pages', site, 'tags', 'index.md'), 'w') as f:
            f.write(BROWSE_MD.format(site=md_file['jekyll_id'], sublinks="releases"))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Automatically create .md files for jekyll to parse."
    )
    parser.add_argument("--root_index_redirect", action="store_true",
                        help="Whether to make the site root index.html page just redirect (else, will create landing page).")
    parser.add_argument("--subdir_index", choices=["redirect", "browse"],
                        help="Whether the subdirectory redirects (e.g., docs/index.html) will redirect or allow users to browse.")
    args = vars(parser.parse_args())
    for site in glob('docs/*/'):
        md_file = collection_md(site)
        if args['subdir_index'] == 'redirect':
            redirect_url = redirect_pages(site, md_file)
        elif args['subdir_index'] == 'browse':
            browse_pages(site, md_file)
    if args['subdir_index'] == 'redirect':
        with open(op.join('docs', 'index.html'), 'w') as f:
            f.write(REDIRECT_HTML.format('../'))
    elif args['subdir_index'] == 'browse':
        with open(op.join('site', 'browse_pages', 'docs', 'index.md'), 'w') as f:
            f.write(BROWSE_MD.format(site="", sublinks="branches,pulls,releases"))
    if args['root_index_redirect']:
        with open(op.join('site', 'index.html'), 'w') as f:
            redirect_url = redirect_pages(site, md_file, write_files=False)
            f.write(REDIRECT_HTML.format(op.join(site, redirect_url)))
