class Validator:
    def __init__(self, value, key, stop_type):
        self.value = value
        self.type = key
        self.stop_type = stop_type

    def validate(self):
        validator_func_dict = {
            "AtcoCode": validate_atcocode,
            "StopAreaRef": validate_atcocode,
            "TiplocRef": validate_tiploc,
            "CommonName": validate_length,

        }
        return validator_func_dict[self.type](self.value, self.stop_type)


class NPTGRefValidator(Validator):  # inherit validator class for NPTG codes which requires list of codes
    def __init__(self, value, key, stop_type, list_of_nptg_ref):
        Validator.__init__(self, value, key, stop_type)
        self.ntpg_list = list_of_nptg_ref

    def validate(self):
        return validate_nptglocalityref(self.value, self.ntpg_list)


def validate_atcocode(val, stop_type):
    type_prefix_dict = {
        "900": ["BST"],
        "910": ["RLY", "RPL"],
        "920": ["GAT"],
        "930": ["FER", "FBT"],
        "940": ["MET", "PLT"]
    }

    if (len(val) > 12 or
        len(val) < 5 or
        " " in val or
        not val.isalnum() or
        not val[:4].isdigit() or
        val[3] != "0"  # note: many of the existing stops don't include leading 0's in the prefix even though this
        # is specified in the schema guide
    ):
        return False

    # if the atco code related to a specific stop type ensure that it matches
    elif val[:3] in type_prefix_dict and stop_type not in type_prefix_dict[val[:3]]:
        return False
    # other checks could include ensuring the TIPLOC code (for rail station entrances) and ATcoAreaCode for coach
    # station entrances have been correctly added to the AtcoCode. This would be useful if this code was to be used
    # to add non-national '90X' stops
    else:
        return True


def validate_tiploc(val, stop_type):
    if (len(val) > 7 or
        " " in val or
        not val.isalnum() or
        len(val) < 2
    ):
        return False
    else:
        return True


def validate_length(val, stop_type):
    if len(val) > 100:
        return False
    else:
        return True


def validate_nptglocalityref(val, nptg_list):
    if val not in nptg_list:
        return False
    else:
        return True
