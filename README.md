Aviation App
-------------------------------
A simple Python web application utilizing the Flask framework with Jinja templating that retrieves information related to north american airports and aviation weather.

Info
-------------------------------

Currently only retrieving weather information. ICAO code is required for querying (ex: KJFK for John F Kennedy International Airport).

Weather information is retreived in METAR format.

Web application is utilizing port 8080.

Docker Container Instructions
-------------------------------

1. Run docker-compose build command in root dir to build services
2. Create and start containers with docker-compose up -d command