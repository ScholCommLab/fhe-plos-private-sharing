# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.3'
#       jupytext_version: 1.0.5
#   kernelspec:
#     display_name: altmetrics
#     language: python
#     name: altmetrics
# ---

# + {"cell_type": "markdown", "toc-hr-collapsed": false}
# # Preprocessing of data for: How much research shared on Facebook is hidden from public view?
#
# 1. Load required data and provide some basic stats
# 2. Remove all articles that have been wrongly aggregated by Facebook
# 3. Process collected metrics
# 4. Match articles with disciplinary information
# 5. Write output files used in analysis notebook
# -

import pandas as pd

# ## 1. Load required data and provide some basic stats

# +
# Input data
disciplines_csv = "data/external/PLOS_2015-2017_idArt-DOI-PY-Journal-Title-LargerDiscipline-Discipline-Specialty.csv"

in_articles_csv = "data/input/plos_one_articles.csv"
details_csv = "data/input/query_details.csv"
fb_metrics_csv = "data/input/graph_api_counts.csv"
am_metrics_csv = "data/input/altmetric_counts.csv"

# Output data
out_articles_csv = "data/articles.csv"
out_responses_csv = "data/responses.csv"

# +
# Load articles and extract years
all_articles = pd.read_csv(in_articles_csv, index_col="doi", parse_dates=['publication_date'])
all_articles['year'] = all_articles.publication_date.map(lambda x: x.year)

# Replace authors of articles by PLOS without author information with "PLOS ONE"
all_articles.loc[all_articles[all_articles.author.isna()].index, "author"] = "PLOS ONE"
# -

# Load responses
all_responses = pd.read_csv(details_csv, index_col="id", parse_dates=['received_at', 'og_updated_time', 'publication_date', 'added_on'])

# +
# Load both metrics files and merge
fb_metrics = pd.read_csv(fb_metrics_csv, index_col="doi")
am_metrics = pd.read_csv(am_metrics_csv, index_col="doi")
all_metrics = fb_metrics.join(am_metrics, how="outer")

# Rename the metrics
col_names = {
    'twitter': 'TW_og',
    'facebook': 'POS_og',
    'shares': 'AES_og',
    'reactions': 'AER_og',
    'comments' : 'AEC_og'
}
all_metrics.rename(columns=col_names, inplace=True)

# +
# Load disciplines
disciplines = pd.read_csv(disciplines_csv, delimiter=";", index_col="DOI")
disciplines.index = disciplines.index.map(lambda x: str(x)[4:])

# Rename columns
col_names = {
    "EGrande_Discipline": "grand_discipline",
    "EDiscipline": "discipline",
    "ESpecialite": "specialty"
}
disciplines.rename(columns=col_names, inplace=True)

# + {"cell_type": "markdown", "toc-hr-collapsed": false}
# **Some basic stats about the data before processing steps were applied:**
# -

print("Altmetrics results - responses:", am_metrics.shape[0])
print("Altmetric results - non-zero responses", am_metrics.dropna(how="all").shape[0])
print("Altmetric results -  at least one POS:", am_metrics.facebook.replace(0, np.nan).count())
print("Altmetric results - at least one TW:", am_metrics.twitter.replace(0, np.nan).count())

print("FB responses - responses:", fb_metrics.shape[0])
print("FB responses - non-zero responses", fb_metrics.dropna(how="all").shape[0])
print("FB responses with at least one share:", fb_metrics.shares.replace(0, np.nan).count())
print("FB responses with at least one reaction:", fb_metrics.reactions.replace(0, np.nan).count())
print("FB responses with at least one comment:", fb_metrics.comments.replace(0, np.nan).count())
print("FB responses with at least one plugin comment:", fb_metrics.plugin_comments.replace(0, np.nan).count())

n = len(all_metrics.replace(0, np.nan)[['AES_og', 'AER_og', 'AEC_og']].dropna(how="all"))
print("Articles with at least one share, reaction, or comment on Facebook: {}".format(n))

# +
n_responses = all_responses[['reactions', 'shares', 'comments']].shape[0]
print("FB queries that returned results: {} ({:.2f}%)".format(n_responses, 100 * n_responses / all_articles.shape[0] / 10))

zero_eng = sum(all_responses[['reactions', 'shares', 'comments']].sum(axis=1)==0)
print("Responses with no engagement at all: {} ({:.2f}%)".format(zero_eng, 100*zero_eng/n_responses))
# -

print("FB queries with results:", all_responses.shape[0])
print("Found articles:", all_articles.shape[0])
print("Found articles with metrics:", all_metrics.shape[0])

# ## 2. Remove all articles that have been wrongly aggregated by Facebook
#
# The following steps removes articles that were wrongly aggregated within the Facebook social graph. See Enkhbayar and Alperin (2018) for more information.

# +
ogid_counts = all_responses.groupby(["doi", "og_id"]).size().groupby(['og_id']).count()

