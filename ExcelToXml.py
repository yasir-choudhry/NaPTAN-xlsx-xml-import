import PySimpleGUI as PyGUI
import time
import pandas as pd
import datetime
import os
import requests
import shutil


def text_from_xml(xml_fp):
    with open(xml_fp, "r") as f:
        text = f.read()
    return text


def put_tag_in(xml_string, tag_name, tag_text, attributes):
    if str(tag_text) == "nan":
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
    return pd.read_excel(spreadsheet_fp, sheet_name=sheet)


def download_xml_from_naptan(la_name: str, xml_name: str, down_dir="downloaded_xmls"):
    """
    Submit a post request and download a xml file from the NaPTAN beta website and save in the downloaded_xmls folder
    :param la_name: properly formatted name of local authority as required by the website (from the drop down)
    :param xml_name: the name that the xml file should be saved as
    :param down_dir: directory where the files are to be saved
    :return:
    """
    req_data = {
        "selectedLasNames": la_name,
        "fileTypeSelect": "xml"
    }
    response = requests.post('https://beta-naptan.dft.gov.uk/Download/MultipleLa', data=req_data)
    data = response.content

    with open(down_dir+"/"+xml_name, 'wb') as s:
        s.write(data)


def check_national_xmls(xmls_req: list, down_dir="downloaded_xmls"):
    """
    Check if all the required xml files are stored in the downloaded_xmls folder
    :param xmls_req: list of strings of xmls file names required ie ['910.xml', '920.xml']
    :param down_dir: directory where the files are
    :return: True if all are there, otherwise true
    """
    try:
        os.makedirs(down_dir)
    except FileExistsError:
        # directory already exists
        pass
    files_present = os.listdir(down_dir)
    for xml_file in xmls_req:
        if xml_file not in files_present:
            return False
    return True


def delete_downloaded_xmls(down_dir="downloaded_xmls"):
    """
    delete all files saved in the downloaded_xmls folder
    :return:
    """
    shutil.rmtree(down_dir)
    os.makedirs(down_dir)


# These are not xml items and therefore need to be added differently
attribute_name_list = ['CreationDateTime', 'ModificationDateTime', 'Modification', 'RevisionNumber', 'Status']


output_text_log = """--OUTPUT LOG--"""


def add_to_log(log_var, str_to_add):
    log_var += "\n"+str(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))+": "+str_to_add
    return log_var


# the file names and local authority names of the cml files required
xml_name_la_names = {"910.xml": "National - National Rail / Great Britain (910)",
                     "920.xml": "National - National Air / Great Britain (920)",
                     "930.xml": "National - National Ferry / Great Britain (930)",
                     "940.xml": "National - National Tram / Great Britain (940)"}

if not check_national_xmls(list(xml_name_la_names.keys())):
    output_text_log = add_to_log(output_text_log, "Missing xmls found, downloading from NaPTAN website")
    delete_downloaded_xmls()
    for xml_name, la_name in xml_name_la_names.items():
        download_xml_from_naptan(la_name, xml_name)
        output_text_log = add_to_log(output_text_log, "Downloaded "+xml_name)


dir_path = os.path.dirname(os.path.realpath(__file__))

# First the window layout in 2 columns
file_list_column = [
    [
        PyGUI.Button("Refresh XML files (delete and re-download form NaPTAN website)")
    ],
    [
        PyGUI.Text("Select Excel file (which contains the request(s)):"),
        PyGUI.Input(key='-IMPORT XLSX-'),
        PyGUI.FileBrowse(file_types=(("Excel Files", "*.xlsx"),))
    ],
    [
        PyGUI.Button("Import from excel to xml")
    ]
]


output_viewer_column = [
    [PyGUI.Multiline(output_text_log, size=(80, 25), key='OUTPUT')]
]

# ----- Full layout -----
layout = [
    [
        PyGUI.Column(file_list_column),
        PyGUI.VSeperator(),
        PyGUI.Column(output_viewer_column),
    ]
]

window = PyGUI.Window("Import new stops and stop areas", layout)

