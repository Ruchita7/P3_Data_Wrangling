#Find occurence of street names which need correction or otherwise in a dictionary
import xml.etree.cElementTree as ET
from collections import defaultdict
import re

osm_file = open("new-york_sample.osm", "r")

street_type_re = re.compile(r'\S+\.?$', re.IGNORECASE)
street_types = defaultdict(int)

#group street names by street_type_re
def audit_street_type(street_types, street_name):
    values = street_name.split();
    for v in values :
        m = street_type_re.search(v)
        if m:
            street_type = m.group()
            street_types[street_type] += 1

#print dictionary collection
def print_sorted_dict(d):
    keys = d.keys()
    keys = sorted(keys, key=lambda s: s.lower())
    for k in keys:
        v = d[k]
        print "%s: %d" % (k, v)

#find values for tags of type "addr:street"
def is_street_name(elem):
    return (elem.tag == "tag") and (elem.attrib['k'] == "addr:street")

#iterate the osm file
def audit():
    for event, elem in ET.iterparse(osm_file):
        if is_street_name(elem):
            audit_street_type(street_types, elem.attrib['v'])
    print_sorted_dict(street_types)

if __name__ == '__main__':
    audit()