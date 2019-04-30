''' this needs a doc-string

for testing do:

CREATE TABLE rain_and_wind_test_schedule_002 LIKE factdata.Schedule;
INSERT INTO rain_and_wind_test_schedule_002 SELECT * FROM factdata.Schedule;

'''
import yaml
from contextlib import contextmanager
from sqlalchemy import create_engine
from datetime import timedelta, datetime
import pandas as pd

def make_engines(path='db_credentials.yml'):
    db_credentials = yaml.load(open(path, 'r'))
    return {
        name: create_engine(cred)
        for name, cred in db_credentials.items()
    }


@contextmanager
def connect(engine):
    connection = engine.connect()
    yield connection
    connection.close()


@contextmanager
def connect_and_lock(engine, table_name):
    '''
    NOTE: connection.execute(f"LOCK TABLES {table_name} WRITE")
    will *BLOCK* until the table is unlocked by whoever was locking it.
    this is not good ... it will block forever and this process will simply
    halt...
    but ... since it is quite unlikely ... for the moment
    I will just accept it
    '''
    with connect(engine) as connection:
        connection.execute(f"LOCK TABLES {table_name} WRITE")
        yield connection
        connection.execute("UNLOCK TABLES")


def select_all_from_locked_table(engine, table_name):
    with connect_and_lock(engine, table_name) as connection:
        result = connection.execute(f"SELECT * FROM {table_name}")
        for row in result:
            yield row


def select_all_from_table(engine, table_name):
    with connect(engine) as connection:
        result = connection.execute(f"SELECT * FROM {table_name}")
        for row in result:
            yield row


def gather_measurement_type_name_to_key_dict(engine):
    # ~134 ms
    measurement_type_names = {}
    for row in select_all_from_table(engine, 'factdata.MeasurementType'):
        name = row['fMeasurementTypeName']
        key = row['fMeasurementTypeKey']
        measurement_type_names[name] = key

    return measurement_type_names


def select_rows_between_now_and_next_noon(
    current_time,  # datetime object
    table_name,
    connection,
    time_column_name='fStart',
):
    next_noon = make_next_noon_from_datetime(current_time)

    query = f'''
        SELECT *
        FROM {table_name}
        WHERE {time_column_name}
        BETWEEN '{current_time:%Y-%m-%d %H:%M:%S}' AND
            '{next_noon:%Y-%m-%d %H:%M:%S}'
    '''
    result = connection.execute(query)
    list_of_dicts = [dict(row.items()) for row in result]
    return list_of_dicts


def delete_entries_for_rows(rows, table_name, connection):

    for row in rows:
        query = f'''
            DELETE FROM {table_name}
            WHERE fScheduleID={row['fScheduleID']}
        '''
        connection.execute(query)


def convert_datetime(dt):
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def insert_rows_into_table(rows, table_name, connection):
    '''
      # INSERT INTO tbl_name (a,b,c) VALUES(1,2,3),(4,5,6),(7,8,9);
    '''
    field_names__converts = [
        ('fStart', convert_datetime),
        ('fMeasurementID', int),
        ('fUser', 'rain_and_wind'),
        ('fData', str),
        ('fSourceKey', int),
        ('fMeasurementTypeKey', int),
    ]

    for row in rows:
        fields = []
        values = []
        for field_name, convert in field_names__converts:
            value = row.get(field_name, None)
            if field_name == 'fUser':
                str_value = convert
            else:
                if value is None:
                    continue
                if convert is None:
                    str_value = str(value)
                else:
                    str_value = convert(value)
            fields.append(field_name)
            values.append(str_value)

        fields = '(' + ', '.join(fields) + ')'
        values = repr(tuple(values))
        query = f'''
            INSERT INTO {table_name}
            {fields}
            VALUES
            {values}
        '''
        connection.execute(query)


def find_shutdown_in_list_of_tasks(tasks, measurement_type_names):
    shutdown_id = measurement_type_names['Shutdown']
    for i, row in enumerate(tasks):
        if row['fMeasurementTypeKey'] == shutdown_id:
            return i
    return None


def make_next_noon_from_datetime(dt):
    tomorrow = (dt + timedelta(hours=12)).date()
    next_noon = datetime(
        tomorrow.year,
        tomorrow.month,
        tomorrow.day,
        12
    )
    return next_noon


