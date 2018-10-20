# This file parses through all of the URLs given in `./sources.txt`, downloads them, and creates a TSV file with all of the information for easier parsing
import re

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
        return str(self.box[0])+" and "+str(self.box[1])
    def get_folder(self):
        if (self.folder[0] == self.folder[1]):
            return self.folder[0]
        return str(self.folder[0])+" and "+str(self.folder[1])
    def get_id(self):
        return self.id
    def get_title(self):
        return self.title

    def __str__(self):
        out  = str(self.get_group())   +"\t"
        out += str(self.get_box())     +"\t"
        out += str(self.get_folder())  +"\t"
        out += str(self.get_id())      +"\t"
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
        return "."+str(self.count)+" (items)"

    def __str__(self):
        return super().__str__()+"\t"+self.get_count()

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

    def __str__(self):
        return super().__str__()



###########################################
#  Parse webpage to create tree of items  #
###########################################
def create_node(group, text):
    node = 0
    # Strip newlines from text, replace with spaces. Search through string to find tags, then get values from tags
    # If the desired tag cannot be found, then skip it and set it to default value
    text = text.replace("\n"," ")
    # Remove duplicate spaces
    while (text.find("  ") != -1):
        text = text.replace("  "," ")

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

    # Strip the tags around the entry for the folder number
    folder_begin = text.find("<td>",box_begin)+4
    folder_end   = text.find("</td>",folder_begin)
    folders = [-1,-1]
    if (folder_begin > 3):
        folders = text[folder_begin:folder_end].split()
        if len(folders) == 1:
            folders.append(folders[0])
        elif len(folders)==3 and folders[2].isdigit():
            folders[1]=folders[2]
            folders = folders[:1]

    # Split the entry into the identifier and the title
    identifier_begin = text.find("<div class")+17
    identifier_end   = text.find("<",identifier_begin)
    identifier = text[identifier_begin:identifier_end].split(":")[0].replace(" ","")
    # Strip tailing period from identifier if exists
    if (identifier[-1]=="."):
        identifier = identifier[:-1]
    title      = text[identifier_begin:identifier_end].split(":")[1].strip()

    # Get the items out of the string
    items_begin = text.find("scopecontent")+15
    items_end   = text.find(" ",items_begin)
    if (items_begin > 15):
        items = re.findall(r'\d+',text[items_begin:items_end])
        item_count = items[-1]
        node = item(group, boxes, folders, identifier, title, item_count)
    else:
        node = category(group, boxes, folders, identifier, title)

    # Return the node
    return node

# DEBUG
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
print(create_node(3,source_1))
print(create_node(3,source_2))
print(create_node(3,source_3))
print(create_node(3,source_4))
print(create_node(3,source_5))

# Read in from file
file = open('../html/testing.html','r')
readed = file.read()
file.close()
