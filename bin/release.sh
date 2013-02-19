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
  "$@"
}

function next_version()
{
  if echo "$1" | grep -q "dev$"; then
    newversion="$(echo "$1" | sed -e "s/dev$//")"
  else
    last="$(echo "$1" | sed -e "s/.*\([0-9]\+\)$/\1/")"
    newversion="$(echo "$1" | sed -e "s/${last}$/$(($last + 1))/")"
  fi
  echo "$newversion"
}

set -e
cd $(dirname "$0")/..

if [ "$1" ]; then
  newversion="$1"
else
  oldversion="$(./setup.py --version)"
  [ "$oldversion" ] || ( echo "Could not find version=." ; exit 1 )
  newversion="$(next_version $oldversion)"
fi

echo_do sed -i setup.py -e "s/^version=.*/version='$newversion'/"
echo_do git commit -a -m "releasing $newversion"
echo_do git tag -u "$key" "$newversion" -m "releasing $newversion"
echo_do git push
echo_do python3 setup.py sdist upload --sign --identity="$key"
