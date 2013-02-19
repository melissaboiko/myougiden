#!/bin/bash
key='<leoboiko@namakajiri.net>'

if ! gpg --list-keys --with-colons | grep "^pub" | grep -q "$key:"
then
  echo "Could not find GPG key $key!"
  exit 1
fi

set -e
cd $(dirname "$0")/..
version="$(./setup.py --version | sed -e "s/dev$//")"
sed -i setup.py -e "s/^version=.*/version='$version'/"
git commit -a -m "releasing $version"
git tag -u "$key" "$version" -m "releasing $version"
git push
python3 setup.py sdist upload --sign --identity="$key"
