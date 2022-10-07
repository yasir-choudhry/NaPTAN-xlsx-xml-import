"""
This code aims to allow for a spreadsheet (which would ideally be filled out by those requesting new stops and stop
areas) to be imported into the relevant xml file.

It currently downloads xml from the NaPTAN website
"""
import PySimpleGUI as PyGUI
import time
import pandas as pd
import datetime
import os
import requests
import shutil
from Validation import Validator, NPTGRefValidator
import zipfile
import csv
from lxml import etree

NptgLocalityCodes = []


def download_extract_get_nptg_localities(down_dir="downloaded_nptg"):
    """
    download nptg data as a csv. Load the locality reference numbers from the localities csv
    :param down_dir: directory where it is to be downloaded
    :return:
    """
    global NptgLocalityCodes
    try:
        os.makedirs(down_dir)
    except FileExistsError:
        # directory already exists
        pass
    shutil.rmtree(down_dir)  # delete old data
    os.makedirs(down_dir)  # create folder again
    response = requests.post('https://beta-naptan.dft.gov.uk/Download/File/Localities.csv')
    data = response.content
    with open(down_dir+"/localities.csv", 'wb') as s:
        s.write(data)  # save nptg data to download folder
    # with zipfile.ZipFile(down_dir+"/nptgcsv.zip", "r") as zip_ref:
    #     zip_ref.extractall(down_dir)  # extract the zip file
    with open(down_dir+'/localities.csv', newline='', encoding='iso-8859-1') as f:
        reader = csv.reader(f)  # read the localities csv
        row1 = next(reader)  # ignore the first row with headers
        NptgLocalityCodes = []
        for row in reader:
            NptgLocalityCodes.append(row[0])  # add all codes to list of codes


def validator_tests():
    global NptgLocalityCodes
    # AtcoCode
    assert Validator("9200HYDEPRK", "AtcoCode", "GAT").validate() is True, "Should be valid"
    assert Validator("9200HYDEPRK", "AtcoCode", "BST").validate() is False, "Should be invalid"
    assert Validator("9200hydeprk", "AtcoCode", "GAT").validate() is True, "Should be valid"
    assert Validator("920HYDEPRK", "AtcoCode", "GAT").validate() is False, "Should be invalid"
    assert Validator("9200HYDE&RK", "AtcoCode", "GAT").validate() is False, "Should be invalid"
    assert Validator("9200HYDE PARK", "AtcoCode", "GAT").validate() is False, "Should be invalid"
    assert Validator("9200HYDEPARKCORNERSTATION", "AtcoCode", "GAT").validate() is False, "Should be invalid"
    assert Validator("9200HYDEPARK ", "AtcoCode", "GAT").validate() is False, "Should be invalid"
    assert Validator("09200HYDEPARK", "AtcoCode", "GAT").validate() is False, "Should be invalid"
    assert Validator("40HYDEPARK", "AtcoCode", "GAT").validate() is False, "Should be invalid"
    assert Validator("TESTHYDEPARK", "AtcoCode", "GAT").validate() is False, "Should be invalid"

    # NptgLocalityRef
    assert NPTGRefValidator("ES003378", "NptgLocalityRef", "GAT", NptgLocalityCodes).validate() is True, \
        "Should be valid"
    assert NPTGRefValidator("ZI003378", "NptgLocalityRef", "BST", NptgLocalityCodes).validate() is False, \
        "Should be invalid"

    # TiplocRef
    assert Validator("HYDPARK", "TiplocRef", "GAT").validate() is True, "Should be valid"
    assert Validator("23DPK", "TiplocRef", "GAT").validate() is True, "Should be valid"
    assert Validator("TESTHYDEPARK", "TiplocRef", "GAT").validate() is False, "Should be invalid"
    assert Validator("HYDE PARK", "TiplocRef", "GAT").validate() is False, "Should be invalid"
    assert Validator("HYDE PARK", "TiplocRef", "GAT").validate() is False, "Should be invalid"

    # miscellaneous
    assert Validator("Hyde Park", "CommonName", "GAT").validate() is True, "Should be valid"
    assert Validator("", "CommonName", "GAT").validate() is True, "Should be valid"
    assert Validator("Hyde Park Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor "
                     "incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation "
                     "ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit "
                     "in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat "
                     "cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum",
                     "CommonName", "GAT").validate() is False, "Should be invalid "


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


