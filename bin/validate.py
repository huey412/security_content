#!/usr/bin/python

'''
Validates Manifest file under the security-content repo for correctness.
'''

import glob
import json
import jsonschema
import sys
import argparse
from os import path


def validate_detection_contentv2(detection, DETECTION_UUIDS, errors):

    if detection['id'] == '':
        errors.append('ERROR: Blank ID')

    if detection['id'] in DETECTION_UUIDS:
        errors.append('ERROR: Duplicate UUID found: %s' % detection['id'])
    else:
        DETECTION_UUIDS.append(detection['id'])

    if detection['name'].endswith(" "):
        errors.append(
            "ERROR: Detection name has trailing spaces: '%s'" %
            detection['search_name'])

    try:
        detection['description'].encode('ascii')
    except UnicodeEncodeError:
        errors.append("ERROR: description not ascii")

    if 'how_to_implement' in detection:
        try:
            detection['how_to_implement'].encode('ascii')
        except UnicodeEncodeError:
            errors.append("ERROR: how_to_implement not ascii")

    if 'eli5' in detection:
        try:
            detection['eli5'].encode('ascii')
        except UnicodeEncodeError:
            errors.append("ERROR: eli5 not ascii")

    if 'known_false_positives' in detection:
        try:
            detection['known_false_positives'].encode('ascii')
        except UnicodeEncodeError:
            errors.append("ERROR: known_false_positives not ascii")

    if detection['detect']['splunk']:

        # do a regex match here instead of key values
        if (detection['detect']['splunk']['correlation_rule']['search'].find('tstats') != -1) or \
                (detection['detect']['splunk']['correlation_rule']['search'].find('datamodel') != -1):

            print "found datamodel keyword"

            if 'data_models' not in detection['data_metadata']:
                errors.append("ERROR: The Splunk search uses a data model but 'data_models' field is not set")

            if not detection['data_metadata']['data_models']:
                errors.append("ERROR: The Splunk search uses a data model but 'data_models' is empty")

        # do a regex match here instead of key values
        if (detection['detect']['splunk']['correlation_rule']['search'].find('sourcetype') != -1):
            if 'data_sourcetypes' not in detection['data_metadata']:
                errors.append("ERROR: The Splunk search specifies a sourcetype but 'data_sourcetypes' \
                            field is not set")

            if not detection['data_metadata']['data_sourcetypes']:
                errors.append("ERROR: The Splunk search specifies a sourcetype but \
                        'data_sourcetypes' is empty")

    return errors


def validate_detection_contentv1(detection, DETECTION_UUIDS, errors):

    try:
        detection['search_description'].encode('ascii')
    except UnicodeEncodeError:
        errors.append("ERROR: description not ascii")

    if detection['search_name'].endswith(" "):
        errors.append(
            "ERROR: Detection name has trailing spaces: '%s'" %
            detection['search_name'])

    if detection['search_id'] == '':
        errors.append('ERROR: Blank ID')

    if detection['search_id'] in DETECTION_UUIDS:
        errors.append('ERROR: Duplicate UUID found: %s' % detection['search_id'])
    else:
        DETECTION_UUIDS.append(detection['search_id'])

    if '| tstats' in detection['search'] or 'datamodel' in detection['search']:
        if 'data_models' not in detection['data_metadata']:
            errors.append(
                "ERROR: The search uses a data model but 'data_models' \
                        field is not set")

        if 'data_models' in detection and not \
                detection['data_metadata']['data_models']:
            errors.append(
                "ERROR: The search uses a data model but 'data_models' is empty")

    if 'sourcetype' in detection['search']:
        if 'data_sourcetypes' not in detection['data_metadata']:
            errors.append(
                "ERROR: The search specifies a sourcetype but 'data_sourcetypes' \
                        field is not set")

        if 'data_sourcetypes' in detection and not \
                detection['data_metadata']['data_sourcetypes']:
            errors.append(
                "ERROR: The search specifies a sourcetype but \
                        'data_sourcetypes' is empty")

    try:
        detection['search_description'].encode('ascii')
    except UnicodeEncodeError:
        errors.append("ERROR: search_description not ascii")

    if 'how_to_implement' in detection:
        try:
            detection['how_to_implement'].encode('ascii')
        except UnicodeEncodeError:
            errors.append("ERROR: how_to_implement not ascii")

    if 'eli5' in detection:
        try:
            detection['eli5'].encode('ascii')
        except UnicodeEncodeError:
            errors.append("eli5 not ascii")

    if 'known_false_positives' in detection:
        try:
            detection['known_false_positives'].encode('ascii')
        except UnicodeEncodeError:
            errors.append("ERROR: known_false_positives not ascii")

    if 'correlation_rule' in detection and 'notable' in \
            detection['correlation_rule']:
        try:
            detection['correlation_rule']['notable']['rule_title'].encode('ascii')
        except UnicodeEncodeError:
            errors.append("ERROR: rule_title not ascii")

        try:
            detection['correlation_rule']['notable']['rule_description'].encode(
                'ascii')
        except UnicodeEncodeError:
            errors.append("ERROR: rule_description not ascii")

    return errors


