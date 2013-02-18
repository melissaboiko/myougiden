#!/bin/bash
key=leoboiko@namakajiri.net

cd $(dirname "$0")
version="$(python3 setup.py --version)"
git tag -u "$key" "$version" -m "releasing $version"
git push
python3 setup.py sdist upload --sign --identity="$key"
