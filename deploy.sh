#!/bin/sh

echo -e "\033[0;32mDeploying updates to GitHub...\033[0m"

# Build the project. 
hugo -t liquorice_mod

# Add changes to git.
git add -A

# Commit changes.
msg="rebuilding site `date`"
if [ $# -eq 1 ]
      then msg="$1"
fi
git commit -m "$msg"

# Push source and build repos.
git push origin hugo
git subtree push --prefix=public git@github.com:Dhole/dhole.github.io.git master
