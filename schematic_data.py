from nbtschematic import SchematicFile
import pandas as pd
import numpy as np
import os
import csv
import util

'''
This function should return:
1 The Dimensions of the schematic
2 The Block ID mappings of the schematic
3 A 3D matrix of the block IDs (X,Y,Z)
'''
def get_schematic_data(file: SchematicFile, name: str) -> ( str , "SchematicData" ):
    #verify file
    if 'Schematic' not in file.keys() or 'SchematicaMapping' not in file['Schematic'].keys():
        return "format error", None
    
    #get basic info
    blocks = file.blocks

    file = file['Schematic']

    mapping = file['SchematicaMapping']
    X = int(file['Length'])
    Y = int(file['Height'])
    Z = int(file['Width'])

    #create normal python dict of mappings, return None for modded schematics
    rtn_mappings = {}
    for key in mapping.keys():
        if not str(key).startswith('minecraft:'):
            return "modded schematic", None
        rtn_mappings[key] = np.uint16(mapping[key]) 

    #create block matrix
    block_matrix = np.zeros((X,Y,Z))
    for x in range(X):
        for y in range(Y):
            for z in range(Z):
                block_matrix[x,y,z] = np.uint8(blocks[y,x,z]) # for some reason its y, x, z; where y is height, x is length, z is width
    rtn_data = SchematicData(block_matrix, rtn_mappings, (X,Y,Z), name)
    return "successful", rtn_data
    
def schem_data_from_dir(src_path: str) -> list["SchematicData"]:
    '''
    Get a list of SchematicData objects from a directory
    '''
    #stats for the data
    total = 0
    n_schem = 0         #.schematic
    n_non_schem = 0     # not .schematic
    n_format_error = 0  #.schematic format error
    n_modded_schem = 0  #.schematic modded
    n_success = 0       #.schematic success

    schem_datas = []

    for name in os.listdir(src_path):
        total += 1
        if not name.endswith('.schematic'):
            n_non_schem += 1
            continue
        n_schem += 1

        print('procesing ', name)

        try: 
            file = SchematicFile.load(src_path + name)
        except Exception:
            n_format_error += 1
        rtn_msg, schem_data = get_schematic_data(file, name)

        if rtn_msg == 'successful':
            n_success += 1
            schem_datas.append(schem_data)
        elif rtn_msg == 'format error':
            n_format_error += 1
        elif rtn_msg == 'modded schematic':
            n_modded_schem += 1
    #print diagnostics
    print('%.schematic files: ', (n_schem / total * 100))
    print('%.schematic files format error: ', (n_format_error / (n_schem + n_format_error) * 100))
    print('%.schematic files modded: ', (n_modded_schem / n_schem * 100))
    print('%.schematic files success: ', (n_success / n_schem * 100))
    
    return schem_datas



class SchematicData(object):
    def __init__(self, blocks: np.ndarray, 
                 mapping: dict, 
                 dimensions: tuple, 
                 filename: str,
                 tkn_filename: str = None):
        self.blocks = blocks
        self.mapping = mapping
        self.dimensions = dimensions
        self.filename = filename
        self.tkn_filename = tkn_filename
    
    @staticmethod
    def values_in_mapping(schem_data: "SchematicData") -> (bool, list):
        '''
        Check whether a schematic data file has a mapping for each unique block in the array
        '''
        block_vals = np.uint8(np.unique(schem_data.blocks))
        available_vals = list(schem_data.mapping.values())
        unavailable_vals = []
        for val in block_vals:
            if val not in available_vals: unavailable_vals.append(val)
        if len(unavailable_vals) > 0: return False, unavailable_vals
        return True, None
    
    @staticmethod
    def tokenize_data(schem_data: "SchematicData", block2token: dict, dtype: np.dtype = np.uint8) -> bool:
        '''
        Convert a SchemData object to use the block tokens being used for training
        '''
        conversion_mapping = {}
        for key in schem_data.mapping.keys():
            if key in list(block2token.keys()):
                conversion_mapping[int(schem_data.mapping[key])] = block2token[key]
            else:
                return False
        new_blocks = np.zeros(schem_data.dimensions, dtype=dtype)
        for x in range(schem_data.blocks.shape[0]):
            for y in range(schem_data.blocks.shape[1]):
                for z in range(schem_data.blocks.shape[2]):
                    new_blocks[x,y,z] = conversion_mapping[schem_data.blocks[x,y,z]]
        schem_data.mapping = block2token
        schem_data.blocks = new_blocks
        return True