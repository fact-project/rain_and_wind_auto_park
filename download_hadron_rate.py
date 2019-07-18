from os import environ
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
import yaml
from sqlalchemy import create_engine

db_connection_url = f"mysql+pymysql://fact:{environ['FACT_PASSWORD']}@ihp-pc45.ethz.ch/factdata"
eng = create_engine(
    db_connection_url,
    connect_args={'ssl': {'ssl-mode': 'required'}}
)

query = '''
SELECT
fRunStart, fRunStop, fR750Cor, fZenithDistanceMean,
fNumThreshold750, fEffectiveOn, fRunTypeKey
FROM
RunInfo
'''

df = pd.read_sql(query, eng)
df = df.dropna(how='all')
df = df[df.fRunStart > '2018-01-01']
df['duration'] = df.fRunStop - df.fRunStart
df['on_time'] = (df['duration'] * df.fEffectiveOn) / np.timedelta64(1, 's')
df['hadron_rate'] = df.fNumThreshold750 / df.on_time

# example on how to cut later
# D = df.query('on_time > 100 & fZenithDistanceMean < 40 & fRunTypeKey==1 & hadron_rate < 4.8')

df.to_hdf('hadron_rate.h5', 'hadron_rate')
