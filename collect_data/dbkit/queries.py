API_ORGS_TABLE_INSERT_SQL = """
INSERT INTO raw_data.api_orgs
(orgs_id, node_id, name, description, company, blog, location, email, twitter_username,
followers, following, is_verified, has_organization_projects, has_repository_projects,
public_repos, public_gists, html_url, avatar_url, type, created_at, updated_at, called_at)
VALUES %s;
"""

API_LICENSES_TABLE_INSERT_SQL = """
INSERT INTO raw_data.api_licenses
(key, name, spdx_id, node_id, url, body, permissions, conditions, limitations, called_at)
VALUES %s;
"""

API_REPOS_LICENSES_TABLE_INSERT_SQL = """
INSERT INTO raw_data.api_repos_licenses
(repo_full_name, license_key, sha, html_url, download_url, git_url, content, called_at)
VALUES %s;
"""

API_REPOS_SELECT_FULL_NAME_SQL = """
SELECT DISTINCT full_name FROM raw_data.api_repos;
"""


API_REPOS_ISSUES_TABLE_INSERT_SQL = """
INSERT INTO raw_data.api_repos_issues
(repository_url, labels_url, comments_url, events_url, html_url, issues_id, node_id, number, title, state, locked,
comments, created_at, updated_at, author_association, body, timeline_url, state_reason, login_user, called_at,
repo_full_name)
VALUES %s;
"""


API_REPOS_COMMITS_TABLE_INSERT_SQL = """
INSERT INTO raw_data.api_repos_commits
(sha, node_id, commit_author_name, commit_author_email, commit_author_date,
commit_committer_name, commit_committer_email, commit_committer_date,
commit_message, author_login, author_id, author_node_id, author_site_admin,
committer_login, committer_id, committer_node_id, committer_site_admin,
repo_full_name, called_at)
VALUES %s;
"""

API_REPOS_TABLE_INSERT_SQL = """
INSERT INTO raw_data.api_repos
(repo_id, node_id, owner_id, name, full_name, description, private, html_url,
url, homepage, fork, created_at, updated_at, pushed_at, called_at, size, stargazers_count, forks_count,
open_issues_count, language, archived, disabled, license, allow_forking)
VALUES %s;
"""

API_REPOS_LANGUAGES_TABLE_INSERT_SQL = """
INSERT INTO raw_data.api_repos_languages (repo_full_name, language, usage_count, called_at)
VALUES %s;
"""

ELT_LICENSES_PER_REPOS_TABLE_CREATE_SQL = """
DROP TABLE IF EXISTS analytics.licenses_per_repos;
CREATE TABLE analytics.licenses_per_repos (
    repo VARCHAR(255),
    organization VARCHAR(255),
    name VARCHAR(255),
    spdx_id VARCHAR(40)
);
"""

ELT_LICENSES_PER_REPOS_TABLE_INSERT_SQL = """
INSERT INTO analytics.licenses_per_repos (repo, organization, name, spdx_id)
SELECT
  DISTINCT repos.full_name as repo,
  orgs.name as organization,
  ls.name,
  ls.spdx_id
FROM raw_data.api_repos repos
JOIN (
  SELECT orgs_id, name FROM raw_data.api_orgs WHERE called_at = (SELECT called_at FROM raw_data.api_orgs ORDER BY 1 DESC LIMIT 1)
) orgs ON repos.owner_id = orgs.orgs_id
JOIN (
  SELECT repo_full_name, license_key FROM raw_data.api_repos_licenses WHERE called_at = (SELECT called_at FROM raw_data.api_repos_licenses ORDER BY 1 DESC LIMIT 1)
) rl ON repos.full_name = rl.repo_full_name
JOIN (
  SELECT key, name, spdx_id FROM raw_data.api_licenses WHERE called_at = (SELECT called_at FROM raw_data.api_licenses ORDER BY 1 DESC LIMIT 1)
) ls ON ls.key = rl.license_key
WHERE repos.called_at = (SELECT called_at FROM raw_data.api_repos ORDER BY 1 DESC LIMIT 1)
ORDER BY 2;
"""

ELT_RECENT_REPOS_TABLE_CREATE_SQL = """
DROP TABLE IF EXISTS analytics.recent_repos;
CREATE TABLE analytics.recent_repos (
    repo_name VARCHAR(255),
    organization VARCHAR(255),
    stars INT,
    language VARCHAR(255),
    description TEXT
);
"""

