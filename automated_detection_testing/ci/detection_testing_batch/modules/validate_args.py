import argparse
import copy
import io
import json
import jsonschema
import jsonschema.exceptions
import jsonschema_errorprinter
import sys
from typing import Union


# If we want, we can easily add a description field to any of the objects here!

setup_schema = {
    "type": "object",
    "properties": {
        "branch": {
            "type": "string",
            "default": "develop"
        },

        "container_tag": {
            "type": "string",
            "default": "latest"
        },

        "interactive_failure": {
            "type": "boolean",
            "default": False
        },
            
        "detections_list": {
            "type":["array"],
            "items": {
                "type":"string"
            },
            "default":[],
        },

        "detections_file":{
            "type": ["string","null"],
            "default": None
        },

        "local_apps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string"
                    },
                    "app_number": {
                        "type": "integer"
                    },
                    "app_version": {
                        "type": "string"
                    },
                    "local_path": {
                        "type": "string"
                    },
                },
                "default": []
            }
        },

        "mode": {
            "type": "string",
            "enum": ["changes", "selected", "all"],
            "default": "changes"
        },

        "num_containers": {
            "type": "integer",
            "minimum": 1,
            "default": 1
        },

        "persist_security_content": {
            "type": "boolean",
            "default": False
        },

        "pr_number": {
            "type": ["integer", "null"],
            "default": None
        },

        "reuse_image": {
            "type": "boolean",
            "default": True
        },

        "show_splunk_app_password": {
            "type": "boolean",
            "default": True

        },

        "splunkbase_apps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string"
                    },
                    "app_number": {
                        "type": "integer"
                    },
                    "app_version": {
                        "type": "string"
                    }
                },
            },
            "default":  [
                {
                    "app_name": "SPLUNK_ADD_ON_FOR_AMAZON_WEB_SERVICES",
                    "app_number": 1876,
                    "app_version": "5.2.0"
                },
                {
                    "app_name": "SPLUNK_ADD_ON_FOR_MICROSOFT_OFFICE_365",
                    "app_number": 4055,
                    "app_version": "2.2.0"
                },
                {
                    "app_name": "SPLUNK_ADD_ON_FOR_AMAZON_KINESIS_FIREHOSE",
                    "app_number": 3719,
                    "app_version": "1.3.2"
                },
                {
                    "app_name": "SPLUNK_ANALYTIC_STORY_EXECUTION_APP",
                    "app_number": 4971,
                    "app_version": "2.0.3"
                },
                {
                    "app_name": "PYTHON_FOR_SCIENTIC_COMPUTING_LINUX_64_BIT",
                    "app_number": 2882,
                    "app_version": "2.0.2"
                },
                {
                    "app_name": "SPLUNK_MACHINE_LEARNING_TOOLKIT",
                    "app_number": 2890,
                    "app_version": "5.2.2"
                },
                {
                    "app_name": "SPLUNK_APP_FOR_STREAM",
                    "app_number": 1809,
                    "app_version": "8.0.1"
                },
                {
                    "app_name": "SPLUNK_ADD_ON_FOR_STREAM_WIRE_DATA",
                    "app_number": 5234,
                    "app_version": "8.0.1"
                },
                {
                    "app_name": "SPLUNK_ADD_ON_FOR_STREAM_FORWARDERS",
                    "app_number": 5238,
                    "app_version": "8.0.1"
                },
                {
                    "app_name": "SPLUNK_ADD_ON_FOR_ZEEK_AKA_BRO",
                    "app_number": 1617,
                    "app_version": "4.0.0"
                },
                {
                    "app_name": "SPLUNK_ADD_ON_FOR_UNIX_AND_LINUX",
                    "app_number": 833,
                    "app_version": "8.3.1"
                },
                {
                    "app_name": "SPLUNK_COMMON_INFORMATION_MODEL",
                    "app_number": 1621,
                    "app_version": "4.20.2"
                }
            ]
        },
        "splunkbase_username": {
            "type": ["string", "null"],
            "default": None
        },
        "splunkbase_password": {
            "type": ["string", "null"],
            "default": None
        },
        "splunk_app_password": {
            "type": ["string", "null"],
            "default": None
        },
        "splunk_container_apps_directory": {
            "type": "string",
            "default": "/opt/splunk/etc/apps"
        },
        "local_base_container_name": {
            "type": "string",
            "default": "splunk_test_%d"
        },

        "mock": {
            "type": "boolean",
            "default": False
        },

        "types": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": ["endpoint", "cloud", "network"]
            },
            "default": ["endpoint", "cloud", "network"]
        },
    }
}


