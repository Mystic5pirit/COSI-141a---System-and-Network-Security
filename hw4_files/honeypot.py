import argparse
from datetime import datetime
import paramiko
import socket
import threading
import select


global_attempts = {'victim55': 0, 'bob': 0, 'garth22': 0} 
# Lock to ensure only one thread modifies the dictionary at a time
attempts_lock = threading.Lock()

# paramiko provides a class to be inherited to be able to make a server
class Server(paramiko.ServerInterface):

    def __init__(self):
        self.event = threading.Event()
        self.current_username = None

    
    # Allows some sort of channel request
    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED
    
    # Allows a shell request to work, all others are false by default
    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

    # Keep track of attempts, all attempts are failed attempts before 5 tries
    def check_auth_password(self, username, password):
        global global_attempts, attempts_lock

        if username in global_attempts:
            
            with attempts_lock:                
                if global_attempts[username] >= 5: 
                    self.current_username = username
                    return paramiko.AUTH_SUCCESSFUL
                else:
                    global_attempts[username] += 1
                    print(f"Failed attempt for {username}.")
        return paramiko.AUTH_FAILED
    
    # What method of authorization is allowed (only password)
    def get_allowed_auths(self, username):
        return 'password'
    
    # Allow a pseudo-terminal
    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True

def connect(client, addr):

    global session_id_counter, session_id_lock 
    
    with session_id_lock:
        session_id_counter += 1
        session_id = session_id_counter

    # active = True
    # while active:
    if True:
        try:
            transport = paramiko.Transport(client)
            transport.add_server_key(key)
            server = Server()
            try:
                transport.start_server(server = server)
            except Exception as e:
                print('Starting server failed: ' + str(e))
                return

            channel = transport.accept(60)
            if channel is None:
                print('No channel')
                return
            
            server.event.wait(10)
            if not server.event.is_set():
                print('Client never asked for a shell')
                return

            # I wanted to add this, but I realized that I wanted parent directories more
            # labyrinth = {}
            # labyrinth['left'] = {
            #     'type': 'dir',
            #     'contents': labyrinth
            # }
            # labyrinth['right'] = {
            #     'type': 'dir',
            #     'contents': labyrinth
            # }

            # In memory file system, not persistent between sessions
            files = {
                'type': 'dir',
                'contents': { },
                'parent': None
            }

            files['contents']['secrets.txt'] = {
                            'type': 'file',
                            'contents': 'pwd1: psj3ffgt5r79s5dbjwrhcbw4c6dvsf4sgpxst4h6dnr205nslgb\r\npwd2: gdwjfd873bf06snv06b37hrcf62jxd6be9tjbsir84bdj3pleku\r\n',
                            'parent': files
                        }

            current_dir = files
            current_path = ['']

            def traverse(path):
                '''
                Traverses down the directory from the current location to the target location
                
                :param path: The list of directories in list form, relative to current directory

                :return dir: The new directory
                :return path: The new path from root, list form
                :return success: If the traversal was successful
                '''
                temp_dir = current_dir
                temp_path = list(current_path)
                success = True

                if path[0] == '': # Starts with /
                    temp_dir = files
                    temp_path = ['']

                for directory in path:
                    if directory == '':
                        continue
                    elif directory == '..':
                        if temp_dir['parent']:
                            temp_path = temp_path[:-1]
                            temp_dir = temp_dir['parent']
                        else:
                            success = False
                            break
                    else:
                        if directory in temp_dir['contents'] and temp_dir['contents'][directory]['type'] == 'dir':
                            temp_path.append(directory)
                            temp_dir = temp_dir['contents'][directory]
                        else:
                            success = False
                            break
                return temp_dir, temp_path, success

            # Shell
            client_ip = transport.getpeername()[0]
            username = server.current_username
            start_time = datetime.now()
            commands = []

            
            channel.send(f'\r\n{username}@honeypot:/$ ')
            char_buffer = ''
            while transport.is_active():

                # Removed because it should not be necessary
                # traversal_error = False
                # for directory in current_path:
                #     if directory in current_dir['contents']:
                #         current_dir = current_dir['contents'][directory]
                #     else: # Shouldn't happen, but just in case
                #         print(f'Current directory {current_path} does not exist, backtracking...')
                #         current_dir.pop()
                #         traversal_error = True
                #         break
                # if traversal_error:
                #     continue

                        
                try:
                    rlist, _, _ = select.select([channel.fileno()], [], [], 60)

                    if rlist:
                        data = channel.recv(1024).decode('utf-8')

                        if len(data) == 0:
                            raise EOFError("Closed connection gracefully")
                        
                        for char in data:
                            if char == '\n' or char == '\r': # Newline character is inconsistent across operating systems, Yay!
                                if char_buffer:
                                    split_cmd = char_buffer.split(maxsplit=1)
                                    cmd = split_cmd[0]
                                    if len(split_cmd) > 1:
                                        args = split_cmd[1].strip()
                                    else:
                                        args = ''

                                    print('Command detected: ' + char_buffer)
                                    print('cmd: ' + cmd)
                                    print('args: ' + args)

                                    
                                    match cmd:
                                        case 'help':
                                            output = '\r\n help \r\n exit \r\n cd \r\n mkdir \r\n mkfile \r\n pwd \r\n ls \r\n echo \r\n cat \r\n cp'
                                        case 'exit':
                                            channel.send('\r\nExiting shell.\r\n')
                                            raise EOFError("Client issued 'exit' command")
                                        case 'cd':
                                            output = ''
                                            split_args = args.split()
                                            if len(split_args) > 1:
                                                output = '\r\n' + ('As this is a rudimentary file system, tags and multiple arguments for cd are not supported')
                                                continue
                                            elif len(split_args) == 0: # No arguments returns to root
                                                current_dir = files
                                                current_path = ['']
                                            else:
                                                path = args.split('/')
                                                
                                                temp_dir, temp_path, success = traverse(path)

                                                if success:
                                                    current_dir = temp_dir
                                                    current_path = temp_path
                                                else:
                                                    output = '\r\n' + ('Error with traversal') 
                                        case 'mkdir':
                                            output = ''
                                            split_args = args.split()
                                            if len(split_args) > 1:
                                                output = '\r\n' + ('As this is a rudimentary file system, tags and multiple arguments for mkdir are not supported')
                                                continue
                                            if len(split_args) == 0:
                                                output = '\r\n' + ('A new directory must be given for mkdir')
                                                continue
                                            if '/' in args:
                                                output = '\r\n' + ('Creating parent directories and traversal is not supported in this rudimentary file system. Please use create directories one at a time in their desired locations')
                                                continue
                                            if '.' in args:
                                                output = '\r\n' + ('The character "." is not supported in directory names')
                                            current_dir['contents'][args] = {
                                                'type': 'dir',
                                                'contents':{},
                                                'parent': current_dir
                                            }
                                        case 'mkfile':
                                            output = ''
                                            split_args = args.split()
                                            if len(split_args) > 1:
                                                output = '\r\n' + ('As this is a rudimentary file system, tags and multiple arguments for mkfile are not supported')
                                                continue
                                            if len(split_args) == 0:
                                                output = '\r\n' + ('A new file name must be given for mkfile')
                                                continue
                                            if '/' in args:
                                                output = '\r\n' + ('Creating parent directories and traversal is not supported in this rudimentary file system. Please use create directories and files one at a time in their desired locations')
                                                continue
                                            if args.split('.')[-1] != 'txt':
                                                output = '\r\n' + ('Unknown file extension')
                                                continue
                                            current_dir['contents'][args] = {
                                                'type': 'file',
                                                'contents':'',
                                                'parent': current_dir
                                            }
                                        case 'pwd':
                                            output = '\r\n' + ('/'.join(current_path))
                                        case 'ls':
                                            output = '\r\n' + ('\r\n'.join(current_dir['contents']))
                                        case 'echo':
                                            output = ''

                                            split_args = args.split('"')
                                            if len(split_args) != 3:
                                                output = '\r\n' + ('As this is a rudimentary file system, tags and arguments not in the form "content" > destination.txt for echo are not supported')
                                                continue
                                            split2 = split_args[-1].split()
                                            if len(split2) != 2 or split2[0] != '>':
                                                output = '\r\n' + ('As this is a rudimentary file system, tags and arguments not in the form "content" > destination.txt for echo are not supported')
                                                continue
                                            dest = split2[1].strip()


                                            if not dest.endswith('.txt'):
                                                output = '\r\n' + ('Unknown file extension')
                                                continue
                                            
                                            dest = dest.split('/')
                                            path = dest[:-1]
                                            if path:
                                                temp_dir, temp_path, success = traverse(path)
                                            else:
                                                success = True
                                                temp_dir = current_dir


                                            contents = '"'.join(split_args[1:-1])
                                            if success:
                                                temp_dir['contents'][dest[-1]] = {
                                                'type': 'file',
                                                'contents':contents + '\r\n',
                                                'parent': temp_dir
                                                }
                                            else:
                                                output = '\r\n' + ('Error with traversal')   
                                        case 'cat':
                                            split_args = args.split()
                                            if len(split_args) > 1:
                                                output = '\r\n' + ('As this is a rudimentary file system, tags and multiple arguments for cat are not supported')
                                                continue
                                            if len(split_args) == 0:
                                                output = '\r\n' + ('A file name must be given for cat')
                                                continue
                                            if not args.endswith('.txt'):
                                                output = '\r\n' + ('Unknown file extension')
                                                continue
                                            dest = args.split('/')
                                            path = dest[:-1]
                                            if path:
                                                temp_dir, temp_path, success = traverse(path)
                                            else:
                                                success = True
                                                temp_dir = current_dir

                                            if success and dest[-1] in temp_dir['contents']:
                                                output = '\r\n' + temp_dir['contents'][dest[-1]]['contents']
                                            else:
                                                output = '\r\n' + (f'File {args} not found')
                                        case 'cp':
                                            output = ''
                                            split_args = args.split()
                                            if len(split_args) != 2:
                                                output = '\r\n' + ('As this is a rudimentary file system, tags and arguments not in the form source.txt destination.txt for cp are not supported')
                                                continue
                                            if not split_args[0].endswith('.txt') or not split_args[1].endswith('.txt'):
                                                output = '\r\n' + ('Unknown file extension')
                                                continue
                                            src = split_args[0].split('/')
                                            src_path = src[:-1]
                                            if src_path:
                                                src_dir, src_path, src_success = traverse(src_path)
                                            else:
                                                src_success = True
                                                src_dir = current_dir
                                            
                                            dst = split_args[1].split('/')
                                            dst_path = dst[:-1]
                                            if dst_path:
                                                dst_dir, dst_path, dst_success = traverse(dst_path)
                                            else:
                                                dst_success = True
                                                dst_dir = current_dir


                                            if src_success and dst_success:
                                                if not src[-1] in src_dir['contents']:
                                                    output = '\r\n' + (f'File {args} not found')
                                                dst_dir['contents'][dst[-1]] = src_dir['contents'][src[-1]]

                                                dst_dir['contents'][dst[-1]]['parent'] = dst_dir
                                            else:
                                                output = '\r\n' + ('Error with traversal')
                                        case _:
                                            output = '\r\n' + ('Unknown Command: ' + cmd + '. Try help')


                                    commands.append(char_buffer.strip())
                                    channel.send(output)
                                
                                path_str = '/'.join(current_path)
                                if not path_str:
                                    path_str = '/'
                                channel.send(f'\r\n{username}@honeypot:{path_str}$ ')
                                char_buffer = ''
                            
                            elif char == '\b' or char == '\x7f':
                                if char_buffer:
                                    char_buffer = char_buffer[:-1]
                                    channel.send('\b \b')
                            
                            elif char.isprintable():
                                char_buffer += char
                                channel.send(char)

                except (socket.timeout, EOFError) as e:
                    channel.close()
                    transport.close()
                    end_time = datetime.now()
                    logged_commands = '"' + ';'.join(commands) + '"'
                    log_entry = f'{session_id},{client_ip},{username},{start_time.isoformat(timespec='seconds')},{end_time.isoformat(timespec='seconds')},{logged_commands}\n'

                    try:
                        with open('logs.csv', 'a') as file:
                            file.write(log_entry)
                    except Exception as e:
                        print(f"Failed to write log: {e}")
                    print('EOFError')
                    break
        except Exception as e:
            print('Transport failed: ' + str(e))
            try:
                transport.close()
            except:
                pass
            return

# Allows command line access to this with arguments
parser = argparse.ArgumentParser(description='Creates a fake SSH server to')
parser.add_argument(
    '-p', '--port',
    help="Defines the TCP port that the honeypot ssh server will bind to. The default SSH port is 22, but the honeypot works on any port number. Must be an integer.",
    type=int,
    required=True,
    dest='port'
)

port = parser.parse_args().port
# The key does not matter, we just need one. 2048 length was what seems to be the prevailing length online
key=paramiko.RSAKey.generate(2048)



# Setting up the server

try:
    sock = socket.socket(socket.AF_INET)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', port))
except Exception as e:
    print('Bind failed: ' + str(e))
    exit(1)


session_id_counter = 0
session_id_lock = threading.Lock()

while True:
    try: 
        sock.listen(100)
        print('Listening...')
        client, addr = sock.accept()
        
        client_thread = threading.Thread(target=connect, args=(client, addr))
        client_thread.start()

    except socket.error as e: 
        print(f"Socket error, probably fine, ignore: {e}")
        continue     
    except KeyboardInterrupt:
        print('\nServer shutting down...')
        break
    except Exception as e:
        print('CRITICAL: Listening failed: ' + str(e))
        exit(1)