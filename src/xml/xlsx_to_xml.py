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
        print(listed)
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
                #TODO Fix this logic. Trying to pad numbers without affecting the letters
                # Get numbers out of string
                n = ''.join(filter(lambda x: x.isdigit(), i))
                # Difference in length
                l_diff = len(i)-len(n)
                if len(n) != 0:
                    n = format(int(n),'04d')[l_diff:]
                else:
                    n = format(0,'04d')[l_diff-1:]
                print(i,n)
                out += i[:-l_diff] + n
            else:
                out += i
            out += "."
    return out

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
    # Sort rows based on 'Comparison' value
    rows.sort(key=operator.itemgetter('Comparison'))
    for i in rows:
        if 'B' in i['Comparison']:
            print(i['Comparison'])
        createEntry(i)

def main():
    dfs = readFile("EAD_Helper.xlsx")
    print(dfs.keys())
    print(type(dfs['Existing']))
    entries = createExistingDictionary(dfs['Existing'])
    return
    for index, row in dfs['Existing'].iterrows():
        pass

main()
