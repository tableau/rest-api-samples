# Tableau Webhooks Assets

This repo contains Postman collection content for accessing Webhooks methods in the Tableau REST API.

> NOTE: See **[tableau-postman](https://github.com/tableau/tableau-postman/blob/main/README.md)** for a comprehensive Postman collection for the entire Tableau REST API. 

To learn more about the Webhooks feature, see the Tableau Webhooks documentation:

- [Developer guide](https://help.tableau.com/current/developer/webhooks/en-us/)

- [REST API Endpoints for Webhooks](https://help.tableau.com/v2020.4/api/rest_api/en-us/REST/rest_api_ref_webhooks.htm) 

To use the Postman collection, you will need to begin with some initial setup

1. A Tableau site that you have administrator access to
2. The id of that site - you can use the [REST API](https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_get_started_tutorial_part_1.htm) or the [Tableau Server Client](https://tableau.github.io/server-client-python/) to fetch this
3. A PAT for the site to log in
4. A webhook destination - this must be a https URL. If you don't have any server where you can read the request as it arrives, there are many public apps that will work, including 
- https://webhook.site
- a project on Glitch (see [existing examples(https://glitch.com/@tableau/webhooks)]
- https://postman-echo.com
- https://requestbin.com/
5. Choose an [event](https://help.tableau.com/current/developer/webhooks/en-us/docs/webhooks-events-payload.html#trigger-events) that will trigger your webhook 
6. And finally, a fun name for your new webhook! 
