import numpy as np
import pandas as pd
from nbtschematic import SchematicFile
import util
import schematic_data
from schematic_data import SchematicData
from functools import reduce

def write_ndarray(blocks: np.ndarray, path: str, name: str) -> None:
    '''
    Write a ndarray to file
    '''
    #get the array as a string
    file_str = util.ndarray_to_str(blocks)
    with open(path + name, 'w') as file:
        file.write(file_str)
        # print(f'wrote {name} to {path}')
    return True

def save_tokenized_schems(schem_datas: list[SchematicData], 
                          exclude_list: list[bool], 
                          tokenization: dict, 
                          path: str) -> bool:
    '''
    Saves all tokenized SchematicData block arrays to .bin,
    src/bin filenames + dimensions to a pandas DataFrame,
    and the tokenization dictionary to json
    '''
    src_filenames = []
    bin_filenames = []
    dimensions = []

    for i, schem in enumerate(schem_datas):
        if exclude_list[i]:
            print(f"skipping {schem.filename}")
            continue
        #add data to lists for df
        src_filenames.append(schem.filename)
        bin_filename = schem.filename.removesuffix('.schematic') + '.bin'
        bin_filenames.append(bin_filename)
        dimensions.append(schem.dimensions)
        # write_ndarray(np.array(schem.blocks, dtype=np.uint16), path + 'arrays/', bin_filename)
        save_ndarray(schem.blocks, path + 'arrays/' + bin_filename)

    #create dataframe
    df_dict = {
        'src_filename' : src_filenames,
        'bin_filename' : bin_filenames,
        'dimensions' : dimensions
    }
    df = pd.DataFrame(df_dict)
    df.to_csv(path + 'file_data.csv')

def load_tokenized_schems(path: str) -> ( list[SchematicData], pd.DataFrame , dict ):
    df = pd.read_csv(path + 'file_data.csv')
    dimensions = df.dimensions.apply(lambda x: tuple(eval(x))).tolist()
    src_filenames = df.src_filename.apply(lambda x: x).to_list()
    bin_filenames = df.bin_filename.apply(lambda x: x).to_list()
    
    schem_datas = []
    
    for i, dims in enumerate(dimensions):
        blocks = load_ndarray(path + 'arrays/' + bin_filenames[i])
        schem_datas.append(SchematicData(blocks, 
                                         None, #need to save tokenized mapping to file still, then will add
                                         dims, 
                                         src_filenames[i], 
                                         bin_filenames[i]))
        print(f'loaded {bin_filenames[i]}')
    
    return schem_datas, df, None
    
def save_ndarray(arr: np.ndarray, path) -> bytes:
    dtype = np.uint8(arr.dtype.num)                                         #dtype stored in 1 byte
    ndims = np.uint8(len(arr.shape))                                        #num dims stored in 1 byte
    dims = np.array([arr.shape[i] for i in range(ndims)], dtype=np.uint32)  #dims stores in 4 bytes each
    
    file_bytes = bytes()
    file_bytes += dtype.tobytes()
    file_bytes += ndims.tobytes()
    file_bytes += dims.tobytes()
    file_bytes += arr.tobytes()
    
    with open(path, 'wb') as file:
        file.write(file_bytes)
    
def load_ndarray(path: str) -> np.ndarray:
    with open(path, 'rb') as file:
        all_bytes = file.read()
        
    dtype = np.sctypeDict[np.frombuffer(all_bytes[0:1], np.uint8)[0]]
    ndims = np.frombuffer(all_bytes[1:2], np.uint8)[0]
    arr_start_idx = 2 + (ndims * np.dtype(np.uint32).itemsize)
    dims = np.frombuffer(all_bytes[2:arr_start_idx], np.uint32)

    size = reduce(lambda x, y: x * y, dims) * np.dtype(dtype).itemsize
    arr = np.frombuffer(all_bytes[arr_start_idx: arr_start_idx + size], dtype=dtype)
    arr.resize(dims)
    return arr