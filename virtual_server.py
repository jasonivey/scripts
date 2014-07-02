import win32com.client

if __name__ == '__main__':
    vs = win32com.client.Dispatch('VirtualServer.Application')
    vs.get_UpTime()