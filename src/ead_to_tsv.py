# This file parses through all of the URLs given in `./sources.txt`, downloads them, and creates a TSV file with all of the information for easier parsing
import re
import urllib.request

# Parent class
class entry:
    def __init__(self, groupNum=-1, boxes=[-1,-1], folders=[-1,-1], identifier="", item_title=""):
        self.group = groupNum
        self.box = boxes
        self.folder = folders
        self.id = identifier
        self.title = item_title
    # Modifier methods
    def set_group(self, groupNumber):
        self.group = groupNumber
    def set_box(self, start,end=None):
        self.box[0] = start
        if (end == None):
            self.box[1] = start
        else:
            self.box[1] = end
    def set_folder(self, start,end=None):
        self.folder[0] = start
        if (end == None):
            self.folder[1] = start
        else:
            self.folder[1] = end
    def set_ead_number(self, ead_number):
        self.id = ead_number
    def set_title(self, item_title):
        self.title = item_title
    # Accessors
    def get_group(self):
        return self.group
    def get_box(self):
        if (self.box[0] == self.box[1]):
            return self.box[0]
        return str(self.box[0])+' and '+str(self.box[1])
    def get_folder(self):
        if (self.folder[0] == self.folder[1]):
            return self.folder[0]
        return str(self.folder[0])+' and '+str(self.folder[1])
    def get_id(self):
        return self.id
    def get_title(self):
        return self.title

    def output_to_file(self, delimeter="\t"):
        out  = str(self.get_box())     +delimeter
        out += str(self.get_folder())  +delimeter
        out += str(self.get_title())   +delimeter
        out += str(self.get_id())
        return out
    def __str__(self):
        out  = str(self.get_group())   +'\t'
        out += str(self.get_box())     +'\t'
        out += str(self.get_folder())  +'\t'
        out += str(self.get_id())      +'\t'
        out += str(self.get_title())
        return out

# Class to keep track of all of our entries.
# Contains functions to be stripped from the HTML, put into TSV, and converted to XML
class item(entry):
    def __init__(self, groupNum=-1, boxes=[-1,-1], folders=[-1,-1], identifier="", item_title="", item_count=-1):
        entry.__init__(self, groupNum, boxes, folders, identifier, item_title)
        self.count = item_count
    # Modifier methods
    def set_count(self, item_count):
        self.count = item_count
    # Accessor methods
    def get_count(self):
        #return '.'+str(self.count)+' (items)'
        return str(self.count)

    def output_to_file(self, delimeter):
        out  = str(super().get_group()) + delimeter
        out += 'item' + delimeter
        out += super().output_to_file(delimeter)
        out += delimeter
        out += self.get_count()
        return out
    def __str__(self):
        return super().__str__()+'\t'+self.get_count()

# Class to keep track of all of the categories
class category(entry):
    def __init__(self, groupNum=-1, boxes=[-1,-1], folders=[-1,-1], identifier="", item_title=""):
        entry.__init__(self, groupNum, boxes, folders, identifier, item_title)
        self.children = []
    # Modifier methods
    def add_child(self, child):
        self.children.append(child)
    def pop_child(self, index=0):
        self.children.pop(index)
    def sort_children(self):
        # TODO Implement sorting of the array for easier conversion later
        pass
    # Accessor methods
    def get_child(self, index=0):
        return self.children[index]
    def get_child_count(self):
        return len(self.children)

    # Output functions
    def output_to_file(self, delimeter):
        out  = str(super().get_group()) + delimeter
        out += 'file' + delimeter
        out += super().output_to_file(delimeter)
        return out
    def __str__(self):
        return super().__str__()



###########################################
#  Parse webpage to create tree of items  #
###########################################
# Group: the group number
# Text:  Text of the webpage
# nodeStart: index of where to start searching for the next node
#
# @return [textOfNode, nextNodeStart]
def find_node_text(group, text, searchStart):
    # Takes in the text from the webpage and get the node out

    # Find token for beginning of row
    nodeStart = text.find("<tr>",searchStart)
    # Find token for end of row
    endOfNode = text.find("</tr>",nodeStart)+5
    # Get the text within the row
    textOfNode = text[nodeStart:endOfNode]
    return [textOfNode, endOfNode]
