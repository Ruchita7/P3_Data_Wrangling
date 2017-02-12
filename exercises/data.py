#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.cElementTree as ET
import pprint
import re
import codecs
import json
"""
Your task is to wrangle the data and transform the shape of the data
into the model we mentioned earlier. The output should be a list of dictionaries
that look like this:

{
"id": "2406124091",
"type: "node",
"visible":"true",
"created": {
          "version":"2",
          "changeset":"17206049",
          "timestamp":"2013-08-03T16:43:42Z",
          "user":"linuxUser16",
          "uid":"1219059"
        },
"pos": [41.9757030, -87.6921867],
"address": {
          "housenumber": "5157",
          "postcode": "60625",
          "street": "North Lincoln Ave"
        },
"amenity": "restaurant",
"cuisine": "mexican",
"name": "La Cabana De Don Luis",
"phone": "1 (773)-271-5176"
}

You have to complete the function 'shape_element'.
We have provided a function that will parse the map file, and call the function with the element
as an argument. You should return a dictionary, containing the shaped data for that element.
We have also provided a way to save the data in a file, so that you could use
mongoimport later on to import the shaped data into MongoDB. 

Note that in this exercise we do not use the 'update street name' procedures
you worked on in the previous exercise. If you are using this code in your final
project, you are strongly encouraged to use the code from previous exercise to 
update the street names before you save them to JSON. 

In particular the following things should be done:
- you should process only 2 types of top level tags: "node" and "way"
- all attributes of "node" and "way" should be turned into regular key/value pairs, except:
    - attributes in the CREATED array should be added under a key "created"
    - attributes for latitude and longitude should be added to a "pos" array,
      for use in geospacial indexing. Make sure the values inside "pos" array are floats
      and not strings. 
- if the second level tag "k" value contains problematic characters, it should be ignored
- if the second level tag "k" value starts with "addr:", it should be added to a dictionary "address"
- if the second level tag "k" value does not start with "addr:", but contains ":", you can
  process it in a way that you feel is best. For example, you might split it into a two-level
  dictionary like with "addr:", or otherwise convert the ":" to create a valid key.
- if there is a second ":" that separates the type/direction of a street,
  the tag should be ignored, for example:

<tag k="addr:housenumber" v="5158"/>
<tag k="addr:street" v="North Lincoln Avenue"/>
<tag k="addr:street:name" v="Lincoln"/>
<tag k="addr:street:prefix" v="North"/>
<tag k="addr:street:type" v="Avenue"/>
<tag k="amenity" v="pharmacy"/>

  should be turned into:

{...
"address": {
    "housenumber": 5158,
    "street": "North Lincoln Avenue"
}
"amenity": "pharmacy",
...
}

- for "way" specifically:

  <nd ref="305896090"/>
  <nd ref="1719825889"/>

should be turned into
"node_refs": ["305896090", "1719825889"]
"""

#regular expression for lower case characters
lower = re.compile(r'^([a-z]|_)*$')
#regular expression for lower case characters containing colon
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
#regular expression for problem characters
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

CREATED = [ "version", "changeset", "timestamp", "user", "uid"]


def shape_element(element):
    node = {}   #dictionary for tag
    node_refs = []  #list for node references
    created = {}    #dictionary for created
    addr = {}       #dictionary for address
    otherKeys = {}  #dictionary for other tags
    if element.tag == "node" or element.tag == "way":
        node["type"] = element.tag
        for key in element.attrib.keys():
            #check if attribute is among created attributes
            if key in CREATED:
                created[key] = element.attrib[key]
            #add latitude/longitude attributes to array "pos"
            elif (key in "lat" or key in "lon"):
                pos = []
                pos.append(float(element.attrib["lat"]))
                pos.append(float(element.attrib["lon"]))
                node["pos"] = pos
            else:
                #add other attributes as it is
                node[key] = element.attrib[key]
            #created dictionary
            node["created"] = created
        #iterate child tag elements
        for child in element:
            if child.tag == "nd":
                node_refs.append(child.attrib["ref"])
            elif is_valid(child):
                if child.attrib['k'].startswith("addr:"):
                    address = child.attrib['k'].split(":")
                    if len(address) == 2:
                        address_tag = address[1]
                        addr[address_tag] = child.attrib['v']


                else:
                    # node[child.attrib['k']]=child.attrib['v']
                    elementTag = child.attrib['k'].split(":")
                    #if attribute does not contain ':' put it as key/value pair
                    if len(elementTag) <= 1:
                        node[child.attrib['k']] = child.attrib['v']
                    #if attribute contains colon then process only second level tags
                    elif len(elementTag) == 2:
                        otherAttribute = elementTag[0]
                        #if tag name already not added to 'node' dictionary then add it as dictionary
                        if not node.has_key(otherAttribute):
                            otherKeys = {}
                        else:
                            obj = node.get(otherAttribute)
                            # determine object type if is string and already present, then set it as dictionary in 'otherKeys'
                            if (type(obj) is str):
                                otherKeys = {}
                                otherKeys[otherAttribute] = obj
                            del node[otherAttribute]
                        #add the new key/value pair to 'otherKeys' dictionary and and add to node
                        otherKeys[elementTag[1]] = child.attrib['v']
                        node[otherAttribute] = otherKeys
        #check if node_refs,addr have length then add to node dictionary
        if (len(node_refs) > 0):
            node["node_refs"] = node_refs
        if (len(addr) > 0):
            node["address"] = addr
        return node
    else:
        return None

#check if key is valid or not
def is_valid(element):
    l=lower.search(element.attrib['k'])
    lc=lower_colon.search(element.attrib['k'])
    pc=problemchars.search(element.attrib['k'])
    if pc:
        return False
    else:
        return True
    

def process_map(file_in, pretty = False):
    # You do not need to change this file
    file_out = "{0}.json".format(file_in)
    data = []
    with codecs.open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in):
            el = shape_element(element)
            if el:
                data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:
                    fo.write(json.dumps(el) + "\n")
    return data

def test():
    # NOTE: if you are running this code on your computer, with a larger dataset, 
    # call the process_map procedure with pretty=False. The pretty=True option adds 
    # additional spaces to the output, making it significantly larger.
    data = process_map('example.osm', True)
    pprint.pprint(data)
    
    correct_first_elem = {
        "id": "261114295", 
        "visible": "true", 
        "type": "node", 
        "pos": [41.9730791, -87.6866303], 
        "created": {
            "changeset": "11129782", 
            "user": "bbmiller", 
            "version": "7", 
            "uid": "451048", 
            "timestamp": "2012-03-28T18:31:23Z"
        }
    }
    assert data[0] == correct_first_elem
    assert data[-1]["address"] == {
                                    "street": "West Lexington St.", 
                                    "housenumber": "1412"
                                      }
    assert data[-1]["node_refs"] == [ "2199822281", "2199822390",  "2199822392", "2199822369", 
                                    "2199822370", "2199822284", "2199822281"]

if __name__ == "__main__":
    test()