def download_nptg_from_naptan(down_dir="downloaded_nptg_xml"):
    """
    Submit a post request and download a xml file from the nptg beta website and save in the downloaded_nptg folder
    :param down_dir: directory where the files are to be saved
    :return:
    """
    response = requests.post('https://beta-naptan.dft.gov.uk/Download/File/NPTG.xml')
    data = response.content
    with open(down_dir+"/NPTG.xml", 'wb') as s:
        s.write(data)  # save nptg data to download folder
    # with zipfile.ZipFile(down_dir+"/nptgxml.zip", "r") as zip_ref:
    #     zip_ref.extractall(down_dir)  # extract the zip file
    xml_fp = down_dir+"/NPTG.xml"
    with open(xml_fp, "r") as f:
        text_all = f.read()

    # do this after to not mess with parsing
    root = etree.fromstring(text_all)
    xml_pretty_str = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="utf-8").decode()
    with open(xml_fp, "w") as text_file:
        text_file.write(xml_pretty_str)


def check_nptg(down_dir="downloaded_nptg_xml"):
    """
    Check if all the required nptg files are stored in the downloaded_nptg folder
    :param down_dir: directory where the files are
    :return: True if all are there, otherwise true
    """
    try:
        os.makedirs(down_dir)
    except FileExistsError:
        # directory already exists
        pass
    files_present = os.listdir(down_dir)
    if 'NPTG.xml' not in files_present:
        return False
    return True


def delete_downloaded_nptg(down_dir="downloaded_nptg_xml"):
    """
    delete all files saved in the downloaded_nptg folder
    :return:
    """
    shutil.rmtree(down_dir)
    os.makedirs(down_dir)


def text_from_xml(xml_fp: str):
    """
    get contents of xml file as string
    :param xml_fp: file location
    :return: file as string
    """
    with open(xml_fp, "r") as f:
        text = f.read()
    return text


def put_tag_in(xml_string: str, tag_name: str, tag_text: str, attributes: list):
    """
    Fill in the xml template with the fields from the spreadsheet row
    :param xml_string: The xml template as a string
    :param tag_name: The name of the
    :param tag_text:
    :param attributes:
    :return:
    """
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


def put_completed_template_in_main(xml_string, xml_main_fp, stop=True, nptg=False):
    """
    Put the filled in template string into the main xml file in the correct place
    :param xml_string: template with fields added
    :param xml_main_fp: file path of main xml file
    :param stop: True if this is a stop (false for stop template)
    :param nptg: True if nptg locality (not stop) -  overrides stop var
    :return:
    """
    main_xml_str = text_from_xml(xml_main_fp)
    if nptg:
        main_xml_str = main_xml_str.replace("</NptgLocalities>", xml_string.replace('&', '&amp;') + "</NptgLocalities>")
    elif stop:
        main_xml_str = main_xml_str.replace("</StopPoints>", xml_string.replace('&', '&amp;') + "</StopPoints>")
    else:
        main_xml_str = main_xml_str.replace("</StopAreas>\n</NaPTAN>", xml_string.replace('&', '&amp;')
                                            + "</StopAreas>\n</NaPTAN>")
    with open(xml_main_fp, 'w', encoding='utf-8') as f:
        f.write(main_xml_str)


def check_if_in_xml(atco_area_code, xml_main_fp):
    """
    Return true if lookup string is in the xml
    :param atco_area_code: string we are looking for
    :param xml_main_fp: file path of xml file to look in
    :return:
    """

    atco_area_list = []
    with open(xml_main_fp, "rb") as f:
        text_all = f.read()
    # root = etree.fromstring(text_all)
    root = etree.XML(text_all)
    stop_points = root.find("{http://www.naptan.org.uk/}StopPoints")
    stop_areas = root.find("{http://www.naptan.org.uk/}StopAreas")
    for stop in stop_points:
        atco_area_list.append(stop.find("{http://www.naptan.org.uk/}AtcoCode").text)
    for area in stop_areas:
        atco_area_list.append(area.find("{http://www.naptan.org.uk/}StopAreaCode").text)

    if atco_area_code in atco_area_list:
        return True
    else:
        return False

    # main_xml_str = text_from_xml(xml_main_fp)
    # if atco_area_code in main_xml_str:
    #     return True
    # else:
    #     return False
#     do this with lxml


def get_xl_df(spreadsheet_fp, sheet):
    """
    load a sheet from an excel spreadsheet as a pandas object
    :param spreadsheet_fp: file path of spreadsheet
    :param sheet: the name of the sheet
    :return:
    """
    return pd.read_excel(spreadsheet_fp, sheet_name=sheet)


# These are not xml items (they are tags) and therefore need to be added differently
attribute_name_list = ['CreationDateTime', 'ModificationDateTime', 'Modification', 'RevisionNumber', 'Status']


output_text_log = """--OUTPUT LOG--"""


