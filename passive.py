'''
Passive Products use SNP files to house data.
The class uses the skrf class to create Touchstone
objects from the SNP file which is uses to conviniently
pull data from. 

https://scikit-rf.readthedocs.io/en/latest/tutorials/Introduction.html
https://scikit-rf.readthedocs.io/en/latest/_modules/skrf/io/touchstone.html


Passives: Couplers, Power Dividers
'''

import skrf as rf
from product import Product

class Passive(Product):
    def __init__(self, name, producttype):
        Product.__init__(self, name)

        self.filepath = 'data/' + producttype + '-files/' + self.products[name]['file']
        self.touchstone = rf.Touchstone(self.filepath)
        self.touchstone_data = self.touchstone.get_sparameter_data('db')

    def get_frequency_data(self):
        return list(map(lambda x : (x / pow(10,9)), self.touchstone_data['frequency']))

class WrongPassiveException(Exception):
    pass