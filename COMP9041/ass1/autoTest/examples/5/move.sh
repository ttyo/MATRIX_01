#!/bin/bash
mv 1 111
if test -r 111
then
    echo 'exit 111'
else
    echo 'not exit 111'
fi
