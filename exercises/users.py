#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.cElementTree as ET
import pprint
import re
"""
Your task is to explore the data a bit more.
The first task is a fun one - find out how many unique users
have contributed to the map in this particular area!

The function process_map should return a set of unique user IDs ("uid")
"""

#return uid of user
def get_user(element):
    return element.attrib.get('uid')


def process_map(filename):
    users = set()
    for _, element in ET.iterparse(filename):
        #iterate tag key attributes to find "uid" attributes
        for key in element.attrib.keys():
            if key=="uid":
            #if uid already in user set then skip
                if get_user(element) in users:
                    pass
         #else add user uid to user set
                else:
                    users.add(get_user(element))
    return users


def test():

    users = process_map('map.osm')
    pprint.pprint(users)
    assert len(users) == 6



if __name__ == "__main__":
    test()