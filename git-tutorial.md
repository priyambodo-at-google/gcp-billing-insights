
# How to Contribute to this Project

Get the Clone URL from the repository: [https://github.com/doddipriyambodo/doddipriyambodo-github-private-repo.git ](https://github.com/priyambodo-at-google/gcp-billing-insights.git)

## Preparation and Configuration for MAC user

Check whether GIT already installed in MAC.
```
$ brew install git
$ git --version
$ which git
```
Configure git for your account:(They will get added to your `~/.gitconfig` file.)
```
$ git config --global user.name "Doddi Priyambodo"
$ git config --global user.email "doddi@bicarait.com"
```
To push code to your GitHub repositories, we're going to use the recommended HTTPS method (versus SSH). So you don't have to type your username and password everytime, let's enable Git password caching:

```
$ git credential-osxkeychain
$ git config --global credential.helper osxkeychain
$ git config --global core.autocrlf input
$ git config --global core.safecrlf true
```

Setup the ignore file followed by running the command to ignore it:
```
$ curl https://raw.githubusercontent.com/github/gitignore/master/Global/macOS.gitignore -o ~/.gitignore
$ git config --global core.excludesfile ~/.gitignore
```

Check the configuration files:
```
$ cat ~/.gitignore
$ cat ~/.gitconfig
```

## GIT Main Implementation

Now, create the GIT repo in local Mac
```
$ git init 
$ git remote add origin https://github.com/priyambodo-at-google/gcp-billing-insights.git
$ touch doddi.priyambodo
$ git add .
$ git status
$ git commit -m "My First Commit"
$ git tag -a v0.1 -m "My First Comment"
$ git status
$ git log 
$ git pull origin main --rebase
$ git push origin main 
```

If you need to cancel the last commit files:
```
$ git filter-branch --force --index-filter "git rm --cached --ignore-unmatch bicarait-tutorial-livestreaming/obs-mac-23.2.1-installer.pkg" --prune-empty --tag-name-filter cat -- --all
$ git commit -m "delete large files"
$ git push origin main --force
```

## GIT Optional Implementation
```
$ git log --pretty=format:'%h %ad | %s%d [%an]' --graph --date=short
$ git checkout <hash>
$ git checkout -b development
$ git branch
$ git checkout main
$ git tag v1
$ git checkout v1
$ git merge main
$ git rebase main
```

## GIT Remote Implementation
```
$ git remote
$ git remote show origin
$ git branch -a
$ git fetch
$ git merge origin/main
$ git log
```
```
$ git pull
$ git push
$ git clone
```


<!--stackedit_data:
eyJoaXN0b3J5IjpbLTM3NTIxNDkzLC0yMDgxNzAxMjgyXX0=
-->
