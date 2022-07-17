import xmltodict
import os
import zipfile


skipped = True
skipped_count = 0

with open('driver_ir_codes_dump.py', 'w') as f:
    f.write("""ir_codes_list_of_dicts = [\r\n""")
    path_to_drivers = '/home/bzuck/Tools/OnlineDrivers'
    folder = os.scandir(path_to_drivers)
    for file in folder:
        if file.name.endswith(".c4i") and file.is_file():
            skipped = True
            # print('found c4i: {0} at path: {1}'.format(file.name, file.path))
            with open(file.path) as fd:
                doc = xmltodict.parse(fd.read())
                if 'devicedata' in doc:
                    if 'config' in doc['devicedata']:
                        if doc['devicedata']['config'] != None:
                            if 'irsection' in doc['devicedata']['config']:
                                if doc['devicedata']['config']['irsection'] != None:
                                    if 'ircodes' in doc['devicedata']['config']['irsection']:
                                        if doc['devicedata']['config']['irsection']['ircodes'] != None:
                                            if 'ircode' in doc['devicedata']['config']['irsection']['ircodes']:
                                                if doc['devicedata']['config']['irsection']['ircodes']['ircode'] != None:
                                                    # print(doc['devicedata']['config']['irsection']['ircodes'])
                                                    for entry in doc['devicedata']['config']['irsection']['ircodes']['ircode']:
                                                        skipped = False
                                                        # f.write('{0}\r\n'.format(str(entry)))
                                                        # print(doc['devicedata']['name'])
                                                        # print(entry['pattern'])
                                                        f.write(
                                                            """, {{ 'driver': '{0}', 'name': '{1}', 'transmit': '{2}', 'repeatcount': '{3}', 'delayafter': '{4}' , 'pronto': '{5}' }}\r\n"""
                                                            .format(file.name
                                                                    , entry['name']
                                                                    , entry['transmit']
                                                                    , entry['repeatcount']
                                                                    , entry['delayafter']
                                                                    , entry['pattern']))

        if file.name.endswith(".c4z") and file.is_file():
            skipped = True
            # print('found c4z: {0} at path: {1}'.format(file.name, file.path))
            try:
                temp_archive = zipfile.ZipFile(file.path, 'r')
            except Exception:
                print('{0} cant be opened as an archive'.format(file.name))
            else:
                with zipfile.ZipFile(file.path, 'r') as archive:
                    doc = xmltodict.parse(archive.read('driver.xml'))
                    if 'devicedata' in doc:
                        if 'config' in doc['devicedata']:
                            if doc['devicedata']['config'] != None:
                                if 'irsection' in doc['devicedata']['config']:
                                    if doc['devicedata']['config']['irsection'] != None:
                                        if 'ircodes' in doc['devicedata']['config']['irsection']:
                                            if doc['devicedata']['config']['irsection']['ircodes'] != None:
                                                if 'ircode' in doc['devicedata']['config']['irsection']['ircodes']:
                                                    if doc['devicedata']['config']['irsection']['ircodes']['ircode'] != None:
                                                        # print(doc['devicedata']['config']['irsection']['ircodes'])
                                                        skipped = False
                                                        for entry in doc['devicedata']['config']['irsection']['ircodes']['ircode']:
                                                            # f.write('{0}\r\n'.format(str(entry)))
                                                            # print(doc['devicedata']['name'])
                                                            # print(entry['pattern'])
                                                            f.write(
                                                                """, {{ 'driver': '{0}', 'name': '{1}', 'transmit': '{2}', 'repeatcount': '{3}', 'delayafter': '{4}' , 'pronto': '{5}' }}\r\n"""
                                                                    .format(file.name
                                                                            , entry['name']
                                                                            , entry['transmit']
                                                                            , entry['repeatcount']
                                                                            , entry['delayafter']
                                                                            , entry['pattern']))
        if skipped:
            print('skipping {0}.  No IR codes found'.format(file.name))
            skipped_count += 1
    f.write("""]\r\n""")
print('skipped_count: {0}'.format(skipped_count))

