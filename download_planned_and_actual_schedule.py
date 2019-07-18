from os import environ
import pandas as pd
from sqlalchemy import create_engine

db_connection_url = f"mysql+pymysql://fact:{environ['FACT_PASSWORD']}@ihp-pc45.ethz.ch/factdata"
eng = create_engine(
    db_connection_url,
    connect_args={'ssl': {'ssl-mode': 'required'}}
)


planned_schedule_query = """
SELECT
    fStart, fSourceName, fUser, fMeasurementTypeName
    FROM AutoSchedule
LEFT JOIN Source USING (fSourceKey)
LEFT JOIN MeasurementType USING (fMeasurementTypeKey)
ORDER BY fStart
"""
planned_schedule = pd.read_sql(planned_schedule_query, eng)
planned_schedule.to_hdf('planned_schedule.h5', 'planned')

actual_schedule_query = """
SELECT
   fStart, fSourceName, fUser, fMeasurementTypeName
   FROM Schedule
LEFT JOIN Source USING (fSourceKey)
LEFT JOIN MeasurementType USING (fMeasurementTypeKey)
ORDER BY fStart
"""
actual_schedule = pd.read_sql(actual_schedule_query, eng)
actual_schedule.to_hdf('actual_schedule.h5', 'actual')
