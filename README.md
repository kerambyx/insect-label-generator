# insect-label-generator
Python script that generates customizable insect labels based on CSV data. Uses the two label system (Data and ID) and outputs Letter sized sheets.

## Usage

```
$ python gen_labels.py labels.csv
```

CSV should be formatted with columns as follows:

```
country,province,city,locality,latitude,longitude,elevation,date,collector,order,family,genus,species,det.
```

