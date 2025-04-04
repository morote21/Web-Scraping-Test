import pandas as pd
import numpy as np
from faker import Faker

datasets_folder = "..\\..\\dataset\\"
csv_path = datasets_folder + "nba_test_dataset.csv"

df = pd.read_csv(csv_path)

faker = Faker()

# Seleccionamos columnas de tipo float
float_cols = df.select_dtypes(include=["float"]).columns

df_info = {}
for c in float_cols:
    df_info[c] = {}
    df_info[c]["mean"] = df[c].mean()
    df_info[c]["std"] = df[c].std()

# Agrupamos temporada/conferencia/posicion y computamos media y desviacion estandar 
df_gb_mean = df.groupby(["Season", "Conference", "Position"]).mean(numeric_only=True)
df_gb_std = df.groupby(["Season", "Conference", "Position"]).std(numeric_only=True)

def randomize(r):
    r_copy = r.copy()

    for col in float_cols:
        key = (r_copy["Season"], r_copy["Conference"], r_copy["Position"])
        val = r_copy[col]
        if not np.isnan(val):
            mean, std = df_gb_mean.loc[key, col], df_gb_std.loc[key, col]
            r_copy[col] = np.random.uniform(val-std, val+std) 
    
    i = 4
    for col in float_cols:
        if "PCT" in col:
            pct = (r_copy.iloc[i - 2] / r_copy.iloc[i - 1]) * 100
            r_copy[col] = pct
        
        i += 1

    return r_copy


df_copy = df.copy()
df_copy = df_copy.apply(randomize, axis=1)

df_copy.to_csv(datasets_folder + "nba_test_dataset_rand_same_distr.csv", sep=",", index=False)
df_copy.to_csv(datasets_folder + "nba_test_dataset_rand_same_distr_excel.csv", sep=";", index=False)