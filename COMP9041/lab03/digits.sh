#!/bin/bash

#sed -e 's/a/A/' -e 's/b/B/' <old >new

sed -e 's/[0-4]/\</g' -e 's/[6-9]/\>/g'
