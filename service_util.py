#!/usr/bin/env python
import os
import sys
import fnmatch
import win32api
import win32service


def GetCurrentStateStr(state):
    if state == win32service.SERVICE_CONTINUE_PENDING:
        return ('SERVICE_CONTINUE_PENDING', 'The service is about to continue.')
    elif state == win32service.SERVICE_PAUSE_PENDING:
        return ('SERVICE_PAUSE_PENDING', 'The service is pausing.')
    elif state == win32service.SERVICE_PAUSED:
        return ('SERVICE_PAUSED', 'The service is paused.')
    elif state == win32service.SERVICE_RUNNING:
        return ('SERVICE_RUNNING', 'The service is running.')
    elif state == win32service.SERVICE_START_PENDING:
        return ('SERVICE_START_PENDING', 'The service is starting.')
    elif state == win32service.SERVICE_STOP_PENDING:
        return ('SERVICE_STOP_PENDING', 'The service is stopping.')
    elif state == win32service.SERVICE_STOPPED:
        return ('SERVICE_STOPPED', 'The service has stopped.')
    else:
        return ('SERVICE_UNKNOWN', 'Unknown service state')


def StopService(serviceName):
    retval = False
    manager = None
    service = None
    try:
        manager = win32service.OpenSCManager('localhost', 'ServicesActive', win32service.SC_MANAGER_CONNECT)
        service = win32service.OpenService(manager, serviceName, win32service.SERVICE_STOP | win32service.SERVICE_QUERY_STATUS)
        status = win32service.QueryServiceStatus(service)
        if status[1] == win32service.SERVICE_STOP_PENDING or status[1] == win32service.SERVICE_STOPPED:
            print(('Service %s is already stopped (%s)' % (serviceName, GetCurrentStateStr(state)[0])))
        else:
            print(('Stopping service %s' % serviceName))
            if win32service.ControlService(service, win32service.SERVICE_CONTROL_STOP):
                win32api.Sleep(1000)
                stopped = False
                slept = 0
                while not stopped and slept < 5:
                    status = win32service.QueryServiceStatus(service)
                    if status[1] == win32service.SERVICE_STOPPED:
                        stopped = True
                    else:
                        win32api.Sleep(500)
                        slept += 1
        retval = True
    except Exception as inst:
        if len( inst.args ) == 3:
            number = inst.args[0]
            function = inst.args[1]
            message = inst.args[2]
            print(('ERROR stopping service: %#08x (%s): %s' % ( number, function, message )))
        else:
            print(('ERROR stopping service: %s' % inst))
    finally:
        if service:
            win32service.CloseServiceHandle(service)
        if manager:
            win32service.CloseServiceHandle(manager)
    return retval

    
def StartService(serviceName):
    retval = False
    manager = None
    service = None
    try:
        manager = win32service.OpenSCManager('localhost', 'ServicesActive', win32service.SC_MANAGER_CONNECT)
        service = win32service.OpenService(manager, serviceName, win32service.SERVICE_START | win32service.SERVICE_QUERY_STATUS)
        status = win32service.QueryServiceStatus(service)
        if status[1] == win32service.SERVICE_RUNNING or status[1] == win32service.SERVICE_START_PENDING:
            print(('Service %s is already started (%s)' % (serviceName, GetCurrentStateStr(state)[0])))
        else:
            print(('Starting service %s' % serviceName))
            if win32service.StartService(service, None):
                started = False
                slept = 0
                while not started and slept < 5:
                    status = win32service.QueryServiceStatus(service)
                    if status[1] == win32service.SERVICE_RUNNING:
                        started = True
                    else:
                        win32api.Sleep(1000)
                        slept += 1
        retval = True
    except Exception as inst:
        if len( inst.args ) == 3:
            number = inst.args[0]
            function = inst.args[1]
            message = inst.args[2]
            print(('ERROR starting service: %#08x (%s): %s' % ( number, function, message )))
        else:
            print(('ERROR starting service: %s' % inst))
    finally:
        if service:
            win32service.CloseServiceHandle(service)
        if manager:
            win32service.CloseServiceHandle(manager)
    return retval


def ListServices(filter):
    manager = None
    try:
        manager = win32service.OpenSCManager('localhost', None, win32service.SC_MANAGER_ENUMERATE_SERVICE)
        services = list(win32service.EnumServicesStatus(manager, win32service.SERVICE_WIN32))
        
        nameLen = max([len(service[0]) for service in services])
        displayLen = max([len(service[1]) for service in services]) + 2
        services.sort( cmp=lambda x,y: cmp(x[0].lower(), y[0].lower()) )
        format = '%-' + str(nameLen) + 's %-' + str(displayLen) + 's : %s'
        
        for service in services:
            if filter and not fnmatch.fnmatch(service[0], filter):
                continue
            status = GetCurrentStateStr(service[2][1])
            print((format % (service[0], '"' + service[1] + '"', status[0])))
    except Exception as inst:
        if len( inst.args ) == 3:
            number = inst.args[0]
            function = inst.args[1]
            message = inst.args[2]
            print(('ERROR enumerating services: %#08x (%s): %s' % ( number, function, message )))
        else:
            print(('ERROR enumerating services: %s' % inst))
    finally:
        if manager:
            win32service.CloseServiceHandle(manager)


def ParseArgs(args):
    startName = None
    stopName = None
    listServices = False
    listFilter = None
    helpStr = 'Invalid command line. Specify -start <service> and/or -stop <service> or -list'
    
    i = 0
    count = len(args)
    while i < count:
        arg = args[i]
        if args[i].lower() == '-start' and i + 1 < count:
            i += 1
            startName = args[i]
        elif args[i].lower() == '-stop' and i + 1 < count:
            i += 1
            stopName = args[i]
        elif args[i].lower() == '-list':
            listServices = True
            if i + 1 < count and not args[i + 1].startswith('-'):
                i += 1
                listFilter = args[i]
        else:
            print(helpStr)
            sys.exit(1)
        i += 1
            
    if not startName and not stopName and not listServices:
        print(helpStr)
        sys.exit(1)
        
    return startName, stopName, listServices, listFilter


def main(args):
    retval = 0
    startName, stopName, listServices, listFilter = ParseArgs(args)
    if listServices:
        ListServices(listFilter)
    if startName:
        retval = StartService(startName)
    if stopName:
        retval = StopService(stopName)
    return retval


if __name__ == '__main__':
    sys.exit( main(sys.argv[1:]) )
