import os, sys, re
from win32com.client import Dispatch

def ReadFile( name ):
    file = open( name, 'r' )
    data = file.read()
    file.close()
    return data

class Timing:
    def __init__(self, name, count, time, average):
        self.mName = name
        self.mCount = count
        self.mTime = time
        if not average:
            self.mAverage = 0
        else:
            self.mAverage = average
        
class Columns:
    def __init__(self):
        self.mName = 0
        self.mCount = 0
        self.mTime = 0
        self.mAverage = 0
        
    def Update(self, timing):
        self.mName = max(self.mName, len(timing.mName))
        self.mCount = max(self.mCount, len('%d' % timing.mCount))
        self.mTime = max(self.mTime, len('%0.3f' % timing.mTime))
        self.mAverage = max(self.mAverage, len('%0.6f' % timing.mAverage))        

class Timings:
    def __init__(self, title, columns):
        self.mTitle = title
        self.mTimings = []
        self.mColumns = columns
        
    def AddItem(self, name, count, time, average):
        if name.lower() != 'app total':
            timing = Timing(name, count, time, average)        
            self.mColumns.Update(timing)
            self.mTimings.append(timing)
        
    def __str__(self):
        namelen = self.mColumns.mName
        countlen = self.mColumns.mCount
        timelen = self.mColumns.mTime
        averagelen = self.mColumns.mAverage
            
        str = '%s\n' % self.mTitle
        for timing in self.mTimings:
            name_column = namelen - len(timing.mName)
            count_column = countlen - len('%d' % timing.mCount)
            time_len = timelen - len('%0.3f' % timing.mTime)
            average_len = averagelen - len('%0.6f' % timing.mAverage)
            str += timing.mName + ' ' * name_column
            str += ' ' * count_column + '  %d' % timing.mCount
            str += ' ' * time_len + '  %0.3f' % timing.mTime
            str += ' ' * average_len + '  %0.6f\n' % timing.mAverage
        return str

def SaveSpreadSheet(name, timings):
    if os.path.isfile(name):
        os.remove(name)
        
    excel = Dispatch("Excel.Application")
    excel.Visible = 0
    excel.Workbooks.Add()
    
    row = 1
    for i in range( len(timings) ):
        excel.ActiveSheet.Cells(row,1).Value = timings[i].mTitle
        row += 1
        items = timings[i].mTimings
        for j in range( len(items) ):
            excel.ActiveSheet.Cells(row,1).Value = '%s' % items[j].mName
            excel.ActiveSheet.Cells(row,2).Value = '%d' % items[j].mCount
            excel.ActiveSheet.Cells(row,3).Value = '%0.3f' % items[j].mTime
            excel.ActiveSheet.Cells(row,4).Value = '%0.6f' % items[j].mAverage
            row += 1
        row += 2
        
    excel.ActiveWorkbook.SaveAs(name)
    excel.ActiveWorkbook.Close(SaveChanges=0)
    excel.Quit()
    del excel

if __name__ == '__main__':
    timing_data_pattern = 'Context: TIMING : INFO\n(?P<name>[^\n]+).*?TimingData'
    timing_data_regex = re.compile(timing_data_pattern, re.S)
    timing_item_pattern = '^ *(?P<name>.+): *(?P<count>[\d]+) *(?P<total>\d+\.\d+)(?: *(?P<average>\d+\.\d+))? *$'
    timing_item_regex = re.compile(timing_item_pattern, re.M)
    
    data = ReadFile( 'd:\\SmeGuiDebug.log' )
    timings = []
    index = 0
    columns = Columns()
    for i in timing_data_regex.finditer(data):
        timings.append( Timings(i.group('name'), columns) )
        index += 1
        start = i.end()
        match = re.search( '\n\n', data[start:] )
        end = start + match.start()
        for j in timing_item_regex.finditer( data[start : end] ):
            name = j.group('name').strip()
            count = int( j.group('count').strip() )
            total = float( j.group('total').strip() )
            average = None
            if j.group('average'):
                average = float( j.group('average').strip() )
            timings[index - 1].AddItem(name, count, total, average)

    SaveSpreadSheet(os.path.abspath(sys.argv[1]), timings)
