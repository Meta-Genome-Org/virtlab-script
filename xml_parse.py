import cdcs_deprec
from cdcs_deprec import CDCS
import pandas as pd
import xml.dom.minidom as md



class xml_control:
    def __init__(self, cdcs_df, xml_string):
        self.cdcs_df = cdcs_df
        self.xml_string = xml_string
    
    
    def inspect_xml(self):
        import xml.etree.ElementTree as ET

        # parse the XML string
        tree = ET.ElementTree(ET.fromstring(self.xml_string))

        # get the root element
        root = tree.getroot()
        root_elems = []
        for child in root.findall("./*"):
            root_elems.append(child)

        # submission type
        submission_type = root_elems[3].tag

        type_elems = []
        for child in root_elems[3]:
            type_elems.append(child)

        # chosen directional sensitivity
        sensitivity = type_elems[-1].tag

        avail_sensitivity = {"isotropic-choice":"-iso",
                             "transversely-isotropic-choice": "-trans",
                             "orthotropic-choice" : "-ortho"}
        
        sensitivity_sufix = avail_sensitivity[type_elems[-1].tag]

        choice_elems = []
        for child in type_elems[-1]:
            choice_elems.append(child.tag)
            print(child.tag.split('-').pop(-1))

        # all properties in directional functionality
        choice_elems_clean = ['-'.join(word.split('-')[:-1]) for word in choice_elems]
        
        print(choice_elems_clean)

        possible_data = ['tensile-modulus', 'compressive-modulus', 'tensile-poissons-ratio', 'compressive-poissons',\
                         'compressive-poissons-ratio', "couple-constant", "yield-strength", "ultimate-yield-strength"]

        # Getting single measures only - i.e. tensile modulus etc.
        identified_properties = []
        for clean_elem in choice_elems_clean:
            print(clean_elem)
            if clean_elem in possible_data:
                identified_properties.append(clean_elem)

        # identified single point properties within this submission:
        print(identified_properties)

        # getting single point values and units
        measure_val_units = {}
        
        for elem in identified_properties:
            val = root.findall(f"./{submission_type}/{sensitivity}/{elem + sensitivity_sufix}/*")
            val = [word for word in val if 'conditions' not in word.tag]
            measure_content ={}
            for element in val:
                measure_content[element.tag] = element.text
            measure_val_units[elem] = measure_content
        
        # getting all single point values into organised dictionary
        # print(measure_val_units)
        
        print("\n\n\t\t*** DATA READOUT ***\n")
        print("Submission Type:", submission_type)
        print("Directional Sensitivity:", sensitivity.split('-')[0])
        print("Measurement Results:")
        for measurement_type, measurement_data in measure_val_units.items():
            print("\t", measurement_type.replace("-", " "), ":")
            for data_type, data_value in measurement_data.items():
                label = " ".join(data_type.split("-")[:3])
                print("\t\t", label, ":", data_value)
        
        return measure_val_units
    


    def get_topologies(self):
        import xml.etree.ElementTree as ET
        # parse the XML string
        tree = ET.ElementTree(ET.fromstring(self.xml_string))

        # get the root element
        root = tree.getroot()
        root_elems = []
        for child in root.findall("./*"):
            root_elems.append(child)

        # submission type
        submission_type = root_elems[3].tag

        type_elems = []
        for child in root_elems[3]:
            type_elems.append(child)

        # chosen directional sensitivity
        sensitivity = type_elems[-1].tag
        # dict to contain each continuous measure set of topologies and unit-cell
        measure_topols = {}
        # list of all topology files for unit cell
        unit_cell_topols = [element.find("./topology-url").text for element in root_elems[3] if 'topol' in element.tag]
        #insert unit cell topologies into topologies dict
        measure_topols["unit-cell-topologies"] = unit_cell_topols

        # all measured properties in submission from choice level
        choice_elems = []
        for child in type_elems[-1]:
            choice_elems.append(child)
            print(child.tag.split('-').pop(-1))

        possible_data = ['stress-strain', 'trans-axial-strain', 'base-stress-relax', 'base-twist-axial-strain']

        # slice to only get continuous measures by keyword search - accounts for variety in phasing
        identified_properties = []
        for elem in choice_elems:
            for data_type in possible_data:
                if data_type in elem.tag:
                    identified_properties.append(elem)
        
        for j, elem in enumerate(identified_properties):
            # get all elems in continuous data:
            continuous_type = root.findall(f"./{submission_type}/{sensitivity}/{elem.tag}/*")
            # get all topology uploads
            topologies = [element for element in continuous_type if 'topology' in element.tag]
            # dict for individual measure topologies
            grouped_topols ={}
            for i, element in enumerate(topologies):
                topol_urls = element.find("./topology-url").text
                grouped_topols[element.tag + "-" + str(i)] = topol_urls
            measure_topols[elem.tag + "-" + str(j)] = grouped_topols
    
        return measure_topols

    def interactive_expansion(self):
        dom = md.parseString(self.xml_string)

        # Print the available elements to the console
        print("Available elements:")
        root_elem = dom.documentElement
        for i, elem in enumerate(root_elem.childNodes):
            if elem.nodeType == md.Node.ELEMENT_NODE:
                print(f"{i}: {elem.tagName}")

        def recur_select(recur_index, recur_elem):
            print(recur_index)
            if recur_index >= 0:
                elems = recur_elem.childNodes[recur_index]
                print(f"\nContents of {elems.tagName}:")
                for j, child in enumerate(elems.childNodes):
                    #if child.nodeType == md.Node.ELEMENT_NODE:
                    if child.nodeType == md.Node.ELEMENT_NODE:
                        print(f"{j}: {child.tagName}")
                    elif child.nodeType == md.Node.TEXT_NODE:
                        print(f"{j}: {child.nodeValue}")
                    
                new_index = int(input("Enter the index of the element to expand (or -1 to go to root level):"))                
                return recur_select(new_index, elems)
            
            if recur_index < 0:
                root_elem = dom.documentElement
                for i, elem in enumerate(root_elem.childNodes):
                    if elem.nodeType == md.Node.ELEMENT_NODE:
                        print(f"{i}: {elem.tagName}")
                
                new_index = int(input("Enter the index of the element to expand (or -1 to go exit):")) 
                if new_index < 0:
                    
                    return (-1)
                else:
                    
                    return recur_select(new_index, root_elem)
        
        # Get user input for which element to expand
        elem_index = int(input("Enter the index of the element to expand (or -1 to exit): "))
            
        while elem_index >= 0:
            # Get the selected element
            elem = root_elem.childNodes[elem_index]

            # Print the contents of the selected element
            print(f"\nContents of {elem.tagName}:")
            for j, child in enumerate(elem.childNodes):
                #if child.nodeType == md.Node.ELEMENT_NODE:
                print(f"{j}: {child.tagName}")

            # Get user input for which child element to expand
            child_index = int(input("Enter the index of the child element to expand (or -1 to go back): "))
            elem_index  = recur_select(child_index, elem)


    def print_publication_details(self):
        import xml.etree.ElementTree as ET
        root = ET.fromstring(self.xml_string)
        print("\n\nPublication Details:\n")
        print("Title:", root.find('publication-info/publication-title').text)
        print("Authors:")
        auth_list = []
        for author in root.findall('publication-info/publication-authors'):
            auth_list.append(author.find('author-initials').text + ". " + author.find('author-surname').text)
            #print(author.find('author-initials').text, author.find('author-surname').text)
        print(", ".join(auth_list))
        print("Journal:", root.find('publication-info/publication-journal').text)
        print("Volume:", root.find('publication-info/publication-volume').text)
        print("Issue:", root.find('publication-info/publication-issue').text)
        print("Page:", root.find('publication-info/publication-page').text)
        print("Year:", root.find('publication-info/publication-year').text)
        print("DOI:", root.find('publication-info/id').text)
        print("URL:", root.find('publication-info/publication-url').text)
        print("Submitter:", root.find('publication-info/Publication-submitter').text)
        print("Submitter Email:", root.find('publication-info/Publication-submitter-email').text)

    def find_sub_elem(self):
        import xml.etree.ElementTree as ET
        root = ET.fromstring(self.xml_string)
        print(root)
        rows = root.find('.//xls-upload-stress-strain-table/rows')
        for row in rows.findall('row'):
            # Get the values of the columns in the row
            values = [c.text for c in row.findall('column')]
            # Print the values
            #print(values)
    
    def get_base_stress_strain(self):
        import xml.etree.ElementTree as ET

        # parse the XML string
        tree = ET.ElementTree(ET.fromstring(self.xml_string))

        # get the root element
        root = tree.getroot()
        base_tree = root.findall("./base-material-info")
        base_count = len(base_tree)
        #print(base_count)
        base_dict = {}
        for i in range(base_count):
            base_stress_strain = root.findall(f"./base-material-info/isotropic-choice/base-stress-strain")
            base_stress_strain_count = len(base_stress_strain)
            
            base_stress_strain_dict = {}
            for j in range(base_stress_strain_count):
                base_stress_strain_indiv = root.findall(f"./base-material-info[{i+1}]/isotropic-choice/base-stress-strain[{j+1}]/stress-strain-xls/xls-upload-stress-strain-table/rows/row")
                all_columns = []
                #print(j)
                for row in base_stress_strain_indiv:
                    all_columns.append([row[0].text, row[1].text])
                
                base_stress_strain_dict[f"stress_strain_{j}"] = all_columns
            
        base_dict[f"base_material_{i}"] = base_stress_strain_dict
        
     
#my_parse = xml_control(my_query, xml_content) 
#my_vals = my_parse.inspect_xml()
#print(my_vals)
#my_topols = my_parse.get_topologies()
#print(my_topols)
#my_parse.interactive_expansion()
#my_parse.print_publication_details()
#my_parse.find_sub_elem()
#my_parse.get_base_stress_strain()