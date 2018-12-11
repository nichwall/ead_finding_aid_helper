import pandas as pd
from collections import OrderedDict
import math
import operator
import re

# Order that things should be put into the XML from column identifiers
#columnOrder = ['box','folder','unitid','unittitle','itemCount','digitalCommons']
did_tags = ['box','folder','unitid','unittitle']
scopecontent_tags = ['itemCount']

# Read the excel file and return a panda object
def readFile(name):
    dfs = pd.read_excel(name, sheet_name=None)
    return dfs

# Recursively find key in dictionary
def finditem(obj, key):
    if key in obj: return obj[key]
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v,dict):
                item = finditem(v, key)
                if item is not None:
                    return item
            elif isinstance(v,list):
                item = finditem(v, key)
                if item is not None:
                    return item
    elif isinstance(obj, list):
        for v in obj:
            if isinstance(v,dict):
                item = finditem(v, key)
                if item is not None:
                    return item

# Get key from dictionary/list mess
"""
def gen_dict_extract(key, var):
    if hasattr(var,'iteritems'):
        for k, v in var.iteritems():
            if k == key:
                yield v
            if isinstance(v, dict):
                for result in gen_dict_extract(key, v):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    for result in gen_dict_extract(key, d):
                        yield result
"""
def gen_dict_extract(key, var):
    if isinstance(var, dict):
        for k, v in var.items():
            if k == key:
                yield v
            if isinstance(v, (dict, list)):
                yield from gen_dict_extract(key, v)
    elif isinstance(var, list):
        for d in var:
            yield from gen_dict_extract(key, d)
def fun(key, d):
    if key in d:
        yield d[key]
    for k in d:
        if isinstance(d[k], list):
            for i in d[k]:
                for j in fun(key, i):
                    yield j
def findObject(key, val, obj):
    if isinstance(obj, dict):
        if key in obj and obj[key] == val:
            return obj
    pass

# Accepts row from DataFrame, and creates entry
def createEntry(row):
    entry = OrderedDict()
    # Create <did> tag
    didTag = OrderedDict()
    # Add all things from the row into our @didTag, in the same order for the XML
    for columns in did_tags:
        if columns in row:
            didTag[columns] = row[columns]
    # Clean up @didTag, getting rid of nan entries
    entry['did'] = OrderedDict()
    for index in didTag:
        if not isinstance(didTag[index],float) or not math.isnan(didTag[index]):
            entry['did'][index] = didTag[index]

    # Create <scopecontent> tag
    scopecontentTag = OrderedDict()
    for columns in scopecontent_tags:
        if columns in row and isinstance(row[columns], float) and not math.isnan(row[columns]):
            scopecontentTag['p'] = "."+str(int(row[columns]))+" (Items)"
    # If we have any digital commons, make sure to check for more entries
    if not isinstance(row['digitalCommons'],float):
        listed = []
        listed.append(row['digitalCommons'])
        #listed.append(entry['did']['digitalCommons'])
        for i in row.keys():
            if "Unnamed" in i and isinstance(row[i],str):
                listed.append(row[i])
        # Convert digitalCommons entries to a string, because the nesting would be a nightmare
        digitalCommonsStr = "Digital Items: "
        for i in range(len(listed)):
            digitalCommonsStr += r'<extref xlink:type="simple" xlink:role="text/html" xlink:show="new" xlink:actuate="onRequest" xlink:href="'
            digitalCommonsStr += listed[i]
            digitalCommonsStr += r'">'
            digitalCommonsStr += str(i)
            digitalCommonsStr += r'</extref>'
            if (i < len(listed)-1):
                digitalCommonsStr += ", \n"
        # Check for prexisting items in @scopecontentTag
        if 'p' in scopecontentTag:
            scopecontentTag['p'] += "; "
            scopecontentTag['p'] += digitalCommonsStr
        else:
            scopecontentTag['p']  = digitalCommonsStr
    # Add scope content to entry
    if (len(scopecontentTag.keys()) != 0):
        entry['scopecontent'] = scopecontentTag

    # Create C tag for children if we don't have scopeContent
    if 'p' not in scopecontentTag and not (isinstance(row['unitid'],float) and math.isnan(row['unitid'])):
        # The level is equal to the number of periods
        level = row['unitid'].count('.')
        clevelTag = OrderedDict()
        clevelTag['@level'] = ('','series','subseries','file','item','otherlevel','otherlevel','otherlevel','otherlevel','otherlevel','otherlevel')[level] # Set the level type
        # TODO Check if there's no nested categories. If there are none, change to 'otherlevel' if not already item.

        # If we are 'otherlevel', set @otherlevel to be the correct value
        if clevelTag['@level'] == 'otherlevel':
            clevelTag['@otherlevel'] = "level"+str(level)

        # Add cLevelTag to entry
        entry['c0'+str(level)] = clevelTag
    
    return entry

