"""
This code is for processing and clean the Open Street Map data set for New York City to be
 converted to json for storing into Mongo Db database.
"""

import xml.etree.ElementTree as ET
import re
import pprint
import codecs
import json

# regular expression for lower case characters
lower = re.compile(r'^([a-z]|_)*$')
# regular expression for lower case characters containing colon
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
# regular expression for problem characters
problem_chars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

# list for created values
CREATED = ["version", "changeset", "timestamp", "user", "uid"]

# regular expression for street type
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

postcode_re = re.compile(r"^\d{5}$", re.IGNORECASE)

# list for expected street types
expected = ["Avenue", "Boulevard", "Common", "Concourse", "Circle", "Crescent", "Court", "Center",
            "Drive", "East", "Heights", "Interstate", "Lane", "Place", "North", "North West", "Parkway",
            "Plaza", "Road", "Ridge", "Square", "Street", "South", "South East", "Trail", "West"]

# dictionary for invalid street type mappings
mapping = {
    "Ave": "Avenue", "Ave.": "Avenue", "ave": "Avenue",
    "Blvd": "Boulevard", "Blvd.": "Boulevard",
    "Com": "Common", "Com.": "Common",
    "Concrs": "Concourse", "Concrs.": "Concourse",
    "Cir": "Circle", "Cir.": "Circle",
    "Cres": "Crescent", "Cres.": "Crescent",
    "Ct.": "Court", "Ct": "Court",
    "Ctr": "Center", "Ctr.": "Center",
    "Dr": "Drive", "Dr.": "Drive",
    "E": "East",
    "Hts": "Heights", "Hts.": "Heights",
    "I": "Interstate",
    "Ln": "Lane", "Ln.": "Lane",
    "Pl": "Place", "Pl.": "Place",
    "Plz": "Plaza", "Plz.": "Plaza",
    "N": "North",
    "NW": "North West",
    "Pkwy": "Parkway", "Pkwy.": "Parkway",
    "Rd": "Road", "Rd.": "Road",
    "Rdg": "Ridge", "Rdg.": "Ridge",
    "S": "South",
    "SE": "South East",
    "Sq": "Square", "Sq.": "Square",
    "St": "Street", "St.": "Street", "st": "Street",
    "Trl": "Trail", "Trl.": "Trail",
    "W": "West"
}


def is_ascii(values):
    """
    Function to check if ascii characters are present in string

    Args:
        values(str) : first parameter, the string to be checked

    Returns:
         bool: The return value. True for success, False otherwise.
    """
    return all(ord(chars) < 128 for chars in values)


def update_postcode(zip_code):
    """
       Function to clean/retrieve correct postal code

       Args:
           zip_code(str) : first parameter, the zip code to be checked

       Returns:
            bool: The return value. True for success, False otherwise.
       """
    m = postcode_re.match(zip_code)
    if m:
        return zip_code
    else:
        clean_postcode = re.findall(r'^(\d{5})-\d{4}$', zip_code)
        if clean_postcode:
            return clean_postcode[0]
    return False


def update_name(name, value_mapping):
    """
           Function to update street/city names if match found

           Args:
               name(str) : first parameter, the street/city name abbreviation to be updated
               value_mapping(str) : second parameter, the full name of the street/city name abbreviation

           Returns:
                str: The return value, the updated street/city name
           """
    # find street names if matching street_type
    address_name = name.split()
    for st in address_name:
        m = street_type_re.search(st)
        if m:
            street_type = m.group()
            # check if street_type is key in mapping, if so substitute mapping
            if street_type in value_mapping.keys():
                name = re.sub(street_type, value_mapping[street_type], name)
    return name


def find_positions(element):
    """
        This function returns an array of latitude and longitude corresponding to the lat/lon attributes of the element

        Args:
            element(element) : first parameter, the element iterated

        Returns:
                array: The return value, the lat/lon attributes of the element

    """
    lst = {float(element.attrib["lat"]), float(element.attrib["lon"])}
    pos = list(lst)
    return pos


