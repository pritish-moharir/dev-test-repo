import warnings 
warnings.filterwarnings(action='ignore',module='.*paramiko.*')
import psycopg2
from sshtunnel import SSHTunnelForwarder
import pandas as pd
import paramiko
from scp import SCPClient
import time
import os
import uuid
from parseFile import parseFile,strip_string_behind,strip_initial,convert_unix_path_to_windows
import sys
from pypsrp.client import Client
class SSH_Server:
    def __init__(self,ip,username,password,patch_file,patchFilePath):
        self.ip = ip
        self.username = username
        self.password = password
        self.patch_file = patch_file
        self.patch_file_path = patchFilePath
        self.server = None
        self.ssh_client = None
        self.conn = None
        self.server_list = None
        self.uuid_1 = None
        self.windows_client = None

    def createSSHClient(self,ip,username,password):
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip,22,username,password)
        return client

    def get_server_details(self):
        try:
            self.ssh_client = self.createSSHClient('10.50.91.166','era','Nutanix.1')
            with SSHTunnelForwarder(
                (self.ip, 22),
                #ssh_private_key="</path/to/private/ssh/key>",
                ### in my case, I used a password instead of a private key
                ssh_username=self.username,
                ssh_password=self.password, 
                remote_bind_address=('localhost', 5432)) as self.server:
                
                self.server.start()
                #print ("server connected")
                #print(server.local_bind_port)
                params = {
                    'database': 'era_repos',
                    'user': 'postgres',
                    'host': 'localhost',
                    'port': self.server.local_bind_port
                    }

                self.conn = psycopg2.connect(**params)
                curs = self.conn.cursor()
                self.server_list = pd.read_sql("select id,name,ip_addresses,type from era_dbservers where status = 'UP' ORDER BY type DESC;",self.conn)
                # psql_query = "select id,name,ip_addresses,type from era_dbservers where status = 'UP' ORDER BY type;"
                # curs.execute(psql_query)
                # self.server_list = curs.fetchall()
                # with open("output_table.csv","w+") as my_csv:
                #     csvWriter = csv.writer(my_csv,delimiter=',')
                #     csvWriter.writerows(self.server_list)
                self.server_list.to_csv('output_table.csv')

                
                ssh_client = self.createSSHClient(self.ip,'era','Nutanix.1')
                scp = SCPClient(ssh_client.get_transport())
                scp.put('getCreds2.py',remote_path = '/home/era/')
                scp.put('output_table.csv',remote_path ='/home/era/')
                #self.ssh_client.exec_command('pip3 install pandas')
                _stdin, _stdout,_stderr = ssh_client.exec_command('python3 getCreds2.py')
                print()
                print('Fetching details from Era Server: {}'.format(str(self.ip)))
                print()
                time.sleep(1)
                scp.get('output2.csv')
                # print(_stdout.read().decode())
                return self.server_list
                # return output_table.to_html(classes='data',header='true')
                
        except Exception as e : 
            print(e)
    
    
    # def get_creds(self,vm_id):
    #     scp = SCPClient(self.ssh_client.get_transport())
    #     scp.put('getCreds.py',remote_path = '/home/era/')
    #     scp.put('output_table.csv',remote_path ='/home/era')
    #     _stdin, _stdout,_stderr = ssh.exec_command('python3 getCreds.py')
    #     print(_stdout.read().decode())




    def get_files_from_era_server(self,path_to_file_list,file_name_list,path_to_file_list_without_strip,server_ip,server_username,server_password,remote__path,server_os_type):
        self.uuid_1 = str(uuid.uuid1())[:4]
        cmd = "sshpass -p Nutanix.1 ssh -oStrictHostKeyChecking=no era@10.50.91.166 'mkdir /tmp/patch_{}_{}'".format(self.ip,str(self.uuid_1))
        os.system(cmd)
        if server_os_type == 'sqlserver_database':
            self.windows_client = Client(server_ip, username=server_username, password=server_password,ssl = False)
        for i in range(len(file_name_list)):
            file = file_name_list[i]
            path = path_to_file_list[i]
            path_without_strip = path_to_file_list_without_strip[i]

            #print(path)
            #print(path_without_strip)
            cmd2 = "sshpass -p Nutanix.1 ssh -oStrictHostKeyChecking=no era@10.50.91.166 'mkdir -p /tmp/patch_{}_{}/{}'".format(self.ip,str(self.uuid_1),strip_string_behind(path_without_strip))
            os.system(cmd2)

            if server_os_type != 'sqlserver_database':

                remote_path = remote__path+path
                command = "sshpass -p Nutanix.1 ssh -oStrictHostKeyChecking=no era@10.50.91.166 'sshpass -p {} scp -oStrictHostKeyChecking=no  {}@{}:{} /tmp/patch_{}_{}/{}'".format(server_password,server_username,server_ip,remote_path,self.ip,str(self.uuid_1),strip_string_behind(path_without_strip))
                #output = subprocess.check_output(command, shell=True)
                #print(output)
                os.system(command)
            
            
            else:
                remote_path = remote__path + convert_unix_path_to_windows(path)
                #print(remote_path)
                self.windows_client.fetch(remote_path,'{}/{}'.format(os.getcwd(),file))
                cmd10 = 'sshpass -p Nutanix.1 scp -oStrictHostKeyChecking=no {} era@10.50.91.166:/tmp/patch_{}_{}/{}'.format(file,self.ip,self.uuid_1,strip_string_behind(path_without_strip))
                os.system(cmd10)
                os.system('cd {} && rm -rf {}'.format(os.getcwd(),file))

        
        


    def apply_patch(self):
        self.get_server_details()
        creds_table = pd.read_csv('output2.csv')
        self.server_list['OS Type'] = ''
        for index2,row in creds_table.iterrows():
            host_id = row['HostID']
            for index1,row1 in self.server_list.iterrows():
                id = row1['id']
                if id == host_id:
                    row1['OS Type'] = row['OS']

        print(self.server_list.iloc[:,1:5].to_markdown())
        print()
        path_to_file_list,file_name_list,path_to_file_list_without_strip = parseFile(self.patch_file)
        #print(path_to_file_list)
        #print(file_name_list)
        #print(path_to_file_list_without_strip)
        
            
        #print(type(cmd2_output))

        str_index = input("Enter indices for the VMs you want to apply patched files : ")
        indices = str_index.split()
        self.server_list['Status'] = ''
        self.server_list['Failure Reason'] = ''
        for index in indices:
            target_server = self.server_list.iloc[int(index)]
            
            server_username_list,server_password_list = [],[]
            for i,row in creds_table.iterrows():
                if row['HostID'] == target_server['id']:
                    server_username_list.append(row['Username'])
                    server_password_list.append(row['Password'])
            
            if len(server_username_list) == 0:
                server_username_list.append('era')
                server_password_list.append('Nutanix.1')
            
            # print('Your Creds are: ')
            # for i in range(len(server_username_list)):
            #     print([server_username_list[i],server_password_list[i]])
            
            #correct_creds = False
            server_username,server_password,server_ip,server_type,server_os_type = None,None,None,None,None
            # while correct_creds != True:
            #     server_username = input('Enter the user you want to SSH with: ')
            #     for i in range(len(server_username_list)):
            #         if server_username == server_username_list[i]:
            #             server_password = server_password_list[i]
            #             correct_creds = True
            #             break
                #print('Enter correct username')
            

            server_username = server_username_list[0]
            server_password = server_password_list[0]
            server_ip = target_server['ip_addresses'][0]
            server_type = str(target_server['type'])
            server_os_type = target_server['OS Type']
            #print(server_type)
            # ssh_client = self.createSSHClient(server_ip,server_username,server_password)
            # scp = SCPClient(ssh_client.get_transport())

            remote_path = None
            if server_type == 'ERA_AGENT' or server_type == "ERA_SERVER":
                remote_path = '/usr/local/lib/python3.6/site-packages/nutanix_era'
            elif server_type == 'DBSERVER':
                if server_os_type != 'sqlserver_database':
                    remote_path = '/opt/era_base/era_engine/stack/linux/python/lib/python3.6/site-packages/nutanix_era'
                else:
                    remote_path = 'C:\\\\NTNX\\\\ERA_BASE\\\\era_engine\\\\stack\\\\windows\\\\python\\\\Lib\\\\site-packages\\\\nutanix_era'
            

            self.get_files_from_era_server(path_to_file_list,file_name_list,path_to_file_list_without_strip,server_ip,server_username,server_password,remote_path,server_os_type)
            cmd1 = "sshpass -p Nutanix.1 scp -oStrictHostKeyChecking=no {}/{} era@10.50.91.166:/tmp/patch_{}_{}/".format(self.patch_file_path,self.patch_file,self.ip,self.uuid_1)
            os.system(cmd1)
            #apply_patch()
            cmd2 = "sshpass -p Nutanix.1 ssh -oStrictHostKeyChecking=no era@10.50.91.166 'cd /tmp/patch_{}_{}/ && patch -p1 -s --reject-file={} < {}'".format(self.ip,self.uuid_1,'-',self.patch_file)
            #cmd2_output = subprocess.check_output(cmd2)
            #print(cmd2_output)
            cmd2_output = os.popen(cmd2).read()
            if len(cmd2_output) != 0:
                #print('Patch Failed to apply to VM with IP {}, reason : '.format(str(server_ip)))
                self.server_list.at[int(index),'Status'] = 'Failed'
                self.server_list.at[int(index),'Failure Reason'] = cmd2_output
                #print(cmd2_output)
                cmd_delete_patch = "sshpass -p Nutanix.1 ssh -oStrictHostKeyChecking=no era@10.50.91.166 'rm -rf /tmp/patch_{}_{}/'".format(self.ip,self.uuid_1)
                os.system(cmd_delete_patch)
                continue









            if server_os_type != 'sqlserver_database':
                cmd3 = "sshpass -p {} ssh -oStrictHostKeyChecking=no {}@{} 'mkdir /tmp/patch_{}_{}/'".format(server_password,server_username,server_ip,self.ip,self.uuid_1)
                os.system(cmd3)
            for i in range(len(path_to_file_list_without_strip)):
                file_path = path_to_file_list_without_strip[i]
                file_path_unstripped = path_to_file_list[i]
                file = file_name_list[i]
                #cmd3 = "sshpass -p Nutanix.1 ssh era@10.50.91.166 'mkdir /tmp/patch_{}_{}'".format(self.ip,str(self.uuid_1))


                if server_os_type != 'sqlserver_database':
                    cmd4 = "sshpass -p Nutanix.1 ssh -oStrictHostKeyChecking=no era@10.50.91.166 'sshpass -p {} scp -oStrictHostKeyChecking=no /tmp/patch_{}_{}/{} {}@{}:/tmp/patch_{}_{}/'".format(server_password,self.ip,self.uuid_1,file_path,server_username,server_ip,self.ip,self.uuid_1)
                    os.system(cmd4)
                    cmd5 = "sshpass -p {} ssh -oStrictHostKeyChecking=no {}@{} 'sudo mv /tmp/patch_{}_{}/{} {}/{}'".format(server_password,server_username,server_ip,self.ip,self.uuid_1,file,remote_path,file_path_unstripped)
                    os.system(cmd5)

                else:
                    cmd12 = "sshpass -p Nutanix.1 scp -oStrictHostKeyChecking=no era@10.50.91.166:/tmp/patch_{}_{}/{} {}/{}".format(self.ip,self.uuid_1,file_path,os.getcwd(),file)
                    os.system(cmd12)
                    self.windows_client.copy('{}/{}'.format(os.getcwd(),file),'{}\\\\{}'.format(remote_path,convert_unix_path_to_windows(file_path_unstripped)))
                    os.system('cd {} && rm -rf {}'.format(os.getcwd(),file))

            #print('Successfully Patched the Files for the VM with IP {}'.format(str(server_ip)))
            self.server_list.at[int(index),'Status'] = "Success"
            #print()





            # scp.put('patchFile.patch',remote_path = remote_path)
            # ssh_client.exec_command('cd '+remote_path)
            # _stdin, _stdout,_stderr = ssh_client.exec_command('patch -p2 --dry-run < patchFile.patch')
            # print(_stdout.read())
            cmd6 = "sshpass -p Nutanix.1 ssh -oStrictHostKeyChecking=no era@10.50.91.166 'rm -rf /tmp/patch_{}_{}/'".format(self.ip,self.uuid_1)
            os.system(cmd6)

            if server_os_type != 'sqlserver_database':
                cmd7 = "sshpass -p {} ssh -oStrictHostKeyChecking=no {}@{} 'rm -rf /tmp/patch_{}_{}/'".format(server_password,server_username,server_ip,self.ip,self.uuid_1)
                os.system(cmd7)
        cmd8 = "rm -rf output_table.csv"
        os.system(cmd8)
        cmd9 = "rm -rf output2.csv"
        os.system(cmd9)
        print()
        print()
        print(self.server_list.iloc[:,1:7].to_markdown())


    
if __name__ == '__main__':
    
    if len(sys.argv)<3:
        print("Syntax: Usage: python3 patch_servers.py <era-server-ip> <file>")
        exit(1)
    
    temp_obj = SSH_Server(sys.argv[1],'era','Nutanix.1',sys.argv[2],os.getcwd())
    temp_obj.apply_patch()
        