# Run the Event Loop
while True:
    event, values = window.read()
    if event == "Exit" or event == PyGUI.WIN_CLOSED:
        break
    elif event == "Refresh XML files (delete and re-download form NaPTAN website)":
        try:
            delete_downloaded_xmls()
            output_text_log = add_to_log(output_text_log, "Deleted all xmls")
            window['OUTPUT'].update(value=output_text_log)
            for xml_name, la_name in xml_name_la_names.items():
                download_xml_from_naptan(la_name, xml_name)
                output_text_log = add_to_log(output_text_log, "Downloaded " + xml_name)
                window['OUTPUT'].update(value=output_text_log)
        except Exception as e:
            output_text_log = add_to_log(output_text_log, "unexpected error when refreshing xmls")
            window['OUTPUT'].update(value=output_text_log)
            print(e)
            pass

    elif event == "Import from excel to xml":  # A spreadsheet was chosen
        try:
            window['OUTPUT'].update(value=output_text_log)
            # set the folders and files from the GUI
            fp_xl = values["-IMPORT XLSX-"]
            fp_tp_folder = "xml templates"
            orig_xml_folder = "downloaded_xmls"

            # run the __main__ code but update log instead of print
            output_text_log = add_to_log(output_text_log, fp_xl)
            window['OUTPUT'].update(value=output_text_log)

            # add stops
            stops_df = get_xl_df(fp_xl, "Stops")

            for index, row in stops_df.iterrows():
                stop_type = row["StopType"]
                atco_prefix = row["AtcoCode"][:3]

                # check if atco code already exists
                if check_if_in_xml("<AtcoCode>"+row["AtcoCode"]+"</AtcoCode>", orig_xml_folder+"/"+atco_prefix+".xml"):
                    output_text_log = add_to_log(output_text_log,
                                                 "ERROR! AtcoCode "+row["AtcoCode"]+" already in xml file!")

                else:
                    template = text_from_xml(fp_tp_folder+"/"+stop_type+".xml")

                    add_dict = row.to_dict()
                    # loop through each item in the row and add to the template
                    for key, value in add_dict.items():
                        template = put_tag_in(template, key, value, attribute_name_list)

                    # add complete template to main xml
                    put_completed_template_in_main(template, orig_xml_folder+"/"+atco_prefix+".xml", stop=True)
                    output_text_log = add_to_log(output_text_log,
                                                 "added stop "+row["AtcoCode"]+" to file: " + orig_xml_folder + "/" +
                                                 atco_prefix + ".xml")
            # add areas
            areas_df = get_xl_df(fp_xl, "StopAreas")
            for index, row in areas_df.iterrows():
                stop_type = "StopArea"
                atco_prefix = row["StopAreaCode"][:3]

                # check if stop area already exists
                if check_if_in_xml("<StopAreaCode>"+row["StopAreaCode"]+"</StopAreaCode>",
                                   orig_xml_folder+"/"+atco_prefix+".xml"):
                    output_text_log = add_to_log(output_text_log,
                                                 "ERROR! StopAreaCode "+row["StopAreaCode"]+" already in xml file!")

                else:
                    template = text_from_xml(fp_tp_folder+"/"+stop_type+".xml")

                    add_dict = row.to_dict()
                    # loop through each item in the row
                    for key, value in add_dict.items():
                        template = put_tag_in(template, key, value, attribute_name_list)

                    # add complete template to main xml
                    put_completed_template_in_main(template, orig_xml_folder+"/"+atco_prefix+".xml", stop=False)
                    output_text_log = add_to_log(output_text_log, "added area "+row["StopAreaCode"]+" to file: " +
                                                 orig_xml_folder + "/" + atco_prefix + ".xml")

            window['OUTPUT'].update(value=output_text_log)
            time.sleep(0.5)

        except Exception as e:
            output_text_log = add_to_log(output_text_log, "unexpected error when importing spreadsheet")
            window['OUTPUT'].update(value=output_text_log)
            print(e)
            pass

window.close()
