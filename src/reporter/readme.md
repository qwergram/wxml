# Reporter

A simple script to report a list of unexpected precinct data.

For instance: `python reporter/ file_input/ "WA_GEO_ID" "NAME10" "REG_08" "ALAND10" txt` will export a csv file of issues.
Issues are:

- Multi polygon precincts
- Precincts with a cumulative landmass of 0
- Precincts with no population
- Precincts with no valid precinct tag

## Example Output

Command: `python reporter/ file_input/ "WA_GEO_ID" "NAME10" "REG_08" "ALAND10" txt`

Output: [![](https://imgur.com/OJ2qfdU.png)](https://github.com/pengra/wxml/blob/master/src/reporter/example.csv)