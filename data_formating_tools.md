# data formatting tools

## triplets

### synopses

the triplets class is a data formatting library that takes ballistic result data and formats them into triplet form

the triplets class can 
- preprocess strings
- extract element data
- match element data to material database

### attributes

* self.df
    - ballistic result dataframe
    - type: dataframe
    - columns:

'editor note', 'Test Panel Description', 'description_reworked',
'Test Date', 'angle', 'Shot Penatration', 'unfair hit ', 'Shot Remarks',
'Test Panel Areal Weight', 'Test Panel Thickness Max', 'Report Number',
'shot number', 'Shot Bullet Velocity AVG.', 'tpd', 'split', 'triplets',
'keyword_triplets'

* self.matdf
    - material database dataframe
    - type: dataframe
    - columns:

'Number', 'material_type', 'material_name', 'material_label',
'manufacturer', 'Keyword', 'grade', 'geometry', 'purity', 'density',
'material_price', 'work_price'

* self.element_data
    - element data dataframe
    - type: dataframe
    - columns:

'rec_index', 'element_raw', 'dimension', 'angle', 'units', 'element',
'material_database_row', 'material_database_keyword', 'triplet',
'keyword_triplet'

### methods

#### init (self, df = None, matdf = None)
* args
    - df: ballistic results dataframe
    - matdf: material database dataframe

#### pre_proc(self,tpd):
* args
    - tpd: test panel description series
* function calls
    - distribute_angle: 
    - remove plus between dp_pu
    - split by newline
    - split by plus
#### init_element_data(self):
* function calls
   - extract dimension
   - extract angle
   - extract units
#### element_data_extract(self):
*function calls
    - init_element_data
    - element classifier
    - material database keyword extraction
#### element_data_processing
* function calls
    - add angle from data
    - format triplet
    - format keyword triplet




### script
ys.path.append('/home/michav/pydev/data_analysis')
from data_formating_tools import triplets as tr

matdf = pd.read_excel('/home/michav/shared/data/matdf.xlsx')
df = pd.read_excel('/home/michav/shared/data/apt.xlsx')

form = tr(df,matdf)

#preprocess data
form.pre_proc('description_reworked')

# extract element data
form.element_data_extract()

# element data processing
form.element_data_processing('angle')

#concatenate triplets into data
form.df['triplets'] = form.df.apply(form.concat_triplets,axis=1)
form.df['keyword_triplets'] = form.df.apply(form.concat_keyword_triplets,axis=1)