def test_make_next_noon_from_datetime():
    inputs_and_expected_outputs = [
        ('2015-02-28T11:59', '2015-02-28T12:00'),
        ('2015-02-28T12:00', '2015-03-01T12:00'),
        ('2015-02-28T12:01', '2015-03-01T12:00'),
        ('2015-02-28T23:59', '2015-03-01T12:00'),
        ('2015-03-01T00:00', '2015-03-01T12:00'),
        ('2015-03-01T04:00', '2015-03-01T12:00'),
        ('2015-03-01T11:59', '2015-03-01T12:00'),
        # 2016 was a leap-year
        ('2016-02-28T18:00', '2016-02-29T12:00'),

    ]
    for in_, out in inputs_and_expected_outputs:
        current_time = datetime.fromisoformat(in_)
        expected_out = datetime.fromisoformat(out)
        result = make_next_noon_from_datetime(current_time)
        assert result == expected_out


@contextmanager
def generic(
    now,
    table_name,
    engine,
):
    with connect_and_lock(engine, table_name) as connection:

        tasks = select_rows_between_now_and_next_noon(
            now, table_name, connection
        )
        delete_entries_for_rows(tasks, table_name, connection)
        yield tasks
        insert_rows_into_table(tasks, table_name, connection)


def insert_suspend_task_into_table_now(
    now,
    table_name,
    engine,
):
    measurement_type_names = gather_measurement_type_name_to_key_dict(engine)

    with generic(now, table_name, engine) as tasks:
        add_suspend_to_tasks(tasks, now, measurement_type_names)


def add_suspend_to_tasks(rows, now, measurement_type_names):
    '''
    MODIFYIES ROWS IN PLACE
    add a suspend task at the beginning of the task list now
    and add a resume task after the shutdown task.
    '''
    remove_existing_suspend_resume_in_place(rows, measurement_type_names)

    suspend_task = {
        # TODO: make sure this time is really smaller than the time
        #       of the first task in the list of tasks
        #       but it also must not be smaller than the
        'fStart': now,
        'fMeasurementID': 0,
        'fMeasurementTypeKey': measurement_type_names['Suspend'],
    }

    position_of_shutdown = find_shutdown_in_list_of_tasks(
        rows, measurement_type_names
    )
    shutdown_task = rows[position_of_shutdown]

    # TODO: normally, shutdown is simply the last task in this list..
    #      I am not sure .. should we print a warning or so,
    #       if this is not the case?

    # TODO: normally there should be only one shutdown in this list ...
    #      I am not sure .. should we somehow notify
    #       if there are more shutdowns?

    resume_task = {
        'fStart': shutdown_task['fStart'] + timedelta(minutes=1),
        'fMeasurementID': 0,
        'fMeasurementTypeKey': measurement_type_names['Resume'],
    }

    rows.insert(0, suspend_task)
    rows.append(resume_task)


def insert_resume_task_into_table_now(
    now,
    table_name,
    engine,
):
    measurement_type_names = gather_measurement_type_name_to_key_dict(engine)

    with generic(now, table_name, engine) as tasks:
        put_resume_now(tasks, now, measurement_type_names)


def put_resume_now(rows, now, measurement_type_names):
    '''
    MODIFYIES ROWS IN PLACE
    add a resume task now into the list of tasks and remove any
    other resume tasks in the future
    '''
    remove_existing_suspend_resume_in_place(rows, measurement_type_names)

    resume_task = {
        # TODO: make sure this time is really smaller than the time
        #       of the first task in the list of tasks
        #       but it also must not be smaller than the
        'fStart': now,
        'fMeasurementID': 0,
        'fMeasurementTypeKey': measurement_type_names['Resume'],
    }

    rows.insert(0, resume_task)


def remove_existing_suspend_resume_in_place(rows, measurement_type_names):

    ids_of_suspend_and_resume_tasks = sorted(
        [
            i for i, row in enumerate(rows)
            if row['fMeasurementTypeKey']
            in (
                measurement_type_names['Resume'],
                measurement_type_names['Suspend'],
            )
        ],
        reverse=True
    )

    # remove these ids from the list
    # in reverted order so the ids stay valid
    for id_ in ids_of_suspend_and_resume_tasks:
        rows.pop(id_)


def show_last_n_rows(TABLE, engine, n=13):
    return pd.read_sql_query(
        f'''
        SELECT fStart, fScheduleID, fUser, fSourceName, fMeasurementTypeName
        FROM {TABLE}
        INNER JOIN factdata.MeasurementType
        ON {TABLE}.fMeasurementTypeKey =
            factdata.MeasurementType.fMeasurementTypeKey
        LEFT JOIN factdata.Source
        ON {TABLE}.fSourceKey = factdata.Source.fSourceKEY
        order by fStart desc limit {n}
        ''',
        engine
    ).set_index('fStart').sort_index()