def add_to_log(str_to_add):
    """
    add text to log string for display in the UI
    :param str_to_add: string to add to log
    :return:
    """
    global window
    global output_text_log
    output_text_log += "\n" + str(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')) + ": " + \
                       str_to_add
    window['OUTPUT'].update(value=output_text_log)


def delete_stop_area_from_xml(stop_code, xml_location, stop=True):
    root = etree.parse(xml_location)
    if stop:
        stoppoints = root.find("{http://www.naptan.org.uk/}StopPoints")
        for stop_ in stoppoints:
            if stop_.find("{http://www.naptan.org.uk/}AtcoCode").text == stop_code:
                stoppoints.remove(stop_)
    else:
        stopareas = root.find("{http://www.naptan.org.uk/}StopAreas")
        for area_ in stopareas:
            if area_.find("{http://www.naptan.org.uk/}StopAreaCode").text == stop_code:
                stopareas.remove(area_)



def delete_locality_from_nptg(nptg_locality_code, xml_location):
    """
    delete a locality  from the nptg xml
    :param nptg_locality_code:
    :param xml_location: file  location
    :return:
    """
    root = etree.parse(xml_location)
    localities = root.find("{http://www.naptan.org.uk/}NptgLocalities")
    for locality in localities:
        if locality.find("{http://www.naptan.org.uk/}NptgLocalityCode").text == nptg_locality_code:
            localities.remove(locality)
    xml_pretty_str = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="utf-8").decode()
    with open(xml_location, "w") as text_file:
        text_file.write(xml_pretty_str)


def update_nptg_locality_list(xml_location):
    """
    :param xml_location: fp of nptg xml
    :return:
    """
    global NptgLocalityCodes
    NptgLocalityCodes = []
    root = etree.parse(xml_location)
    localities = root.find("{http://www.naptan.org.uk/}NptgLocalities")
    for locality in localities:
        NptgLocalityCodes.append(locality.find("{http://www.naptan.org.uk/}NptgLocalityCode").text)


# the file names and local authority names of the xml files required
xml_name_la_names = {"910.xml": "National - National Rail / Great Britain (910)",
                     "920.xml": "National - National Air / Great Britain (920)",
                     "930.xml": "National - National Ferry / Great Britain (930)",
                     "940.xml": "National - National Tram / Great Britain (940)"}

# download NPTG locality data (this is only 1.5mb and can be cleared/downloaded each time the program is run)
download_extract_get_nptg_localities()

validator_tests()  # run tests

dir_path = os.path.dirname(os.path.realpath(__file__))

if not check_national_xmls(list(xml_name_la_names.keys())):
    # add_to_log("Missing xmls found, downloading from NaPTAN website")
    delete_downloaded_xmls()
    for xml_name_, la_name_ in xml_name_la_names.items():
        download_xml_from_naptan(la_name_, xml_name_)
        # add_to_log("Downloaded "+xml_name_)

if not check_nptg():
    # add_to_log("Missing nptg found, downloading from NaPTAN website")
    delete_downloaded_nptg()
    download_nptg_from_naptan()

