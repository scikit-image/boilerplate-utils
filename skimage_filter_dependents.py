"""
At the time this script was created (July 2020), GitHub did not offer an
official way to query dependent packages through their API. So, we went
for a web-scraping approach using BeautifulSoup, patterned after a response
in this stack-overflow thread:
https://stackoverflow.com/questions/58734176/how-to-use-github-api-to-get-a-repositorys-dependents-information-in-github

To retrieve topic lists via the GitHub API, the user must have defined a
GITHUB_TOKEN environment variable.

This script generates three lists of packages:

1.) One that has ALL dependents that are active repositories (i.e. no "Ghost"
icon in the web page).
2.) Another one that only retains packages with >= min_stars stars, but also
includes a list of the GitHub "topics" associated with each package.
3.) A third list that is based on filtering the second list. During filtering,
a package is retained if either:
    a.) Any string from repo_name_terms is in the repository organization/name
    b.) A topic in the repo's topic list matches a topic in topic_search_terms

The three variables containing the lists described above are:

Outputs
-------
all_packages : list of tuple
    Each element is a (name, forks, stars) tuple.
popular_packages : list of tuple
    Each element is a (name, forks, stars, topics) tuple.
popular_filtered_packages : list, tuple
    Each element is a (name, forks, stars, topics) tuple.
"""

import os
import pickle

from bs4 import BeautifulSoup
from github import Github
import pandas
import requests

# we use PyGitHub to retrieve topic lists
token = os.environ['GITHUB_TOKEN']
g = Github(token)

# ----------------------------------
# START OF USER-CONFIGURABLE OPTIONS
# ----------------------------------

# The repository we will query (whose dependents we want to find)
repo_to_query = "scikit-image/scikit-image"

# Retrieve detailed topic lists only for packages with >= min_stars stars.
min_stars = 5

# If True, will write the three lists to .pickle files in the current directory
save_to_pickle = False
# If True, will write the three lists to .csv files in the current directory
save_to_csv = True

# Search terms of interest in the repository organization/name.
# (see description at top)
# All terms should be in lower case.
repo_name_terms = [
    'brain',
    'cell',
    'ecg',
    'eeg',
    'medi',
    'mri',
    'neuro',
    'pathol',
    'retin',
    'slide',
    'spectro',
    'tissue',
    'tomo',
]

# Search terms of interest in the repository's topics (see description at top).
# This list was created to match bio-image applications by manually curating
# topic names from the full list of dependent packages.
topic_search_terms = [
    'airways',
    'anatomy',
    'arteries',
    'astrocytes',
    'atomic-force-microscopy',
    'afm',
    'axon',
    'bioimage-informatics',
    'bioinformatics',
    'biologists',
    'biomedical-image-processing',
    'bionic-vision',
    'biophysics',
    'brain-connectivity',
    'brain-imaging',
    'brain-mri',
    'brain-tumor-segmentation',
    'brats',
    'calcium',
    'cancer-research',
    'cell-biology',
    'cell-detection',
    'cell-segmentation',
    'computational-pathology',
    'connectome',
    'connectomics',
    'cryo-em',
    'ct-data',
    'deconvolution-microscopy',
    'dicom',
    'dicom-rt',
    'digital-pathology-data',
    'digital-pathology',
    'digital-slide-archive',
    'dmri',
    'electron-microscopy',
    'electrophysiology',
    'fluorescence',
    'fluorescence-microscopy-imaging',
    'fmri',
    'fmri-preprocessing',
    'functional-connectomes',
    'healthcare-imaging',
    'histology',
    'voxel',
    'microorganism-colonies',
    'microscopy',
    'microscopy-images',
    'neuroimaging',
    'medical',
    'medical-image-computing',
    'medical-image-processing',
    'medical-images',
    'medical-imaging',
    'mri',
    'myelin',
    'neural-engineering',
    'neuroanatomy',
    'neuroimaging',
    'neuroimaging-analysis',
    'neuropoly',
    'neuroscience',
    'nih-brain-initiative',
    'openslide',
    'pathology',
    'pathology-image',
    'radiation-oncology',
    'radiation-physics',
    'raman',
    'retinal-implants',
    'scanning-probe-microscopy',
    'scanning-tunnelling-microscopy',
    'single-cell-imaging',
    'slide-images',
    'spectroscopy',
    'spinalcord',
    'stm',
    'stem',
    'stitching',
    'structural-connectomes',
    'tissue-localization',
    'tomography',
    'volumetric-images',
    'whole-slide-image',
    'whole-slide-imaging',
]

# Omit the following repositories from the filtered list.
# These match at least one of the search terms above, but do not appear to be
# biology-focused. (e.g. the term "cell" appears in "Marcello").
omit_list = [
    'Marcello-Sega/pytim',
    'PMEAL/porespy'
]

# --------------------------------
# END OF USER-CONFIGURABLE OPTIONS
# --------------------------------

# Parse at most this many web pages.
# Parsing should automatically stop when reaching the last page.
max_page_num = 100

packages = True
url = ('https://github.com/{}/network/dependents'
       '?dependent_type=PACKAGE').format(repo_to_query)

