import pandas as pd

def load_schedules_actual_planned():
    result = []
    # order here is important .. 1st actual, 2nd planned
    for path in ["actual_schedule.h5", "planned_schedule.h5"]:
        schedule = pd.read_hdf(path)
        schedule.set_index("fStart", inplace=True)
        schedule.sort_index(inplace=True)
        result.append(schedule)

    return result

def join_with_schedules(df):
    actual, planned = load_schedules_actual_planned()
    colname_and_schedules = [
        ("planned_observation", planned, ('Startup',), ('Shutdown',)),
        ("actual_observation", actual, ('Startup', 'Resume'), ('Shutdown', 'Sleep', 'Suspend')),
    ]

    for colname, schedule, stafu, endfu, in colname_and_schedules:

        schedule = schedule[schedule.fMeasurementTypeName.isin(["Startup", "Shutdown"])]
        last_before = schedule[: df.index.min()].index.max()
        first_after = schedule[df.index.max() :].index.min()

        schedule = schedule[last_before:first_after]

        ## Join the planned schedule to the data
        stuff = df.join(schedule, how='outer')
        take_data = []
        previous = True
        for element in stuff.fMeasurementTypeName:
            if element in stafu:
                take_data.append(True)
            elif element in endfu:
                take_data.append(False)
            else:
                take_data.append(previous)
            previous = take_data[-1]

        stuff['take_data'] = take_data
        df[colname] = stuff.take_data[df.index]
    return df
