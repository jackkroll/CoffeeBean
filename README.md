# CoffeeBean
Coffee Bean is a web application that allows coffee drinkers to submit a rating on how bitter or sweet their drink from a given coffee shop was. This allows users to know what to expect from a shop, and can empower them to make more informed decisions when requesting their drink to ensure it is to their liking.
# Development Guide
Make sure Python is in installed (at least 3.12)\
Install [here](https://www.python.org/downloads/)

Then you will need to install the required packages\
```pip install -r requirements.txt```

You will need a flask secret for accounts to function properly
1. Create a `.env` file in the project directory
2. Add `FLASK_SECRET="YOUR_SECRET_HERE"`, and replace YOUR_SECRET_HERE with a [secure secret](https://www.uuidgenerator.net/version4)

## FAQ
I ran the database, updated my project, and SQL throws errors
> Delete the `/instance/project.db` file, the schema was likely changed
