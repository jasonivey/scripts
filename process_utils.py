import os
import sys
import exceptions
import optparse
import win32process
import win32con
import win32api
import win32security

def PrintHeader( file ):
    file.write( 'ProcessUtils.py - Version 0.11\n' )

def PrintHelp():
    print('\nList all processess and the memory usage or kill a process.')
    print('\nUsage:')
    print('\tProcessUtil.py [<PID|Process Name>...]')
    
    print('\n\tThe process name is the EXE name with or without an')
    print('\textension and may include the full path to qualify it.')
    print('\tIf no processes are given the script will simply list')
    print('\tall the process names and thier associated PID.')

    print('\nUsage to kill a processes:')
    print('\tProcessUtil.py -k <PID|Process Name>...')
    print('\tNote: If the process name is used the script will kill')
    print('\tall matching processes of that same name.')

    #Code snippet which supposedly sets the security up to DebugPrivilege's but still didn't help opening all processes on the system
    #try:    
    #    token = win32security.OpenProcessToken( win32api.GetCurrentProcess(), win32con.TOKEN_ALL_ACCESS )
    #    #win32api.CloseHandle( token )
    #    #token = win32security.OpenThreadToken( win32api.GetCurrentThread(), win32con.TOKEN_ADJUST_PRIVILEGES | win32con.TOKEN_QUERY, 1 )
    #    value = win32security.LookupPrivilegeValue( 'DEV-JASONI', 'SeDebugPrivilege' )
    #    
    #    newPrivileges = [( value, 2 )]
    #    oldPrivileges = win32security.AdjustTokenPrivileges( token, 0, newPrivileges )
    #    #if len( oldPrivileges ) < 1:
    #    #    oldPrivileges = [( value, 2 )]
    #    #else:
    #    #    oldPrivileges[0][1] |= 2;
    #    #newPrivileges = win32security.AdjustTokenPrivileges( token, 0, oldPrivileges )
    #    
    #except Exception, inst:
    #    if len( inst.args ) == 3:
    #        number = inst.args[0]
    #        function = inst.args[1]
    #        message = inst.args[2]
    #        print 'ERROR %#08x (%s): %s' % ( number, function, message )
    #    else:
    #        print inst

def GetLineDivider():
    return '-' * 45 + '\n'


class Process:
    '''Structure to encapsulate a running process.'''
    def __init__(self, pid = -1, name = ''):
        self.PID = pid
        self.Name = name

    def TerminateProcess(self):
        retstr = ''
        rights = win32con.PROCESS_ALL_ACCESS
        handle = None
        try:
            handle = None
            handle = win32api.OpenProcess( rights, 0, self.PID )
            exit_code = win32process.TerminateProcess(handle, 0)
                
            retstr += '\n' + GetLineDivider()
            retstr += 'TERMINATING PROCESS\n'
            retstr += 'Process Name                  : %10s\n' % self.Name
            retstr += 'Process ID                    : %10d\n' % self.PID
            retstr += 'Success/Failure               : %10s\n' % ('SUCCEEDED' if exit_code != 0 else 'FAILED')
        except Exception as inst:
            if len( inst.args ) == 3:
                number = inst.args[0]
                function = inst.args[1]
                message = inst.args[2]
                retstr += 'ERROR %#08x (%s): %s\n' % ( number, function, message )
            else:
                retstr += str(inst) + '\n'
        finally:
            if handle:
                win32api.CloseHandle(handle)
    
        return retstr + '\n' + GetLineDivider()

    def GetStatistics(self):
        retstr = ''
        rights = win32con.PROCESS_ALL_ACCESS
        #totalPeak = 0
        #totalWorking = 0
        
        handle = None
        try:
            handle = None
            handle = win32api.OpenProcess( rights, 0, self.PID )
            memory = win32process.GetProcessMemoryInfo( handle )
                
            retstr += '\n' + GetLineDivider()
            retstr += 'Process Name                  : %10s\n' % self.Name
            retstr += 'Process ID                    : %10d\n' % self.PID
            
            index = 0
            for i in list(memory.keys()):
                if memory[i] < 0:
                    memory[i] = 0
                if index < 2:
                    retstr += '%-30s: %10u\n' % ( i, memory[i] )
                else:
                    retstr += '%-30s: %10u KB\n' % ( i, memory[i] / 1024 )
                index = index + 1
                
            #totalPeak = totalPeak + ( memory["PeakWorkingSetSize"] / 1024 )
            #totalWorking = totalWorking + ( memory["WorkingSetSize"] / 1024 )
        except Exception as inst:
            if len( inst.args ) == 3:
                number = inst.args[0]
                function = inst.args[1]
                message = inst.args[2]
                retstr += 'ERROR %#08x (%s): %s\n' % ( number, function, message )
            else:
                retstr += str(inst) + '\n'
        finally:
            if handle:
                win32api.CloseHandle(handle)
    
        return retstr + '\n' + GetLineDivider()
        #retstr += 'Total Peak Working Set Size   : %10s KB\n' % totalPeak
        #retstr += 'Total Working Set Size        : %10s KB\n' % totalWorking

    def __cmp__(self, other):
        #return self.PID - other.PID
        return cmp( os.path.basename( self.Name ).lower(), os.path.basename( other.Name ).lower() )

    def __str__(self):
        return ('%-' + str( 29 ) + 's : %10s\n') % ( os.path.basename(self.Name), self.PID )