ELT_RECENT_REPOS_TABLE_INSESRT_SQL = """
WITH tmp_recent_repos AS (
    SELECT *
    FROM (
        SELECT
            org.name as organization,
            repo.name as repo_name,
            stargazers_count as stars,
            repo.description as description,
            language,
            repo.called_at,
            ROW_NUMBER() OVER (PARTITION BY repo.name ORDER BY repo.called_at DESC) AS time_rank
        FROM raw_data.api_repos repo
        JOIN raw_data.api_orgs org
        ON repo.owner_id = org.orgs_id
    ) AS sub
    WHERE time_rank = 1
)
INSERT INTO analytics.recent_repos (repo_name, organization, stars, language, description)
SELECT
    repo_name,
    organization,
    stars,
    language,
    description
FROM tmp_recent_repos;
"""

ELT_LANGUAGES_PER_REPOS_TABLE_CREATE_SQL = """
DROP TABLE IF EXISTS analytics.languages_per_repos;
CREATE TABLE analytics.languages_per_repos (
    repo_name VARCHAR(255),
    organization VARCHAR(255),
    language VARCHAR(255),
    usage_count INT
);
"""

ELT_LANGUAGES_PER_REPOS_TABLE_INSERT_SQL = """
INSERT INTO analytics.languages_per_repos (repo_name, organization, language, usage_count)
SELECT
    DISTINCT SPLIT_PART(lang.repo_full_name, '/', 2) as repo_name,
    org.name as organization,
    lang.language,
    usage_count
FROM raw_data.api_repos_languages lang
JOIN raw_data.api_repos repos ON lang.repo_full_name = repos.full_name
JOIN raw_data.api_orgs org ON repos.owner_id = org.orgs_id
WHERE lang.called_at = (SELECT called_at FROM raw_data.api_repos_languages ORDER BY 1 DESC LIMIT 1)
"""

ELT_REPOS_COMMITS_PER_PER_REPOS_AND_SHA_TABLE_CREATE_SQL = """
DROP TABLE IF EXISTS analytics.commits_per_sha;
CREATE TABLE analytics.commits_per_sha (
	sha	varchar(255),
	commit_author_name varchar(70),
	commit_author_date	timestamp,
	commit_message text,
	repo_full_name varchar(255),
	called_at timestamp
);
"""

ELT_TEMP_REPOS_COMMITS_PER_REPOS_AND_SHA_TABLE_CREATE_SQL = """
CREATE TEMP TABLE t_commits_per_sha AS SELECT * FROM raw_data.api_repos_commits;
"""

ELT_COMMITS_PER_REPOS_AND_SHA_TABLE_INCREMENTAL_UPDATE_SQL = """
INSERT INTO analytics.commits_per_sha
SELECT sha, commit_author_name, commit_author_date, commit_message, repo_full_name, called_at
FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY sha ORDER BY called_at DESC) seq
    FROM t_commits_per_sha
) subquery_alias
WHERE seq = 1;
"""

ELT_REPOS_CONTRIBUTORS_COUNT_PER_REPOS_AND_DAY_TABLE_CREATE_SQL = """
DROP TABLE IF EXISTS analytics.contributors_per_day;
CREATE TABLE analytics.contributors_per_day (
    commit_date DATE,
    commit_author_name VARCHAR(70),
    repo_full_name VARCHAR(255)
);
"""

ELT_REPOS_CONTRIBUTORS_COUNT_PER_REPOS_AND_DAY_TABLE_INSERT_SQL = """
INSERT INTO analytics.contributors_per_day (commit_date, commit_author_name, repo_full_name)
SELECT
    DATE(commit_author_date) AS commit_date,
    commit_author_name,
    repo_full_name
FROM
    raw_data.api_repos_commits
WHERE
    commit_author_date >= now() - INTERVAL '31 days' AND
    commit_author_date < CURRENT_DATE - INTERVAL '1 day' + INTERVAL '1 day' - INTERVAL '1 microsecond'
GROUP BY
    DATE(commit_author_date),
    repo_full_name,
    commit_author_name
ORDER BY
    commit_date;
"""
