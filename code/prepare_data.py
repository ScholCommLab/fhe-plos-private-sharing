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

import pandas as pd

disciplines_csv = "data/external/PLOS_2015-2017_idArt-DOI-PY-Journal-Title-LargerDiscipline-Discipline-Specialty.csv"

# +
in_articles_csv = "data/input/articles.csv"
details_csv = "data/input/details.csv"
fb_metrics_csv = "data/input/fb_metrics.csv"
am_metrics_csv = "data/input/am_metrics.csv"
responses_csv = "data/input/fb_objects.csv"

out_articles_csv = "data/output/articles.csv"
metrics_csv = "data/output/metrics.csv"
# -

# # Load articles, responses, metrics

# +
# Load articles and extract years
all_articles = pd.read_csv(in_articles_csv, index_col="doi", parse_dates=['publication_date'])
all_articles['year'] = all_articles.publication_date.map(lambda x: x.year)

# Filter articles by year
min_year = 2015
all_articles = all_articles[all_articles.year >= min_year]

# replace authors of articles by PLOS without authors with "PLOS ONE"
all_articles.loc[all_articles[all_articles.author.isna()].index, "author"] = "PLOS ONE"
# -

# # Load responses and extract years
# all_responses = pd.read_csv(details_csv, index_col="id", parse_dates=['received_at', 'og_updated_time', 'publication_date', 'added_on'])
#
# # Filter responses, metrics, disciplines by selected articles
# all_responses = all_responses[all_responses.doi.isin(all_articles.index)]

# +
fb_metrics = pd.read_csv(fb_metrics_csv, index_col="doi")
fb_metrics = fb_metrics[fb_metrics.index.isin(all_articles.index)]

am_metrics = pd.read_csv(am_metrics_csv, index_col="doi")
am_metrics = am_metrics[am_metrics.index.isin(all_articles.index)]

all_metrics = fb_metrics.join(am_metrics, how="outer")
# -

# ## Altmetric responses

print("Altmetrics results - responses:", am_metrics.shape[0])
print("Altmetric results - non-zero responses", am_metrics.dropna(how="all").shape[0])
print("Altmetric results -  at least one POS:", am_metrics.facebook.replace(0, np.nan).count())
print("Altmetric results - at least one TW:", am_metrics.twitter.replace(0, np.nan).count())

# ## Graph API responses

print("FB responses - responses:", fb_metrics.shape[0])
print("FB responses - non-zero responses", fb_metrics.dropna(how="all").shape[0])
print("FB responses with at least one share:", fb_metrics.shares.replace(0, np.nan).count())
print("FB responses with at least one reaction:", fb_metrics.reactions.replace(0, np.nan).count())
print("FB responses with at least one comment:", fb_metrics.comments.replace(0, np.nan).count())
print("FB responses with at least one plugin comment:", fb_metrics.plugin_comments.replace(0, np.nan).count())

# ## Overall

print("Articles:", all_articles.shape[0])
print("Metrics:", all_metrics.shape[0])
print("Responses:", all_responses.shape[0])

# +
n_responses = all_responses[['reactions', 'shares', 'comments']].shape[0]
print("FB responses:", n_responses, 100*n_responses/618720)

zero_eng = sum(all_responses[['reactions', 'shares', 'comments']].sum(axis=1)==0)
print("Zero engagement:", zero_eng, 100*zero_eng/n_responses)
# -

# # Filter by bad facebook responses

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

print("Articles:", articles.shape[0])
print("Metrics:", metrics.shape[0])
print("Responses:", responses.shape[0])

# # Process metrics

# +
# Load metrics and rename columns
col_names = {
    'twitter': 'TW_og',
    'facebook': 'POS_og',
    'shares': 'AES_og',
    'reactions': 'AER_og',
    'comments' : 'AEC_og'
}

metrics.rename(columns=col_names, inplace=True)
# -

metrics.replace(0, np.nan)[['AES_og', 'AER_og', 'AEC_og']].dropna(how="all").shape

# +
# Replace any fb metric of 0 with nan
for _ in ['AES', 'AER', 'AEC', "POS", "TW"]:
    metrics[_] = metrics[_+"_og"][metrics[_+"_og"] != 0]
    
x = all_metrics[['AES_og', 'AEC_og', 'AER_og']] == 0
print("{} articles with 0/0/0 AE".format(x.all(axis=1).sum()))
print("{} articles with 0 POS".format(sum(all_metrics['POS_og']==0)))
print("{} articles with 0 TW".format(sum(all_metrics['TW_og']==0)))
# -

articles = articles.join(metrics[["AES", "POS", "TW", "AER", "AEC"]])

# # Process disciplines

# +
# Load disciplines
disciplines = pd.read_csv(disciplines_csv, delimiter=";", index_col="DOI")
disciplines.index = disciplines.index.map(lambda x: str(x)[4:])

col_names = {
    "EGrande_Discipline": "g_disc",
    "EDiscipline": "disc",
    "ESpecialite": "spec"
}
disciplines.rename(columns=col_names, inplace=True)
# -

# match articles by DOI is done
x = articles.join(disciplines[["g_disc", "disc", "spec"]], how="left")
print(x.index.duplicated().sum(), "articles with multiple disciplines. Selecting one randomly.")
x = x[~x.index.duplicated()]

# +
# convert titles to alphanum & lowercase
x['title_'] = x['title'].map(lambda x: ''.join(e for e in x.lower() if e.isalnum()))
disciplines['title_'] = disciplines['title'].map(lambda x: ''.join(e for e in x.lower() if e.isalnum()))

# select those that still miss disciplines
missings = x[x.disc.isna()].copy()
missings = missings.drop(["g_disc", "disc", "spec"], axis=1)
print("Missing articles after DOI matching:", missings.shape[0])

# +
# try to match these with titles and replace in x
found = missings.reset_index().merge(disciplines[["g_disc", "disc", "spec", "title_"]], left_on="title_", right_on="title_", how="inner").set_index('index')
print("Title matching found:", found.shape)
x.loc[found.index] = found

# select those that still miss disciplines
missings = x[x.disc.isna()].copy()
missings = missings.drop(["g_disc", "disc", "spec"], axis=1)
print("Missing articles after title matching:", missings.shape[0])
# -

articles = x.drop(columns="title_")

# +
author_plos = articles.author.str.contains("PLOS")
type_corr = articles.title.str.contains("Correction: ")
type_retr = articles.title.str.contains("Retraction: ")

print("Artices by PLOS", author_plos.sum())
print("Corrections", type_corr.sum())
print("Retractions", type_retr.sum())
print("")
print("Articles with disciplines:", sum(~articles.disc.isna()))
print("Total articles not covered by Piwowar et al:", sum([any(x) for x in zip(author_plos, type_corr, type_retr)]))
print("Actual missing articles:", articles.disc.isna().sum()-sum([any(x) for x in zip(author_plos, type_corr, type_retr)]))

# +
articles.index.name = "doi"

articles.to_csv("data/articles.csv")
responses.to_csv("data/responses.csv")