def retrieve_address(child, element_tag):
    """
        This function cleans the address tag of the dataset

        Args:
            child: tag of element
            element_tag: key of child element
        Returns:
            str: the corresponding/updated value

    """
    if len(element_tag) == 2:
        if child.attrib['k'] == "addr:street" or child.attrib['k'] == "addr:city":
            return update_name(child.attrib['v'], mapping)
        elif element_tag[1] == "postcode":
            postcode=update_postcode(child.attrib['v'])
            if postcode is False:
                return ""
            else:
                return postcode
        # process other address tags of level two
        else:
                return child.attrib['v']


def shape_element(element):
    """
        This function processes and cleans the values of the data set

        Args:
            element(element) : first parameter, the element iterated

        Returns:
            node(dict) : dictionary of the key/value pair of the cleaned dataset

    """

    node = {}  # dictionary for tag
    node_refs = []  # list for node references
    created = {}  # dictionary for created
    address_dict = {}  # dictionary for address
    other_keys = {}  # dictionary for other tags
    if element.tag == "node" or element.tag == "way":
        node["type"] = element.tag
        for key in element.attrib.keys():
            value = element.attrib[key]
            # check if attribute is among created attributes
            if key in CREATED:
                created[key] = value
            # add latitude/longitude attributes to array "pos"
            elif key in "lat" or key in "lon":
                node["pos"] = find_positions(element)
            else:
                # add other attributes as it is
                node[key] = value
            # created dictionary
            node["created"] = created
        # iterate child tag elements
        for child in element:
            # if attribute tag is "nd"
            if child.tag == "nd":
                node_refs.append(child.attrib["ref"])
            # determine if attribute key/value is valid
            elif is_valid(child):
                # handle street values and update if needed
                element_tag = child.attrib['k'].split(":")
                if child.attrib['k'].startswith("addr:"):
                    updated_value=retrieve_address(child, element_tag)
                    if updated_value:
                        address_dict[element_tag[1]] = updated_value
                # process other tag attributes
                else:
                    # if attribute does not contain ':' put it as key/value pair
                    if len(element_tag) <= 1:
                        node[child.attrib['k']] = child.attrib['v']
                    # if attribute contains colon then process only second level tags
                    elif len(element_tag) == 2:
                        other_attribute = element_tag[0]
                        # if tag name already not added to 'node' dictionary then add it as dictionary
                        if not node.has_key(other_attribute):
                            other_keys = {}
                        else:
                            obj = node.get(other_attribute)
                            # determine object type if is string and already present, then set it as dictionary in 'other_keys'
                            if type(obj) is str:
                                other_keys = {}
                                other_keys[other_attribute] = obj
                            del node[other_attribute]
                        # add the new key/value pair to 'other_keys' dictionary and and add to node
                            other_keys[element_tag[1]] = child.attrib['v']
                        node[other_attribute] = other_keys
        # check if node_refs,address_dict have length then add to node dictionary
        if len(node_refs) > 0:
            node["node_refs"] = node_refs
        if len(address_dict) > 0:
            node["address"] = address_dict
        return node
    else:
        return None


def is_valid(element):
    """
        This function checks if keys of the tag are valid or not

        Args:
            element(element) : The first parameter, the element iterated

        Returns:
            bool: The return value. True for success, False otherwise.

    """
    l = lower.search(element.attrib['k'])
    lc = lower_colon.search(element.attrib['k'])
    pc = problem_chars.search(element.attrib['k'])
    # if problem characters found return false
    if pc or not is_ascii(element.attrib['v']):
        return False
    else:
        return True


def process_data(file_in, pretty=False):
    """
        This function processes the osm input file to be converted to json

        Args:
            file_in(str) : the first argument, the name of file to be processed
            pretty(boolean) : the second argument, with value = False to indent the resulting json

        Returns :
            data(array) : the resulting json

    """
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
    data = process_data('new_york_sample_small.osm', False)
    # pprint.pprint(data)


if __name__ == "__main__":
    test()