import pandas as pd

'''Marki colors for line plot colors'''
LINE_COLORS = [
    '#724993',  #purple
    '#7FB539',  #green
    '#008BC4',  #blue
    '#EBEB7C',  #yellow-green
    '#00A6A6',  #teal
]

DEBUG = False

class Product:
    graph_options = None
    graph_labels = None
    products = None
    data_sheets = {}

    def __init__(self, name):
        self.name = name
        self.datasheet = 'https://www.markimicrowave.com/Assets/DataSheets/' + name + '.pdf'

        self.color = None
    
        self.data = {}
        self.linekeys = {}

    # get object's column info
    def get_col_data(self):
        return Product.products[self.name]

    #Get data to plot graph
    def getdata(self, graph, d=None):
        if graph not in self.data:
            self.load_graph_data(graph)
        if d == None:
            return self.data[graph]
        return self.data[graph][d]

    #Get lables for ploted lines
    def getlinekeys(self, graph):
        if graph not in self.data:
            self.load_graph_data(graph)
        return self.linekeys[graph]

    #sets color of product's graph plots
    def set_color(self):
        self.color = line_color()

    # get min/max/med of a graph
    def getystats(self, xlow, xhigh, graph):
        if graph not in self.data:
            self.load_graph_data(graph)
        min, max, med = None, None, None
        graph_data = self.data[graph]
        if len(graph_data) == 0: return None, None, None, None, None, None
        dict = graph_data[list(graph_data.keys())[0]]
        x = dict['xdata']
        y = dict['ydata']
        data_list = []
        for i in range(len(x)):
            if xlow <= x[i] <= xhigh:
                data_list.append(y[i])
            elif x[i] > xhigh:
                break
        if len(data_list) == 0: return None, None, None, None, None, None
        sorted_list = sort_list(data_list)
        min = sorted_list[0]
        max = sorted_list[-1]
        med = get_median(sorted_list)
        
        if len(graph_data) == 2:
            bmin, bmax, bmed = None, None, None
            dict = graph_data[list(graph_data.keys())[1]]
            x = dict['xdata']
            y = dict['ydata']
            data_list = []
            for i in range(len(x)):
                if xlow <= x[i] <= xhigh:
                    data_list.append(y[i])
                elif x[i] > xhigh:
                    break
            sorted_list = sort_list(data_list)
            bmin = sorted_list[0]
            bmax = sorted_list[-1]
            bmed = get_median(sorted_list)
            return min,max,med,bmin,bmax,bmed
        else:
            return min,max,med,None,None,None


'''helper functions'''

#uses merge sort (recursive)
def sort_list(list):
    if len(list) == 0 or len(list) == 1:
        return list
    L1 = sort_list(list[:int(len(list)/2)])
    L2 = sort_list(list[int(len(list)/2):])
    sorted = []
    while (len(L1) > 0):
        if len(L2) == 0:
            for i in range(len(L1)):
                sorted.append(L1.pop(0))
        elif L1[0] < L2[0]:
            sorted.append(L1.pop(0))
        else:
            sorted.append(L2.pop(0))
    if len(L2) > 0:
        for i in range(len(L2)):
            sorted.append(L2.pop(0))
    return sorted

def get_median(list):
    if len(list) % 2 == 0:
        med = ( list[int(len(list) / 2)] + list[int(len(list) / 2) - 1] ) / 2
    else:
        med = list[int(len(list) / 2)]
    return med     

# cycles through colors used for plot lines
def line_color():
    global LINE_COLORS
    color = LINE_COLORS.pop(0)
    LINE_COLORS.append(color)
    return color

#translate a set of letter(s) into an excel's column number
def column_index(c):
    if len(c) == 1: return char_value(c) - 1
    total = 0
    for i in range(len(c)):
        index_c = c[i]
        value_c = char_value(index_c)
        total += pow(26, len(c) - 1 - i) * value_c
    return total - 1

#numerical value of a letter
def char_value(c):
    return ord(c.upper()) - ord('@')

# use a specific format on the spreadsheet to know where the requested data will be
def get_cell_parameters(df,row,col):
    label = df.iloc[row,col]
    xsheet = df.iloc[row,col+1]
    xaxis = df.iloc[row,col+2]
    xmin = df.iloc[row,col+3]
    xmax = df.iloc[row,col+4]
    ysheet = df.iloc[row,col+5]
    yaxis = df.iloc[row,col+6]
    ymin = df.iloc[row,col+7]
    ymax = df.iloc[row,col+8]
    return label, xsheet, xaxis, xmin, xmax, ysheet, yaxis, ymin, ymax

#Get cells from excel sheet
def getcelldata(i_graph, excel, xsheet, xaxis, xmin, xmax, ysheet, yaxis, ymin, ymax):
    if DEBUG: print(excel, xsheet, xaxis, xmin, xmax, ysheet, yaxis, ymin, ymax)
    if xsheet in Product.data_sheets[excel]:
        df = Product.data_sheets[excel][xsheet]
        if DEBUG: print('sheet1 retrieved')
    else:
        df = pd.read_excel(excel, sheet_name=xsheet, header=None, na_filter=False)
        Product.data_sheets[excel][xsheet] = df
        if DEBUG: print('sheet1 read')
    if ysheet in Product.data_sheets[excel]:
        df2 = Product.data_sheets[excel][ysheet]
        if DEBUG: print('sheet2 retrieved')
    else: 
        df2 = pd.read_excel(excel, sheet_name=ysheet, header=None, na_filter=False)
        Product.data_sheets[excel][ysheet] = df2
        if DEBUG: print('sheet2 read')

    data = {'xdata' 
                : list(df.iloc[xmin-1:xmax,column_index(xaxis)]), 
            'ydata'
                : list(df2.iloc[ymin-1:ymax,column_index(yaxis)]), }
    
    return data