# # c4i section:
# with open('driver_ir_codes_dump.py', 'w') as f:
#     f.write("""ir_codes_list_of_dicts = [\r\n""")
#     # path_to_file = '/home/bzuck/Tools/OnlineDrivers/avswitch_Atlona_AT-SAV-42M (IR).c4i'
#     path_to_file = '/home/bzuck/Tools/OnlineDrivers/cd_houseLogix_voicepod audio out.c4i'
#     with open(path_to_file) as fd:
#         doc = xmltodict.parse(fd.read())
#         if 'devicedata' in doc:
#             if 'config' in doc['devicedata']:
#                 if  doc['devicedata']['config'] != None:
#                     if 'irsection' in doc['devicedata']['config']:
#                         if doc['devicedata']['config']['irsection'] != None:
#                             if 'ircodes' in doc['devicedata']['config']['irsection']:
#                                 if doc['devicedata']['config']['irsection']['ircodes'] != None:
#                                     if 'ircode' in doc['devicedata']['config']['irsection']['ircodes']:
#                                         if doc['devicedata']['config']['irsection']['ircodes']['ircode'] != None:
#                                             print(doc['devicedata']['config']['irsection']['ircodes'])
#                                             for entry in doc['devicedata']['config']['irsection']['ircodes']['ircode']:
#                                                 # f.write('{0}\r\n'.format(str(entry)))
#                                                 print(doc['devicedata']['name'])
#                                                 print(entry['pattern'])
#                                                 f.write(""", {{ 'driver': '{0}', 'name': '{1}', 'transmit': '{2}', 'repeatcount': '{3}', 'delayafter': '{4}' , 'pronto': '{5}' }}\r\n"""
#                                                         .format(doc['devicedata']['name']
#                                                                 , entry['name']
#                                                                 , entry['transmit']
#                                                                 , entry['repeatcount']
#                                                                 , entry['delayafter']
#                                                                 , entry['pattern']))
#
#     f.write("""]\r\n""")

# # c4z section:
# with open('driver_ir_codes_dump.py', 'w') as f:
#     f.write("""ir_codes_list_of_dicts = [\r\n""")
#     # path_to_file = '/home/bzuck/Tools/OnlineDrivers/avswitch_Atlona_AT-SAV-42M (IR).c4i'
#     path_to_file = '/home/bzuck/Tools/OnlineDrivers/lg_tv_55UK7700PUD.c4z'
#     # with open(path_to_file) as fd:
#     with zipfile.ZipFile(path_to_file, 'r') as archive:
#         # doc = xmltodict.parse(fd.read())
#         doc = xmltodict.parse(archive.read('driver.xml'))
#         if 'devicedata' in doc:
#             if 'config' in doc['devicedata']:
#                 if  doc['devicedata']['config'] != None:
#                     if 'irsection' in doc['devicedata']['config']:
#                         if doc['devicedata']['config']['irsection'] != None:
#                             if 'ircodes' in doc['devicedata']['config']['irsection']:
#                                 if doc['devicedata']['config']['irsection']['ircodes'] != None:
#                                     if 'ircode' in doc['devicedata']['config']['irsection']['ircodes']:
#                                         if doc['devicedata']['config']['irsection']['ircodes']['ircode'] != None:
#                                             print(doc['devicedata']['config']['irsection']['ircodes'])
#                                             for entry in doc['devicedata']['config']['irsection']['ircodes']['ircode']:
#                                                 # f.write('{0}\r\n'.format(str(entry)))
#                                                 print(doc['devicedata']['name'])
#                                                 print(entry['pattern'])
#                                                 f.write(""", {{ 'driver': '{0}', 'name': '{1}', 'transmit': '{2}', 'repeatcount': '{3}', 'delayafter': '{4}' , 'pronto': '{5}' }}\r\n"""
#                                                         .format(doc['devicedata']['name']
#                                                                 , entry['name']
#                                                                 , entry['transmit']
#                                                                 , entry['repeatcount']
#                                                                 , entry['delayafter']
#                                                                 , entry['pattern']))
#
#     f.write("""]\r\n""")