# Check that we have a valid node that can be generated
def is_valid_node(text):
    # Check for content
    if (len(text) == 0):
        return False
    # Check that we are not dealing with a header in the guide
    if (text.find("Container(s)") != -1):
        return False
    # Check that we aren't dealing with the Box/Folder lines
    if (text.find('<td><span class="containerLabel">Box</span></td>') != -1):
        return False
    # Check that not at the end of the table
    if (text.find("tbody>") != -1):
        return False
    return True

# Remove extra spaces between words
def clear_spaces(text):
    while (text.find("  ") != -1):
        text = text.replace("  "," ")
    return text

# Create the node from the text given
def create_node(group, text):
    if (not is_valid_node(text)):
        return -1
    node = 0
    # Strip newlines from text, replace with spaces. Search through string to find tags, then get values from tags
    # If the desired tag cannot be found, then skip it and set it to default value
    text = text.replace('\n'," ")
    text = text.replace('\r'," ")
    # Remove duplicate spaces
    clear_spaces(text)

    # Strip the tags around the entry for the box number
    box_begin = text.find("<td>")+4
    box_end   = text.find("</td>")
    boxes = [-1,-1]
    if (box_begin > 3):
        boxes = text[box_begin:box_end].split()
        if len(boxes) == 1:
            boxes.append(boxes[0])
        elif len(boxes)==3 and boxes[2].isdigit():
            boxes[1]=boxes[2]
            boxes = boxes[:1]
        elif len(boxes) == 0:
            boxes = [-1, -1]

    # Strip the tags around the entry for the folder number
    folder_begin = text.find("<td>",box_begin)+4
    folder_end   = text.find("</td>",folder_begin)
    folders = [-1,-1]
    if (folder_begin > 3):
        folders = text[folder_begin:folder_end].split()
        if len(folders) == 1:
            folders.append(folders[0])
        elif len(folders)==3 and folders[2].isdigit():
            folders.pop(1)
        elif len(folders) == 0:
            folders = [-1, -1]

    # Split the entry into the identifier and the title
    identifier_begin = text.find("<div class")+17
    identifier_end   = text.find("</",identifier_begin)
    identifier = text[identifier_begin:identifier_end].split(":")[0].replace(" ","")
    # Check we actually have an identifier and not just a placeholder
    if (len(identifier) != 0):
        # Strip out bold tag if it's a major category TODO Store that it was bolded?
        if (identifier.find("<") != -1):
            identifier = identifier[identifier.find(">")+1:]
        # Strip tailing period from identifier if exists
        if (identifier[-1]=="."):
            identifier = identifier[:-1]
        # Get the title from the text, ignoring everything after "<" because of additional tags
    title = text[identifier_begin:identifier_end].split(":")[-1].strip().split("<")[0]

    # Get the items out of the string
    items_begin = text.find("scopecontent")+15
    items_end   = text.find(" ",items_begin)
    # Check that this is an item and not a category
    if (items_begin > 15):
        items = re.findall(r'\d+',text[items_begin:items_end])
        item_count = 0
        # Check that there's actually an item. Handles if the item count was entered intcorrectly
        if (len(items) != 0):
            item_count = items[-1]
        node = item(group, boxes, folders, identifier, title, item_count)
    else:
        node = category(group, boxes, folders, identifier, title)

    # Return the node
    return node

