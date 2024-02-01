import numpy as np
import pandas as pd
import schemfio
import schematic_data
from schematic_data import SchematicData
from numpy.lib.stride_tricks import sliding_window_view

def create_dataset(schem_arrays: list[SchematicData], 
                   data_shape: tuple,
                   dest: str,
                   dtype: np.dtype) -> int:
    filenames = []
    extracted = []
    empty = []

    for i, schem_data in enumerate(schem_arrays):
        if schem_data.blocks.shape[0] < data_shape[0] or schem_data.blocks.shape[1] < data_shape[1] or schem_data.blocks.shape[2] < data_shape[2]:
            continue
        slice_result = slice_ndarray(schem_data, data_shape, dest + 'data/', dtype)
        filenames.append(schem_data.filename)
        empty.append(slice_result[1])
        extracted.append(slice_result[0])
        print(f'extracted data from {schem_data.filename} with {slice_result[1]} empty slices | {slice_result[0]} extracted')
    
    df_dict = {'filenames': filenames,
               'extracted': extracted,
               'empty': empty}
    df = pd.DataFrame(df_dict)
    df.to_csv(dest + 'data.csv')
    return empty

def slice_ndarray(schem_data: SchematicData, shape: tuple, dest: str, dtype: np.dtype) -> (int, int):
    filenames = []
    blocks = schem_data.blocks
    basename = schem_data.tkn_filename.removesuffix('.bin')
    empty = 0
    extracted = 0
    
    for x in range(schem_data.blocks.shape[0] - shape[0] + 1):
        for y in range(schem_data.blocks.shape[1] - shape[1] + 1):
            for z in range(schem_data.blocks.shape[2] - shape[2] + 1):
                slice = np.array(blocks[x:x+shape[0],y:y+shape[1],z:z+shape[2]], dtype=dtype)
                if len(np.unique(slice)) == 1:
                    empty += 1
                    continue
                name = basename + f'_{x}_{y}_{z}.bin'
                filenames.append(name)
                schemfio.save_ndarray(slice, dest + name)
                extracted += 1
    return extracted, empty