# Crossfit
To produce score distributions for 202* Crossfit Open

# How to
The tool is based on selenium for parsing score data and ROOT for ploting
```bash
# installation
# assumed conda has been installed
conda create -n open python=3.11
conda activate open
pip install selenium
conda install -c conda-forge ROOT
```
parse data and plot
```bash
# parse data - the scores will be stored as logs/scores.$DATE.$TIME.csv
python parse_scores.py
# plot, based on specific open workout, e.g. Open 24.1
python plot_24p1.py --file logs/scores.2024-03-02.20-50-04.csv
```