# DEBUG
def debug():
    source_1 = """<tr>
    <td>1</td>
    <td>8</td>
    <td class="c0x_content" id="id2_c03_3_c04_7">
    <div class="c04">1.1.2.6 : Rice Pudding with Secret
                               Almond<div class="scopecontent">.2 (item)</div>
    </div>
    </td>
    </tr>"""
    source_2 = """<tr>
    <td>1</td>
    <td>6</td>
    <td class="c0x_content" id="id1_c02_9_c03_3">
    <div class="c03">1.8.2 : Dinner for "Midsummers"<div class="scopecontent">.1 (items)</div>
    </div>
    </td>
    </tr>"""
    source_3 = """<tr>
    <td>2</td>
    <td>4</td>
    <td class="c0x_content" id="id13_c03_34_c04_3">
    <div class="c04">1.12.0.2: Skiing<div class="scopecontent">.1(items)</div>
    </div>
    </td>
    </tr>"""
    source_4 = """<tr>
    <td colspan="2"></td>
    <td class="c0x_content" id="id14_c03_14_c04_13">
    <div class="c04">1.13.13.12: Visit Other Family Members<div class="scopecontent">.1(item)</div>
    </div>
    </td>
    </tr>"""
    source_5 = """<tr>
    <td>5</td>
    <td>1</td>
    <td class="c0x_content" id="id1_c02_14_c03_18">
    <div class="c03">1.13.0. : Miscellaneous </div>
    </td>
    </tr>"""
    source_6 = """<tr>
    <td>8</td>
    <td>4</td>
    <td class="c0x_content" id="id10_c03_5_c04_7">
    <div class="c04">2.9.4.6: "Uitzet" Dress<div class="scopecontent">.1(Items)</div>
    </div>
    </td>
    </tr>
    """
    print(create_node(3,source_1))
    print(create_node(3,source_2))
    print(create_node(3,source_3))
    print(create_node(3,source_4))
    print(create_node(3,source_5))
    print(create_node(1,source_6))

def page_parse(group=1, readed=""):
    nodes = []

    table_index = readed.find("<h4 id=")
    while (table_index > 0):
        identifier_begin = readed.find(">",table_index)+1
        identifier_end   = readed.find(":",identifier_begin)
        identifier = readed[identifier_begin:identifier_end].strip()
        if (identifier.find(".") != 0):
            identifier = identifier.split(".")[0]

        title_end = readed.find("<",identifier_end)
        #title = readed[identifier_end+8:title_end] # This is for if using downloaded files
        title = readed[identifier_end+1:title_end].strip()
        title = clear_spaces(title)
        node = category(group, identifier=identifier, item_title=title)
        nodes.append(node)

        table_index = readed.find("<h4 id=",identifier_end)

    # Get every item out of the webpage, create the node, and insert into correct value
    start_point = 1
    lastStart = 0
    # Loop until we wrap around to the beginning of the file
    while (lastStart < start_point):
        # Get the text for the next node from the webpage
        found_node_output = find_node_text(group, readed, start_point)
        # Create the node!
        node = create_node(group,found_node_output[0])
        nodes.append(node)

        # Figure out where to search next
        lastStart = start_point
        start_point = found_node_output[1]

    # Clean up nodes
    while (nodes.count(-1) != 0):
        nodes.remove(-1)
    return nodes

def create_tsv(filename="output.tsv", nodes=[]):
    file = open(filename, 'w')
    for i in nodes:
        file.write(i.output_to_file("\t"))
        file.write("\n")
    file.close()

def get_webpage(url):
    #mystr = urllib.request.urlopen(url).read().decode("utf8")
    #fp = urllib.request.urlopen(url)
    #charset = fp.headers.get_param('charset')
    #mystr = fp.read().decode(charset)
    fp = urllib.request.urlopen(url)
    mybytes = fp.read()
    mystr = mybytes.decode("utf8")
    fp.close()
    #print(mystr)
    return mystr

def test_webpage():
    webpage = get_webpage("http://archiveswest.orbiscascade.org/ark:/80444/xv36322")
    file = open("download.html",'w')
    file.write(webpage)
    file.close()

def load_sources(name="sources.txt"):
    file = open(name,'r')
    readed = file.read().split()
    file.close()
    return readed

def load_from_file(name):
    file = open(name,'r')
    readed = file.read()
    file.close()
    return readed

def main():
    #sources = load_sources("local_sources.txt")
    sources = load_sources()

    allNodes = []
    for i in range(len(sources)):
        print(sources[i])

        print(" Downloading EAD guides from the internet...",end='')
        html_text = get_webpage(sources[i])
        print("not implemented")
        """
        print(" Loading file...",end='')
        html_text = load_from_file(sources[i])
        print("done")
        """

        print(" Converting to TSV...",end='')
        nodes = page_parse(i+1,html_text)
        for n in nodes:
            allNodes.append(n)
        print("done")

    print(" Writing to file...",end='')
    create_tsv("output.tsv", allNodes)
    print("done")

#debug()
#page_parse()
#test_webpage()
main()
