# rain_and_wind_auto_park
A continously running process, which modifies the FACT schedule in order to park in case of adverse weather conditions

## Plan for software development stuff

 - we want a project that can be "pip installed", like:
     pip install rain_and_wind_...
   for this we need a `setup.py` file in our project.

 - in the end, we want a single program, which can be called (started) on LA Palma, maybe with a command like: ".. dunno .." for this, we need to devine a "console_script" inside the setup.py, so we automatically get a callable "entry point" after the installation.





