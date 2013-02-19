#!/bin/bash
key='<leoboiko@namakajiri.net>'

if ! gpg --list-keys --with-colons | grep "^pub" | grep -q "$key:"
then
  echo "Could not find GPG key $key!"
  exit 1
fi

function echo_do()
{
  echo '***' "$@"
  $*
}

set -e
cd $(dirname "$0")/..
version="$(./setup.py --version | sed -e "s/dev$//")"
[ "$version" ] || ( echo "Could not find version=." ; exit 1 )

echo_do sed -i setup.py -e "s/^version=.*/version='$version'/"
echo_do git commit -a -m "releasing $version"
echo_do git tag -u "$key" "$version" -m "releasing $version"
echo_do git push
echo_do python3 setup.py sdist upload --sign --identity="$key"
