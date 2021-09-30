import pandas as pd
from product import Product as P
import product as p

'''index corresponds to graph_objects'''
CL_INDEX = 0
IIP3_INDEX = 1
LORF_ISO_INDEX = 2
LOIF_ISO_INDEX = 3
RFIF_ISO_INDEX = 4
IF_R_INDEX = 5
CLvLO_INDEX = 6
IIP3vLO_INDEX = 7

def load_specs():
    df = pd.read_excel('data/mixerexcels/mixerproductspecs.xlsx', sheet_name='Sheet1', index_col=0)

    datasheet = {}

    for id in df.index:
        sheet = {
            'id' : id,
            'model' : id,
            'excel' : df.at[id, 'excel'],
            'rf-low' : df.at[id, 'rf-low'],
            'rf-high' : df.at[id, 'rf-high'],
            'rf-high-b' : df.at[id, 'rf-high-b'],
            'lo-low' : df.at[id, 'lo-low'],
            'lo-high' : df.at[id, 'lo-high'],
            'lo-high-b' : df.at[id, 'lo-high-b'],
            'if-low' : df.at[id, 'if-low'],
            'if-high' : df.at[id, 'if-high'],
            'lodr-low' : df.at[id, 'lodr-low'],
            'lodr-high' : df.at[id, 'lodr-high'],
            'p1db' : df.at[id, 'p1db'],
        }
        datasheet[id] = sheet
    
    return datasheet

# Class for Mixers
class Mixer(P):

    def __init__(self, name):
        super().__init__(name)

        self.spreadsheet = 'data/mixerexcels/' + P.products[name]['excel'] + '.xlsx'
        P.data_sheets[self.spreadsheet] = {}

    def load_graph_data(self, graph):
        if graph in self.data: return
        if graph == P.graph_options[CL_INDEX]:
            self.loaddata(CL_INDEX, 10, 0)
        elif graph == P.graph_options[IIP3_INDEX]:
            self.loaddata(IIP3_INDEX, 10, 10)
        elif graph == P.graph_options[LORF_ISO_INDEX]:
            self.loaddata(LORF_ISO_INDEX, 10, 20)
        elif graph == P.graph_options[LOIF_ISO_INDEX]:
            self.loaddata(LOIF_ISO_INDEX, 20, 0)
        elif graph == P.graph_options[RFIF_ISO_INDEX]:
            self.loaddata(RFIF_ISO_INDEX, 20, 10)
        elif graph == P.graph_options[IF_R_INDEX]:
            self.loaddata(IF_R_INDEX, 20, 20)
        elif graph == P.graph_options[CLvLO_INDEX]:
            self.loaddata(CLvLO_INDEX, 30, 0)
        elif graph == P.graph_options[IIP3vLO_INDEX]:
            self.loaddata(IIP3vLO_INDEX, 30, 10)
        
    #load product data for graph
    def loaddata(self, index, row, col):
        if 'Mapping' in P.data_sheets[self.spreadsheet]:
            df = P.data_sheets[self.spreadsheet]['Mapping']
        else:
            df = pd.read_excel(self.spreadsheet, sheet_name='Mapping', header=None, na_filter=False)
            P.data_sheets[self.spreadsheet]['Mapping'] = df
        
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
            'Conversion Loss',
            'Input IP3',
            'LO to RF Isolation',
            'LO to IF Isolation',
            'RF to IF Isolation',
            'IF Response',
            'Conversion Loss vs. LO Power',
            'Input IP3 vs. LO Power',
            'Spectrum Analyzer',
            ]

        P.graph_labels = {
            P.graph_options[CL_INDEX] : {
                'xlabel' : 'RF Freq',
                'ylabel' : 'Conv. Loss',
                'xunit' : '(GHz)',
                'yunit' : '(dB)',
            },
            P.graph_options[IIP3_INDEX] : {
                'xlabel' : 'RF Freq',
                'ylabel' : 'Input IP3',
                'xunit' : '(GHz)',
                'yunit' : '(dBm)',
            },
            P.graph_options[IF_R_INDEX] : {
                'xlabel' : 'IF Freq',
                'ylabel' : 'Relative IF Response',
                'xunit' : '(GHz)',
                'yunit' : '(dB)',
            },
            P.graph_options[LORF_ISO_INDEX] : {
                'xlabel' : 'LO Freq',
                'ylabel' : 'LO-RF Isolation',
                'xunit' : '(GHz)',
                'yunit' : '(dB)',
            },
            P.graph_options[CLvLO_INDEX] : {
                'xlabel' : 'RF Freq',
                'ylabel' : 'Conv. Loss',
                'xunit' : '(GHz)',
                'yunit' : '(dB)',
            },
            P.graph_options[IIP3vLO_INDEX] : {
                'xlabel' : 'RF Freq',
                'ylabel' : 'Input IP3',
                'xunit' : '(GHz)',
                'yunit' : '(dBm)',
            },
            P.graph_options[LOIF_ISO_INDEX] : {
                'xlabel' : 'LO Freq',
                'ylabel' : 'LO-IF Isolation',
                'xunit' : '(GHz)',
                'yunit' : '(dB)',
            },
            P.graph_options[RFIF_ISO_INDEX] : {
                'xlabel' : 'RF Freq',
                'ylabel' : 'RF-IF Isolation',
                'xunit' : '(GHz)',
                'yunit' : '(dB)',
            },   
        }  

        P.products = load_specs()


