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

<img width="1700" height="2200" alt="sample labels" src="https://github.com/user-attachments/assets/bcb61d1a-246c-43c6-b8d6-af47660513b8" />
