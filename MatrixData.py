import numpy as np
import pandas as pd

dest_path = './data/block_arrays/minecraft-schematic-scrape.csv'


def ConvertBlockArraysToData(src_path):
    df = pd.read_csv(src_path)

    block_arrays = df['block_arrays']
    schem_dims = df['schem_dims']
    filename_titles = df['schematic_names']
    mappings = df['mappings']

    #verify mappings & create unified mapping
    unified_mapping = {}

    arrays = []
    arrays_transposed = []
    arrays_transposed_rotated = []
    for array in block_arrays:
        arrays.append(arrays)
    for array in arrays:
        arrays_transposed.append(array)
        arrays_transposed.append(GetTranspose(array))
    for array in arrays_transposed:
        arrays_transposed_rotated.append(array)
        for arr in GetRotations(array):
            arrays_transposed_rotated.append(arr)
    
    
    pass


def GetTranspose(df: pd.DataFrame):
    pass

def GetRotations(df: pd.DataFrame):
    pass

def GetAllDataFromArray(blocks: np.ndarray):
    pass