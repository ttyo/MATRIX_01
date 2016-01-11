#!/bin/bash
if test -r /dev/null && test a = a || [ -r nonexistantfile ]
then
    echo a
else 
	echo b
fi