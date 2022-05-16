# -*- coding: utf-8 -*-
"""
Created on Thu Nov 21 13:23:30 2019

@author: Micha.Vardy
"""
import pandas as pd

def remove_duplicates(lista):
    return(list( dict.fromkeys(lista) ))
def remove_nan(lista):
    return([i for i in lista if str(i)!='nan' ])

def df_filter_spec(df_spec , df):
    """
        example:
            
            family = ['ALUMINUM']
            spec_type = ['AL 7075-T651','AL6061-T651']
            element_name = ['Elongation 5%', 'Elongation % 2','Hardness - Min','Tensile Strength MPA', 'Yield Point MPA']

            df_spec = {
                1:('FAMILY' ,family),
                2: ('SPEC_TYPE',spec_type),
                3:('ELEMENT NAME' ,element_name )
                }
    """
    
    keys = list(df_spec.keys())
    keys.sort()
    for i in keys:
        df = df_filter(df,df_spec[i][0] , df_spec[i][1])
    return(df)

def df_filter(df,column,value_list):
    return(df[df[column].isin(value_list)])