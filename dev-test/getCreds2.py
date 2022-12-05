from nutanix_era.common.mgmt_server.ERAHostUtil import ERAHostUtil
try:
    import nutanix_era.common.mgmt_server.ExecutionContextUtil as ExecutionContextUtil
    import nutanix_era.common.generic.constants as CONSTANTS
    exexution_context = {}
    exexution_context[CONSTANTS.USE_CLIENT_CREDS] = True
    ExecutionContextUtil.init_context(exexution_context)
    era_conn = ExecutionContextUtil.ERA_CONN
    __host_util = ERAHostUtil(era_conn=era_conn)
except Exception as e:
    pass

def parse_csv(file):
    with open(file, 'r') as f:
        results = []
        count = 0
        for line in f:
            if count == 0:
                count+=1
                continue
            words = line.split(',')
            results.append(words)
    print(results)
    return results
try:
    output_table = parse_csv('output_table.csv')
    hostId_list,username_list,password_list,os_type_list = [],[],[],[]
    for row in output_table:
        id = row[1]
        current_cred = ERAHostUtil().get_host_creds(host_id=id)
        if current_cred is not None: 
            for cred in current_cred: 
                print(cred)
                __dbserver = __host_util.get_detailed_host_with_id(cred['hostId'], all_types=True)
                os_type_list.append(__dbserver["metadata"]["databaseType"])
                hostId_list.append(cred['hostId'])
                username_list.append(cred['username'])
                password_list.append(cred['password'])

    creds_table = []
    for i in range(len(hostId_list)):
        a = []
        a.append(hostId_list[i])
        a.append(username_list[i])
        a.append(password_list[i])
        a.append(os_type_list[i])
        creds_table.append(a)
    # df = pd.DataFrame(columns=['HostID','Username','Password','OS'])
    # df['HostID'] = hostId_list
    # df['Username'] = username_list
    # df['Password'] = password_list
    # df['OS'] = os_type_list
    f=open('output2.csv','w')
    headers = ['HostID','Username','Password','OS']
    print(",".join([str(i) for i in headers]), file = f)
    for x in creds_table:
        print(",".join([str(i) for i in x]), file=f)
    f.close()
    



except Exception as e:
    print(e)