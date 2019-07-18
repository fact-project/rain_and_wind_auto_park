import pandas as pd

def calculate_hyst(rolling, hyst_min, hyst_window):
    """Prevent decisions from happening "too quickly"
    """
    hyst = []
    hyst_max = hyst_min + hyst_window
    previous = True
    for i in rolling:
        if i <= hyst_min:
            hyst.append(False)
        elif i >= hyst_max:
            hyst.append(True)
        elif (i >= hyst_min) & (i <= hyst_max):
            hyst.append(previous)
        else:
            # this only happens if i is not a number: np.nan
            hyst.append(previous)
        previous = hyst[-1]

    new_column = pd.Series(hyst, index=rolling.index)
    return new_column

