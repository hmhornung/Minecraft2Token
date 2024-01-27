import numpy as np
import pandas as pd
import torch
import os
import math
import schematic_data
from schematic_data import SchematicData

def ndarray_from_str(arr_str: str, dims: tuple) -> np.ndarray:
    '''
    Gets an np ndarray from a string
    '''
    arr = np.zeros(dims, dtype=np.uint16)
    arr_str = arr_str.removeprefix('[\n')
    arr_str = arr_str.removesuffix('],\n')#remove this dimensions outer braces
    if len(dims) == 1:
        arr_str.replace('\n', '')
        nums = str.split(arr_str, ',')
        remove_from_list(nums, '')
        nums = [x for x in nums if x.isdigit() ]
        return np.array(nums, dtype=np.uint16)
    else:
        arr_str = str.split(arr_str, '\n')
        total = 1
        num_lines = 0
        for dim in dims[:-2]:
            # print(dim)
            num_lines += total * dim * 2
            total = total * dim
        num_lines += total * dims[-2] * 3
        line_len = num_lines / dims[0]
        # print(num_lines)
        for j in range(dims[0]):
            line = arr_str[int(j*line_len):int(j*line_len+line_len)] #take likes for individual subarray
            line = '\n'.join(line)
            arr[j] = ndarray_from_str(line, dims[1:]) # go on to next dimension
    arr.dtype = np.uint16
    return arr
    
def ndarray_to_str(arr: np.ndarray) -> str:
    arr_str = ''
    arr_str += ('[\n')
    
    dim_sizes = arr.shape
    num_dims = len(dim_sizes)

    if num_dims == 1:
        for i in range(dim_sizes[0]):
            arr_str += str(arr[i]) + ','
        arr_str += ('\n')
    else:
        for i in range(dim_sizes[0]):
            arr_str += (ndarray_to_str(arr[i]))
    arr_str += ('],\n')
    return arr_str

def remove_from_list(items: list, removable : any) -> list:
    del_indicies = []
    for i in range(len(items)):
        if items[i] == removable:
            del_indicies.append(i)
    del_indicies.reverse()
    for index in del_indicies:
        del items[index]
    return items

def get_tokens(mappings: list) -> dict:
    '''
    Get token mapping for all blocks from a list of mappings
    '''
    universal_mappings = {} # { block id : number}
    for map in mappings:
        for key in map.keys():
            if not key in universal_mappings.keys():
                universal_mappings[key] = int(map[key])
    # get keys and values to flip them
    mapping_keys = list(universal_mappings.keys())
    mapping_values = list(universal_mappings.values())
    # {number : block id}
    rev_mapping = {mapping_values[i] : mapping_keys[i] for i in range(len(mapping_keys))} #reversed lookup for universal mapping

    ordered_ids = list(rev_mapping.keys())
    ordered_ids.sort()
    blocks_ordered = [rev_mapping[id] for id in ordered_ids]

    #all block ids tokenized, so that they will be rougly in the same order of the actual block ids
    tokenized = {blocks_ordered[i]: i for i in range(len(blocks_ordered))}

    return tokenized

def tokenize_and_exclude(schem_datas: list[SchematicData]) -> (dict, list[bool]):
    #Cell for checking which schematics lack a mapping for any of the blocks in their array
    num_good = 0
    num_bad = 0
    exclude_list = []
    for data in schem_datas:
        full_mapping, missing_mappings = SchematicData.values_in_mapping(data)
        if full_mapping:
            num_good += 1
            exclude_list.append(False)
        else:
            num_bad += 1
            print(f"{data.filename} | {len(data.mapping)} | {missing_mappings}")
            exclude_list.append(True)

    print(f"good: {num_good}\nbad: {num_bad}")

    #Create a a tokenization for all blocks available in the mappings
    all_mappings = []
    for i, schem in enumerate(schem_datas):
        if exclude_list[i]:
            print(f"skipping {schem.filename}")
            print(f"{schem.mapping}")
            continue
        all_mappings.append(schem.mapping)
    tokenization = get_tokens(all_mappings)
    for i, schem in enumerate(schem_datas):
        if exclude_list[i]:
            print(f"Skipping {schem.filename}")
            continue
        if not SchematicData.tokenize_data(schem, tokenization):
            print(f"{schem.filename} had a mapping not in universal mappings")
            exclude_list[i] = True
    
    return tokenization, exclude_list
