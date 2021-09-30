import pandas as pd
from passive import Passive, WrongPassiveException
from product import Product as P

'''index corresponds to graph_objects'''
RL = 'Return Loss'
IL = 'Insertion Loss'
DIR = 'Directivity'
CR = 'Coupled Ratio'

def load_specs():
    df = pd.read_excel('data/coupler-files/couplerproductspecs.xlsx', sheet_name='Sheet1', index_col=0)

    datasheet = {}

    for id in df.index:
        sheet = {
            'id' : id,
            'model' : id,
            'file' : df.at[id, 'file'],
            'freq-low' : df.at[id, 'freq-low'],
            'freq-high' : df.at[id, 'freq-high'],
            'vswr' : df.at[id, 'vswr'],
            'mn-coup' : df.at[id, 'mn-coup'],
            'direct' : df.at[id, 'direct'],
        }
        datasheet[id] = sheet
    
    return datasheet

class Coupler(Passive):

    def __init__(self, name):
        Passive.__init__(self, name, 'coupler')

        self.coupledport = None
        self.inport = None
        self.outport = None
        self.set_port_config()

    def set_port_config(self):
        comments = self.touchstone.get_comments()
        comment_lines = comments.split('\n')
        is_coupler = False
        pc = ''
        for line in comment_lines:
            if 'Coupler' in line:
                is_coupler = True
            l = line.lower()
            if 'input' in l or 'output' in l or 'coupled' in l:
                pc = pc + l
        if not is_coupler:
            print(self.name)
            raise WrongPassiveException
        port_configs = pc.lower()
        coupled, input, output = None, None, None

        coupled_split = port_configs.split('coupled')
        if '3' in coupled_split[0]:
            coupled = '3'
        elif '2' in coupled_split[0]:
            coupled = '2'
        elif '1' in coupled_split[0]:
            coupled = '1'
        
        input_split = port_configs.split('input')
        if '3' in input_split[0]:
            input = '3'
        elif '2' in input_split[0]:
            input = '2'
        elif '1' in input_split[0]:
            input = '1'

        output_split = port_configs.split('output')
        if '3' in output_split[0]:
            output = '3'
        elif '2' in output_split[0]:
            output = '2'
        elif '1' in output_split[0]:
            output = '1'
        
        self.coupledport = coupled
        self.inport = input
        self.outport = output

    def load_graph_data(self, graph):
        if graph in self.data: return
        if graph == RL:
            self.get_returnloss_data()
        elif graph == IL:
            self.get_insertionloss_data()
        elif graph == DIR:
            self.get_directivity_data()
        elif graph == CR:
            self.get_coupledratio_data()

    def load_class_vars():
        P.graph_options = [RL,IL,DIR,CR]

        P.graph_labels = {
            RL : {
                'xlabel': 'Frequency',
                'xunit': '(GHz)',
                'ylabel': 'Return Loss',
                'yunit': '(dB)',
            },
            IL : {
                'xlabel': 'Frequency',
                'xunit': '(GHz)',
                'ylabel': 'Insertion Loss',
                'yunit': '(dB)',
            },
            DIR : {
                'xlabel': 'Frequency',
                'xunit': '(GHz)',
                'ylabel': 'Directivity',
                'yunit': '(dB)',
            },
            CR : {
                'xlabel': 'Frequency',
                'xunit': '(GHz)',
                'ylabel': 'Coupled Ratio',
                'yunit': '(dB)',
            },
        }  

        P.products = load_specs()

    def get_returnloss_data(self):
        data = dict()
        xdata = self.get_frequency_data()
        data['Coupled'] = {'xdata' : xdata,
                            'ydata' : self.touchstone_data['S' + self.coupledport + self.coupledport + 'DB']}
        data['Input'] = {'xdata' : xdata,
                            'ydata' : self.touchstone_data['S' + self.inport + self.inport + 'DB']}
        data['Output'] = {'xdata' : xdata,
                            'ydata' : self.touchstone_data['S' + self.outport + self.outport + 'DB']}
        
        self.data[RL] = data
        self.linekeys[RL] = ['Coupled', 'Input', 'Output']

    def get_insertionloss_data(self):
        data = dict()
        xdata = self.get_frequency_data()
        data[IL] = {'xdata' : xdata,
                    'ydata' : self.touchstone_data['S' + self.outport + self.inport + 'DB']}
        self.data[IL] = data
        self.linekeys[IL] = [IL]

    def get_directivity_data(self):
        coupling_ratio = self.touchstone_data['S' + self.coupledport + self.inport + 'DB']
        isolation = self.touchstone_data['S' + self.coupledport + self.outport + 'DB']
        directivity = []
        for i in range(len(coupling_ratio)):
            directivity.append((coupling_ratio[i] - isolation[i]) * -1)

        data = dict()
        data[DIR] = {'xdata' : self.get_frequency_data(),
                        'ydata' : directivity}
        self.data[DIR] = data
        self.linekeys[DIR] = [DIR]

    def get_coupledratio_data(self):
        coupled_il = self.touchstone_data['S' + self.coupledport + self.inport + 'DB']
        insertion_loss = self.touchstone_data['S' + self.outport + self.inport + 'DB']
        coupled_ratio = []
        for i in range(len(coupled_il)):
            coupled_ratio.append((coupled_il[i] - insertion_loss[i]))
        
        data = dict()
        data[CR] = {'xdata' : self.get_frequency_data(),
                        'ydata' : coupled_ratio}
        self.data[CR] = data
        self.linekeys[CR] = [CR]



