# CoffeeBean

# Development Guide
Make sure Python is in installed (anything modern should be fine)\
Install [here](https://www.python.org/downloads/)

Then you will need to install the required packages\
```pip install -r requirements.txt```

You will need a flask secret for accounts to function properly
1. Create a `.env` file in the project directory
2. Add `FLASK_SECRET=YOUR_SECRET_HERE`, and replace YOUR_SECRET_HERE with a [secure secret](https://www.uuidgenerator.net/version4)

## FAQ
I ran the database, updated my project, and SQL throws errors
> Delete the `/instance/project.db` file, the schema was likely changed