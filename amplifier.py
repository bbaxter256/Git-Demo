import pandas as pd
from product import Product as P
import product as p

'''index corresponds to graph_objects'''
OCP_INDEX = 0
SSG_INDEX = 1
NF_INDEX = 2
OIP3_INDEX = 3
IRL_INDEX = 4
ORL_INDEX = 5
RI_INDEX = 6

def load_specs():
    df = pd.read_excel('data/ampexcels/ampproductspecs.xlsx', sheet_name='Sheet1', index_col=0)

    datasheet = {}

    for id in df.index:
        sheet = {
            'id' : id,
            'model' : id,
            'excel' : df.at[id, 'excel'],
            'freq-low' : df.at[id, 'freq-low'],
            'freq-high' : df.at[id, 'freq-high'],
            'ssg' : df.at[id, 'ssg'],
            'sop' : df.at[id, 'sop'],
        }
        datasheet[id] = sheet
    
    return datasheet


class Amplifier(P):

    def __init__(self, name):
        super().__init__(name)

        self.spreadsheet = 'data/ampexcels/' + P.products[name]['excel'] + '.xlsx'
        P.data_sheets[self.spreadsheet] = {}

    def load_graph_data(self, graph):
        if graph in self.data: return
        if graph == P.graph_options[OCP_INDEX]:
            self.loaddata(OCP_INDEX, 10, 0)
        elif graph == P.graph_options[SSG_INDEX]:
            self.loaddata(SSG_INDEX, 10, 10)
        elif graph == P.graph_options[NF_INDEX]:
            self.loaddata(NF_INDEX, 10, 20)
        elif graph == P.graph_options[OIP3_INDEX]:
            self.loaddata(OIP3_INDEX, 20, 0)
        elif graph == P.graph_options[IRL_INDEX]:
            self.loaddata(IRL_INDEX, 20, 10)
        elif graph == P.graph_options[ORL_INDEX]:
            self.loaddata(ORL_INDEX, 20, 20)
        elif graph == P.graph_options[RI_INDEX]:
            self.loaddata(RI_INDEX, 30, 0)
        
    #load product data for graph
    def loaddata(self, index, row, col):
        if 'MappingLODr' in P.data_sheets[self.spreadsheet]:
            df = P.data_sheets[self.spreadsheet]['MappingLaAm']
        else:
            df = pd.read_excel(self.spreadsheet, sheet_name='MappingLaAm', header=None, na_filter=False)
            P.data_sheets[self.spreadsheet]['MappingLaAm'] = df
        
        self.data[P.graph_options[index]] = {}
        self.linekeys[P.graph_options[index]] = []

        numlines = df.iloc[row-2,col+1]
        for i in range(numlines):
            label, xsheet, xaxis, xmin, xmax, ysheet, yaxis, ymin, ymax = p.get_cell_parameters(df,row+i,col)
            if type(label) == type('string'):
                data = p.getcelldata(index, self.spreadsheet, xsheet, xaxis, xmin, xmax, ysheet, yaxis, ymin, ymax)
                self.data[P.graph_options[index]][label] = data
                self.linekeys[P.graph_options[index]].append(label)

    def load_class_vars():
        P.graph_options = [
                'Output Compression Points',
                'Small Signal Gain',
                'Noise Figure',
                'Output IP3',
                'Input Return Loss',
                'Output Return Loss',
                'Reverse Isolation',
            ]

        P.graph_labels = {
            P.graph_options[OCP_INDEX] : {
                'xlabel' : 'Frequency',
                'ylabel' : 'Output Comp. Points',
                'xunit' : '(GHz)',
                'yunit' : '(dBm)',
            },
            P.graph_options[SSG_INDEX] : {
                'xlabel' : 'Frequency',
                'ylabel' : 'Sm. Signal Gain',
                'xunit' : '(GHz)',
                'yunit' : '(dB)',
            },
            P.graph_options[NF_INDEX] : {
                'xlabel' : 'Frequency',
                'ylabel' : 'Noise Figure',
                'xunit' : '(GHz)',
                'yunit' : '(dB)',
            },
            P.graph_options[OIP3_INDEX] : {
                'xlabel' : 'Frequency',
                'ylabel' : 'OIP3',
                'xunit' : '(GHz)',
                'yunit' : '(dBm)',
            },
            P.graph_options[IRL_INDEX] : {
                'xlabel' : 'Frequency',
                'ylabel' : 'Input Return Loss',
                'xunit' : '(GHz)',
                'yunit' : '(dB)',
            },
            P.graph_options[ORL_INDEX] : {
                'xlabel' : 'Frequency',
                'ylabel' : 'Output Return Loss',
                'xunit' : '(GHz)',
                'yunit' : '(dB)',
            },
            P.graph_options[RI_INDEX] : {
                'xlabel' : 'Frequency',
                'ylabel' : 'Reverse Isolation',
                'xunit' : '(GHz)',
                'yunit' : '(dB)',
            },
        }  

        P.products = load_specs()


