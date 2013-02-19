#!/bin/bash
# usage:
# 1. update version in setup.py
# 2. call this script (before git-commiting)
key='<leoboiko@namakajiri.net>'

if ! gpg --list-keys --with-colons | grep "^pub" | grep -q "$key:"
then
  echo "Could not find GPG key $key!"
  exit 1
fi

set -e
cd $(dirname "$0")/..
version="$(python3 setup.py --version)"
git commit -a -m "releasing $version"
git tag -u "$key" "$version" -m "releasing $version"
git push
python3 setup.py sdist upload --sign --identity="$key"