def padder(val):
    w = val.split(" ")
    out = w[0] + " " # Get group identifier
    if len(w) == 2:
        nums = w[1].split(".")[:-1]
        for i in nums:
            if i.isnumeric():
                if int(i) == 0:
                    # Replace occurances with ZZZZ so they end up on the end when sorted
                    out += "ZZZZ"
                else:
                    out += format(int(i),'04d')
            elif len(i) > 0:
                # Pad identifiers with letters
                # Get numbers out of string
                n = ''.join(filter(lambda x: x.isdigit(), i))
                # Get characters out of string
                c = ''.join(filter(lambda x: x.isalpha(), i))
                # Difference in length
                if len(n) != 0:
                    n = format(int(n),'04d')[:4-len(c)]
                else:
                    n = format(0,'04d')[:4-len(c)]
                out += c + n
            else:
                out += i
            out += "."
    return out

def last(text, pattern):
    return text.rfind(pattern, 0)
def secondToLast(text, pattern):
    return text.rfind(pattern, 0, text.rfind(pattern))
def thirdToLast(text, pattern):
    return text.rfind(pattern, 0, secondToLast(text,pattern))

# TODO Use smaller set to test this function
def insertIntoTable(entry, table):
    # Find parent in table
    parent = None
    print("Table: ",table)
    print("Entry: ",entry)
    print("Searching for 1 in table: ",list(gen_dict_extract('1', table)))
    print("Fun output, search for unitid: ",list(fun('unitid',table)))
    if 'unitid' in entry['did']:
        print("Unitid exists")
        # Change entry unitid
        parentName = entry['did']['unitid']
        #parentId = parentName[0:thirdToLast(parentName, ".")] + parentName[secondToLast(parentName, "."):]
        entry['did']['unitid'] = parentName[0:last(parentName, ".")-1]
        parentName = entry['did']['unitid']
        parentId = parentName[0:last(parentName, ".")]
        print("Our unitID: ", entry['did']['unitid'])
        
        #parent = list(gen_dict_extract(parentId, table))
        parent = list(gen_dict_extract(str(parentId), table))
        #print(entry['did'])
        print("Parent unitID: ", parentId)
        print(parent)
    # If we didn't find the parent, add it to c01
    if parent is None or len(parent) == 0:
        print("Parent is None")
        # Check if first level is empty
        if len(table['c01']) == 0:
            print("first level empty")
            table['c01'] = entry
        # If not, check if there's only one entry to convert to list
        elif isinstance(table['c01'], dict):
            print("Only one entry")
            temp = table['c01']
            table['c01'] = []
            table['c01'].append(temp)
            table['c01'].append(entry)
        # Otherwise, just add to it
        else:
            print ("More than one entry")
            table['c01'].append(entry)
    # We found the parent, so add it to child
    else:
        parent = list(parent)
        print(parent)
        clevel = 'c0'+str(level-1)
        # Check if the clevel exists
        if clevel in parent:
            if isinstance(parent[clevel], dict):
                temp = parent[clevel]
                parent[clevel] = []
                parent[clevel].append(temp)
                parent[clevel].append(entry)
            else:
                parent[clevel].append(entry)
        else:
            parent[clevel] = entry

    return table

# Accepts dataframe of the existing data
# Returns object for conversion to XML
def createExistingDictionary(df):
    # Covert the DataFrame to an array of rows for easier recursion
    rows = []
    for index, row in df.iterrows():
        rows.append(row)
    # Replace all numeric values to be zero padded to a length of 3
    for row in rows:
        row['Comparison'] = padder(row['Comparison'])
    # Create dictionary that will be the table for every XML
    masterTable = {}
    for i in rows:
        masterTable[i['Comparison'].split(" ")[0]] = OrderedDict()
    for table in masterTable:
        if 'c01' not in masterTable[table]:
            masterTable[table]['c01'] = []
    # Sort rows based on 'Comparison' value
    rows.sort(key=operator.itemgetter('Comparison'))
    # Create all entries from existing table and create array of them
    entries = []
    for i in rows:
        #entries.append(createEntry(i))
        # Loop through entries, attempting to insert them into the dictionary
        masterTable[i['Comparison'].split(" ")[0]] = insertIntoTable(createEntry(i), masterTable[i['Comparison'].split(" ")[0]])
        print("Master table index: ",i['Comparison'].split(" ")[0])
        print("Master table: ",masterTable)
        print()

def main():
    #dfs = readFile("EAD_Helper.xlsx")
    dfs = readFile("SmallSet.xlsx")
    print(dfs.keys())
    print(type(dfs['Existing']))
    entries = createExistingDictionary(dfs['Existing'])
    return
    for index, row in dfs['Existing'].iterrows():
        pass

main()
