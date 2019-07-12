''' functions to interact with FACT scheduling DB

The scheduling DB contains a table behind this website:
    https://www.fact-project.org/schedule/

In order to suspend or resume the FACT observation for some time use
these functions:

 * insert_suspend_task_into_table_now(now, name, engine)
 * insert_resume_task_into_table_now(now, name, engine)

In order to create one or many engines, just write the connection
credentials into a YAML (text) file like this:

engine_name: mysql+pymysql://user:password@host/db_name

Make sure to never commit this file into version control (git) since
login credentials should never be stored somewhere on a public server.

and then create the engine like:

    engine = make_engines(path)['engine_name']

Depending on use-case one might need different engines, like sandbox or
factread.


For testing these functions you might want to create a copy of the real
Schedule table into the sandbox database. For this the function
`make_copy_for_testing()` can be used.

Finally in order to see, if the functions worked as expected,
it is convenient to look at the last N rows of the schedule table.
For this the function `show_last_n_rows(table_name, engine, n)`
should be convenient.

There is also a Jupyter notebook called database_example.ipynb
which can be used to explore these functions.
'''
from contextlib import contextmanager
from datetime import timedelta, datetime
import yaml
from sqlalchemy import create_engine
import pandas as pd


def insert_suspend_task_into_table_now(
        now,
        table_name,
        engine,
):
    '''insert suspend task `now` into table with `table_name`
    using `engine` to connect to DB server.

    in addition to inserting the suspend task right now, it will also
    insert an additional resume task after the next shutdown.

    It will also remove all pre-existing suspend and resume tasks between
    now and the next noon (which is astronomers end of day.)

    Takes ~1.3 sec.

    Parameters:
    -----------
    now: datetime object
        time where suspend task should be entered into schedule
    table_name:  str
        name of table to write into should be "Schedule" unless during tests
    engine: sqlalchemy.Engine
        engine instance used to connect to DB
    '''
    measurement_type_names = gather_measurement_type_name_to_key_dict(engine)

    with generic(now, table_name, engine) as tasks:
        add_suspend_to_tasks_in_place(tasks, now, measurement_type_names)


def insert_resume_task_into_table_now(
        now,
        table_name,
        engine,
):
    '''insert resume task `now` into table with `table_name`
    using `engine` to connect to DB server.

    in addition to inserting the resume task right now, it will also remove
    the already existing resume task, which should be coming after the next
    shutdown. It does this by removing all kinds of pre-existing suspend or
    resume tasks between now and next noon (which is astronomers end of day).

    Takes ~1.3 sec.

    Parameters:
    -----------
    now: datetime object
        time where suspend task should be entered into schedule
    table_name:  str
        name of table to write into should be "Schedule" unless during tests
    engine: sqlalchemy.Engine
        engine instance used to connect to DB
    '''
    measurement_type_names = gather_measurement_type_name_to_key_dict(engine)

    with generic(now, table_name, engine) as tasks:
        put_resume_now_in_place(tasks, now, measurement_type_names)


def make_copy_for_testing(
        engine,
        copy_name='rain_and_wind_test_schedule',
        original_name='factdata.Schedule',
):
    '''copy table for testing'''
    orig = original_name
    copy = copy_name
    with connect(engine) as conn:
        conn.execute(f'DROP TABLE IF EXISTS {copy}')
        conn.execute(f'CREATE TABLE {copy} LIKE {orig}')
        conn.execute(f'INSERT INTO {copy} SELECT * FROM {orig}')
    return copy_name


def show_last_n_rows(table_name, engine, n=13):
    '''convenience function to look at "factdata.Schedule" or copies of it'''
    return pd.read_sql_query(
        f'''
        SELECT fStart, fScheduleID, fUser, fSourceName, fMeasurementTypeName
        FROM {table_name}
        INNER JOIN factdata.MeasurementType
        ON {table_name}.fMeasurementTypeKey =
            factdata.MeasurementType.fMeasurementTypeKey
        LEFT JOIN factdata.Source
        ON {table_name}.fSourceKey = factdata.Source.fSourceKEY
        order by fStart desc limit {n}
        ''',
        engine
    ).set_index('fStart').sort_index()


def make_engines(path='db_credentials.yml'):
    '''read yml file from `path` and return dict of `sqlalchemy.Engine`s'''
    db_credentials = yaml.load(open(path, 'r'))
    return {
        name: create_engine(cred)
        for name, cred in db_credentials.items()
    }


# ----------------------------------------------------------------------------
# ----- below this line there are the ugly internals of this module ----------
# ----------------------------------------------------------------------------


@contextmanager
def connect(engine):
    '''contect manager to open and close connection'''
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


def select_all_from_table(engine, table_name):
    with connect(engine) as connection:
        result = connection.execute(f"SELECT * FROM {table_name}")
        for row in result:
            yield row


def gather_measurement_type_name_to_key_dict(engine):
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


def add_suspend_to_tasks_in_place(rows, now, measurement_type_names):
    '''
    MODIFYIES ROWS IN PLACE
    add a suspend task at the beginning of the task list now
    and add a resume task after the shutdown task.
    '''
    remove_existing_suspend_resume_in_place(rows, measurement_type_names)

    starts = [row['fStart'] for row in rows]
    # we have to make sure now is not identical to an existing entry,
    # so we add seconds until we found a time, which does not happen
    # to exist already
    while now in starts:
        now += timedelta(seconds=1)

    suspend_task = {
        'fStart': now,
        'fMeasurementID': 0,
        'fMeasurementTypeKey': measurement_type_names['Suspend'],
    }

    position_of_shutdown = find_shutdown_in_list_of_tasks(
        rows, measurement_type_names
    )
    shutdown_task = rows[position_of_shutdown]

    resume_task = {
        'fStart': shutdown_task['fStart'] + timedelta(minutes=1),
        'fMeasurementID': 0,
        'fMeasurementTypeKey': measurement_type_names['Resume'],
    }

    rows.insert(0, suspend_task)
    rows.append(resume_task)


def put_resume_now_in_place(rows, now, measurement_type_names):
    '''
    MODIFYIES ROWS IN PLACE
    add a resume task now into the list of tasks and remove any
    other resume tasks in the future
    '''
    remove_existing_suspend_resume_in_place(rows, measurement_type_names)

    starts = [row['fStart'] for row in rows]
    # we have to make sure now is not identical to an existing entry,
    # so we add seconds until we found a time, which does not happen
    # to exist already
    while now in starts:
        now += timedelta(seconds=1)

    resume_task = {
        'fStart': now,
        'fMeasurementID': 0,
        'fMeasurementTypeKey': measurement_type_names['Resume'],
    }

    rows.insert(0, resume_task)


def remove_existing_suspend_resume_in_place(rows, measurement_type_names):
    # we need to iterate in reversed order so the indices stay valid
    # while modifying in place
    for i, row in reversed(list(enumerate(rows))):
        if row['fMeasurementTypeKey'] in (
            measurement_type_names['Resume'],
            measurement_type_names['Suspend'],
        ):
            rows.pop(i)
