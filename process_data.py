import xml.etree.ElementTree as ET
from collections import defaultdict
import re
import pprint
import codecs
import json

#regular expression for lower case characters
lower = re.compile(r'^([a-z]|_)*$')
#regular expression for lower case characters containing colon
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
#regular expression for problem characters
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

#list for created values
CREATED = [ "version", "changeset", "timestamp", "user", "uid"]

#regular expression for street type
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

postcode_re = re.compile(r"^[0-9]{5}$", re.IGNORECASE)

#list for expected street types
expected = ["Avenue","Boulevard","Common","Concourse","Circle","Crescent","Court","Center",
            "Drive","East","Heights","Interstate","Lane","Place","North","North West","Parkway",
            "Plaza","Road","Ridge", "Square","Street", "South","South East", "Trail","West"]

#dictionary for invalid street type mappings
mapping = {
            "Ave": "Avenue","Ave.": "Avenue","ave": "Avenue",
            "Blvd": "Boulevard","Blvd.": "Boulevard",
            "Com": "Common","Com.": "Common",
            "Concrs": "Concourse","Concrs.": "Concourse",
            "Cir": "Circle","Cir.": "Circle",
            "Cres": "Crescent","Cres.": "Crescent",
            "Ct.": "Court","Ct": "Court",
            "Ctr": "Center","Ctr.": "Center",    
            "Dr": "Drive","Dr.": "Drive",
            "E": "East",
            "Hts": "Heights","Hts.": "Heights",
            "I" : "Interstate",
            "Ln": "Lane","Ln.": "Lane",
            "Pl": "Place","Pl.": "Place",
            "Plz": "Plaza","Plz.": "Plaza",
            "N":"North",
            "NW":"North West",
            "Pkwy": "Parkway","Pkwy.": "Parkway",
            "Rd": "Road","Rd.": "Road",
             "Rdg": "Ridge","Rdg.": "Ridge",
            "S":"South",
            "SE": "South East",
            "Sq": "Square","Sq.": "Square",
            "St": "Street","St.": "Street","st": "Street", 
            "Trl" : "Trail","Trl." : "Trail",
            "W":"West"
            }

def is_ascii(str):
    return all(ord(chars) < 128 for chars in str)

#match post code
def match_postcode(zip):
    m = postcode_re.match(zip)
    if m:
        return True
    return False
        
#update street/city names if match found
def update_name(name, mapping):
    #find street names if matching street_type
    address_name = name.split();
    for st in address_name :
        m = street_type_re.search(st)
        if m:
            street_type = m.group()
        #check if street_type is key in mapping, if so substitute mapping
            if street_type in mapping.keys():
                name = re.sub(street_type, mapping[street_type],name)
    return name

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
            #if attribute tag is "nd"
            if child.tag == "nd":
                node_refs.append(child.attrib["ref"])
            #determine if attribute key/value is valid
            elif is_valid(child):
                #handle street values and update if needed
                elementTag = child.attrib['k'].split(":")
                #update mapping for street or city
                if child.attrib['k']=="addr:street" or child.attrib['k']=="addr:city":
                        addr[elementTag[1]]=update_name(child.attrib['v'],mapping)
                    
                #process other address tags of level two
                elif child.attrib['k'].startswith("addr:"):
                    if len(elementTag) == 2:
                        if elementTag[1]=="postcode":
                            if match_postcode(child.attrib['v'])==False:
                                pass
                        address_tag = elementTag[1]
                        addr[address_tag] = child.attrib['v']
                #process other tag attributes
                else:                 
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
    #if problem characters found return false
    if pc or is_ascii(element.attrib['v'])==False:
        return False
    else:
        return True

#process osm file
def process_data(file_in, pretty=False):
    # You do not need to change this file
    file_out = "{0}.json".format(file_in)
    data = []
    with codecs.open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in):
            el = shape_element(element)
            if el:
                data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2) + "\n")
                else:
                    fo.write(json.dumps(el) + "\n")
    return data


def test():
    data = process_data('new_york_sample.osm', False)
    #pprint.pprint(data)

if __name__ == "__main__":
    test()