# First the window layout in 2 columns
file_list_column = [
    [
        PyGUI.Button("Refresh XML files (delete and re-download form NaPTAN/NPTG website)")
    ],
    [
        PyGUI.Text("Select Excel file (which contains the request(s)):"),
        PyGUI.Input(key='-IMPORT XLSX-'),
        PyGUI.FileBrowse(file_types=(("Excel Files", "*.xlsx"),))
    ],
    [
        PyGUI.Checkbox("Update/overwrite existing stops/localities?", default=False, key='overwrite')
    ],
    [
        PyGUI.Button("Import from excel to xml")
    ]  # ,
    # [
    #     PyGUI.Text("Edit individual stops:"),
    #     PyGUI.Input(size=(25, 1), enable_events=True, key="-XML-FILE-"),
    #     PyGUI.FileBrowse(file_types=[".xml"])
    # ],
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


def refresh_xmls(xml_la_dict):
    """
    Delete all main xmls (NaPTAN and  NPTG) and download them from the naptan website
    :param xml_la_dict:
    :return:
    """
    global output_text_log
    global window
    delete_downloaded_xmls()
    delete_downloaded_nptg()
    add_to_log("Deleted all xmls")
    for xml_file_name, la in xml_la_dict.items():
        download_xml_from_naptan(la, xml_file_name)
        add_to_log("Downloaded " + xml_file_name)
    download_nptg_from_naptan()
    add_to_log("Downloaded NPTG xml")


def add_stops_or_areas(excel_file_path, template_folder, xml_folder, stop=True, overwrite_=False):
    """
    iterate through the rows in either the stops or areas sheet and add them to the template, them put this completed
    template in the main xml file
    :param excel_file_path:
    :param template_folder:
    :param xml_folder:
    :param stop:
    :param overwrite_: whether to overwrite
    :return:
    """
    global output_text_log
    global window
    if stop:
        sheet_name = "Stops"
        code_name = "AtcoCode"
        type = "stop"
    else:
        sheet_name = "StopAreas"
        code_name = "StopAreaCode"
        type = "area"
    stops_df = get_xl_df(excel_file_path, sheet_name)

    for index, row in stops_df.iterrows():
        if stop:
            stop_type = row["StopType"]
        else:
            stop_type = "StopArea"
        atco_prefix = row[code_name][:3]

        # check if atco code already exists

        already_exists = check_if_in_xml(row[code_name], xml_folder + "/" + atco_prefix + ".xml")
        if already_exists:
            if overwrite_:
                stop_ =False
                if type == "stop":
                    stop_ = True
                delete_stop_area_from_xml(row[code_name], xml_folder + "/" + atco_prefix + ".xml", stop=stop_)
                add_to_log("Found existing and deleted " + code_name + " " + row[code_name] + " to overwrite")
            else:
                add_to_log("ERROR! "+code_name+" " + row[code_name] + " already in xml file!")

        if (not already_exists) or overwrite_:
            template = text_from_xml(template_folder + "/" + stop_type + ".xml")

            add_dict = row.to_dict()
            # loop through each item in the row and add to the template
            for key, value in add_dict.items():
                template = put_tag_in(template, key, value, attribute_name_list)

            # add complete template to main xml
            put_completed_template_in_main(template, xml_folder + "/" + atco_prefix + ".xml", stop=stop, nptg=False)
            add_to_log("added "+type+" " + row[code_name] + " to file: " + xml_folder + "/" + atco_prefix + ".xml")


def add_nptg_locality(excel_file_path, template_folder, xml_folder, overwrite_=False):
    """
    Import from xlsx into NPTG  xml
    :param excel_file_path:
    :param template_folder:
    :param xml_folder:
    :param overwrite_: whether to overwrite existing
    :return:
    """
    global output_text_log
    global window
    global NptgLocalityCodes
    nptg_df = get_xl_df(excel_file_path, "Sheet1")
    for index, row in nptg_df.iterrows():
        nptglocalitycode = row["NptgLocalityCode"]

        if nptglocalitycode in NptgLocalityCodes:
            if overwrite_:
                delete_locality_from_nptg(nptglocalitycode, xml_folder + "/NPTG.xml")
                add_to_log("NPTG code" + nptglocalitycode + " already in xml file, deleted to be overwritten")
            else:
                add_to_log("ERROR! NPTG code" + nptglocalitycode + " already in xml file!")
        if (nptglocalitycode not in NptgLocalityCodes) or overwrite_:
            template = text_from_xml(template_folder + "/NPTG_Locality.xml")
            add_dict = row.to_dict()
            # loop through each item in the row and add to the template
            for key, value in add_dict.items():
                template = put_tag_in(template, key, value, attribute_name_list)
            # add complete template to main xml
            put_completed_template_in_main(template, xml_folder + "/NPTG.xml", stop=False, nptg=True)
            add_to_log("added locality " + nptglocalitycode + " to file: NPTG.xml")
            update_nptg_locality_list(xml_folder + "/NPTG.xml")


# Run the Event Loop
while True:
    event, values = window.read()
    if event == "Exit" or event == PyGUI.WIN_CLOSED:
        break
    elif event == "Refresh XML files (delete and re-download form NaPTAN/NPTG website)":
        try:
            refresh_xmls(xml_name_la_names)
        except Exception as e:
            add_to_log("unexpected error when refreshing xmls")
            print(e)
            pass

    elif event == "Import from excel to xml":  # A spreadsheet was chosen
        try:
            # set the folders and files from the GUI
            fp_xl = values["-IMPORT XLSX-"]
            fp_tp_folder = "xml templates"
            orig_xml_folder = "downloaded_xmls"

            overwrite = values["overwrite"]

            add_to_log(fp_xl)

            basename = os.path.basename(fp_xl)
            if basename == "NPTG_Locality.xlsx":
                download_folder = "downloaded_nptg_xml"
                add_nptg_locality(fp_xl, fp_tp_folder, download_folder, overwrite_=overwrite)
            else:
                add_stops_or_areas(fp_xl, fp_tp_folder, orig_xml_folder, stop=True, overwrite_=overwrite)  # add stops
                add_stops_or_areas(fp_xl, fp_tp_folder, orig_xml_folder, stop=False, overwrite_=overwrite)  # add areas

            time.sleep(0.5)

        except Exception as e:
            add_to_log("unexpected error when importing spreadsheet")
            print(e)
            pass

window.close()

