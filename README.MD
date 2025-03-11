# NOTES

## Docker setup
### first steps were setting up docker container. 
- Create a ```docker-composer.yml``` file
- Add a ```Dockerfile``` to both the _backend_ and _frontend_ folders
    - #### Backend
        - Requirements.txt was created to easily install the different libraries, but is also useful to manage imported libraries. Like a package.json
        - To run locally, run the command ```uvicorn main:app --host 0.0.0.0 --port 8000 --reload``` where uvicorn is fastapi, running the main.py app, locally with port 8000, with the --reload tag
        - copy all the files also with the . .  command
    - #### Frontend
        - 