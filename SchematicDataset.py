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
    data_names = []
    empty = 0
    for i, schem_data in enumerate(schem_arrays):
        slice_result = slice_ndarray(schem_data, data_shape, dest + 'data/', dtype)
        data_names = data_names + slice_result[0]
        empty += slice_result[1]
        print(f'extracted data from {schem_data.filename}')
    
    df_dict = {'data_filenames': data_names}
    df = pd.DataFrame(df_dict)
    df.to_csv(dest + 'data.csv')
    return empty

def slice_ndarray(schem_data: SchematicData, shape: tuple, dest: str, dtype: np.dtype) -> (list[str], int):
    filenames = []
    blocks = schem_data.blocks
    basename = schem_data.tkn_filename.removesuffix('.bin')
    
    slices = sliding_window_view(blocks, shape)
    i = 0
    empty = 0
    for slice_ in slices:
        if len(np.unique(slice_)) == 1:
            empty += 1
        else:
            name = basename + f'_{i}.bin'
            filenames.append(name)
            schemfio.write_ndarray(slice_, dest, name)
            i += 1
    # for x in range(schem_data.blocks.shape[0] - shape[0] + 1):
    #     for y in range(schem_data.blocks.shape[1] - shape[1] + 1):
    #         for z in range(schem_data.blocks.shape[2] - shape[2] + 1):
    #             slice = np.empty(shape, dtype=dtype)
    #             for i in range(shape[0]):
    #                 for j in range(shape[1]):
    #                     for k in range(shape[2]):
    #                         slice[i,j,k] = blocks[ x+i , y+j , z+k ]
    #             name = basename + f'_{x}_{y}_{z}.bin'
    #             filenames.append(name)
    #             schemfio.write_ndarray(slice, dest, name)
    return filenames