bad_ogids = ogid_counts[ogid_counts>1].keys()
bad_dois = all_responses[all_responses.og_id.isin(bad_ogids)].doi

responses = all_responses[~all_responses.doi.isin(bad_dois)]
articles = all_articles.drop(bad_dois, axis=0)
metrics = all_metrics.drop(bad_dois, axis=0)

dropped_years = all_articles.reindex(bad_dois).year.value_counts()

# Article counts - base dataset
n_articles_by_year = articles.groupby("year").count()['title']
n_all_articles_by_year = all_articles.groupby("year").count()['title']

df_article_counts = pd.DataFrame({
    'All articles': n_all_articles_by_year,
    'Dropped': dropped_years,
    'Final article count': n_articles_by_year
})
df_article_counts.loc['All years'] = df_article_counts.sum(axis=0)
df_article_counts.index.name = ""

df_article_counts
# -

# ## 3. Process collected metrics
#
# Replace zero counts with NAs.

# +
# Replace any fb metric of 0 with nan
for _ in ['AES', 'AER', 'AEC', "POS", "TW"]:
    all_metrics[_] = all_metrics[_+"_og"][all_metrics[_+"_og"] != 0]
    
x = all_metrics[['AES_og', 'AEC_og', 'AER_og']] == 0
print("{} articles with 0/0/0 AE".format(x.all(axis=1).sum()))
# -

# Add metrics to articles
articles = articles.join(all_metrics[["AES", "POS", "TW", "AER", "AEC"]])

# ## 4. Match articles with disciplinary information
#
# Disciplinary information for each article is provided by Piwowar et al. (2018). In order to use the data the articles were matched with several steps:
#
# 1. Match articles by DOIs
# 2. Match articles by titles (after conversion to alphanum & lowercase)
#
# In 6 cases the disciplinary information provided multiple disciplines for articles in which we chose one randomly.

# Convert titles to alphanum & lowercase for in both datasets
articles['title_'] = articles['title'].map(lambda x: ''.join(e for e in x.lower() if e.isalnum()))
disciplines['title_'] = disciplines['title'].map(lambda x: ''.join(e for e in x.lower() if e.isalnum()))

# +
# Naive join of articles and disciplinary information by DOIs
x = articles.join(disciplines[["grand_discipline", "discipline", "specialty"]], how="left")

# Articles with multiple disciplines
print(x.index.duplicated().sum(), "articles with multiple disciplines. Selecting one randomly.")

# Dropping of the duplicate disciplines randomly
x = x[~x.index.duplicated()]
# -

# select those that still miss disciplines
missings = x[x.discipline.isna()].copy()
missings = missings.drop(["grand_discipline", "discipline", "specialty"], axis=1)
print("Missing articles after DOI matching:", missings.shape[0])

# +
# try to match these with titles and replace in x
found = missings.reset_index().merge(disciplines[["grand_discipline", "discipline", "specialty", "title_"]], left_on="title_", right_on="title_", how="inner").set_index('index')
print("Title matching found:", found.shape[0])
x.loc[found.index] = found

# select those that still miss disciplines
missings = x[x.discipline.isna()].copy()
missings = missings.drop(["grand_discipline", "discipline", "specialty"], axis=1)
print("Missing articles after title matching:", missings.shape[0])
# -

# drop temp column with modified titles
articles = x.drop(columns="title_")

# +
author_plos = articles.author.str.contains("PLOS")
type_corr = articles.title.str.contains("Correction: ")
type_retr = articles.title.str.contains("Retraction: ")

print("Artices by PLOS", author_plos.sum())
print("Corrections", type_corr.sum())
print("Retractions", type_retr.sum())
# -

df = pd.DataFrame(columns=["Count"])
df.loc['Articles with disciplines'] = sum(~x.discipline.isna())
df.loc['Articles not in disc. dataset'] = sum([any(x) for x in zip(author_plos, type_corr, type_retr)])
df.loc['Actual missing articles'] = x.discipline.isna().sum()-sum([any(x) for x in zip(author_plos, type_corr, type_retr)])
df.loc['Sum'] = df.sum()
df

# ## 5. Write output files used in analysis notebook

# +
articles.index.name = "doi"

articles.to_csv("data/articles.csv")
responses.to_csv("data/responses.csv")

# + {"cell_type": "markdown", "toc-hr-collapsed": false}
# # References
#
# Enkhbayar, A., & Alperin, J. P. (2018). Challenges of capturing engagement on Facebook for Altmetrics. STI 2018 Conference Proceedings, 1460–1469. Retrieved from http://arxiv.org/abs/1809.01194
#
# Piwowar, H., Priem, J., Larivière, V., Alperin, J. P., Matthias, L., Norlander, B., … Haustein, S. (2018). The state of OA: A large-scale analysis of the prevalence and impact of Open Access articles. PeerJ, 6, e4375. doi: [10/ckh5](https://doi.org/10/ckh5)
