# Debugging

**Strings to look for in logs**

```
2022-03-07 21:15:25 [crawlallcommand] INFO: crawlallcommand >> STARTED crawling news (2021-03-07 to 2021-03-08)
2022-03-07 21:17:46 [crawlallcommand] INFO: crawlallcommand >> DONE crawling news (2021-03-07 to 2021-03-08)
```


## Cloud Run

* Deploying to Cloud Run with a custom service account failed with iam.serviceaccounts.actAs error
  - grant the users a role that includes the iam.serviceAccounts.actAs permission, like the Service Account User role (roles/iam.serviceAccountUser). 