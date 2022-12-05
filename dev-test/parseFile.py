def strip_initial(path):
    i = 0
    while path[i] != '/':
        i+=1
    return path[i+1:]
#print(strip_initial('a/era_common/nutanix_era/common/era/ERAProtectionDomain.py'))

def strip_string_behind(path):
    i = len(path) - 1
    while path[i] != '/':
        i-=1
    return path[:i+1]


def strip_string(file_path):
    i = 0
    count = 0
    while i < len(file_path) and count != 3:
        if file_path[i] == '/':
            count+=1
        i+=1
    if i == len(file_path):
        return ''
    return '/'+file_path[i:]

def check_valid(file_path):
    if file_path.split('/')[1] in ['common','era_cli','era_drivers','era_server_cli']:
        return True
    return False

def parseFile(file):
    with open(file) as f:
        patchFileLines = f.readlines()
    count = 0
    path_to_file_list = []
    path_to_file_list_without_strip = []
    file_name_list = []
    for line in patchFileLines:
        
        if line.startswith('diff --git'):
            line_split = line.split()
            path_to_file_without_strip = strip_initial(line_split[2])
            path_to_file = strip_string(line_split[2])
            if len(path_to_file) > 0 and check_valid(path_to_file):
                path_to_file_list.append(path_to_file)
                file_name = path_to_file.split('/')[-1]
                file_name_list.append(file_name)
                path_to_file_list_without_strip.append(path_to_file_without_strip)
                #print('Path to file is : {}'.format(str(path_to_file)))
                #print('File Name is: {}'.format(str(file_name)))
                count+=1
    return path_to_file_list,file_name_list,path_to_file_list_without_strip


def convert_unix_path_to_windows(path):
    modified_path = path.replace("/","\\\\")
    return modified_path



#parseFile('omkar_diff.patch')

#print(strip_string_behind('/era_cli/client/cli_framework/Abstraction/AbstractEntity.py'))