def validate_file(file:io.TextIOWrapper)->tuple[Union[dict, None], dict]:
    try:
        settings = json.loads(file.read())
        return validate(settings)
    except Exception as e:
        raise(e)
    



def check_dependencies(settings: dict)->bool:
    #Check complex mode dependencies
    error_free = True
    if settings['mode'] == 'selected':
        #Make sure that exactly one of the following fields is populated
        if settings['detections_file'] == None and settings['detections_list'] == []:
            print("Error - mode was 'selected' but no detections_list or detections_file were supplied.",file=sys.stderr)
            error_free = False
        elif settings['detections_file'] != None and settings['detections_list'] != []:
            print("Error - mode was 'selected' but detections_list and detections_file were supplied.",file=sys.stderr)
            error_free = False
    if settings['mode'] != 'selected'and settings['detections_file'] != None:
        print("Error - mode was not 'selected' but detections_file was supplied.",file=sys.stderr)
        error_free = False
    elif settings['mode'] != 'selected' and settings['detections_list'] != []:
        print("Error - mode was not 'selected' but detections_list was supplied.",file=sys.stderr)
        error_free = False

    #Returns true if there are not errors
    return error_free

def validate(configuration: dict) -> tuple[Union[dict, None], dict]:
    #v = jsonschema.Draft201909Validator(argument_schema)

    try:
        validation_errors, validated_json = jsonschema_errorprinter.check_json(
            configuration, setup_schema)
        no_complex_errors = check_dependencies(validated_json)
        if len(validation_errors) == 0 and no_complex_errors:
            print("Input configuration successfully validated!")
            return validated_json, setup_schema
        elif no_complex_errors == False:
            print("Failed due to error(s) listed above.", file=sys.stderr)
            return None,setup_schema
        else:
            print("[%d] failures detected during validation of the configuration!" % (
                len(validation_errors)))
            for error in validation_errors:
                print(error, end="\n\n", file=sys.stderr)
            return None, setup_schema
    except Exception as e:
        print(str(e), file=sys.stderr)
        return None, setup_schema

    """
    try:
        v.validate({"action":"doot", "branch":"15"}  )
    except jsonschema.exceptions.ValidationError as e:
        print("Error validating the json", file=sys.stderr)
        print(e)
        return False
        
    except jsonschema.exceptions.SchemaError as e:
        print("Error validating the schema", file=sys.stderr)
    """


if __name__ == "__main__":
    c = v({"action": "test", "branch": "wow"})
    print(c)
    if c is False:
        print("whoops")
    else:
        print(c.keys())
"""
def load(json_settings: io.TextIOWrapper) -> dict:
    default_settings = json.load(json_settings)
    return default_settings


def load_and_validate(json_settings: io.TextIOWrapper) -> dict:
    settings = load(json_settings)
    validate(settings)
    return settings


def validate(args: dict) -> bool:
    validate_common_arguments()

    validate_mode()

    return True


def validate_mode(args: dict) -> bool:
    return True


def validate_mode_selected(args: dict) -> bool:
    return True


def validate_mode_changes(args: dict) -> -bool:
    return True


def validate_mode_all(args: dict) -> bool:
    return True
"""
