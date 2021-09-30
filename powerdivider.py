from numpy import DataSource
import pandas as pd
from passive import Passive, WrongPassiveException
from product import Product as P

'''index corresponds to graph_objects'''
RL = 'Return Loss'
IL = 'Insertion Loss'
ISO = 'Isolation'
AMP_B = 'Amplitude Balance'
PH_B = 'Phase Balance'

def load_specs():
    df = pd.read_excel('data/powdiv-files/powdivproductspecs.xlsx', sheet_name='Sheet1', index_col=0)

    datasheet = {}

    for id in df.index:
        sheet = {
            'id' : id,
            'model' : id,
            'file' : df.at[id, 'file'],
            'freq-low' : df.at[id, 'freq-low'],
            'freq-high' : df.at[id, 'freq-high'],
        }
        datasheet[id] = sheet
    
    return datasheet

class PowerDivider(Passive):

    def __init__(self, name):
        Passive.__init__(self, name, 'powdiv')

        self.commonport = None
        self.outport1 = None
        self.outport2 = None
        self.set_port_config()

    def set_port_config(self):
        comments = self.touchstone.get_comments()
        comment_lines = comments.split('\n')
        is_powdiv = False
        for line in comment_lines:
            if 'Power Divider' in line:
                is_powdiv = True
            if 'Port Configuration' in line:
                pc = line
        if not is_powdiv:
            raise WrongPassiveException
        port_configs = pc.split('\t')[1].lower()
        common, out1, out2 = None, None, None

        common_split = port_configs.split('common')
        if '3' in common_split[0]:
            common, out1, out2 = '3','1','2'
        elif '2' in common_split[0]:
            common, out1, out2 = '2','1','3'
        elif '1' in common_split[0]:
            common, out1, out2 = '1','2','3'
        self.commonport = common
        self.outport1 = out1
        self.outport2 = out2

    def load_graph_data(self, graph):
        if graph in self.data: return
        if graph == RL:
            self.get_returnloss_data()
        elif graph == IL:
            self.get_insertionloss_data()
        elif graph == ISO:
            self.get_isolation_data()
        elif graph == AMP_B:
            self.get_amplitudebal_data()
        elif graph == PH_B:
            self.get_phasebal_data()
            
    def load_class_vars():
        P.graph_options = [RL, IL, ISO, AMP_B, PH_B]

        P.graph_labels = {
            RL : {
                'xlabel' : 'Frequency',
                'ylabel' : 'Return Loss',
                'xunit' : '(GHz)',
                'yunit' : '(dB)',
            },
            IL : {
                'xlabel' : 'Frequency',
                'ylabel' : 'Insertion Loss',
                'xunit' : '(GHz)',
                'yunit' : '(dB)',
            },
            ISO : {
                'xlabel' : 'Frequency',
                'ylabel' : 'Isolation',
                'xunit' : '(GHz)',
                'yunit' : '(dB)',
            },
            AMP_B : {
                'xlabel' : 'Frequency',
                'ylabel' : 'Amplitude Bal',
                'xunit' : '(GHz)',
                'yunit' : '(cB)',
            },
            PH_B : {
                'xlabel' : 'Frequency',
                'ylabel' : 'Phase Bal',
                'xunit' : '(GHz)',
                'yunit' : '(degrees)',
            },
        }  

        P.products = load_specs()

    def get_returnloss_data(self):
        data = dict()
        xdata = self.get_frequency_data()
        data['Common'] = {'xdata' : xdata,
                        'ydata' : self.touchstone_data['S' + self.commonport + self.commonport + 'DB']}
        data['Out 1'] = {'xdata' : xdata,
                        'ydata' : self.touchstone_data['S' + self.outport1 + self.outport1 + 'DB']}
        data['Out 2'] = {'xdata' : xdata,
                        'ydata' : self.touchstone_data['S' + self.outport2 + self.outport2 + 'DB']}
       
        self.data[RL] = data 
        self.linekeys[RL] = ['Common', 'Out 1', 'Out 2']

    def get_insertionloss_data(self):
        data = dict()
        frequencydata = self.get_frequency_data()
        out1 = self.touchstone_data['S' + self.commonport + self.outport1 + 'DB']
        out2 = self.touchstone_data['S' + self.commonport + self.outport2 + 'DB']

        xdata1, ydata1 = self.handle_outliers(frequencydata, out1)
        xdata2, ydata2 = self.handle_outliers(frequencydata, out2)

        data['Out 1'] = {'xdata' : xdata1,
                        'ydata' : ydata1}
        data['Out 2'] = {'xdata' : xdata2,
                        'ydata' : ydata2}
        
        self.data[IL] = data
        self.linekeys[IL] = ['Out 1', 'Out 2']

    def get_isolation_data(self):
        data = dict()
        xdata = self.get_frequency_data()
        data[ISO] = {'xdata' : xdata, 
                    'ydata' : self.touchstone_data['S' + self.outport1 + self.outport2 + 'DB']}
        self.data[ISO] = data
        self.linekeys[ISO] = [ISO]

    def get_amplitudebal_data(self):
        out1 = self.touchstone_data['S' + self.commonport + self.outport1 + 'DB']
        out2 = self.touchstone_data['S' + self.commonport + self.outport2 + 'DB']
        zipped = zip(out2, out1)
        ampbal = []

        for one,two in zipped:
            ampbal.append(two-one)

        xdata, ydata = self.handle_outliers(self.get_frequency_data(), ampbal)

        data = dict()
        data[AMP_B] = {'xdata' : xdata,
                        'ydata' : ydata}
        self.data[AMP_B] = data
        self.linekeys[AMP_B] = [AMP_B]

    def get_phasebal_data(self):
        if self.name[0:3] == 'PBR':
            data = dict()
            data[PH_B] = {'xdata' : [],
                            'ydata' : []}
            self.data[PH_B] = data
            self.linekeys[PH_B] = [PH_B]
            return

        out1 = self.touchstone_data['S' + self.commonport + self.outport1 + 'A']
        out2 = self.touchstone_data['S' + self.commonport + self.outport2 + 'A']        
        zipped = zip(out1, out2)
        phasebal = []

        for one,two in zipped:
            phasebal.append(two - one)

        xdata, ydata = self.handle_outliers(self.get_frequency_data(), phasebal)

        data = dict()
        data[PH_B] = {'xdata' : xdata,
                        'ydata' : ydata}
        self.data[PH_B] = data
        self.linekeys[PH_B] = [PH_B]

    def handle_outliers(self, xdata, ydata):
        xreturn = []
        yreturn = []

        prev, prev_diff = None, None

        for i in range(len(xdata)):
            yval = ydata[i]
            xval = xdata[i]

            if prev == None:
                prev = yval
                prev_diff = None
                yreturn.append(yval)
                xreturn.append(xval)
            elif prev_diff == None:
                prev_diff = yval - prev
                prev = yval
                yreturn.append(yval)
                xreturn.append(xval)
            elif abs(prev_diff - (yval - prev)) < 1:
                prev_diff = yval - prev
                prev = yval
                yreturn.append(yval)
                xreturn.append(xval)

        return xreturn, yreturn
