# ------------------------------------------------------------------------------
# Name:        connect2workforce.py
# Purpose:     generates identifiers for features

# Copyright 2017 Esri

#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

# ------------------------------------------------------------------------------

from datetime import datetime as dt
from os import path, sys
from arcgis.gis import GIS
from arcgis.features import FeatureLayer

orgURL = 'http://arcgis4localgov2.maps.arcgis.com'     # URL to ArcGIS Online organization or ArcGIS Portal
username = 'amuise_lg'   # Username of an account in the org/portal that can access and edit all services listed below
password = 'pigsfly'   # Password corresponding to the username provided above

services = [{'source url': 'https://services.arcgis.com/b6gLrKHqgkQb393u/arcgis/rest/services/AnimalProblemReports/FeatureServer/0',
             'target url': 'https://services.arcgis.com/b6gLrKHqgkQb393u/arcgis/rest/services/assignments_314f2ba1d1cb46009aa4b173fdbf57fd/FeatureServer/0',
             'query': '1=1',
             'fields': {
                 'DETAILS': 'description'},
             'update field': '',
             'update value': ''
             }]

def main():
    # Create log file
    with open(path.join(sys.path[0], 'attr_log.log'), 'a') as log:
        log.write('\n{}\n'.format(dt.now()))

        # connect to org/portal
        gis = GIS(orgURL, username, password)

        for service in services:
            try:
                # Connect to source and target layers
                fl_source = FeatureLayer(service['source url'], gis)
                fl_target = FeatureLayer(service['target url'], gis)

                # get field map
                fields = [[key, service['fields'][key]] for key in service['fields'].keys()]

                # Get source rows to copy
                rows = fl_source.query(service['query'])
                adds = []
                updates = []

                for row in rows:
                    # build dictionary of attributes & geometry in schema of target layer
                    attributes = {}
                    status = False
                    priority = False
                    for field in fields:
                        attributes[field[1]] = row.attributes[field[0]]
                        if field[1] == 'status' and row.attributes[field[0]]:
                            status = True
                        elif field [1] == 'priority' and row.attributes[field[0]]:
                            priority = True
                    if not status:
                        attributes['status'] = 0
                    if not priority:
                        attributes['priority'] = 0

                    new_request = {'attributes': attributes,
                                   'geometry': {'x': row.geometry['x'],
                                                'y': row.geometry['y']}}
                    adds.append(new_request)

                    # update row to indicate record has been copied
                    if service['update field']:
                        row.attributes[service['update field']] = service['update value']
                        updates.append(row)

                # add records to target layer
                if adds:
                    add_result = fl_target.edit_features(adds=adds)
                    for result in add_result['updateResults']:
                        if not result['success']:
                            raise Exception('error {}: {}'.format(result['error']['code'],
                                                                  result['error']['description']))

                # update records:
                if updates:
                    update_result = fl_source.edit_features(updates=updates)
                    for result in update_result['updateResults']:
                        if not result['success']:
                            raise Exception('error {}: {}'.format(result['error']['code'],
                                                                  result['error']['description']))

            except Exception as ex:
                msg = 'Failed to copy feature from layer {}'.format(service['url'])
                print(ex)
                print(msg)
                log.write('{}\n{}\n'.format(msg, ex))

if __name__ == '__main__':
    main()
