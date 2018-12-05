import xmltodict
import copy
import sys

def readFile(name):
    file = open(name,'r')
    readed = file.read()
    file.close()
    return readed

def to_dict(text):
    return xmltodict.parse(text)

# Recursively find key in dictionary
def finditem(obj, key):
    if key in obj: return obj[key]
    for k, v in obj.items():
        if isinstance(v,dict):
            item = finditem(v, key)
            if item is not None:
                return item

gCount = 0
# Iterate through each level, create an array and pass back up
def forEach(obj, group):
    if isinstance(obj,str):
        return []
    global gCount
    gCount += 1
    # Get initial information, also check that each of the keys exist or there are issues
    entry = {}
    entry['group'] = group
    entry['@level'] = obj['@level']
    if 'unitid' in obj['did'].keys():
        entry['unitid'] = obj['did']['unitid']
    else:
        entry['unitid'] = -1
    if 'unittitle' in obj['did'].keys() and '#text' in obj['did']['unittitle'].keys():
        entry['unittitle'] = obj['did']['unittitle']['#text']
    else:
        entry['unittitle'] = ""

    # Clean up newlines in the middle of the title
    entry['unittitle'] = entry['unittitle'].replace('\n','')
    while (entry['unittitle'].count('  ') != 0):
        entry['unittitle'] = entry['unittitle'].replace('  ',' ')

    # Finish creating entry if we are not a series
    if (obj['@level'] != 'series'):
        # Check that we have the container key
        if 'container' in obj['did'].keys():
            # Check that we only have 2
            if type(obj['did']['container']) is list:
                # Get box and folder number out, assuming it exists
                temp = obj['did']['container']
                for i in temp:
                    if '#text' in i.keys():
                        entry[i['@type'].lower()] = i['#text']
            # Otherwise, we only have one so use that
            else:
                entry[obj['did']['container']['@type']] = obj['did']['container']['#text']
        # Get item count if we have scopecontent
        #if 'scopecontent' in obj.keys() and isinstance(obj['scopecontent']['p'],str):
        if 'scopecontent' in obj.keys():
            #print("Adding items!")
            entry['itemCount'] = obj['scopecontent']['p']
            # Digital Commons things
            #print(entry['itemCount'])
            if entry['itemCount'] is not None and not isinstance(entry['itemCount'],str):
                #print(entry['unitid'])
                entry['digitalCommons'] = copy.deepcopy(entry['itemCount'])
                if '#text' in entry['digitalCommons'].keys():
                    # Put things in correct indices
                    del entry['digitalCommons']['#text']
                    entry['itemCount'] = entry['itemCount']['#text'].split("(")[0]
                    # Get all links for digital commons into an array
                    links = []
                    # Check if we have an array or a dictionary
                    if isinstance(entry['digitalCommons']['extref'], list):
                        for l in entry['digitalCommons']['extref']:
                            #print(l)
                            links.append( l['@xlink:href'] )
                    else:
                        links.append( entry['digitalCommons']['extref']['@xlink:href'] )
                    entry['digitalCommons'] = links
                else:
                    entry['itemCount'] = ""
            # Get rid of extra information from text
            if isinstance(entry['itemCount'],str):
                entry['itemCount'] = ''.join([i for i in entry['itemCount'] if i.isdigit()])

    # Recurse to get all children
    entries = []
    if entry['unitid'] == "1.1.2.13.4.":
        print(obj.keys())
    for k,v in obj.items():
        if 'c0' in k:
            if isinstance(v,dict):
                for e in forEach(v,group):
                    entries.append(e)
            elif isinstance(v,list):
                for i in v:
                    for e in forEach(i,group):
                        entries.append(e)
            """
            for i in v:
                if entry['unitid'] == "1.1.2.13.4.":
                    print(type(k), type(v))
                    print(k,type(i),i)
                    print(v[i])
                    if isinstance(v[i],dict):
                        print("Dictionary")
                if (type(i) is not list and type(i) is not str):
                    for e in forEach(i,group):
                        entries.append(e)
                if isinstance(v,dict) and isinstance(v[i],dict):
                    for e in forEach(v,group):
                        for q in entries:
                            if e['unitid'] == q['unitid']:
                                print("We already exist!")
                            else:
                                entries.append(e)
            """

    # Keep track of all entries
    # Check that what we're adding isn't already in the entries
    for e in entries:
        if e['unitid'] == entry['unitid']:
            print("We already exist!")
    entries.append(entry)
    return entries

# Create TSV file
def sendToFile(name, entries):
    out = ""
    keys = ['group','@level','box','folder','unitid','unittitle','itemCount','digitalCommons']
    # Create the header at the top
    for i in keys:
        out += i + "\t"
    out += "\n"
    # Add all entries to output
    #print(type(entries))
    #print(entries[0])
    for e in entries:
        #print(e)
        for i in keys:
            #print(type(i),type(e.keys()))
            #print(e.keys(),i)
            if i in e.keys():
                if isinstance(e[i],str):
                    out += e[i]
                elif e[i] is not None:
                    for j in e[i]:
                        out += j + '\t'
            out += '\t'
        out += '\n'

    file = open(name,'w')
    file.write(out)
    file.close()

def main():
    # Get all source files
    file = open("sources.txt",'r')
    sources = file.read().split()
    file.close()

    allEntries = []

    for i in sources:
        print(i)
        # Read file and convert to dictionary
        parsed = to_dict(readFile(i))
        
        # Get the tables out
        found = finditem(parsed, 'dsc')
        table = found['c01']

        ret = []
        if isinstance(table, list):
            for j in table:
                ret = forEach(j,i)
                for e in ret:
                    allEntries.append(e)
        else:
            ret = forEach(table,i)
            for e in ret:
                allEntries.append(e)

    print("Total found:",len(allEntries))
    print("Expected entries:",gCount)
    print()

    sendToFile("output.tsv",allEntries)

main()
