import PySimpleGUI as sg
import os.path
import time
import pandas as pd
import csv
import os
import re
import datetime


def text_from_xml(xml_fp):
    with open(xml_fp, "r") as f:
        text = f.read()
    return text

def put_tag_in(xml_string, tag_name, tag_text, attributes):
    if str(tag_text)=="nan":
        pass
    elif tag_name in attributes:
        # replace the attribute
        if 'Date' in tag_name:
            # add date in iso format
            tag_text = str(datetime.datetime.fromisoformat(str(tag_text)).isoformat())
        xml_string = xml_string.replace(str(tag_name)+'=""', str(tag_name)+'="'+str(tag_text)+'"')
    else:
        # replace the tag
        xml_string = xml_string.replace('></'+str(tag_name)+'>', '>'+str(tag_text)+'</'+str(tag_name)+'>')
    return xml_string

def put_completed_template_in_main(xml_string, xml_main_fp, stop=True):
    main_xml_str = text_from_xml(xml_main_fp)
    if stop:
        main_xml_str = main_xml_str.replace("</StopPoints>", xml_string+"</StopPoints>")
    else:
        main_xml_str = main_xml_str.replace("</StopAreas>\n</NaPTAN>", xml_string+"</StopAreas>\n</NaPTAN>")
    with open(xml_main_fp, 'w') as f:
        f.write(main_xml_str)

def check_if_in_xml(string_to_check, xml_main_fp):
    main_xml_str = text_from_xml(xml_main_fp)
    if string_to_check in main_xml_str:
        return True
    else:
        return False

def get_xl_df(spreadsheet_fp, sheet):
    return pd.read_excel(fp_xl, sheet_name=sheet)

# These are not xml items and therefore need to be added differently
attribute_name_list = ['CreationDateTime', 'ModificationDateTime', 'Modification', 'RevisionNumber', 'Status']


output_text_log = """--OUTPUT LOG--"""

def add_to_log(log_var, str_to_add):
    log_var += "\n"+str(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))+": "+str_to_add
    return log_var

# First the window layout in 2 columns
file_list_column = [
    [
        sg.Text("Select main XML folder (where the 900 xmls are saved):"),
        sg.In(size=(25, 1), enable_events=False, key="-MAIN FOLDER-"),
        sg.FolderBrowse(),
    ],
    [
        sg.Text("Select templates folder (where the stop xml templates are saved):"),
        sg.In(size=(25, 1), enable_events=False, key="-TEMPLATE FOLDER-"),
        sg.FolderBrowse(),
    ],
    [
        sg.Text("Select Excel file (which contains the request(s)):"),
        sg.Input(key='-IMPORT XLSX-'),
        sg.FileBrowse(file_types=(("Excel Files", "*.xlsx"),))
    ],
    [
        sg.Button("Import from excel to xml")
    ],
]


output_viewer_column = [
    [sg.Multiline(output_text_log, size=(80, 25), key='OUTPUT')]
]

# ----- Full layout -----
layout = [
    [
        sg.Column(file_list_column),
        sg.VSeperator(),
        sg.Column(output_viewer_column),
    ]
]

window = sg.Window("Import new stops and stop areas", layout)

# Run the Event Loop
while True:
    event, values = window.read()
    if event == "Exit" or event == sg.WIN_CLOSED:
        break
    elif event == "Import from excel to xml":  # A spreadsheet was chosen
        try:
            window['OUTPUT'].update(value=output_text_log)
            # set the folders and files from the GUI
            fp_xl = values["-IMPORT XLSX-"]
            fp_tp_folder = values["-TEMPLATE FOLDER-"]
            orig_xml_folder = values["-MAIN FOLDER-"]

            # run the __main__ code but update log instead of print
            output_text_log = add_to_log(output_text_log, fp_xl)
            output_text_log = add_to_log(output_text_log, fp_tp_folder)
            output_text_log = add_to_log(output_text_log, orig_xml_folder)
            window['OUTPUT'].update(value=output_text_log)

            # add stops
            stops_df = get_xl_df(fp_xl, "Stops")

            for index, row in stops_df.iterrows():
                stop_type = row["StopType"]
                atco_prefix = row["AtcoCode"][:3]

                # check if atco code already exists
                if check_if_in_xml("<AtcoCode>"+row["AtcoCode"]+"</AtcoCode>", orig_xml_folder+"/"+atco_prefix+".xml"):
                    output_text_log = add_to_log(output_text_log, "ERROR! AtcoCode "+row["AtcoCode"]+" already in xml file!")

                else:
                    template = text_from_xml(fp_tp_folder+"/"+stop_type+".xml")

                    add_dict = row.to_dict()
                    # loop through each item in the row and add to the template
                    for key, value in add_dict.items():
                        template = put_tag_in(template, key, value, attribute_name_list)

                    # add complete template to main xml
                    put_completed_template_in_main(template, orig_xml_folder+"/"+atco_prefix+".xml", stop=True)
                    output_text_log = add_to_log(output_text_log, "added stop "+row["AtcoCode"]+" to file: " + orig_xml_folder+"/"+atco_prefix+".xml")
            # add areas
            areas_df = get_xl_df(fp_xl, "StopAreas")
            for index, row in areas_df.iterrows():
                stop_type = "StopArea"
                atco_prefix = row["StopAreaCode"][:3]

                # check if stop area already exists
                if check_if_in_xml("<StopAreaCode>"+row["StopAreaCode"]+"</StopAreaCode>", orig_xml_folder+"/"+atco_prefix+".xml"):
                    output_text_log = add_to_log(output_text_log, "ERROR! StopAreaCode "+row["StopAreaCode"]+" already in xml file!")

                else:
                    template = text_from_xml(fp_tp_folder+"/"+stop_type+".xml")

                    add_dict = row.to_dict()
                    # loop through each item in the row
                    for key, value in add_dict.items():
                        template = put_tag_in(template, key, value, attribute_name_list)

                    # add complete template to main xml
                    put_completed_template_in_main(template, orig_xml_folder+"/"+atco_prefix+".xml", stop=False)
                    output_text_log = add_to_log(output_text_log, "added area "+row["StopAreaCode"]+" to file: " + orig_xml_folder+"/"+atco_prefix+".xml")


            window['OUTPUT'].update(value=output_text_log)
            time.sleep(0.5)

        except Exception as e:
            output_text_log = add_to_log(output_text_log, "unexpected error")
            window['OUTPUT'].update(value=output_text_log)
            print(e)
            pass

window.close()
