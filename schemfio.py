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
        print(f'wrote {name} to {path}')
    return True

'''
format of .blockdata file:
input size:x,y,z\n      (size of the input)
output size:x,y,z\n     (size of the output)
dim of continuity:n\n   (dimension the output extends of the input 0/1/2)
dir of continuity:b\n   (direction the output extends -/+ )  
'''
def load_blockdata(src_path: str) -> (np.ndarray, np.ndarray, (int, str)):
    lines = ''
    with open(src_path, 'r') as file:
        lines = file.readlines()
    lines = ''.join(lines)
    lines = lines.split('<>\n')

    metadata = lines[0]
    input = lines[1]
    output = lines[2]

    #get the metadata
    metadata = metadata.split('\n')
    tuple_str = metadata[0].split(':')[1].split(', ')[0]
    input_dims = tuple(map(int, tuple_str.split(',')))
    tuple_str = metadata[1].split(':')[1].split(', ')[0]
    output_dims = tuple(map(int, tuple_str.split(',')))
    print(input_dims)

    #get the input and output array
    input_ndarray = util.ndarray_from_str(input, input_dims)
    output_ndarray = util.ndarray_from_str(output, output_dims)

    return input_ndarray, output_ndarray, (None,None)


'''
format of .blockdata file:
input size:x,y,z\n      (size of the input)
output size:x,y,z\n     (size of the output)
dim of continuity:n\n   (dimension the output extends of the input 0/1/2)
dir of continuity:b\n   (direction the output extends -/+ )  
'''
def np_to_blockdata(input: np.ndarray, output: np.ndarray, io_relation: (int, str), dest_path: str) -> None:
    #verify the data
    if len(input.shape) != 3 or len(input.shape) != 3:
        print('numpy arrays must be 3 dimensional')
        return
    if io_relation[0] not in [0,1,2]:
        print('io_relation[0] must be 0, 1, or 2')
        return
    if io_relation[1] not in '+-' or len(io_relation[1]) != 1:
        print('io_relation[1] must be + or - as str')
        return
    # if not dest_path.endswith('.blockdata'):
    #     print('dest_path must be a path ending with /filename.blockdata')
    #     return

    #create and verify metadata
    inp_sz_X, inp_sz_Y, inp_sz_Z = input.shape
    out_sz_X, out_sz_Y, out_sz_Z = output.shape
    dim_of_continuity = io_relation[0]
    dir_of_continuity = io_relation[1]

    #verify dimension of continuity by checking input & output dimensions
    dims = [0,1,2]
    dims.remove(dim_of_continuity)
    #other 2 dims of output should = dims of input
    discrepency = False
    for dim in dims:
        if input.shape[dim] != output.shape[dim]:
            print(f"dimensions of input and output should be same, except the dimension of continutiy.\nDimension {dim} of input and output arent equal")
            discrepency = True
    if discrepency: return

    file_str = '' #the string to write to .blockdata

    #add metadata
    file_str += (f'input size:{inp_sz_X},{inp_sz_Y},{inp_sz_Z}\n')
    file_str += (f'output size:{out_sz_X},{out_sz_Y},{out_sz_Z}\n')
    file_str += (f'dim of continuity:{dim_of_continuity}\n')
    file_str += (f'dir of continuity:{dir_of_continuity}\n')

    #seperate metadata and arrays
    file_str += ('<>\n')

    #get the str for the input block array
    input_str = util.ndarray_to_str(input)
    file_str += input_str
    print(util.ndarray_from_str(input_str, (inp_sz_X, inp_sz_Y, inp_sz_Z)))

    #seperate input and output arrays
    file_str += ('<>\n')

    #get the str for the block array
    file_str += (util.ndarray_to_str(output))

    #finally, write the file string to path & name given in parameters
    with open(dest_path, 'w') as file:
        file.write(file_str)

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

def save_ndarray(arr: np.ndarray) -> None:
    arr_as_bytes = bytes()
    
    dims = arr.shape
    n_dims = np.uint8(dims)
    
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