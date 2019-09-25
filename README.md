![logo](logo.png)

# Reproduction code for: 

> 
*Authors: Asura Enkhbayar, Stefanie Haustein, Juan Pablo Alperin*

| Resource | Link |
|-|-|
| Preprint | TBD |
| Article | TBD |
| Code | TBD |
| Data | TBD |

---

This repository contains all figures and tables present in the manuscript for "". Output files can be found in:

- `figures/` - contains all figures used in the manuscript
- `tables/` - contains all programmatically created tables used in the manuscript

Furthermore, all the input data and code required to reproduce results are provided with instructions. Provided scripts include:

- `download_data.sh` - to download input data
- `prepare_data.py` - data preprocessing
- `analysis.py` - data analysis and outputs

This article is part of a broader investigation of the hidden engagement on Facebook. More information about the project can be found [here](https://github.com/ScholCommLab/facebook-hidden-engagement).

## Initial Data Collection

The data used in this paper was collected using our own methods. The data collection method is described in [Enkhbayar and Alperin (2018)(https://arxiv.org/abs/1809.01194)]. Code & instructions can be found [here](https://github.com/ScholCommLab/fhe-private-sharing).

## Reproduce results

All scripts have been written with Python 3.5+. To explore results interactively a working instance of Jupyter Notebooks/Labs is required.

Packages specified in `requirements.txt` can be installed via

```pip install -r requirements.txt```

1. Clone this repository and cd into the scripts folder

    ```
    git clone git@github.com:ScholCommLab/fhe-private-sharing.git
    cd fhe-plos-paper/scripts
    ```

2. Download data from Dataverse.

    All the data is hosted on dataverse: TBD

    Using the helper script provided, you can download all files into the respective locations. Make the script executable and ensure that you have `wget` installed.

    ```
    chmod +x download_data.sh
    ./download_data.sh
    ```

3. Preprocess data

    Run the preprocessing script to apply transformations on the input dataset. This step creates the file `data/articles.csv`

    ```python process_data.py```

4. (Re)produce results

    Run the analysis script to produce figures and tables.

    ```python analysis.py```

    Optionally, you can also open the notebook `analysis.ipynb` with Jupyter to explore the dataset and results.