class Processes:
    '''Structure to encapsulate all the running processes on a computer.'''
    def __init__(self):
        self.ProcessIds = list(win32process.EnumProcesses())
        self.FailedOpen = 0
        self.FailedName = 0
        self.Processes = {}
        self._FindAllProcesses()

    def _FindAllProcesses(self):
        #rights = win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ | win32con.PROCESS_VM_WRITE
        rights = win32con.PROCESS_ALL_ACCESS

        for id in self.ProcessIds:
            handle = None
            try:
                handle = win32api.OpenProcess( rights, 0, id )
                name = win32process.GetModuleFileNameEx( handle, 0 )

                proc = Process( id, name )
                assert(id not in self.Processes)
                self.Processes[id] = proc
            except Exception as inst:
                if len( inst.args ) > 1:
                    if inst.args[1] == 'OpenProcess':
                        self.FailedOpen = self.FailedOpen + 1
                    else:
                        self.FailedName = self.FailedName + 1
            finally:
                if handle:
                    win32api.CloseHandle(handle)

    def GetProcess(self, name):
        if name == 'all':
            return list(self.Processes.values())

        matching_processes = []
        for process in list(self.Processes.values()):
            if os.path.basename(process.Name).lower() == os.path.basename(name).lower() or \
               os.path.splitext(os.path.basename(process.Name))[0].lower() == os.path.splitext(os.path.basename(name))[0].lower():
                matching_processes.append(process)

        if len(matching_processes) == 0:
            raise exceptions.RuntimeError('Unable to find process %s' % name)

        # If we only found one process without the fully qualified directory name then return that
        if len(matching_processes) == 1:
            return matching_processes
        
        # Otherwise look for the the process looking for the fully qualified directory name
        original_matching_processes = matching_processes
        matching_processes = []
        for process in list(self.Processes.values()):
            if process.Name.lower() == name.lower():
                matching_processes.append(process)

        if len(matching_processes) != 0:
            # If we found one or more matching the fully qualified directory name then return that set
            return matching_processes
        else:
            # If we didn't find any with the fully qualified directory name then return the original set
            return original_matching_processes

    def GetProccessIds(self, process_id):
        pids = []
        if isinstance(process_id, str):
            try:
                matching_processes = self.GetProcess(process_id)
                for process in matching_processes:
                    pids.append(process.PID)
            except RuntimeError as inst:
                print(inst)
        else:
            if process_id not in self.Processes and process_id in self.ProcessIds:
                print(('ERROR: The process (%d) exists but we could not open a handle to it!' % process_id))
            elif process_id not in self.Processes:
                print(('ERROR: The specified PID (%d) does not exist amoung this list of processes!' % process_id))
            else:
                pids.append(process_id)
        return pids

    def __str__(self):
        processes = list(self.Processes.values())
        processes.sort()

        retstr = '\n         Process Name         :       PID\n'
        retstr += GetLineDivider()

        for process in processes:
            retstr += str(process)

        retstr += '\n' + GetLineDivider()
        retstr += 'Total Processes               : %10s\n' % len( self.ProcessIds )
        retstr += 'Failed Opening                : %10s\n' % self.FailedOpen
        retstr += 'Failed Retrieving File Names  : %10s\n' % self.FailedName
        retstr += 'Total Success                 : %10s\n' % ( len( self.ProcessIds ) - self.FailedOpen - self.FailedName )
        retstr += 'Total Failed                  : %10s\n\n' % ( self.FailedOpen + self.FailedName )
        return retstr

def GetArgAsInt(arg):
    retval = None
    try:
        retval = int(arg)
    except:
        retval = arg
    return retval
    
def ParseArgs(args):
    if len(args) == 0:
        return [], []
    
    detail_processes = []
    process_ids_to_kill = []
    i = 0
    while i < len(args):
        if (args[i].startswith('-') or args[i].startswith('/')) and args[i][1:].lower().startswith('k') and i + 1 < len(args):
            process_ids_to_kill.append(GetArgAsInt(args[i + 1]))
            i = i + 1
        elif (args[i].startswith('-') or args[i].startswith('/')) and args[i][1:].lower().startswith('h'):
            PrintHelp()
            sys.exit(1)
        else:
            detail_processes.append(GetArgAsInt(args[i]))
        i = i + 1

    return detail_processes, process_ids_to_kill

if __name__ == '__main__':
    PrintHeader( sys.stdout )

    detail_processes, process_ids_to_kill = ParseArgs(sys.argv[1:])

    processes = Processes()
    print(processes)
    
    for process_id in detail_processes:
        pids = processes.GetProccessIds(process_id)
        for pid in pids:
            print((processes.Processes[pid].GetStatistics()))

    for process_id in process_ids_to_kill:
        pids = processes.GetProccessIds(process_id)
        for pid in pids:
            print((processes.Processes[pid].TerminateProcess()))