package_list = []
ghost_list = []
prev_len = 0
for i in range(max_page_num):
    # retrieve HTML for the current URL
    print("GET " + url)
    r = requests.get(url)
    soup = BeautifulSoup(r.content, "html.parser")

    page_package_list = []
    page_ghost_list = []
    for t in soup.findAll("div", {"class": "Box-row"}):
        try:
            # find repository org/name
            name = "{}/{}".format(
                t.find('a', {"data-repository-hovercards-enabled": ""}).text,
                t.find('a', {"data-hovercard-type": "repository"}).text
            )
        except AttributeError:
            # Ghost repositories will give None for the find() calls above.
            # This results in an AttributeError when trying to access .text
            page_ghost_list.append(t.text)
            continue

        # extract the number of stars
        stars = 'unknown'
        for span in t.find_all('span', attrs={'class': 'text-gray-light'}):
            svg_star = span.find_all('svg', attrs={'class': 'octicon-star'})
            if svg_star:
                # replace ","" in e.g. "1,000" before casting to int
                stars = int(span.text.strip().replace(",", ""))
                break

        # extract the number of forks
        forks = 'unknown'
        for span in t.find_all('span', attrs={'class': 'text-gray-light'}):
            svg_fork = span.find_all('svg',
                                     attrs={'class': 'octicon-repo-forked'})
            if svg_fork:
                # replace ","" in e.g. "1,000" before casting to int
                forks = int(span.text.strip().replace(",", ""))
                break

        page_package_list.append((name, forks, stars))

    # append packages from the current page to the overall lists
    package_list = package_list + page_package_list
    ghost_list = ghost_list + page_ghost_list

    # remove any duplicates
    package_list = list(set(package_list))
    ghost_list = list(set(ghost_list))

    # terminate if no change from the prior URL
    new_len = len(package_list) + len(ghost_list)
    if new_len == prev_len:
        print("no change in package lists... stopping scraping")
        break
    prev_len = new_len

    # find the URL for the "Next" page of packages
    paginationContainers = soup.find(
        "div", {"class": "paginate-container"}).find_all('a')
    url = None
    for paginationContainer in paginationContainers:
        # Make sure we are retrieving the "Next" page and not the "Previous"
        if paginationContainer.text == "Next":
            url = paginationContainer["href"]
    if url is None:
        print("No additional next page found, ... stopping scraping")
        break

# sort by descending number of stars
# This is the first list mentioned at the top.
all_packages = sorted(package_list, key=lambda x: x[2], reverse=True)

# Create the second list by retaining only those with >= min_stars
# Note that in the package list, the tuple is:
#   (name, # of forks, # of stars)
_popular_packages = [p for p in all_packages if p[2] >= min_stars]
n_popular = len(_popular_packages)

# add a 4th term to each tuple, containing the GitHub topic list
popular_packages = []

for n, p in enumerate(_popular_packages):
    print("Retrieving topics for package {} of {}".format(n + 1, n_popular))
    repo_name = p[0]
    repo = g.get_repo(repo_name)
    topics = repo.get_topics()
    popular_packages.append(p + (topics,))

print("Applying filtering")
popular_filtered_packages = []
for p in popular_packages:
    name = p[0]
    name_lower = name.lower()
    if name in omit_list:
        continue
    topics = p[3]
    keep = False  # unless we match a term below, we will exclude the package

    # check match based on repository organization/name
    for m in repo_name_terms:
        if m in name_lower:
            keep = True
            break

    # If not already a match, search based on topic search terms
    if not keep:
        for topic in topics:
            if topic in topic_search_terms:
                keep = True
                break
    if keep:
        popular_filtered_packages.append(p)

# dump output lists to pickle
fname_base = repo_to_query.replace('/', '_')
if save_to_pickle:
    print("Writing pickle files")

    os.chdir('/media/lee8rx/data/Dropbox/Dropbox/Grants/CZI')
    with open(fname_base + '_all_packages.pickle', 'wb') as f:
        pickle.dump(all_packages, f)

    with open(fname_base + '_popular_packages.pickle', 'wb') as f:
        pickle.dump(popular_packages, f)

    with open(fname_base + '_popular_filtered_packages.pickle', 'wb') as f:
        pickle.dump(popular_filtered_packages, f)

if save_to_csv:
    print("Writing CSV files")
    df_all = pandas.DataFrame(
        all_packages,
        columns=('name', '# of forks', '# of stars')
    )
    df_all = df_all.set_index('name')
    df_all.to_csv(fname_base + '_all_dependents.csv')

    df_popular = pandas.DataFrame(
        popular_packages,
        columns=('name', '# of forks', '# of stars', 'topics')
    )
    df_popular = df_popular.set_index('name')
    df_popular.to_csv(fname_base + '_popular_dependents.csv')

    df_filtered_popular = pandas.DataFrame(
        popular_filtered_packages,
        columns=('name', '# of forks', '# of stars', 'topics')
    )
    df_filtered_popular = df_filtered_popular.set_index('name')
    df_filtered_popular.to_csv(fname_base + '_filtered_dependents.csv')

    # print(df_filtered_popular.to_markdown())