def validate_detection_content(detection, DETECTION_UUIDS):
    ''' Validate that the content of a detection manifest is correct'''
    errors = []

    # run v1 content validation
    if detection["spec_version"] == 1:
        errors = validate_detection_contentv1(detection, DETECTION_UUIDS, errors)

    if detection["spec_version"] == 2:
        errors = validate_detection_contentv2(detection, DETECTION_UUIDS, errors)

    return errors


def validate_story_content(story, STORY_UUIDS):
    ''' Validate that the content of a story manifest is correct'''
    errors = []

    if story['id'] == '':
        errors.append('ERROR: Blank ID')

    if story['id'] in STORY_UUIDS:
        errors.append('ERROR: Duplicate UUID found: %s' % story['id'])
    else:
        STORY_UUIDS.append(story['id'])

    try:
        story['description'].encode('ascii')
    except UnicodeEncodeError:
        errors.append("ERROR: description not ascii")

    try:
        story['narrative'].encode('ascii')
    except UnicodeEncodeError:
        errors.append("ERROR: narrative not ascii")

    return errors


def validate_detection(REPO_PATH, verbose):
    ''' Validates Detections'''

    DETECTION_UUIDS = []
    # retrive
    v1_schema_file = path.join(path.expanduser(REPO_PATH), 'spec/v1/detection_search.json.spec')
    try:
        v1_schema = json.loads(open(v1_schema_file, 'rb').read())
    except IOError:
        print "ERROR: reading version 1 detection schema file {0}".format(v1_schema_file)

    v2_schema_file = path.join(path.expanduser(REPO_PATH), 'spec/v2/detections.spec.json')
    try:
        v2_schema = json.loads(open(v2_schema_file, 'rb').read())
    except IOError:
        print "ERROR: reading version 2 detection schema file {0}".format(v2_schema_file)

    error = False
    manifest_files = path.join(path.expanduser(REPO_PATH), "detections/*.json")

    for manifest_file in glob.glob(manifest_files):
        if verbose:
            print "processing detection {0}".format(manifest_file)

        # read in each story
        try:
            detection = json.loads(
                open(manifest_file, 'r').read())
        except IOError:
            print "Error reading {0}".format(manifest_file)
            error = True
            continue

        # validate v1 and v2 stories against spec
        if detection['spec_version'] == 1:
            try:
                jsonschema.validate(instance=detection, schema=v1_schema)
            except jsonschema.exceptions.ValidationError as json_ve:
                print "ERROR: {0} at:\n\t{1}".format(json.dumps(json_ve.message), manifest_file)
                print "\tAffected Object: {}".format(json.dumps(json_ve.instance))
                error = True

        elif detection['spec_version'] == 2:
            try:
                jsonschema.validate(instance=detection, schema=v2_schema)
            except jsonschema.exceptions.ValidationError as json_ve:
                print "ERROR: {0} at:\n\t{1}".format(json.dumps(json_ve.message), manifest_file)
                print "\tAffected Object: {}".format(json.dumps(json_ve.instance))
                error = True

        else:
            print "ERROR: Story {0} does not contain a spec_version which is required".format(manifest_file)
            error = True
            continue

        # now lets validate the content
        detection_errors = validate_detection_content(detection, DETECTION_UUIDS)
        if detection_errors:
            error = True
            for err in detection_errors:
                print "{0} at:\n\t {1}".format(err, manifest_file)

    return error


