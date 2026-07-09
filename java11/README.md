# Tableau REST API Sample Code -- Java 11

A self-contained Java 11 application that demonstrates the Tableau REST API:

1. Sign in (username/password or Personal Access Token)
2. Query projects
3. Publish a workbook (simple or chunked)
4. Create a group
5. Add permissions on the workbook for the group
6. Query workbooks for the current user
7. Sign out

## Prerequisites

- Java 11 or later
- Maven 3.6 or later (or use the included wrapper: `mvnw`)

## Configuration

Copy `res/config.properties.example` to `res/config.properties` and fill in your
Tableau Server or Tableau Cloud details:

```
server.host=https://your-server-or-pod.online.tableau.com
pat.token.name=<your-token-name>
pat.token.secret=<your-token-secret>
site.default.contentUrl=<your-site-content-url>
```

The `res/config.properties` file is excluded from source control. Never commit credentials.

### Authentication

The demo uses **Personal Access Tokens (PAT)** by default. Create a PAT in your
Tableau account settings (My Account Settings > Personal Access Tokens) and set
`pat.token.name` and `pat.token.secret` in `config.properties`.

To use username/password instead, uncomment the `user.admin.*` keys in
`config.properties` and update `Demo.java` to call `invokeSignIn()` instead of
`invokeSignInWithPAT()`.

### API version

`server.api.version` in `config.properties` controls the REST API version used in
URL paths. The binding classes in this project are hand-written against schema 3.29.
If you point at a different API version, the URL paths will change but the request
and response objects will still reflect the 3.29 schema -- you may need to update
the binding classes manually for compatibility.

## Building and running

```bash
# Build
./mvnw package

# Run (config loaded from res/config.properties by default)
java -jar target/tab-documentation-api-1.0-SNAPSHOT.jar

# Override config location
java -Dconfig=/path/to/config.properties -jar target/tab-documentation-api-1.0-SNAPSHOT.jar
```

## Project structure

```
java11/
  res/
    config.properties.example   -- copy to config.properties and fill in
    World Indicators-En-US.twbx -- sample workbook to publish
  src/main/
    java/com/tableausoftware/documentation/api/rest/
      Demo.java                 -- entry point and demo flow
      bindings/                 -- hand-written JAXB bindings (schema 3.29)
      util/
        RestApiUtils.java       -- HTTP client, marshalling, API methods
    resources/
      log4j2.xml                -- logging configuration
    xsd/
      ts-api_3_29.xsd           -- Tableau REST API schema v3.29
      ts-api_3_28.xsd           -- Tableau REST API schema v3.28
```

## License

MIT. See [LICENSE](LICENSE).
