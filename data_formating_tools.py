import pandas as pd
import re
import numpy as np
import itertools
import Levenshtein
from tqdm.auto import tqdm


class triplets():
    def __init__(self, df = None, matdf = None):
        self.df = df
        self.matdf = matdf
        self.techdf = self.matdf[self.matdf.is_tech == True]
        self.gen_technology_alias_df()
        self.dimension_normal = 3
    def gen_technology_alias_df(self):
        columns = list(self.techdf.columns[self.techdf.columns.str.contains('technology.*alias')])
        columns.append('material_id') 
        self.technology_alias_df = self.techdf[columns]
    def distribute_angle(self,row):
        angle_field = re.search('\(.*\)\@\-*\d+',row,re.I)
        if angle_field:
            angle = re.search('\@\-*\d+',angle_field.group(),re.I).group()
            angle = re.search('\-*\d+',angle,re.I).group()
            content = re.search('\(.*\)',angle_field.group(),re.I).group()[1:-1]
            replace = re.sub('\s\+\s',f'@{angle} + ',content)
            replace = replace + f'@{angle}'
            row_replace = row[:angle_field.start()] + replace +row[angle_field.end():]
            row_replace = row_replace.strip()
            return (row_replace)
        else:
            return(row)
    def check_distributed_angle(self,row):
        angle_field = re.search('\@',row,re.I)
        if angle_field:
            return (True)
        else:
            return(False)
    def multiply_by_star(self,row):
        star_field = re.search('\*',row)
        if star_field:
            extract_multiply = re.search('\d+[a-zA-Z]+\*\d+',row,re.I)
            if extract_multiply:
                multiply_string = extract_multiply.group()
                multiply_list = re.split('\*',multiply_string)
                new_string = ' + '.join([multiply_list[0] for i in range(int(multiply_list[1]))])
                row = row[:extract_multiply.start()] + new_string + row[extract_multiply.end():]
        return (row)
    def remove_plus_between_dp_pu(self,row):
        while True:
            dpp = re.search('\+\s*pu',row,re.I)
            if dpp:
                row = row[:dpp.start()] + ',PU' + row[dpp.end():]
            else:
                return(row)
    def format_dp_pu(self,row):
        dp_pu = re.search('DP,PU',row)
        if dp_pu: 
            row = row[:dp_pu.start()] + ',DP,PU' + row[dp_pu.end():] 
        return(row)
    def split_by_newline(self,row):
        if re.search('\n',row):
            split = re.split('\n',row)
            split = [i.strip() for i in split]
        else:
            return(row)
        if re.search('Area:',split[0],re.I):
            return(split[1])
        else:
            return(split[0])
    def split_by_plus(self,row):
        split = re.split('\+',row)
        split = [i.strip() for i in split]
        return(split)
    def remove_actual_thickness(self,tpd):
        actual_thickness = '\(\d+\.\d+\)'
        ats = list(re.finditer(actual_thickness,tpd,re.I))
        while len(ats) > 0:
            i = ats[0]
            tpd = tpd[:i.start()] + tpd[i.end():]
            ats = list(re.finditer(actual_thickness,tpd,re.I))
        return(tpd)
    def pre_proc(self,tpd):
        self.df['tpd'] = self.df[tpd].astype(str).apply(self.distribute_angle)
        self.df = self.df.dropna(subset = ['tpd'])
        self.df.tpd = self.df.tpd.apply(self.remove_plus_between_dp_pu)
        self.df.tpd = self.df.tpd.apply(self.split_by_newline)
        #self.df.tpd = self.df.tpd.apply(self.format_dp_pu)
        self.df.tpd = self.df.tpd.apply(self.remove_actual_thickness)
        self.df.tpd = self.df.tpd.apply(lambda row: re.sub('Hull','',row,re.I)) 
        self.df.tpd = self.df.tpd.apply(lambda row: re.sub('\(',' ',row))
        self.df.tpd = self.df.tpd.apply(lambda row: re.sub('\)','',row))
        self.df.tpd = self.df.tpd.apply(self.multiply_by_star)
        self.df['split'] = self.df.tpd.apply(self.split_by_plus)
    def extract_dimension(self,row):
        dim = '^\d+\.*\d*'
        dim_row = []
        # iterate over elements in row
        for element in row:
            # if element has a dimensions
            if re.search(dim,element,re.I):
                dim_row.append(float(re.search(dim,element,re.I).group()))
            else:
                dim_row.append(False)
        return(dim_row)

    def extract_angle(self,row):
        ang = '\@-*\d+'
        angle_row = []
        # iterate over elements in row
        for element in row:
            
            # if element has a angle
            if re.search(ang,element,re.I):
                angle = re.search(ang,element,re.I).group()
                angle_row.append(int(re.search('-*\d+',angle,re.I).group()))
            else:
                angle_row.append(False)
        return(angle_row)
    
    def extract_units(self,row):
        unit = 'mm'
        unit_row = []
        # iterate over elements in row
        for element in row:
            # if element has a angle
            if re.search(unit,element,re.I):
                unit_row.append('mm')
            else:
                unit_row.append(False)
        return(unit_row)
    def extract_facets(self,element):
        ceramics_token = '\d+x\d+|\d+x\d+x\d+'
        ceramics_regex = re.search(ceramics_token,element.element_raw,re.I)
        if ceramics_regex: 
            facet = ceramics_regex.group()
            dimension = re.search('\d+',facet,re.I)
            facet = facet[dimension.end():]
            return(facet)
        else:
            return(None)

    def extract_element(self,element):
        # this function takes element data dataframe and not test panel description dataframe
        if element.facets:
            return( re.sub('mm','',element.element_raw))
        elif element.units:
            element_start = re.search(str(element.units),element.element_raw,re.I).end()
        elif element.dimension:
            element_start = re.search(str(element.dimension),element.element_raw,re.I)
            if element_start:
                element_start = element_start.end()
            else:
                element_start = 0
        else:
            element_start = 0
        if element.angle:
            element_end = re.search('\@',element.element_raw,re.I).start()
        else:
            element_end = None
        return(element.element_raw[element_start:element_end])

    def init_element_data(self):
        # this function takes a row dataframe and returns an element dataframe
        element_data = pd.DataFrame()
        for index,row in pd.DataFrame.iterrows(self.df):
            row = row.split
            ed = pd.DataFrame({'rec_index': index,
                               'element_raw':[elem for elem in row],
                               'dimension':self.extract_dimension(row),
                               'angle':self.extract_angle(row),
                               'units':self.extract_units(row)})
            element_data = element_data.append(ed)
        self.element_data = element_data
    
    def element_data_extract(self):
        tqdm.pandas(desc = 'classify elements')
        self.init_element_data()
        self.element_data['facets'] = self.element_data.apply(self.extract_facets,axis = 1)
        self.element_data['element'] = self.element_data.apply(self.extract_element,axis = 1)
        self.element_data['material_database_row'] = self.element_data.element.progress_apply(self.element_classifier)
        self.element_data['material_database_row'] = self.element_data.apply(self.element_technology_classifier, axis = 1)
        self.element_data['material_database_keyword'] = self.element_data.material_database_row.apply(self.material_database_keyword_extraction)
        self.element_data['material_database_id'] = self.element_data.material_database_row.apply(self.material_database_id_extraction)


    def element_material_database_distance(self,material_row,element):
        self.test = {'mr':material_row,'e':element}
        row_index = material_row.name
        n = len([i for i in material_row.keys() if type(material_row[i]) == str])
        distance_list = [Levenshtein.distance(material_row[i],element)
                        for i in material_row.keys()
                        if type(material_row[i]) == str]
        if not distance_list:
            return(pd.Series({'avg_dist':None,'row_index':None}))
        avg_dist = sum(distance_list)/n
        return(pd.Series({'avg_dist':avg_dist,'row_index':row_index}))

    def element_material_database_distance_by_alias(self,material_row,element):
        row_index = material_row.name
        alias = re.split(', ',material_row.alias)
        distance_list = [Levenshtein.distance(i,element)
                        for i in alias]
        min_dist = min(distance_list)
        return(pd.Series({'min_dist':min_dist,'row_index':row_index}))
    def element_material_database_distance_by_alias_test(self,material_row,element):
        row_index = material_row.name
        alias = re.split(', ',material_row.alias)
        distance_dict = {Levenshtein.distance(i,element):i for i in alias}
        distance_list = [Levenshtein.distance(i,element) for i in alias]
        min_dist = min(distance_list)
        return(pd.Series({'min_dist':min_dist, 'keyword':material_row.Keyword, 'alias_dist': distance_dict}))
    def element_classifier(self,elem):
        #dist_df= pd.DataFrame(self.matdf.apply(self.element_material_database_distance,element = elem,axis=1))
        dist_df= pd.DataFrame(self.matdf.apply(self.element_material_database_distance_by_alias,element = elem,axis=1))
        minimal_distance_index = int(dist_df.iloc[dist_df.min_dist.idxmin()].row_index)
        return(minimal_distance_index)
    def element_technology_classifier(self,elem_data):
        minimal_distance_index = elem_data.material_database_row
        if self.matdf.iloc[elem_data.material_database_row].is_tech==True:
            self.dist_df= pd.DataFrame(self.technology_alias_df.loc[:,self.technology_alias_df.columns != 'material_id'].apply(
                self.element_material_database_distance,
                element = elem_data.element,axis=1))
            self.dist_df = self.dist_df.dropna(axis = 0)
            matid = self.dist_df.row_index.apply(lambda r: self.technology_alias_df.loc[r].material_id)
            self.dist_df['keyword'] = matid.apply(lambda id: self.matdf[self.matdf.material_id == id].Keyword.values[0])
            minimal_distance_index = self.dist_df.loc[self.dist_df.avg_dist.idxmin()].row_index 
        return(minimal_distance_index)
    def element_classifier_test(self,elem, deviation):
        dist_df= pd.DataFrame(self.matdf.apply(self.element_material_database_distance_by_alias_test,element = elem,axis=1))
        min = dist_df.min_dist.min()
        dist_df = dist_df[dist_df.min_dist < min + deviation]
        return(dist_df)
    def material_database_keyword_extraction(self,matdb_row):
        return(self.matdf.iloc[int(matdb_row)].Keyword)
    def material_database_id_extraction(self,matdb_row):
        return(self.matdf.iloc[int(matdb_row)].material_id)
    
    def element_data_processing(self,angle):
        self.element_data['angle'] = self.element_data.apply(self.add_angle_from_data,axis = 1)
        self.element_data['dimension'] = self.element_data.apply(self.sika_dimension,axis = 1)
        self.element_data['dimension'] = self.element_data.apply(self.fabric_dimension,axis = 1)
        self.element_data['triplet'] = self.element_data.apply(self.format_triplet,axis = 1)
        self.element_data['keyword_triplet'] = self.element_data.apply(self.format_keyword_triplet,axis = 1)
        self.element_data['dimension_normalized'] = self.element_data.dimension.apply(lambda d: d*self.dimension_normal)
        self.element_data['triplet_normalized'] = self.element_data.apply(self.format_normalized_triplet,axis = 1)
    def sika_dimension(self,row):
        if row.dimension == False and row.material_database_keyword == 'SIKA':
            return(1)
        else:
            return(row.dimension)
    def fabric_dimension(self,row):
        if row.material_database_keyword == 'K3000':
            row.dimension = row.dimension / 2
        return(row.dimension)
    def add_angle_from_data(self,row):
        if row.angle == False:
            a = self.df.iloc[int(row.rec_index)].angle
            return(a)
        else:
            return(row.angle)
    def format_triplet(self,row):
        triplet = f"{row.dimension};m{row.material_database_id};{row.angle}"
        return(triplet)
    def format_keyword_triplet(self,row):
        triplet = f"{int(row.dimension)};{row.material_database_keyword};{row.angle}"
        return(triplet)
    def format_normalized_triplet(self,row):
        triplet = f"{row.dimension_normalized};m{row.material_database_id};{row.angle}"
        return(triplet)
    def concat_triplets(self,row):
        element_df = self.element_data[self.element_data.rec_index == row.name]
        triplet_string = ' + '.join(element_df.triplet)
        return(triplet_string)
    def concat_keyword_triplets(self,row):
        element_df = self.element_data[self.element_data.rec_index == row.name]
        triplet_string = ' + '.join(element_df.keyword_triplet)
        return(triplet_string)
    def concat_triplets_normalized(self,row):
        element_df = self.element_data[self.element_data.rec_index == row.name]
        triplet_string = ' + '.join(element_df.triplet_normalized)
        return(triplet_string)
         