def validate_story(REPO_PATH, verbose):
    ''' Validates Stories'''

    STORY_UUIDS = []

    # retrive
    v1_schema_file = path.join(path.expanduser(REPO_PATH), 'spec/v1/analytic_story.json.spec')
    try:
        v1_schema = json.loads(open(v1_schema_file, 'rb').read())
    except IOError:
        print "ERROR: reading version 1 story schema file {0}".format(v1_schema_file)

    v2_schema_file = path.join(path.expanduser(REPO_PATH), 'spec/v2/story.spec.json')
    try:
        v2_schema = json.loads(open(v2_schema_file, 'rb').read())
    except IOError:
        print "ERROR: reading version 2 story schema file {0}".format(v2_schema_file)

    error = False
    story_manifest_files = path.join(path.expanduser(REPO_PATH), "stories/*.json")

    for story_manifest_file in glob.glob(story_manifest_files):
        if verbose:
            print "processing story {0}".format(story_manifest_file)

        # read in each story
        try:
            story = json.loads(
                open(story_manifest_file, 'r').read())
        except IOError:
            print "Error reading {0}".format(story_manifest_file)
            error = True
            continue

        # validate v1 and v2 stories against spec
        if story['spec_version'] == 1:
            try:
                jsonschema.validate(instance=story, schema=v1_schema)
            except jsonschema.exceptions.ValidationError as json_ve:
                print "ERROR: {0} at:\n\t{1}".format(json.dumps(json_ve.message), story_manifest_file)
                print "\tAffected Object: {}".format(json.dumps(json_ve.instance))
                error = True

        elif story['spec_version'] == 2:
            try:
                jsonschema.validate(instance=story, schema=v2_schema)
            except jsonschema.exceptions.ValidationError as json_ve:
                print "ERROR: {0} at:\n\t{1}".format(json.dumps(json_ve.message), story_manifest_file)
                print "\tAffected Object: {}".format(json.dumps(json_ve.instance))
                error = True

        else:
            print "ERROR: Story {0} does not contain a spec_version which is required".format(story_manifest_file)
            error = True
            continue

        # now lets validate the content
        story_errors = validate_story_content(story, STORY_UUIDS)
        if story_errors:
            error = True
            for err in story_errors:
                print "{0} at:\n\t {1}".format(err, story_manifest_file)

    return error


if __name__ == "__main__":
    # grab arguments
    parser = argparse.ArgumentParser(description="validates security content manifest files", epilog="""
        Validates security manifest for correctness, adhering to spec and other common items.""")
    parser.add_argument("-p", "--path", required=True, help="path to security-security content repo")
    parser.add_argument("-v", "--verbose", required=False, action='store_true', help="prints verbose output")
    # parse them
    args = parser.parse_args()
    REPO_PATH = args.path
    verbose = args.verbose

    story_error = validate_story(REPO_PATH, verbose)

    detection_error = validate_detection(REPO_PATH, verbose)

    if story_error:
        sys.exit("Errors found")
    elif detection_error:
        sys.exit("Errors found")
    else:
        print "No Errors found"
