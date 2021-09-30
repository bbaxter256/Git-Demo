import pandas as pd
from passive import Passive, WrongPassiveException
from product import Product as P

'''index corresponds to graph_objects'''

RL = 'Common Port Return Loss'
IL = 'Insertion Loss as a mode converter'
ISO = 'Isolation'
AMP_B = 'Amplitude Balance'
PH_B = 'Phase Balance'

def load_specs():
    df = pd.read_excel('data/balun-files/balunproductspecs.xlsx', sheet_name='Sheet1', index_col=0)

    datasheet = {}

    for id in df.index:
        sheet = {
            'id' : id,
            'model' : id,
            'file' : df.at[id, 'file'],
            'freq-low' : df.at[id, 'freq-low'],
            'freq-high' : df.at[id, 'freq-high'],
            'amplitude balance (dB)' : df.at[id, 'ampBal'],
        }
        datasheet[id] = sheet
    
    return datasheet

class Balun(Passive):

    def __init__(self, name):
        super().__init__(name, 'balun')

        self.commonport = None
        self.outport0 = None
        self.outport180 = None
        self.set_port_config()

    def set_port_config(self):
        comments = self.touchstone.get_comments()
        comment_lines = comments.split('\n')
        is_balun = False
        pc = ''
        for line in comment_lines:
            if 'Balun' in line:
                is_balun = True
            l = line.lower()
            if 'output' in l or 'common' in l:
                pc = pc + l
        if not is_balun:
            print(self.name)
            raise WrongPassiveException
        port_configs = pc.lower()
        common, out180, out0 = None, None, None

        common_split = port_configs.split('common')
        if '3' in common_split[0]:
            common = '3'
        elif '2' in common_split[0]:
            common = '2'
        elif '1' in common_split[0]:
            common = '1'
        
        out180_split = port_configs.split('180')
        if '3' in out180_split[0]:
            out180 = '3'
        elif '2' in out180_split[0]:
            out180 = '2'
        elif '1' in out180_split[0]:
            out180 = '1'

        out0_split = port_configs.split('0')
        if '3' in out0_split[0]:
            out0 = '3'
        elif '2' in out0_split[0]:
            out0 = '2'
        elif '1' in out0_split[0]:
            out0 = '1'
        
        self.commonport = common
        self.outport180 = out180
        self.outport0 = out0

    def load_graph_data(self, graph):
        # return
        if graph in self.data: return
        if graph == RL:
            self.get_returnloss_data()
        elif graph == IL:
            # pass 
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
                'ylabel' : RL,
                'xunit' : '(GHz)',
                'yunit' : '(dB)',
            },
            IL : {
                'xlabel' : 'Frequency',
                'ylabel' : IL,
                'xunit' : '(GHz)',
                'yunit' : '(dB)',
            },
            ISO : {
                'xlabel' : 'Frequency',
                'ylabel' : ISO,
                'xunit' : '(GHz)',
                'yunit' : '(dB)',
            },
            AMP_B : {
                'xlabel' : 'Frequency',
                'ylabel' : AMP_B,
                'xunit' : '(GHz)',
                'yunit' : '(cB)',
            },
            PH_B : {
                'xlabel' : 'Frequency',
                'ylabel' : PH_B,
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
        data['Out 0'] = {'xdata' : xdata,
                        'ydata' : self.touchstone_data['S' + self.outport0 + self.outport0 + 'DB']}
        data['Out 180'] = {'xdata' : xdata,
                        'ydata' : self.touchstone_data['S' + self.outport180 + self.outport180 + 'DB']}
       
        self.data[RL] = data 
        self.linekeys[RL] = ['Common', 'Out 0', 'Out 180']

    def get_insertionloss_data(self):
        # pass

        data = dict()
        frequencydata = self.get_frequency_data()
        out0 = self.touchstone_data['S' + self.commonport + self.outport0 + 'DB']
        out180 = self.touchstone_data['S' + self.commonport + self.outport180 + 'DB']

        xdata1, ydata1 = self.handle_outliers(frequencydata, out0)
        xdata2, ydata2 = self.handle_outliers(frequencydata, out180)

        data['Out 0'] = {'xdata' : xdata1,
                        'ydata' : ydata1}
        data['Out 180'] = {'xdata' : xdata2,
                        'ydata' : ydata2}
        
        self.data[IL] = data
        self.linekeys[IL] = ['Out 0', 'Out 180']

    def get_isolation_data(self):
        data = dict()
        xdata = self.get_frequency_data()
        data[ISO] = {'xdata' : xdata, 
                    'ydata' : self.touchstone_data['S' + self.outport0 + self.outport180 + 'DB']}
        self.data[ISO] = data
        self.linekeys[ISO] = [ISO]

    def get_amplitudebal_data(self):
        out0 = self.touchstone_data['S' + self.commonport + self.outport0 + 'DB']
        out180 = self.touchstone_data['S' + self.commonport + self.outport180 + 'DB']
        ampbal = []
        for i in range(len(out0)):
            ampbal.append((out0[i]-out180[i]) * 10)
        
        data = dict()
        xdata = self.get_frequency_data()
        data[AMP_B] = {'xdata' : xdata,
                        'ydata' : ampbal}
        self.data[AMP_B] = data
        self.linekeys[AMP_B] = [AMP_B]

    def get_phasebal_data(self):
        out0 = self.touchstone_data['S' + self.commonport + self.outport0 + 'A']
        out180 = self.touchstone_data['S' + self.commonport + self.outport180 + 'A']
        frequencydata = self.get_frequency_data()
        xdata = []
        phasebal = []
        for i in range(len(out0)):
            o2 = out180[i]
            o1 = out0[i]
            x = frequencydata[i]
            if (o2 < 0 and o1 < 0) or (o2 > 0 and o1 > 0):
                phasebal.append(abs(o1 - o2))
                xdata.append(x)
            else:
                phasebal.append(abs(o1 - o2))
                xdata.append(x)
        
        data = dict()
        data[PH_B] = {'xdata' : xdata,
                        'ydata' : phasebal}
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
